import math
import sys
import time
import os

import numpy as np
import pygame
import gymnasium
import stable_baselines3 as sb
import matplotlib
import matplotlib.pyplot as plt
import torch.cuda
import torch as th

import pandas as pd

# TODO threading for windows - so they don't crash
import threading

from FactoryObjects.Factory import Factory
from FactoryObjects.Machine import Machine  # needed for reward function
import MachineLearning.RainbowNetwork
from MachineLearning.RainbowNextVersion import RainbowLearning

is_ipython = 'inline' in matplotlib.get_backend()
if is_ipython:
    from IPython import display


class CustomEnvironment(gymnasium.Env):
    def __init__(self, render=False, variation_training=False, var_save_path=None, var_save_name=None, timestep=1.0,
                 adjust_ep_len=False, reward_type=1, episode_length=2048, rainbow_algo=False, reward_fac=1):
        super(CustomEnvironment, self).__init__()
        self.agv_positioning = None
        self.coupling_command = None
        self.agv_couple_count = None
        self.coupling_master = None
        self.factory = Factory()
        self.factory.time_step = timestep
        self.step_counter = 0
        self.last_end_product_count = 0
        self.last_critical_conditions = 0
        self.factory.create_temp_factory_machines()
        # self.time_step = 0.1
        self.time_step = timestep  # should be the same for AGV.move_state(self) "distance if" (AGV have a speed of 1)
        # self.sleep_time = 0.0001
        self.sleep_time = 0.00001

        self.end_product_count = []  # only used for plotting
        self.reward_history = []  # only used for plotting
        plt.ion()

        self.n_agv = len(self.factory.agvs)
        self.n_agv_commands = 5

        self.action_space = gymnasium.spaces.Discrete(n=self.n_agv * self.n_agv_commands)
        self.observation_space = gymnasium.spaces.Box(low=0.0, high=1.0,
                                                      shape=(self.n_agv * (2 + len(self.factory.warehouses) + len(
                                                          self.factory.machines) + 1) +
                                                             len(self.factory.warehouses) * 2 + len(
                                                          self.factory.machines) * 3,), dtype=float)

        self.pixel_size = 50
        self.height = self.factory.length
        self.width = self.factory.width
        self.reference_size = self.factory.cell_size * 1000
        self.screen = None

        self.render = render
        if render:
            pygame.init()
            self.screen = pygame.display.set_mode((self.width * self.pixel_size, self.height * self.pixel_size))
            pygame.display.set_caption('Color Data Display')

        self.GoodAGVs = []  # AGVs that are in a "good" position will be in this list (for reward function)
        self.step_start_time = time.time()
        self.coupling_at = []
        self.coupling_at.extend([False] * self.n_agv_commands)
        self.agv_couple_count_at = []
        self.agv_couple_count_at.extend([0] * self.n_agv_commands)
        self.coupling_master_at = []
        self.coupling_master_at.extend([None] * self.n_agv_commands)
        self.agv_positioning_at = [[1 for _ in range(2)] for _ in range(self.n_agv_commands)]

        self.render_delay = 0
        self.render_window = 0
        self.good_consecutive_runs = 0
        self.not_utilizing_agv_penalty = False

        self.last_episode = 0
        self.show_result = False
        self.plot_update = False

        # plot_thread = threading.Thread(target=self.plot_threading)
        # plot_thread.start()

        self.variation_training = variation_training
        self.var_save_path = var_save_path
        self.var_save_name = var_save_name
        self.machine_status_history = [[] for _ in range(3)]
        self.agv_free_history = [[] for _ in range(6)]
        self.last_machine_priority = [[4, 4] for _ in range(3)]

        self.adjust_ep_len = adjust_ep_len
        self.restart_logger = []
        self.reward_type = reward_type
        self.episode_length = episode_length
        self.running_rainbow = rainbow_algo
        self.reward_factor = reward_fac

    def plot_threading(self):
        plt.ion()  # Turn on interactive mode
        plt.show()
        # Keep the plot open and update if needed
        while True:
            plt.pause(0.1)  # Pause to allow interaction and updating
            if self.plot_update:
                plt.figure(self.render_window)
                if self.show_result:
                    plt.clf()
                    plt.title('Result')
                else:
                    plt.clf()
                    plt.title('Running...')
                plt.xlabel('Time in ' + str(self.time_step) + 's Steps')
                plt.ylabel('Products')
                plt.plot(self.end_product_count, label='Finished Products', color='b', linewidth=3, linestyle=':')
                plt.plot(self.reward_history, label='Reward', color='g', linewidth=2)
                plt.legend()
                plt.pause(0.01)  # pause required for constructor
                if is_ipython:
                    if not self.show_result:
                        display.display(plt.gcf())
                        display.clear_output(wait=True)
                    else:
                        display.display(plt.gcf())
                self.plot_update = False

    def reset(self, seed=None, options=None):
        self.factory.reset()
        self.step_counter = 0
        self.last_end_product_count = 0
        self.last_critical_conditions = 0

        self.coupling_command = None
        self.GoodAGVs.clear()

        self.coupling_at.clear()
        self.coupling_at.extend([False] * self.n_agv_commands)
        self.agv_couple_count_at.clear()
        self.agv_couple_count_at.extend([0] * self.n_agv_commands)
        self.coupling_master_at.clear()
        self.coupling_master_at.extend([None] * self.n_agv_commands)
        self.agv_positioning_at = [[1 for _ in range(2)] for _ in range(self.n_agv_commands)]

        index = 0
        for machine in self.factory.machines:
            input_priority, output_priority = machine.get_buffer_status()
            self.last_machine_priority[index][0] = input_priority
            self.last_machine_priority[index][1] = output_priority
            index += 1

        if len(self.restart_logger) > 0:
            self.restart_logger.pop()
            self.restart_logger.append(True)

        return self._create_observation(), {'info': "Nothing"}

    def step(self, action):
        self.step_counter += 1
        # self._block_until_synchronized()  # may be used when threading agvs
        self._perform_action(action)
        truncated = False
        # TODO: According to https://stable-baselines3.readthedocs.io/en/master/guide/rl_tips.html
        terminated = False
        # time.sleep(0.001)       # TODO TODO Action Update in AGV needs to be ensured before simulating factory
        self._simulate_factory_objects()
        # !!! Factory simulation has to be done before processing step information (especially reward and observation)
        self._block_until_synchronized()

        reward = self._get_reward()
        self._collect_train_data(reward)
        # plot training within an episode

        if self.step_counter % math.inf == 0:  # math.inf => (almost) never triggered   #512 is reasonable for observation
            if self.step_counter != 0:
                # self.render_window += 1
                self._plot_training(window_number=str(self.render_window))
                plt.show()
                time.sleep(0.025)
                print(reward)



        # display env continuously
        if self.render:
            self.display_colors()
            time.sleep(0.0125)  # necessary  delay to regulate run speed

        # used for SB-learning (e.g. PPO)
        if not self.running_rainbow:
            truncated = self.sb3_step_completion()
        # "!truncated is used when "time limit" is hit AND time is not part of the observation space, else terminated!"

        return self._create_observation(), reward, terminated, truncated, {'info': "Nothing"}

    def sb3_step_completion(self):
        truncated = False
        divisor = self.time_step if self.adjust_ep_len else 1
        if self.step_counter > ((self.episode_length/divisor)-1):  # for smaller time steps 10* to 20*
            # for special condition display options
            if self.last_end_product_count > math.inf:
                self.conditional_display(self.render_delay)  # render_delay indicates episode (count)
            self.render_delay += 1
            # plot training at the end of every n episodes
            if self.render_delay % math.inf == 0 and self.step_counter != 0:  # math.inf => (almost) never triggered
                # only works if thread is started in the Environments __init__
                #self.plot_update = True     # TODO Slows down learning significantly
                self._plot_training(window_number=str(self.render_window))
                plt.show()
                time.sleep(0.1)
            # create a new render window for the results so-and-so often
            if self.render_delay % math.inf == 0 and self.render_delay != 0:  # math.inf => never triggered
                # self.render_window += 1
                self.end_product_count = []  # only used for plotting
                self.reward_history = []  # only used for plotting
            # regular reset according to SB3 Website: Custom Environments
            truncated = True
            self.reset()  # referring to SB3 Website: Custom Environments
            self.step_counter = 0  # UNNECESSARY HERE (ALREADY IN RESET)
            # self.display_colors()         # visual to ensure factory reset properly
        return truncated

    def conditional_display(self, episode):
        if episode == self.last_episode + 1:
            self.good_consecutive_runs += 1
            if self.good_consecutive_runs >= 5:
                self.display_colors()
                time.sleep(0.1)
        else:
            self.good_consecutive_runs = 0
        self.last_episode = episode

    def close(self):
        self.factory.shout_down()
        # self._plot_training(True, window_number='Final')
        # plt.ioff()
        # plt.show()
        if self.variation_training and self.reward_history:
            np_ar_end_prod = np.array(self.end_product_count)
            np_ar_end_prod_name = str(self.var_save_name) + "_end_product_counts"
            file_path = os.path.join(self.var_save_path, np_ar_end_prod_name)
            np.save(file_path, np_ar_end_prod)
            print("Reward history saved in: " + self.var_save_path)
            np_ar_rew_hist = np.array(self.reward_history)
            np_ar_rew_hist_name = str(self.var_save_name) + "_reward_history"
            file_path = os.path.join(self.var_save_path, np_ar_rew_hist_name)
            np.save(file_path, np_ar_rew_hist)
            np_ar_mach_hist = np.array(self.machine_status_history)
            np_ar_mach_hist_name = str(self.var_save_name) + "_machine_status_history"
            file_path = os.path.join(self.var_save_path, np_ar_mach_hist_name)
            np.save(file_path, np_ar_mach_hist)
            np_ar_agv_free_hist = np.array(self.agv_free_history)
            np_ar_agv_free_hist_name = str(self.var_save_name) + "_agv_free_history"
            file_path = os.path.join(self.var_save_path, np_ar_agv_free_hist_name)
            np.save(file_path, np_ar_agv_free_hist)
            np_ar_rest_hist = np.array(self.restart_logger)
            np_ar_rest_hist_name = str(self.var_save_name) + "_restart_history"
            file_path = os.path.join(self.var_save_path, np_ar_rest_hist_name)
            np.save(file_path, np_ar_rest_hist)

    def create_obs(self):  # temporary solution to get access
        return self._create_observation()

    def _create_observation(self):
        observation = []
        for agv in self.factory.agvs:
            if agv.is_free:  # free status
                observation.append(1.0)
            else:
                observation.append(0.0)
            if agv.loaded_product is None:  # load status
                observation.append(1.0)
            else:
                observation.append(0.0)
            observation += self._get_agv_distances_normal(agv)  # distances
            observation.append(agv.task_number / (self.n_agv_commands - 1))  # AGVs' task
        for warehouse in self.factory.warehouses:
            if len(warehouse.buffer_output_load) > 0:
                observation.append(1.0)
            else:
                observation.append(0.0)
            observation.append(warehouse.get_production_rest_time_percent())
        for machine in self.factory.machines:
            input_priority, output_priority = machine.get_buffer_status()
            observation.append(input_priority * 0.25)
            observation.append(output_priority * 0.25)
            observation.append(machine.get_production_rest_time_percent())
        return observation

    def _get_agv_distances_normal(self, agv):
        agv_machines_distances_normal = []
        pos_agv = agv.get_middle_position()
        for warehouse in self.factory.warehouses:
            pos_warehouse = warehouse.get_middle_position()
            agv_machines_distances_normal.append(self._calculate_agv_distances(pos_agv, pos_warehouse))

        for machine in self.factory.machines:
            pos_machine = machine.get_middle_position()
            agv_machines_distances_normal.append(self._calculate_agv_distances(pos_agv, pos_machine))

        max_distance = max(agv_machines_distances_normal)
        for i in range(len(agv_machines_distances_normal)):
            agv_machines_distances_normal[i] = agv_machines_distances_normal[i] / max_distance
        return agv_machines_distances_normal

    @staticmethod
    def _calculate_agv_distances(pos_a, pos_b):
        return math.sqrt(math.pow(pos_a[0] - pos_b[0], 2) + math.pow(pos_a[1] - pos_b[1], 2))

    def _perform_action(self, action_numpy):
        if isinstance(action_numpy, np.ndarray):
            action = action_numpy.item()
        else:
            action = action_numpy
        # command_index = int(action % self.n_agv_commands)  # the 1d action array is now used as a pseudo 2d array
        # agv_index = int(action / self.n_agv_commands)
        # flipped interpretation to make right decision easier - better transport with a not perfect agv than not at all
        command_index = int(action / self.n_agv)  # the 1d action array is now used as a pseudo 2d array
        agv_index = int(action % self.n_agv)

        # temporary enablement to send all stuck agv to the temp storage (no longer a timer runs down)
        if command_index == 0:
            for agv in self.factory.agvs:
                agv.unload_stucked_agvs = True
        else:
            for agv in self.factory.agvs:
                agv.unload_stucked_agvs = False

        if command_index == 1:
            self.environment_set_action(self.factory.agvs[agv_index], self.factory.warehouses[0],
                                        self.factory.machines[0], command_index)
        elif command_index == 2:
            self.environment_set_action(self.factory.agvs[agv_index], self.factory.machines[0],
                                        self.factory.machines[1], command_index)
        elif command_index == 3:
            self.environment_set_action(self.factory.agvs[agv_index], self.factory.machines[1],
                                        self.factory.machines[2], command_index)
        elif command_index == 4:
            self.environment_set_action(self.factory.agvs[agv_index], self.factory.machines[2],
                                        self.factory.warehouses[0], command_index)

        self.eliminate_two_searching_masters()  # ALTERNATIVE A LIFO SYSTEM FOR EVERY AGV POSITION
        # elif action == 5:
        #    self.unload_agv(self.factory.agvs[0], self.factory.warehouses[0])

    # def environment_set_action(agv, loading, unloading):
    #    if agv.is_free:
    #        product = unloading.input_products[0]
    #        if loading.has_product(product):
    #            agv.deliver(loading, unloading, product)

    def environment_set_action(self, agv, output_object, input_object,
                               command_index):  # caution: self.coup... is a StableBas.Learn.Test variable
        if not agv.is_free:  # TODO !perhaps! NN should be able to always change targets unless agv is loaded
            #  => add function/-s (especially regarding coupling)
            return

        # TODO Does this work when threading (in current implementation reassignment has to be prevented)
        if agv.task_number == command_index:
            return

        # print(self.agv_couple_count_at[1], self.agv_couple_count_at[2])
        # print(str(agv)+ " " + str(command_index)) # useful for debugging
        # process all actions that don't require coupling
        if command_index == 3 or command_index == 4:
            self.deliver(agv, command_index, input_object, output_object)
        # process actions that require coupling
        else:
            first = True
            for AGV in self.factory.agvs:
                if AGV.task_number == command_index and AGV != agv:  # check whether different agv/s is/are first (/already assigned)
                    try:  # since AGVs are running in a thread an update might rarely cause an AttributeError
                        # (coupling_master does not exist) TODO should no longer be an issue
                        if AGV.coupling_master == AGV:  # safe some computing power
                            if not AGV.coupling_master.will_coupling_be_complete():
                                # condition triggered when a master agv still needs slaves
                                first = False
                    except:
                        pass

            if first:
                self.deliver(agv, command_index, input_object, output_object)
            else:
                if not self.agv_couple_count_at[command_index] > 0:
                    print("WFF")
                self._couple(agv, output_object, command_index)

    def deliver(self, agv, command_index, input_object, output_object):  # added _at[command_index] to all self.(...)
        # TO-DO: (eventually) unsophisticated implementation when there are more input products (with different origins)
        for product in input_object.input_products:  # required to get product properties
            if output_object is not None:
                # implemented for masters that move away
                if agv.coupling_master == agv:
                    self.replace_master(agv)
                    self.agv_couple_count_at[agv.task_number] += 1
                    # CAUTION! Such operations have to be processed before agv.task_number = command_index
                # implemented to hinder coupled master to deliver - the leaving agv will cause a reset of the coupling process
                if agv.coupling_master and agv.coupling_master != agv:  # masters got handled with above
                    if agv.coupling_master.is_coupling_complete():  # masters' coupling was completed (a slave will be removed now though)
                        agv.coupling_master.command = 'coupling'  # resetting master to coupling (waiting for slaves)
                        agv.coupling_master.status = 'wait_for_coupling'
                    # implemented for agvs that are slaves of a waiting coupling master
                    '''if agv.coupling_master == self.coupling_master_at[agv.coupling_master.task_number]:  # if not there will be two masters and count_at will be figured out later
                                        self.agv_couple_count_at[agv.coupling_master.task_number] += 1'''
                    self.coupling_master_at[agv.coupling_master.task_number] = agv.coupling_master
                    self.agv_couple_count_at[
                        agv.coupling_master.task_number] += 1  # inconveniences will be resolved later anyways
                agv.free_from_coupling()  # TODO it may happen that when several masters and their slaves leave a position the agv_couple_count_at become unsensible high
                #  however, this isn't a significant issue (as soon as an agv gets assigned to the position as a master or several masters look for slaves the count will be reset to a sophisticated ammount)
                agv.task_number = command_index
                self.agv_positioning_at[command_index] = self.factory.get_agv_needed_for_product(product, agv)
                if self.agv_positioning_at[command_index][0] > 1 or self.agv_positioning_at[command_index][
                    1] > 1:  # triggers if bigger than [1,1] (size of a solo transport)
                    self.coupling_master_at[command_index] = agv
                    self.agv_couple_count_at[command_index] = self.agv_positioning_at[command_index][0] * \
                                                              self.agv_positioning_at[command_index][1] - 1
                    self.coupling_at[command_index] = True
                    agv.coupling(agv, [0, 0], self.agv_couple_count_at[command_index], output_object, input_object,
                                 product, self.agv_positioning_at[command_index])
                else:
                    agv.deliver(output_object, input_object, product)

    def _couple(self, agv, output_object, command_index):
        if self.agv_couple_count_at[command_index] > 0:
            # if self.master_prevention(agv):
            #     return
            # implemented for masters that move away (become no master)
            if agv.coupling_master == agv:
                self.replace_master(agv)
                self.agv_couple_count_at[agv.task_number] += 1
                # CAUTION! Such operations have to be processed before agv.task_number = command_index
            # implemented to hinder coupled master to deliver - the leaving agv will cause a reset of the coupling process
            if agv.coupling_master and agv.coupling_master != agv:  # masters got handled with above
                if agv.coupling_master.is_coupling_complete():  # masters' coupling was completed (a slave will be removed now though)
                    agv.coupling_master.command = 'coupling'  # resetting master to coupling (waiting for slaves)
                    agv.coupling_master.status = 'wait_for_coupling'
                # implemented for agvs that are slaves of a waiting coupling master
                '''if agv.coupling_master == self.coupling_master_at[agv.coupling_master.task_number]:  # if not there will be two masters and count_at will be figured out later
                                    self.agv_couple_count_at[agv.coupling_master.task_number] += 1'''
                self.coupling_master_at[agv.coupling_master.task_number] = agv.coupling_master
                self.agv_couple_count_at[
                    agv.coupling_master.task_number] += 1  # inconveniences will be resolved later anyways
            agv.free_from_coupling()
            agv.task_number = command_index
            count = 0
            pos = [0, 0]
            for length in range(self.agv_positioning_at[command_index][1]):
                for width in range(self.agv_positioning_at[command_index][0]):
                    '''
                    if count == self.agv_positioning_at[command_index][0] * self.agv_positioning_at[command_index][
                        1] - self.agv_couple_count_at[command_index]:
                        pos = [width, length]
                    count += 1
                    '''
                    # check whether spot is occupied
                    occ = False
                    for AGV in self.factory.agvs:
                        if AGV.coupling_master == self.coupling_master_at[command_index]:
                            if AGV.coupling_formation_position == [width, length]:
                                occ = True
                                break
                    if not occ:
                        pos = [width, length]
                        break
                if pos != [0, 0]:
                    break
            agv.coupling(self.coupling_master_at[command_index], pos, output_object=output_object)
            self.agv_couple_count_at[command_index] -= 1
            return
        else:  # safeguard - todelete
            print("MISTAKE")
            self.coupling_at[command_index] = False

    def master_prevention(self, agv):  # artefact function - todelete
        if agv.coupling_master == agv:
            # return True
            # reduce the incapability by those that have no slaves
            for AGV in self.factory.agvs:  # check for alternative agv to be first
                if AGV.coupling_master == agv and AGV != agv:
                    return True
        return False

    def replace_master(self, old_master):
        # rather slaves that are already at the output should become master
        for AGV in self.factory.agvs:
            if AGV.coupling_master == old_master and AGV != old_master:
                if AGV.command == 'follow_master':
                    self.assign_new_master(old_master, AGV)
                    return
        for AGV in self.factory.agvs:
            if AGV.coupling_master == old_master and AGV != old_master:
                if AGV.status == 'master_slave_decision':
                    self.assign_new_master(old_master, AGV)
                    return
        for AGV in self.factory.agvs:
            if AGV.coupling_master == old_master and AGV != old_master:
                if AGV.status == 'move_to_coupling_position':  # (most likely) technically this condition is not needed
                    self.assign_new_master(old_master, AGV)
                    return
        self.coupling_master_at[old_master.task_number] = None  # if no slaves are found
        self.coupling_at[old_master.task_number] = False
        return

    def assign_new_master(self, old_master, new_master):
        slave_list = [agv for agv in self.factory.agvs if agv.coupling_master == old_master and agv != old_master]
        for slave in slave_list:
            slave.coupling_master = new_master  # assign AGV as new master
        new_master.coupling(new_master, [0, 0], old_master.agv_couple_count, old_master.output_object,
                            old_master.input_object, old_master.target_product,
                            self.agv_positioning_at[old_master.task_number])
        new_master.status = 'move_to_coupling_position'
        new_master.move_target = old_master.move_target
        self.coupling_master_at[old_master.task_number] = new_master
        # old_master.coupling_master = new_master     # necessary for some operation - will be shortly anyways

    def eliminate_two_searching_masters(self):
        masters = []
        master_tasks = []
        # catch all masters
        for agv in self.factory.agvs:
            if agv.coupling_master == agv:
                masters.append(agv)
                master_tasks.append(agv.task_number)
        for i in range(1, self.n_agv_commands):
            if master_tasks.count(i) > 1:  # true if there are several masters with the same task
                masters_need_slaves = []
                for task, master_agv in zip(master_tasks, masters):
                    if task == i:
                        if not master_agv.will_coupling_be_complete():
                            masters_need_slaves.append(master_agv)
                            if len(masters_need_slaves) > 1:
                                if len(masters_need_slaves) > 2:
                                    print("MISTAKE: CHECK OUT eliminate_tow_searching_masters FUNCTION")
                                # find master with more slaves
                                m1_slaves = []
                                m2_slaves = []
                                for agv in self.factory.agvs:
                                    if agv.coupling_master == masters_need_slaves[0]:
                                        if agv != agv.coupling_master:
                                            m1_slaves.append(agv)
                                    elif agv.coupling_master == masters_need_slaves[1]:
                                        if agv != agv.coupling_master:
                                            m2_slaves.append(agv)
                                if len(m2_slaves) > 0 or len(m1_slaves) > 0:  # when at least one master has a slave
                                    if len(m2_slaves) > len(m1_slaves):
                                        # assign a slave of m1 to m2
                                        if len(m1_slaves) > 0:
                                            m1_slaves[-1].free_from_coupling()
                                            m1_slaves[-1].task_number = masters_need_slaves[1].task_number
                                            self._couple(m1_slaves[-1], masters_need_slaves[1].output_object,
                                                         masters_need_slaves[1].task_number)
                                            if masters_need_slaves[
                                                1].will_coupling_be_complete():  # ensure everything worked and sort out env-variables
                                                self.agv_couple_count_at[i] = masters_need_slaves[
                                                                                  0].agv_couple_count - len(
                                                    m1_slaves) + 1  # +1 for the removed slave
                                                self.coupling_master_at[i] = masters_need_slaves[0]
                                            else:
                                                print(
                                                    "MISTAKE: THERE WAS A MASTER ALTHOUGH A DIFFERENT MASTER WITH SAME TASK WAITED FOR MORE THAN ONE SLAVE TO BE ASSIGNED @1")
                                        else:
                                            self.master_becomes_slave(masters_need_slaves[0], masters_need_slaves[1], i,
                                                                      len(m2_slaves))
                                    else:
                                        # assign a slave of m2 to m1
                                        if len(m2_slaves) > 0:
                                            m2_slaves[-1].free_from_coupling()
                                            m2_slaves[-1].task_number = masters_need_slaves[0].task_number
                                            self._couple(m2_slaves[-1], masters_need_slaves[0].output_object,
                                                         masters_need_slaves[0].task_number)
                                            if masters_need_slaves[
                                                0].will_coupling_be_complete():  # ensure everything worked and sort out env-variables
                                                self.agv_couple_count_at[i] = masters_need_slaves[
                                                                                  1].agv_couple_count - len(
                                                    m2_slaves) + 1  # +1 for the removed slave
                                                self.coupling_master_at[i] = masters_need_slaves[1]
                                            else:
                                                print(
                                                    "MISTAKE: THERE WAS A MASTER ALTHOUGH A DIFFERENT MASTER WITH SAME TASK WAITED FOR MORE THAN ONE SLAVE TO BE ASSIGNED @2")
                                        else:
                                            self.master_becomes_slave(masters_need_slaves[1], masters_need_slaves[0], i,
                                                                      len(m1_slaves))
                                else:  # both masters have no slaves (=> make second master slave of first)
                                    # self.master_becomes_slave(masters_need_slaves[1], masters_need_slaves[0], i, 0) # TODO when ensured @3 is not needed this instead of following code:
                                    masters_need_slaves[1].free_from_coupling()
                                    masters_need_slaves[1].task_number = masters_need_slaves[0].task_number
                                    self.coupling_master_at[i] = masters_need_slaves[0]  # necessary before _couple()
                                    self._couple(masters_need_slaves[1], masters_need_slaves[0].output_object,
                                                 masters_need_slaves[0].task_number)
                                    self.agv_couple_count_at[i] = masters_need_slaves[
                                                                      0].agv_couple_count - 1  # one slave got assigned (possibly not needed)
                                    if masters_need_slaves[0].will_coupling_be_complete():  # should m1 in any case
                                        self.agv_couple_count_at[i] = 0
                                        self.coupling_master_at[
                                            i] = None  # since one master is filled and other master became slave
                                    else:
                                        print(
                                            "MISTAKE: THERE WAS A MASTER ALTHOUGH A DIFFERENT MASTER WITH SAME TASK WAITED FOR MORE THAN ONE SLAVE TO BE ASSIGNED @3")

    def master_becomes_slave(self, new_slave, new_master, i, masters_slave_count):
        new_slave.free_from_coupling()
        new_slave.task_number = new_master.task_number
        self.coupling_master_at[i] = new_master  # necessary before _couple()
        self._couple(new_slave, new_master.output_object, new_master.task_number)
        self.agv_couple_count_at[i] = new_master.agv_couple_count - masters_slave_count - 1  # one slave is old_master
        if new_master.will_coupling_be_complete():  # should m1 in any case
            self.agv_couple_count_at[i] = 0
            self.coupling_master_at[i] = None

    @staticmethod
    def agv_is_master(self, agv):  # unused ? - todelete
        if agv.coupling_master == agv:
            return True
        return False

    def _get_reward(self):
        reward = 0

        # Reward for finishing product
        product_count = len(self.factory.warehouses[0].end_product_store)
        if product_count > self.last_end_product_count:
            reward += (product_count - self.last_end_product_count) * self.reward_factor
            self.last_end_product_count = product_count


        divIn = 4
        divOut = 4
        if self.reward_type == 2:
            divIn *= 2
            divOut *= 2

        if self.reward_type == 3:
            divOut *= 4

        if self.reward_type == 4:
            divIn *= 2
            divOut *= 4

        # Reward for lowering priority
        index = 0
        for machine in self.factory.machines:
            input_priority, output_priority = machine.get_buffer_status()
            if input_priority < self.last_machine_priority[index][0]:
                reward += self.last_machine_priority[index][0] * 1/divIn * self.reward_factor
            if output_priority < self.last_machine_priority[index][1]:
                reward += self.last_machine_priority[index][1] * 1/divOut * self.reward_factor# TODO for some reason I once ignored output_priority (old "wrong" reward implementation)
            self.last_machine_priority[index][0] = input_priority
            self.last_machine_priority[index][1] = output_priority
            index += 1

        # Reward for when an AGV is at an output that holds at least one product ("good position")
        for AGV in self.factory.agvs:
            #try:  # TODO: (occasionally values that should be "defined" were "undefined" due to threading)
            arrived = False
            prod_needed = False
            prod_available = False
            if AGV.coupling_master:     # coupling_master only exists if task requires coupling
                arrived = (AGV.status == 'waiting_with_master' or AGV.status == 'wait_for_coupling' or AGV.status == 'master_slave_decision')
                prod_available = AGV.coupling_master.output_object.has_product(AGV.coupling_master.target_product)

                if isinstance(AGV.coupling_master.input_object, Machine):
                    input_priority, output_priority = AGV.coupling_master.input_object.get_buffer_status()
                    prod_needed = False if input_priority <= 0 else True
                if AGV.coupling_master.target_product in self.factory.warehouses[0].input_products:
                    prod_needed = True
            if prod_available and arrived and prod_needed:
                if AGV not in self.GoodAGVs:
                    reward += 0.1
                    self.GoodAGVs.append(AGV)
                # Reward for being in a good position (to reinforce staying)
                else:
                    if AGV.waiting_in_good_position_timer < 20:
                        reward += 0.005 * self.time_step  # time payments should be scaled accordingly
                        if self.reward_type != 5:
                            AGV.waiting_in_good_position_timer += self.time_step
            # remove from list if position is no longer good (for example other agvs realized the transport)
            elif arrived:
                if not prod_available or not prod_needed:
                    if AGV in self.GoodAGVs:
                        self.GoodAGVs.remove(AGV)
            #except:
             #   pass

            # Negative Reward for leaving a good positions (punishment)
            if AGV.is_moving and AGV in self.GoodAGVs:
                if AGV.coupling_master:
                    is_agv_delivering = (AGV.coupling_master.status == 'move_to_input')
                else:
                    is_agv_delivering = (AGV.status == 'move_to_input')
                if is_agv_delivering:
                    self.GoodAGVs.remove(AGV)
                else:
                    reward -= 0.1
                    self.GoodAGVs.remove(AGV)

        return reward


    def all_agv_stand_still(self):  # artefact function - todelete
        for AGV in self.factory.agvs:
            if AGV.is_moving:
                return False
        return True

    def all_agv_are_free(self):
        for agv in self.factory.agvs:
            if not agv.is_free:
                return False
        return True

    @staticmethod  # TODO: in use?
    def _unload_agv(agv, unloading):
        agv.unload(unloading)

    def _block_until_synchronized(self):
        all_synchronized = True
        for i in range(10000):
            all_synchronized = True
            for agv in self.factory.agvs:
                if agv.step_counter_last != self.step_counter:  # -1 when threading (WHY?)
                    all_synchronized = False
                    # print("\n bla")
                    break
            if all_synchronized:
                break
            time.sleep(self.sleep_time)
        if not all_synchronized:
            print("SYNCHRONIZATION TIMEOUT")
            print(self.step_counter, self.factory.agvs[0].step_counter_next,
                  self.factory.agvs[0].step_counter_last, self.factory.agvs[1].step_counter_last,
                  self.factory.agvs[2].step_counter_last, self.factory.agvs[3].step_counter_last,
                  self.factory.agvs[4].step_counter_last, self.factory.agvs[5].step_counter_last)

    def _simulate_factory_objects(self):  # perhaps change order
        index = 0
        for agv in self.factory.agvs:
            agv.step(self.time_step, self.step_counter)
            self.agv_free_history[index].append(agv.is_free)
            index += 1

        # IMPORTANT when AGV don't run on threads
        self._simulate_agvs_without_threading()

        for warehouse in self.factory.warehouses:
            warehouse.step(self.time_step)
        index = 0
        for machine in self.factory.machines:
            machine.step(self.time_step)
            self.machine_status_history[index].append(machine.status)
            index += 1

    def _simulate_agvs_without_threading(self):
        # simulate masters first
        slaves = []
        for agv in self.factory.agvs:
            if agv.coupling_master == agv:  # TODO check whether this is working
                agv.run_without_threads()
            else:
                slaves.append(agv)
        for agv in slaves:
            agv.run_without_threads()

    def _collect_train_data(self, reward):
        self.end_product_count.append(len(self.factory.warehouses[0].end_product_store))
        self.reward_history.append(reward)
        self.restart_logger.append(False)

    def _plot_training(self, show_result=False, window_number=str(1)):
        plt.figure(window_number)
        if show_result:
            plt.clf()
            plt.title('Result')
        else:
            plt.clf()
            plt.title('Running...')
        plt.xlabel('Time in ' + str(self.time_step) + 's Steps')
        plt.ylabel('Products')
        plt.plot(self.end_product_count, label='Finished Products', color='b', linewidth=3, linestyle=':')
        plt.plot(self.reward_history, label='Reward', color='g', linewidth=2)
        plt.legend()
        plt.pause(0.05)  # pause required for constructor
        if is_ipython:
            if not show_result:
                display.display(plt.gcf())
                display.clear_output(wait=True)
            else:
                display.display(plt.gcf())

    def display_colors(self):
        """
        Display a 2D list of color data using pygame.
        """
        color_data = self.factory.get_color_grid()

        # Main loop to draw the colors and handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        # Draw the color data
        for y in range(self.height):
            for x in range(self.width):
                pygame.draw.rect(self.screen, color_data[x][y],
                                 (x * self.pixel_size, y * self.pixel_size, self.pixel_size, self.pixel_size))

        # Draw the AGVs
        for agv in self.factory.agvs:
            agv_pos = [agv.pos_x, agv.pos_y]
            pygame.draw.rect(self.screen, [0, 0, 0],
                             (agv_pos[0] * self.pixel_size, agv_pos[1] * self.pixel_size,
                              agv.width / self.reference_size * self.pixel_size,
                              agv.length / self.reference_size * self.pixel_size),
                             border_radius=3)

        for agv in self.factory.agvs:
            if agv.loaded_product is not None:
                agv_pos = [agv.pos_x, agv.pos_y]
                pygame.draw.rect(self.screen, [180, 180, 0],
                                 (agv_pos[0] * self.pixel_size + 2,
                                  agv_pos[1] * self.pixel_size + 2,
                                  agv.loaded_product.width / self.reference_size * self.pixel_size,
                                  agv.loaded_product.length / self.reference_size * self.pixel_size))

        # Draw machines data
        for machine in self.factory.machines:
            font = pygame.font.SysFont('arial', 20)
            text = font.render(machine.get_status() +
                               " I:" + str(len(machine.buffer_input_load)) +
                               " O:" + str(len(machine.buffer_output_load)), True, (0, 0, 0))
            self.screen.blit(text, [self.pixel_size * machine.pos_x, self.pixel_size * machine.pos_y])

            font = pygame.font.SysFont('arial', 20)
            text = font.render(str(int(machine.rest_process_time)), True, (0, 0, 0))
            self.screen.blit(text, [self.pixel_size * machine.pos_x, self.pixel_size * (machine.pos_y + 1)])

        for warehouse in self.factory.warehouses:
            font = pygame.font.SysFont('arial', 20)
            text = font.render(str(int(warehouse.rest_process_time)), True, (0, 0, 0))
            self.screen.blit(text, [self.pixel_size * warehouse.pos_x, self.pixel_size * (warehouse.pos_y + 1)])

        pygame.display.flip()


def sb_train_variation():
    # flipped_actions means that action 1 = agent 1 drive to 1, action 2 = agent 2 drive to 1...
    episodes = 512
    episode_length = 2048
    gamma = 0.99
    trial = "_1"
    save_folder = "./data/flipped_actions/DQN_tests/"
    save_name_start = "DQN_1s_" + str(episodes) + "x" + str(episode_length) + "_"
    save_name_end = "_no_threading" # "_adjusted_episode_length__no_threading"

    '''
    episodes = 512
    repetition = 16
    folder_spes = "train_len/"
    folder_spes += "train_len" + str(repetition) + "x" + str(episodes) + "x" + str(episode_length) + "_1/"
    create_folder(save_folder + folder_spes)
    id_name = "train_len_" + str(repetition) + "x" + str(episodes) + "x" + str(
        episode_length)
    save_path = save_folder + folder_spes
    save_name = save_name_start + id_name + trial + save_name_end
    env = CustomEnvironment(render=False, variation_training=True, var_save_path=save_path, var_save_name=save_name,
                            episode_length=episode_length)
    env.reset()
    save_nameApath = save_path + save_name
    model = sb.A2C('MlpPolicy', env=env, verbose=1, gamma=0.99, device="cpu")
    for i in range(20):
        model.learn(episodes * episode_length)
        model.save(save_nameApath + "_" + str(i+1) + ".zip")
        time.sleep(0.25)
    env.close()
    time.sleep(1)
    '''
    '''
    for i in [1,8296,2466]:
        folder_spes = "learning_rate/learning_rate0.0003_2/"
        create_folder(save_folder + folder_spes)
        id_name = "learning_rate0.0003"
        if i != 1:
            id_name += "_seed" + str(i)
        save_path = save_folder + folder_spes
        save_name = save_name_start + id_name + trial + save_name_end
        env = CustomEnvironment(render=False, variation_training=True, var_save_path=save_path, var_save_name=save_name, episode_length=episode_length)
        env.reset()
        save_nameApath = save_path + save_name
        if i == 1:
            model = sb.A2C('MlpPolicy', env=env, verbose=1, gamma=gamma, device="cpu", learning_rate=0.0003)
        else:
            model = sb.A2C('MlpPolicy', env=env, verbose=1, gamma=gamma, device="cpu", seed=i, learning_rate=0.0003)
        model.learn(episodes * episode_length)
        model.save(save_nameApath + ".zip")
        env.close()
        time.sleep(1)
        '''
    '''
    save_folder = "./data/flipped_actions/reward_variation/PPO_tests/"
    save_name_start = "PPO_1s_" + str(episodes) + "x" + str(episode_length) + "_"
    for i in [10]:
        folder_spes = "default/" + "reward_factor" + str(i) + "/"
        create_folder(save_folder + folder_spes)
        id_name = "reward_factor" + str(i)
        save_path = save_folder + folder_spes
        save_name = save_name_start + id_name + trial + save_name_end
        env = CustomEnvironment(render=False, variation_training=True, var_save_path=save_path, var_save_name=save_name, reward_fac=i)
        env.reset()
        save_nameApath = save_path + save_name
        model = sb.PPO('MlpPolicy', env=env, verbose=1, gamma=gamma, device="cpu")
        model.learn(episodes * episode_length)
        model.save(save_nameApath + ".zip")
        env.close()
        time.sleep(1)
    '''
    '''
    # LOOK AT TO_DO FÜRS SCHREIBEN
    # TODO rewardfactor von 1,25 wäre evtl. besser (vgl. DQN und PPO), aber dann vergleichbarkeit geringer
    for n_steps in [5]:
        folder_spes = "optimization/"
        folder_spes += "optimization_n_steps_and_lr_optimized_reward/"
        create_folder(save_folder + folder_spes)
        id_name = "optimization_" + str(episodes) + "x" + str(episode_length) + "_learning_rate0.0005"+"_n_steps"+str(n_steps)+"_optimized_reward"
        save_path = save_folder + folder_spes
        save_name = save_name_start + id_name + trial + save_name_end
        env = CustomEnvironment(render=False, variation_training=True, var_save_path=save_path, var_save_name=save_name,
                                episode_length=episode_length)
        env.reset()
        save_nameApath = save_path + save_name
        model = sb.A2C('MlpPolicy', env=env, verbose=1, gamma=0.99, device="cpu", learning_rate=0.0005, n_steps=n_steps)
        model.learn(episodes * episode_length)
        model.save(save_nameApath + ".zip")
        time.sleep(0.25)
        env.close()
        time.sleep(1)

    for n_steps in [5]:
        folder_spes = "optimization/"
        folder_spes += "optimization_n_steps_and_lr_optimized_reward/"
        create_folder(save_folder + folder_spes)
        id_name = "optimization"+"_learning_rate0.0002"+"_n_steps"+str(n_steps)+"_optimized_reward"
        save_path = save_folder + folder_spes
        save_name = save_name_start + id_name + trial + save_name_end
        env = CustomEnvironment(render=False, variation_training=True, var_save_path=save_path, var_save_name=save_name,
                                episode_length=episode_length)
        env.reset()
        save_nameApath = save_path + save_name
        model = sb.A2C('MlpPolicy', env=env, verbose=1, gamma=0.99, device="cpu", learning_rate=0.0002, n_steps=n_steps)
        model.learn(episodes * episode_length)
        model.save(save_nameApath + ".zip")
        time.sleep(0.25)
        env.close()
        time.sleep(1)

    for n_steps2 in [10,17]:
        # episode_length = 2048
        episodes = 1024
        repetition = 8
        folder_spes = "train_len/"
        folder_spes += "train_len" + str(repetition) + "x" + str(episodes) + "x" + str(episode_length) + "_lr0.00045_n_steps"+str(n_steps2)+"/"
        create_folder(save_folder + folder_spes)
        id_name = "train_len_" + str(repetition) + "x" + str(episodes) + "x" + str(episode_length) + "_lr0.00045_n_steps"+str(n_steps2)
        save_path = save_folder + folder_spes
        save_name = save_name_start + id_name + trial + save_name_end
        env = CustomEnvironment(render=False, variation_training=True, var_save_path=save_path, var_save_name=save_name,
                                episode_length=episode_length, reward_type=5)
        env.reset()
        save_nameApath = save_path + save_name
        model = sb.A2C('MlpPolicy', env=env, verbose=1, gamma=0.99, device="cpu", learning_rate=0.00045, n_steps=n_steps2)
        for i in range(repetition):
            model.learn(episodes * episode_length)
            model.save(save_nameApath + "_" + str(i) + ".zip")
            time.sleep(0.25)
        env.close()
        time.sleep(1)

        episodes = 1024 * 8
        folder_spes = "train_len/"
        folder_spes += "train_len" + str(episodes) + "x" + str(episode_length) + "_lr0.00045_n_steps"+str(n_steps2)+"/"
        create_folder(save_folder + folder_spes)
        id_name = "train_len_" + str(episodes) + "x" + str(episode_length) + "_lr0.00045_n_steps"+str(n_steps2)
        save_path = save_folder + folder_spes
        save_name = save_name_start + id_name + trial + save_name_end
        env = CustomEnvironment(render=False, variation_training=True, var_save_path=save_path, var_save_name=save_name,
                                episode_length=episode_length, reward_type=5)
        env.reset()
        save_nameApath = save_path + save_name
        model = sb.A2C('MlpPolicy', env=env, verbose=1, gamma=0.99, device="cpu", learning_rate=0.00045, n_steps=n_steps2)
        model.learn(episodes * episode_length)
        model.save(save_nameApath + ".zip")
        time.sleep(0.25)
        env.close()
        time.sleep(1)
    '''

    '''
    for i2 in range(10):
        gamma = 0.9 + (i2/100)
        folder_spes = "gamma/"
        folder_spes += "gamma" + str(gamma) + "/"
        create_folder(save_folder + folder_spes)
        id_name = "gamma" + str(gamma)
        save_path = save_folder + folder_spes
        save_name = save_name_start + id_name + trial + save_name_end
        env = CustomEnvironment(render=False, variation_training=True, var_save_path=save_path, var_save_name=save_name, reward_type=5)
        env.reset()
        save_nameApath = save_path + save_name
        model = sb.DQN('MlpPolicy', env=env, verbose=1, gamma=gamma,device="cpu")
        model.learn(episodes * episode_length)
        model.save(save_nameApath + ".zip")
        env.close()
        time.sleep(1)

    for i2 in range(16):
        lr = 0.00002 * ((i2%5)+1) * (10**(i2//5))
        folder_spes = "learning_rate/"
        folder_spes += "lr" + str(lr) + "/"
        create_folder(save_folder + folder_spes)
        id_name = "lr" + str(lr)
        save_path = save_folder + folder_spes
        save_name = save_name_start + id_name + trial + save_name_end
        env = CustomEnvironment(render=False, variation_training=True, var_save_path=save_path, var_save_name=save_name, reward_type=5)
        env.reset()
        save_nameApath = save_path + save_name
        model = sb.DQN('MlpPolicy', env=env, verbose=1, learning_rate=lr,device="cpu")
        model.learn(episodes * episode_length)
        model.save(save_nameApath + ".zip")
        env.close()
        time.sleep(1)
    '''
    for i2 in [128, 256, 512, 1024]:
        folder_spes = "batch_size/"
        folder_spes += "batch_size" + str(i2) + "/"
        create_folder(save_folder + folder_spes)
        id_name = "lr" + str(i2)
        save_path = save_folder + folder_spes
        save_name = save_name_start + id_name + trial + save_name_end
        env = CustomEnvironment(render=False, variation_training=True, var_save_path=save_path, var_save_name=save_name, reward_type=5)
        env.reset()
        save_nameApath = save_path + save_name
        model = sb.DQN('MlpPolicy', env=env, verbose=1, batch_size=i2, device="cpu")
        model.learn(episodes * episode_length)
        model.save(save_nameApath + ".zip")
        env.close()
        time.sleep(1)

    for i2 in [500, 1000, 2000, 5000, 10000, 20000, 50000, 100000]:
        folder_spes = "target_update_interval/"
        folder_spes += "target_update_interval" + str(i2) + "/"
        create_folder(save_folder + folder_spes)
        id_name = "target_update_interval" + str(i2)
        save_path = save_folder + folder_spes
        save_name = save_name_start + id_name + trial + save_name_end
        env = CustomEnvironment(render=False, variation_training=True, var_save_path=save_path, var_save_name=save_name, reward_type=5)
        env.reset()
        save_nameApath = save_path + save_name
        model = sb.DQN('MlpPolicy', env=env, verbose=1, target_update_interval=i2,device="cpu")
        model.learn(episodes * episode_length)
        model.save(save_nameApath + ".zip")
        env.close()
        time.sleep(1)

    '''
    for i2 in range(4,10):
        i = 2 ** i2
        folder_spes = "restarts2_output_prio_nerf/"
        folder_spes += "restartAfter" + str(i) + "_output_prio_nerf/"
        create_folder(save_folder + folder_spes)
        id_name = "restart" + str(i) + "_output_prio_nerf_"
        save_path = save_folder + folder_spes
        save_name = save_name_start + id_name + trial + save_name_end
        env = CustomEnvironment(render=False, variation_training=True, var_save_path=save_path, var_save_name=save_name, reward=3)
        env.reset()
        save_nameApath = save_path + save_name
        model = sb.DQN('MlpPolicy', env=env, verbose=1, gamma=0.99, device="cpu")
        epis_done = 0
        while epis_done < 512:
            model.learn(i * episode_length)
            epis_done += i
            model.save(save_nameApath + "_" + str(epis_done) + "episodes_done.zip")
            time.sleep(0.25)
        env.close()
        time.sleep(1)

    for i2 in range(4, 10):
        i = 2 ** i2
        folder_spes = "restarts2_halved_prio_rewards_+output_nerf/"
        folder_spes += "restartAfter" + str(i) + "_halved_prio_rewards_+output_nerf/"
        create_folder(save_folder + folder_spes)
        id_name = "restart" + str(i) + "_halved_prio_rewards_+output_nerf_"
        save_path = save_folder + folder_spes
        save_name = save_name_start + id_name + trial + save_name_end
        env = CustomEnvironment(render=False, variation_training=True, var_save_path=save_path, var_save_name=save_name,
                                reward=4)
        env.reset()
        save_nameApath = save_path + save_name
        model = sb.DQN('MlpPolicy', env=env, verbose=1, device="cpu")
        epis_done = 0
        while epis_done < 512:
            model.learn(i * episode_length)
            epis_done += i
            model.save(save_nameApath + "_" + str(epis_done) + "episodes_done.zip")
            time.sleep(0.25)
        env.close()
        time.sleep(1)
    '''
def create_folder(save_folder):#
    if not os.path.exists(save_folder):
        os.makedirs(save_folder)

def sb_train():
    env = CustomEnvironment(render=True)  # True for display (creates the factory display window)
    env.display_colors()
    time.sleep(2)
    env.reset()
    model = sb.A2C('MlpPolicy', env=env, verbose=1, gamma=0.99, device="cpu")
    model = sb.A2C.load(
        "data/flipped_actions/A2C_tests/optimization/optimization_n_steps_and_lr/A2C_1s_1024x1024_optimization_learning_rate0.0002_n_steps14_1_no_threading.zip",
        env=env, verbose=1, gamma=0.99)

    #model = sb.PPO.load("data/flipped_actions/PPO_tests/timestep/timestep1.0/PPO_1s_512x2048_timestep1.0_1_no_threading.zip", env=env, verbose=1, gamma=0.99)  # for DQN: exploration_initial_eps=0.002, exploration_final_eps=0.001,
    print(model.policy)


    save_name_start = "./data/flipped_actions/DQN_tests/timestep/timestep1.0_"
    save_name_end = "_no_threading.zip"
    for i in range(1):
        save_name = save_name_start + str(i) + save_name_end
        model.learn(512 * 2048)  # !CAUTION! Make sure episode length is set right in step()
        model.save(save_name)

    # model.learn(128 * 2 * 2048)
    # model.save("./data/PPO_1s_128x2x2048_3.1_no_threading.zip")     # TODO: perhaps implement saves into env.step()

    env.close()


def sb_run_model():
    env = CustomEnvironment(render=True)  # True for display (creates the factory display window)
    env.reset()
    # model = sb.PPO('MlpPolicy', env=env, verbose=1, gamma=0.99)
    #model = sb.PPO.load("data/flipped_actions/PPO_tests/timestep/timestep1.0/PPO_1s_512x2048_timestep1.0_1_no_threading.zip", env=env, verbose=1, gamma=0.99)
    model = sb.A2C.load("data/flipped_actions/A2C_tests/optimization/optimization_n_steps_and_lr/A2C_1s_1024x1024_optimization_learning_rate0.0002_n_steps17_1_no_threading.zip", env=env, verbose=1, gamma=0.99)

    vec_env = model.get_env()
    obs = vec_env.reset()
    while True:
        accu_reward = 0
        for e in range(2048):
            action, _states = model.predict(obs, deterministic=True)
            obs, reward, done, _, info = env.step(action)
            accu_reward += reward
        print("Episode",str(e+1),", reward sum: "+str(accu_reward))



def custom_sb_train():
    env = CustomEnvironment(render=True)  # True for display (creates the factory display window)
    env.reset()
    policy_kwargs = dict(activation_fn=th.nn.ReLU,
                         net_arch=dict(pi=[32, 32, 32, 32, 32], vf=[32, 32, 32, 32, 32]))
    model = sb.PPO('MlpPolicy', env=env, policy_kwargs=policy_kwargs, verbose=1, gamma=0.99)
    # model = sb.PPO.load("./data/flipped_actions/5x32/custom_PPO_1s_64x2048_1.2_no_threading.zip", env=env, verbose=1, gamma=0.99)
    # print(model.policy)
    save_name_start = "./data/flipped_actions/5x32/custom_PPO_1s_64x2048_1."
    save_name_end = "_no_threading.zip"
    for i in range(21):
        save_name = save_name_start + str(i+1) + save_name_end
        model.learn(64 * 2048)
        model.save(save_name)

    # model.learn(128 * 2 * 2048)                     # TODO: perhaps implement saves into env.step()
    # model.save("./data/2x128_2x64_2x32_2x16/custom_PPO_1s_128x2x2048_2.1_no_threading.zip")

    env.close()


def custom_train():
    episodes = 46  # defines number of training episodes
    save_interval = 4  # defines the saving rate (episodes)
    max_steps = 2048  # defines episode lengths
    #ml_agent.load("flipped_actions/Rainbow_RN_all64_at.size20__1s_64x2048_tr.freq.128__1.2_no_threading")

    highscore = -math.inf
    save_folder = "flipped_actions/Rainbow_DQN/RainbowNetworkSmall/new_default_parameters"
    create_folder("models/" + save_folder)
    save_name_start = "RainbowNetworkSmall_1s_defaultParameters_" + str(episodes) + "x" + str(max_steps) + "_"
    save_name_end = "episodes_trail3"
    save_i = 1

    env = CustomEnvironment(render=False, variation_training=True, var_save_path=("models/" + save_folder + "/"),
                            var_save_name=(save_name_start + save_name_end), rainbow_algo=True)  # True for display (creates the factory display window)
    # env.display_colors()
    net = MachineLearning.RainbowNetwork.RainbowNetworkSmall
    ml_agent = RainbowLearning(state_d=env.observation_space.shape[0], action_d=env.action_space.n, net=net)
    #ml_agent.load("models/flipped_actions/Rainbow_DQN/RainbowNetworkSmall/default_parameters_updatefreq_256/RainbowNetworkSmall_1s_defaultParameters_8x2048_63episodes_trail3.pth")
    repetitions = 1
    for e in range(episodes * repetitions):
        steps = 0
        state = env.reset()
        state = state[0]  # ??
        ml_agent.set_state(state)
        done = False
        accu_reward = 0
        # actions = []                                                    # for monitoring
        # rewards = []                                                    # for monitoring
        ep_start_time = time.time()
        while not done:
            steps += 1
            print("steps:",steps)
            env.step_start_time = time.time()
            action_index = ml_agent.get_action_without_state()
            new_state, reward, done, _, info = env.step(action_index)
            # actions.append(action_index)                                # for monitoring
            if steps >= max_steps:  # should rather be in env.step()?
                done = True
                #print(e)
                print("Produced products:", str(env.end_product_count))
                env.reset()  # env reset required when terminating(?)
                env.step_counter = 0

            ml_agent.add_memory_data(new_state, reward, done)
            accu_reward += reward
            # rewards.append(reward)                                      # for monitoring

            ml_agent.train()

        #ml_agent.train()
        sys.stdout.write(
            "\r" + "Epoch: " + str(e + 1) + " Score: " + str(accu_reward) + " last steps: " + str(steps) +
            " fps: " + str(max_steps / (time.time() - ep_start_time)) + "\n")

        # print(actions)                                                  # for monitoring
        # print(rewards)                                                  # for monitoring
        if e % save_interval == save_interval - 1:
            ml_agent.save(save_folder + "/" + save_name_start + str(e)+"episodes" + save_name_end)
            print("Model saved")
            time.sleep(0.1)
            save_i += 1

            #reset plotting arrays
            # env.end_product_count = []
            # env.reward_history = []


        if accu_reward > highscore:  # save the NN that achieved the highest score
            ml_agent.save(save_folder + save_name_start + "__Highscore")
            print("highscore: " + str(accu_reward))
            highscore = accu_reward

    env.close()


def custom_run_model():  # TODO
    env = CustomEnvironment(render=True)  # True for display (creates the factory display window)
    env.display_colors()
    net = MachineLearning.RainbowNetwork.RainbowNetworkSmall
    ml_agent = RainbowLearning(state_d=env.observation_space.shape[0], action_d=env.action_space.n, net=net, std_init=0)
    ml_agent.load("models/flipped_actions/Rainbow_DQN/RainbowNetworkSmall/default_parameters_updatefreq_256/RainbowNetworkSmall_1s_defaultParameters_8x2048_63episodes_trail3.pth")


    state = env.reset()
    state = state[0]  # ??
    ml_agent.set_state(state)
    while True:
        env.step_start_time = time.time()
        action_index = ml_agent.get_action_without_state()
        new_state, reward, done, _, info = env.step(action_index)
        ml_agent.add_memory_data(new_state, reward, done)
    env.close()


def test():
    env = CustomEnvironment(render=True)
    env.reset()
    env.display_colors()
    action_state = 'idle'
    for i in range(5000):
        if action_state == 'idle' and len(env.factory.warehouses[0].buffer_output_load) > 0:
            action_state = 'deliver1-1'
        #  0 m1 m2 m3 w1 0 m1 m2 m3 w1 0 m1
        elif action_state == 'idle':
            env.step(0)
        elif action_state == 'deliver1-1':
            env.step(1)
            action_state = 'deliver1-2'
        elif action_state == 'deliver1-2':
            env.step(6)
            action_state = 'deliver1-3'
        elif action_state == 'deliver1-3':
            env.step(11)
            action_state = 'deliver1-4'
        elif action_state == 'deliver1-4':
            env.step(16)
            action_state = 'deliver1-5'
        elif action_state == 'deliver1-5':
            env.step(21)
            action_state = 'deliver1-6'
        elif action_state == 'deliver1-6':
            env.step(2)
            action_state = 'idle'
        # env.display_colors()
    env.close()


def test2():
    env = CustomEnvironment(render=True)
    env.reset()
    env.display_colors()
    delivery = 1

    val = 0
    while True:
        '''
        if val == 2:
            env.step(0)
        else:
            val = test2_helper(env, 1)
        '''
        if delivery == 1:
            delivery = test2_helper(env, delivery)
        elif delivery == 2:
            delivery = 1
            # delivery = test2_helper(env, delivery)
        elif delivery == 3:
            delivery = test2_helper(env, delivery)
        elif delivery == 4:
            delivery = test2_helper(env, delivery)
        elif delivery == 5:
            delivery = 1


def test2_helper(env, delivery):
    all_done = True
    for i in range(env.n_agv):
        if env.factory.agvs[i].task_number == delivery - 1 or (env.factory.agvs[i].task_number == 4 and delivery == 1):
            if env.factory.agvs[i].is_free:
                env.step(delivery * env.n_agv + i)  # for flipped commands
                all_done = False
                break
    if all_done:
        delivery += 1
        env.step(0)
    return delivery


def extract_collected_data():
    folder_start = "data/flipped_actions/A2C_tests/optimization/optimization_n_steps_and_lr"
    name_start = "/A2C_1s_1024x1024_optimization_"
    end_name_prod = "_1_no_threading_end_product_counts.npy"
    end_name_rew = "_1_no_threading_reward_history.npy"
    end_name_reset = "_1_no_threading_restart_history.npy"
    for a in range(3):
        # Load the .npy file
        assist_array = ["",
                        "_seed2466",
                        "_seed8296"]
        s = assist_array[a]
        '''
        if s in [0.3, 0.03, 0.6, 0.09]:
            print("SKIP",s)
            time.sleep(5)
            continue
        '''
        np_array = np.load("data/flipped_actions/A2C_tests/learning_rate/learning_rate0.0003_2/A2C_1s_1024x1024_learning_rate0.0003"+s+"_2_no_threading_end_product_counts.npy")# folder_start + name_start + str(s) + end_name_prod)
        reset_np_array = np.load("data/flipped_actions/A2C_tests/learning_rate/learning_rate0.0003_2/A2C_1s_1024x1024_learning_rate0.0003"+s+"_2_no_threading_restart_history.npy")    # folder_start + name_start + str(s) + end_name_reset)

        excel_file_name = 'A2C_tests_learning_rate/learning_rate0.0003_2'+str(s)+'.xlsx'
        # extract reward in each timestep to excel sheet
        reward_np_array = np.load("data/flipped_actions/A2C_tests/learning_rate/learning_rate0.0003_2/A2C_1s_1024x1024_learning_rate0.0003"+s+"_2_no_threading_reward_history.npy") # folder_start + name_start + str(s) + end_name_rew)

        # Define the maximum number of rows per sheet
        max_rows_per_sheet = 1048575

        # Calculate the number of sheets needed
        num_sheets = len(reward_np_array) // max_rows_per_sheet + 1
        print("sheets:",num_sheets,"total_datapoints:",len(reward_np_array))
        with pd.ExcelWriter(excel_file_name, engine='openpyxl') as writer:
            for i in range(num_sheets):
                start_row = i * max_rows_per_sheet
                end_row = min((i + 1) * max_rows_per_sheet, len(reward_np_array))
                chunk_df = pd.DataFrame(reward_np_array[start_row:end_row])
                sheet_name = f'Sheet{i+1}'
                chunk_df.to_excel(writer, sheet_name=sheet_name, index=False)
                print(f"Chunk {i+1} written to {sheet_name}")
        print("All data has been successfully written to Excel.")
        
        '''
        # machine status
        # Extract the first list from the 2D np_array
        first_list = np_array[0]  # Assuming np_array has shape (n, m), and we need np_array[0]
    
        # Map the string values to numbers
        status_mapping = {"idle": 0, "process": 1, "blocked": 2}
        mapped_values = np.array([status_mapping[status] for status in first_list])
    
        # Calculate the number of sheets needed
        num_sheets = len(mapped_values) // max_rows_per_sheet + 1
    
        # Write the data to Excel
        with pd.ExcelWriter(excel_file_name, engine='openpyxl') as writer:
            for i in range(num_sheets):
                start_row = i * max_rows_per_sheet
                end_row = min((i + 1) * max_rows_per_sheet, len(mapped_values))
                chunk_df = pd.DataFrame(mapped_values[start_row:end_row], columns=['Machine Status'])
                sheet_name = f'Sheet{i + 1}'
                chunk_df.to_excel(writer, sheet_name=sheet_name, index=False)
                print(f"Chunk {i + 1} written to {sheet_name}")
        print("All data has been successfully written to Excel.")
        '''
        normal_array = np_array.tolist()
        reset_array = reset_np_array.tolist()


        # extract value at end of time step (e. g. end product count)
        for i in range(len(reset_array)-1):
            if reset_array[i]:
                # print(i)
                print(normal_array[i])
                assert normal_array[i+1] == 0, print(str(normal_array[i])+", "+str(normal_array[i+1]))
        print(normal_array[-1])
    
        # print(max(normal_array))

        '''
        # old end product extraction
        for i in range(1,1024):
            print(normal_array[i*1025-2])
            assert normal_array[i * 1025 - 1] == 0, print("Mistake: no reset at",i)
        #print(normal_array[-1])

        #ensure no mistakes
        for i in range(1,1024):
            for j in range(500):
                assert normal_array[i * 1025 - 3 - j] <= normal_array[i * 1025 - 2], print("Mistake: ",i)
            #print(i)
        print()
        print("gamma",s)
        
        # for tests with >2048 condition
        for i in range(179*2049-5,179*2049+5):
            end_prod = normal_array[i]
            print(str(i)+":",end_prod)
            # assert end_prod >= normal_array[i*2049-1], print(i)
            #assert normal_array[i*2049-1] == 0, print(i)
        #print(normal_array[-1])
        i = 366772
        a = True
        while a:
            end_prod = normal_array[i]
            print(str(i) + ":", end_prod)
            i += 1
            if end_prod == 0:
                a = False
        '''
        '''
        # extract discounted reward sum per episode
        discount = 1
        _ep_rew = 0
        for i in range(len(reset_array)-1):
            _ep_rew += (normal_array[i] )#* discount)
            if reset_array[i]:
                print(str(_ep_rew).replace('.', ','))
                _ep_rew = 0
                discount = 1
                assert normal_array[i + 1] == 0, print(
                    str(normal_array[i]).replace('.', ',') + ", " + str(normal_array[i + 1]).replace('.', ','))
            else:
                discount *= 0.99
        print(str(_ep_rew).replace('.', ','))
        '''
if __name__ == '__main__':
    print("Cuda is available: " + str(torch.cuda.is_available()))

    '''
    # arr = np.load("./data/flipped_actions/A2C_tests/gamma/gamma0.99/A2C_1s_8x1024_gamma0.99_1_no_threading_reward_history.npy")
    # arr = np.load("./data/flipped_actions/A2C_tests/gamma/gamma0.99/A2C_1s_8x1024_gamma0.99_1_no_threading_end_product_counts.npy")
    arr = np.load("./data/flipped_actions/A2C_tests/gamma/gamma0.99/A2C_1s_8x1024_gamma0.99_1_no_threading_machine_status_history.npy")
    # arr = np.load("./data/flipped_actions/A2C_tests/gamma/gamma0.99/A2C_1s_8x1024_gamma0.99_1_no_threading_agv_free_history.npy")
    print(arr)

    arr = arr.tolist()
    print(arr)
    '''

    # sb_train()
    # sb_train_variation()
    # sb_run_model()
    # custom_sb_train()

    custom_train()
    # custom_run_model()  # TODO
    # test()
    # test2()

    # extract_collected_data()
    '''
    np_array = np.load("data/flipped_actions/DQN_tests/target_update_interval/target_update_interval50000/DQN_1s_512x2048_target_update_interval50000_1_no_threading_end_product_counts.npy")  # folder_start + name_start + str(s) + end_name_prod)
    reset_np_array = np.load("data/flipped_actions/DQN_tests/target_update_interval/target_update_interval50000/DQN_1s_512x2048_target_update_interval50000_1_no_threading_restart_history.npy")  # folder_start + name_start + str(s) + end_name_reset)
    reward_np_array = np.load("data/flipped_actions/DQN_tests/target_update_interval/target_update_interval50000/DQN_1s_512x2048_target_update_interval50000_1_no_threading_reward_history.npy")  # folder_start + name_start + str(s) + end_name_rew)

    normal_array = np_array.tolist()
    reset_array = reset_np_array.tolist()
    reward_array = reward_np_array.tolist()

    prod = True
    if prod:
        # extract value at end of time step (e. g. end product count)
        for i in range(len(reset_array)):
            if reset_array[i]:
                # print(i)
                print(normal_array[i])
                if i < len(normal_array)-1:
                    assert normal_array[i + 1] == 0, print(str(normal_array[i]) + ", " + str(normal_array[i + 1]))
    else:
        accu_rew = 0
        for i in range(len(reset_array)):
            accu_rew += reward_array[i]
            if reset_array[i]:
                print(str(accu_rew).replace('.', ','))
                accu_rew = 0
    '''