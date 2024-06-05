import math
import sys
import time
import pygame
import gymnasium
import stable_baselines3 as sb
import matplotlib
import matplotlib.pyplot as plt
import torch.cuda

# TODO threading for windows - so they don't crash
import threading

from FactoryObjects.Factory import Factory
from FactoryObjects.Machine import Machine  # needed for reward function
import MachineLearning.RainbowNetwork
from MachineLearning.RainbowLearning import RainbowLearning

is_ipython = 'inline' in matplotlib.get_backend()
if is_ipython:
    from IPython import display


class CustomEnvironment(gymnasium.Env):
    def __init__(self, render=False):
        super(CustomEnvironment, self).__init__()
        self.agv_positioning = None
        self.coupling_command = None
        self.agv_couple_count = None
        self.coupling_master = None
        self.factory = Factory()
        self.step_counter = 0
        self.last_end_product_count = 0
        self.last_critical_conditions = 0
        self.factory.create_temp_factory_machines()
        # self.time_step = 0.1
        self.time_step = 1  # should be the same for AGV.move_state(self) "distance if" (AGV have a speed of 1)
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

        return self._create_observation(), {'info': "Nothing"}

    def step(self, action):
        self.step_counter += 1
        # self._block_until_synchronized()  # may be used when threading agvs
        self._perform_action(action)
        truncated = False  # Failed / Accident
        # TODO: According to https://stable-baselines3.readthedocs.io/en/master/guide/rl_tips.html
        terminated = False  # End of cycle          TODO: it is the other way around
        # time.sleep(0.001)       # TODO TODO Action Update in AGV needs to be ensured before simulating factory
        # TODO FRAGE: Wo wird eine von Außen aufgerufene Funktion eines agvs ausgeführt und wann sind die
        #  self.werteverändert (wenn der thread z.B. gerade eigentlich wartet z.B.)
        self._simulate_factory_objects()
        # !!! Factory simulation has to be done before processing step information (especially reward and observation)
        self._block_until_synchronized()

        # used for SB-learning (e.g. PPO)
        truncated = self.sb3_step_completion()
        # "!truncated is used when "time limit" is hit AND time is not part of the observation space, else terminated!"

        reward = self._get_reward()
        self._collect_train_data(reward)
        # plot training within an episode
        if self.step_counter % (128*2*2048) == 0:   # math.inf => (almost) never triggered
            if self.step_counter != 0:
                self.render_window += 1
                self._plot_training(True, window_number=str(self.render_window))
                plt.ioff()
                plt.show()
                time.sleep(0.2)

        # display env continuously

        self.display_colors()
        time.sleep(0.1)         # necessary  delay to regulate run speed

        # TODO ensure the implementation of terminated and truncated is correct
        return self._create_observation(), reward, terminated, truncated, {'info': "Nothing"}

    def conditional_display(self, episode):
        if episode == self.last_episode + 1:
            self.good_consecutive_runs += 1
            if self.good_consecutive_runs >= 5:
                self.display_colors()
                time.sleep(0.1)
        else:
            self.good_consecutive_runs = 0
        self.last_episode = episode

    def sb3_step_completion(self):
        truncated = False
        if self.step_counter > 2 * 2048:    # for smaller time steps 10* to 20*
            # for special condition display options
            if self.last_end_product_count > math.inf:
                self.conditional_display(self.render_delay)     # render_delay indicates episode (count)
            # regular reset according to SB3 Website: Custom Environments
            truncated = True
            self.reset()                    # referring to SB3 Website: Custom Environments
            self.step_counter = 0           # UNNECESSARY HERE (ALREADY IN RESET)
          # self.display_colors()           # visual to ensure factory reset properly
            # create a new render window for the results so-and-so often
            if self.render_delay % math.inf == 0:   # math.inf => never triggered
                self.render_window += 1
                self.end_product_count = []  # only used for plotting
                self.reward_history = []  # only used for plotting
            self.render_delay += 1
            # plot training
            if self.render_delay % math.inf == 0:   # update rate (math.inf => never updated)
                self._plot_training(window_number=str(self.render_window))      # TODO updating does not work reliable
                pygame.display.flip()
                time.sleep(0.1)
        return truncated


    def render(self, mode='human'):
        print("Rendering")

    def close(self):
        self.factory.shout_down()
        self._plot_training(True, window_number='Final')
        plt.ioff()
        plt.show()

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

    def _perform_action(self, action):
        command_index = int(action % self.n_agv_commands)  # the 1d action array is now used as a pseudo 2d array
        agv_index = int(action / self.n_agv_commands)

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

        # process all actions that don't require coupling
        if command_index == 3 or command_index == 4:
            self.deliver(agv, command_index, input_object, output_object)
        # process actions that require coupling
        else:
            first = True
            for AGV in self.factory.agvs:
                if AGV.task_number == command_index and AGV != agv:  # check whether different agv/s is/are first (already assigned)
                    try:  # since AGVs are running in a thread an update might rarely cause an AttributeError
                        # (coupling_master does not exist) TODO should no longer be an issue
                        if not AGV.coupling_master.will_coupling_be_complete():
                            # condition triggered when a master agv still needs slaves
                            first = False
                            break
                    except:
                        pass

            if first:
                self.deliver(agv, command_index, input_object, output_object)
            else:
                self._couple(agv, output_object, command_index)

    def deliver(self, agv, command_index, input_object, output_object):  # added _at[command_index] to all self.(...)
        # TO-DO: (eventually) unsophisticated implementation when there are more input products (with different origins)
        for product in input_object.input_products: # required to get product properties
            if output_object is not None:
                # implemented for masters that move away
                if agv.coupling_master == agv:
                    self.replace_master(agv)
                    # CAUTION! Such operations have to be processed before agv.task_number = command_index
                # implemented for agvs that are slaves of a waiting coupling master
                if agv.coupling_master:
                    self.agv_couple_count_at[agv.coupling_master.task_number] += 1
                agv.free_from_coupling()
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

    def _couple_simple(self, agv, output_object):   # artefact function - todelete
        if self.agv_couple_count > 0:
            for agv in self.factory.agvs:
                if agv.is_free:
                    count = 0
                    pos = [0, 0]
                    for length in range(self.agv_positioning[1]):
                        for width in range(self.agv_positioning[0]):
                            if count == self.agv_positioning[0] * self.agv_positioning[1] - self.agv_couple_count:
                                pos = [width, length]
                            count += 1
                    agv.coupling(self.coupling_master, pos, output_object=output_object)
                    self.agv_couple_count -= 1
                    return
        else:
            self.coupling_command = None

    def _couple(self, agv, output_object, command_index):
        if self.agv_couple_count_at[command_index] > 0:
            # if self.master_prevention(agv):
            #     return
            # implemented for masters that move away (become no master) # TODO (might become junk)
            if agv.coupling_master == agv:
                self.replace_master(agv)    # TODO fix position management (positions are assigned by the slave count,
                                            #  not whether position is occupied - does not work properly)
            # implemented for agvs that are slaves of a waiting coupling master
            if agv.coupling_master:
                self.agv_couple_count_at[agv.coupling_master.task_number] += 1
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
                if pos != [0,0]:
                    break
            agv.coupling(self.coupling_master_at[command_index], pos, output_object=output_object)
            self.agv_couple_count_at[command_index] -= 1
            return
        else:  # safeguard - todelete
            print("MISTAKE")
            self.coupling_at[command_index] = False

    def master_prevention(self, agv):   # artefact function - todelete
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
                if AGV.status == 'move_to_coupling_position':# (most likely) technically this condition is not needed
                    self.assign_new_master(old_master, AGV)
                    return
        self.coupling_master_at[old_master.task_number] = None  # if no slaves are found
        return

    def assign_new_master(self, old_master, new_master):
        slave_list = [agv for agv in self.factory.agvs if agv.coupling_master == old_master and agv != old_master]
        for slave in slave_list:
            slave.coupling_master = new_master  # assign AGV as new master
        new_master.coupling(new_master, [0, 0], old_master.agv_couple_count, old_master.output_object,
                            old_master.input_object, old_master.target_product, self.agv_positioning_at[old_master.task_number])
        new_master.status = 'move_to_coupling_position'
        new_master.move_target = old_master.move_target
        self.coupling_master_at[old_master.task_number] = new_master

    @staticmethod
    def agv_is_master(self, agv):   # unused ? - todelete
        if agv.coupling_master == agv:
            return True
        return False

    def _get_reward(self):  # TODO check whether reward function implementation still works and makes sense
        reward = 0
        critical_conditions = 0

        # Reward for finishing product
        product_count = len(self.factory.warehouses[0].end_product_store)
        if product_count > self.last_end_product_count:
            self.last_end_product_count = product_count
            reward = 10

        # Reward for lowering priority
        for machine in self.factory.machines:
            input_priority, output_priority = machine.get_buffer_status()
            critical_conditions += input_priority
            critical_conditions += output_priority
        if critical_conditions < self.last_critical_conditions:
            reward += (self.last_critical_conditions - critical_conditions) * 0.8
        self.last_critical_conditions = critical_conditions

        # Reward for when an AGV is at an output that holds at least one product ("good position")
        for AGV in self.factory.agvs:
            try:    # TODO: (occasionally values that should be "defined" were "undefined" due to threading)
                prod_needed = False
                if AGV.coupling_master:
                    prod_available = AGV.coupling_master.output_object.has_product(AGV.coupling_master.target_product)
                    arrived = (AGV.command == 'follow_master' or AGV.status == 'wait_for_coupling' or AGV.status == 'master_slave_decision')
                    if isinstance(AGV.coupling_master.input_object, Machine):
                        input_priority, output_priority = AGV.coupling_master.input_object.get_buffer_status()
                        prod_needed = False if input_priority <= 0 else True
                else:   # rather irrelevant since product will be loaded immediately
                    prod_available = AGV.output_object.has_product(AGV.target_product)
                    arrived = (AGV.command == 'load_product')
                    if isinstance(AGV.input_object, Machine):
                        input_priority, output_priority = AGV.input_object.get_buffer_status()
                        prod_needed = False if input_priority <= 0 else True
                if prod_available and arrived and prod_needed:
                    if not AGV.is_moving() and id(AGV) not in self.GoodAGVs:
                        reward += 0.1
                        self.GoodAGVs.append(id(AGV))
            except:
                pass

            # Reward for being in a good position (to reinforce staying)
            if not AGV.is_moving() and id(AGV) in self.GoodAGVs:
                reward += 0.002

            # Negative Reward for leaving a good positions (punishment)
            if AGV.is_moving() and id(AGV) in self.GoodAGVs:
                if AGV.coupling_master:
                    is_agv_delivering = (AGV.coupling_master.status == 'move_to_input')
                else:
                    is_agv_delivering = (AGV.status == 'move_to_input')
                if is_agv_delivering:
                    self.GoodAGVs.clear()
                else:
                    reward -= 0.1
                    self.GoodAGVs.remove(id(AGV))

        return reward

        '''    
            if AGV.status == 'move_to_input' or AGV.status == 'wait_for_coupling' or AGV.command == 'follow_master' or AGV.command == 'coupling':
                #product has to be available - coupled/slave AGVs need special treatment
                output_got_product = False
                if AGV.coupling_master:
                    if AGV.coupling_master.output_object.has_product(AGV.coupling_master.target_product):
                        if not AGV.is_moving():
                            if id(AGV) not in self.GoodAGVs:  # temporary solution to only give "good" AGVs rewards on arrival
                                reward += 0.01
                                print("+0.01 "+str(self.step_counter))
                                self.GoodAGVs.append(id(AGV))
                elif AGV.output_object.has_product(AGV.target_product):
                    if not AGV.is_moving():
                        if id(AGV) not in self.GoodAGVs: #temporary solution to only give "good" AGVs rewards on arrival
                            reward += 0.01
                            print("+0.01 " + str(self.step_counter))
                            self.GoodAGVs.append(id(AGV))
            
            if AGV.is_moving() and id(AGV) in self.GoodAGVs:    #TODO Temporary solution to catch some - differentiation for different Tasked AGVs
                #product moves away unloaded - coupled/slave AGVs need special treatment
                AGVs_loaded = False
                if AGV.coupling_master != None:
                    if AGV.coupling_master.loaded_product != None:
                        AGVs_loaded = True
                if AGV.loaded_product != None or AGVs_loaded:
                    self.GoodAGVs.clear()
                else:
                    reward -= 0.01
                    print("-0.01 " + str(self.step_counter))
                    print(AGV.task_number)
                    self.GoodAGVs.remove(id(AGV))
        '''

    def all_agv_stand_still(self):      # artefact function - todelete
        for AGV in self.factory.agvs:
            if AGV.is_moving():
                return False
        return True

    def all_agv_are_free(self):
        for agv in self.factory.agvs:
            if not agv.is_free:
                return False
        return True

    @staticmethod   # TODO: in use?
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

    def _simulate_factory_objects(self):    # perhaps change order
        for agv in self.factory.agvs:
            agv.step(self.time_step, self.step_counter)

        # IMPORTANT when AGV don't run on threads
        self._simulate_agvs_without_threading()

        for warehouse in self.factory.warehouses:
            warehouse.step(self.time_step)
        for machine in self.factory.machines:
            machine.step(self.time_step)

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

    def _plot_training(self, show_result=False, window_number=str(1)):
        plt.figure(window_number)
        if show_result:
            plt.clf()
            plt.title('Result')
        else:
            plt.clf()
            plt.title('Running...')
        plt.xlabel('Time in '+str(self.time_step)+'s Steps')
        plt.ylabel('Products')
        plt.plot(self.end_product_count, label='Finished Products', color='b', linewidth=3, linestyle=':')
        plt.plot(self.reward_history, label='Reward', color='g', linewidth=2)
        plt.legend()
        plt.pause(0.01)  # pause required for constructor
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


def sb_train():
    env = CustomEnvironment(render=True)  # True for display (creates the factory display window)
    env.reset()
    model = sb.PPO('MlpPolicy', env=env, verbose=1, gamma=0.99)
    # model = sb.PPO.load("./data/PPO_1s_128x2x2048_2.2_no_threading.zip", env=env, verbose=1, gamma=0.99)
    # print(model.policy)
    model.learn(128 * 2 * 2048)
    model.save("./data/PPO_1s_128x2x2048_3.1_no_threading.zip")     # TODO: perhaps implement saves into env.step()
    model.learn(128 * 2 * 2048)
    model.save("./data/PPO_1s_128x2x2048_2.2_no_threading.zip")
    model.learn(128 * 2 * 2048)
    model.save("./data/PPO_1s_128x2x2048_2.3_no_threading.zip")
    model.learn(128 * 2 * 2048)
    model.save("./data/PPO_1s_128x2x2048_2.4_no_threading.zip")
    env.close()


def sb_run_model():  # TODO (As of now this does not function)
    env = CustomEnvironment(render=True)  # True for display (creates the factory display window)
    env.reset()
    # model = sb.PPO('MlpPolicy', env=env, verbose=1, gamma=0.99)
    model = sb.PPO.load("./data/PPO_1s_128x2x2048_2.2_no_threading.zip", env=env, verbose=1, gamma=0.99)

    vec_env = model.get_env()
    obs = vec_env.reset()
    while True:
        action, _states = model.predict(obs, deterministic=True)
        obs, reward, done, _, info = env.step(action)


def custom_train():
    env = CustomEnvironment(render=False)  # True for display (creates the factory display window)
    # env.display_colors()
    net = MachineLearning.RainbowNetwork.RainbowNetwork
    ml_agent = RainbowLearning(state_d=env.observation_space.shape[0], action_d=env.action_space.n, net=net, lr=1e-3,
                               gamma=0.95, memory_size=1000, batch_size=256, alpha=0.2, beta=0.6, prior_eps=1e-6,
                               target_update=100, std_init=0.5, n_step=4, v_min=0, v_max=200)
    episodes = 1000                                                     # defines number of training episodes
    save_interval = 20                                                  # defines the saving rate (episodes)
    max_steps = 1024                                                    # defines episode lengths
    # ml_agent.load("Gen3_Sub6")
    highscore = None
    for e in range(episodes):
        steps = 0
        state = env.reset()
        state = state[0]  # ??
        ml_agent.set_state(state)
        done = False
        accu_reward = 0
        actions = []                                                    # for monitoring
        rewards = []                                                    # for monitoring
        while not done:
            env.step_start_time = time.time()
            # action_index = ml_agent.get_action_without_state()          # why?
            action_index = ml_agent.get_action(env.create_obs())        # added this line to replace the one above
            new_state, reward, done, _, info = env.step(action_index)
            actions.append(action_index)                                # for monitoring
            if steps > max_steps:                                       # should rather be in env.step()?
                done = True

                env.reset()  # env reset required when terminating(?)
                env.step_counter = 0

            ml_agent.add_memory_data(new_state, reward, done)
            accu_reward += reward
            rewards.append(reward)                                      # for monitoring
            steps += 1
            # TODO: Training more frequently (and within an episode) might enhance learning performance
            if steps % 128 == 0:
                ml_agent.train()

        ml_agent.train()
        sys.stdout.write(
            "\r" + "Epoch: " + str(e + 1) + " Score: " + str(accu_reward) + " last steps: " + str(steps) + "\n")
        # print(actions)                                                  # for monitoring
        # print(rewards)                                                  # for monitoring
        if e % save_interval == save_interval - 1:
            ml_agent.save("Gen4_Sub1")
            print(" saved")
            # time.sleep(0.2)
        if accu_reward > highscore:                                     # save the NN that achieved the highest score
            ml_agent.save("Gen4_Sub1_highscore")
            highscore = accu_reward
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


if __name__ == '__main__':
    print("Cuda is available: " + str(torch.cuda.is_available()))

    # test()
    sb_train()
    # sb_run_model()
    # custom_train()
