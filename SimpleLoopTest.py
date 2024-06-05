import sys
import time
import pygame
import pandas
import random
import matplotlib
import matplotlib.pyplot as plt

from FactoryObjects.Factory import Factory
# from MachineLearning.MachineLearningEnvironment import MachineLearningEnvironment

is_ipython = 'inline' in matplotlib.get_backend()
if is_ipython:
    from IPython import display


class LoopTest:
    def __init__(self):
        self.factory = Factory()
        self.factory.create_temp_factory_machines()
        self.time_step = 0.1
        self.simulation_speed = 5

        self.pixel_size = 50
        self.height = self.factory.length
        self.width = self.factory.width
        self.reference_size = self.factory.cell_size * 1000
        self.screen = None

        plt.ion()
        self.agvs_workload = []
        self.machines_workload = []
        self.system_stock_data = [0.0]
        self.system_transport_data = [0.0]
        for i in range(len(self.factory.agvs)):
            self.agvs_workload.append([0])
        for i in range(len(self.factory.machines)):
            self.machines_workload.append([0])
        self.mle = None
        self.state = "idle"
        self.step_counter = 0
        self.agv_positioning = [1, 1]
        self.coupling_master = None
        self.output_object = None
        self.agv_couple_count = 0
        self.sleep_time = 0.0001
        self.factory_index_list = list(range(len(self.factory.machines)))

    def run_display(self):
        #print("warehouse source_products: %s" % self.factory.warehouses[0].source_products)
        #print("machine input_products: %s" % self.factory.machines[0].input_products)
        #print(self.factory.machines[0].get_status())
        #print("agv max speed: %s" % self.factory.agvs[0].max_speed)
        #print(f"agv position : {self.factory.agvs[0].pos_x}, {self.factory.agvs[0].pos_y}")
        pygame.init()
        # Create pygame display. Calculate window width and height based on color_data dimensions and pixel size
        self.screen = pygame.display.set_mode((self.width * self.pixel_size, self.height * self.pixel_size))
        pygame.display.set_caption('Color Data Display')
        color_grid = self.factory.get_color_grid()
        self.display_colors(color_grid)
        real_time_lapsed = 0
        start_time = time.time()
        last_time = start_time
        self.step_counter = 0   # Counts every simulation step. (Frame counter)
        speed_time_step = self.time_step / self.simulation_speed    # Calculation for the accelerated step time
        speed_sleep_time = speed_time_step / 4  # Sleep time. Small enough to not get over the time edge
        while real_time_lapsed < 600:   # Simulation time in seconds. Real Time!
            time.sleep(speed_sleep_time)
            current_time = time.time()
            delta_sim_time = (current_time - last_time)
            if delta_sim_time < speed_time_step:    # if the time is not done, go back th the while commandline
                continue
            last_time += speed_time_step
            real_time_lapsed = current_time - start_time
            self.agv_basic_controller_step()
            self.collect_data()  # collects data for csv and  plot, needs to be active for self.plot_durations()
            if (self.step_counter % self.simulation_speed) == 0:
                self.display_colors(color_grid)  # Updates the pygame display
                self.time_convert(real_time_lapsed)  # prints current time in console
            if (self.step_counter % 1000) == 0:
                self.plot_durations()  # plots data
            self.step_counter += 1

        self.plot_durations(True)
        # self.write_csv()
        pygame.quit()
        plt.ioff()
        plt.show()
        self.factory.shout_down()

    def run(self):
        for self.step_counter in range(10000):  # Do x steps, attention: depends on time_step
            self.agv_basic_controller_step()
            self.collect_data()
            if self.step_counter % 100 == 0:
                self.plot_durations()
        self.plot_durations(True)
        plt.ioff()
        plt.show()
        self.factory.shout_down()

    @staticmethod
    def time_convert(sec):
        mins = sec // 60
        sec = sec % 60
        hours = mins // 60
        mins = mins % 60

        sys.stdout.write("\rTime Lapsed = {0}:{1}:{2}".format(int(hours), int(mins), sec))

    def agv_basic_controller_step(self):
        self.block_until_synchronized()
        self.simulate_factory_objects()
        if self.state == 'idle' or self.state == 'deliver':
            self.find_delivery_pair()
        elif self.state == 'couple':  # agv.unload_if_stuck() prevents the system for unlimited waiting time
            self.command_agvs_to_couple()

    def block_until_synchronized(self):
        all_synchronized = True
        for i in range(100):
            all_synchronized = True
            for agv in self.factory.agvs:
                if agv.step_counter_last < self.step_counter-1:
                    all_synchronized = False
                    break
            if all_synchronized:
                break
            time.sleep(self.sleep_time)
        if not all_synchronized:
            print("\n\n !!! ERROR can not synchronize !!!\n\n")
            print(self.step_counter, self.factory.agvs[0].step_counter_next,
                  self.factory.agvs[0].step_counter_last, self.factory.agvs[1].step_counter_last,
                  self.factory.agvs[2].step_counter_last, self.factory.agvs[3].step_counter_last,
                  self.factory.agvs[4].step_counter_last, self.factory.agvs[5].step_counter_last)

    def simulate_factory_objects(self):
        for agv in self.factory.agvs:
            agv.step(self.time_step, self.step_counter)
        for warehouse in self.factory.warehouses:
            warehouse.step(self.time_step)
        for machine in self.factory.machines:
            machine.step(self.time_step)

    def find_delivery_pair(self):
        # random.shuffle(self.factory.agvs)  # Only needed if agv accumulators are simulated
        for agv in self.factory.agvs:
            if agv.is_free:
                if random.random() >= 0.5:
                    found = self.find_delivery_pair_warehouse(agv)
                    if found:
                        return
                    found = self.find_delivery_pair_machine(agv)
                    if found:
                        return
                else:
                    found = self.find_delivery_pair_machine(agv)
                    if found:
                        return
                    found = self.find_delivery_pair_warehouse(agv)
                    if found:
                        return

    def find_delivery_pair_warehouse(self, agv):
        for warehouse in self.factory.warehouses:
            found = self.find_input_product(warehouse, agv)
            if found:
                return found

    def find_delivery_pair_machine(self, agv):
        random.shuffle(self.factory_index_list)
        for i in range(len(self.factory_index_list)):
            if self.factory.machines[self.factory_index_list[i]].get_buffer_status()[0] > 0:
                found = self.find_input_product(self.factory.machines[self.factory_index_list[i]], agv)
                if found:
                    return found
        return False

    def find_input_product(self, input_object, agv):
        for product in input_object.input_products:
            output_object = self.find_delivery_pair_for_input(product)
            if output_object is not None:
                self.agv_positioning = self.factory.get_agv_needed_for_product(product, agv)
                if self.agv_positioning[0] > 1 or self.agv_positioning[1] > 1:
                    self.coupling_master = agv
                    self.agv_couple_count = self.agv_positioning[0] * self.agv_positioning[1] - 1
                    self.state = 'couple'
                    self.output_object = output_object
                    agv.coupling(self.coupling_master, [0, 0], self.agv_couple_count, output_object, input_object,
                                 product, self.agv_positioning)     #creates master - slaves will find itself since factory.state = 'couple'
                else:
                    agv.deliver(output_object, input_object, product)
                return True

    def find_delivery_pair_for_input(self, product):
        for warehouse in self.factory.warehouses:
            if warehouse.has_product(product):
                return warehouse
        for machine in self.factory.machines:
            if machine.has_product(product):
                return machine
        return None

    def command_agvs_to_couple(self):
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
                    agv.coupling(self.coupling_master, pos, output_object=self.output_object)
                    self.agv_couple_count -= 1
                    return
        else:
            self.state = 'deliver'

    def display_colors(self, color_data):
        """
        Display a 2D list of color data using pygame.

        :param color_data: 2D list of RGB values.
        """

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
                              agv.width / self.reference_size * self.pixel_size, agv.length / self.reference_size * self.pixel_size),
                             border_radius=3)

        for agv in self.factory.agvs:
            if agv.loaded_product is not None:
                agv_pos = [agv.pos_x, agv.pos_y]
                pygame.draw.rect(self.screen, [180, 180, 0],
                                 (agv_pos[0] * self.pixel_size + 2,
                                  agv_pos[1] * self.pixel_size + 2,
                                  agv.loaded_product.width / self.reference_size * self.pixel_size, agv.loaded_product.length / self.reference_size * self.pixel_size))

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

    def collect_data(self):
        for i in range(len(self.factory.agvs)):
            if ((self.factory.agvs[i].status != 'idle' or self.factory.agvs[i].status != 'unload_product') and self.factory.agvs[i].loaded_product is not None or
                    self.factory.agvs[i].coupling_master is not None and self.factory.agvs[i].coupling_master.loaded_product is not None):
                workload = 1  # if agv is loaded by itself or master is loaded
            else:
                workload = 0

            workload += self.agvs_workload[i][-1] * len(self.agvs_workload[i])
            workload /= len(self.agvs_workload[i]) + 1
            self.agvs_workload[i].append(workload)

        for i in range(len(self.factory.machines)):
            workload = 0
            if self.factory.machines[i].get_status() == 'process':
                workload = 1
            workload += self.machines_workload[i][-1] * len(self.machines_workload[i])
            workload /= len(self.machines_workload[i]) + 1
            self.machines_workload[i].append(workload)

        self.get_system_stock_data()
        self.get_transport_stock_data()

    def get_system_stock_data(self):
        count = 0
        for product in self.factory.products:
            if product.stored_in != self.factory.warehouses[0]:
                count += 1
        mean = (self.system_stock_data[-1] * len(self.system_stock_data) + count) / (len(self.system_stock_data) + 1)
        self.system_stock_data.append(mean)

    def get_transport_stock_data(self):
        count = 0
        for product in self.factory.products:
            for agv in self.factory.agvs:
                if product.stored_in == agv:
                    count += 1
                    break
        mean = (self.system_transport_data[-1] * len(self.system_transport_data) + count) / (len(self.system_transport_data) + 1)
        self.system_transport_data.append(mean)

    def plot_durations(self, show_result=False):
        # plt.figure(1)
        plt.clf()
        plt.subplot(1, 2, 1)  # row 1, column 2, count 1
        plt.plot(self.system_transport_data, label='transport stock', color='r', linewidth=4)
        plt.plot(self.system_stock_data, label='system stock', color='g', linewidth=2)
        if show_result:
            plt.title('Result')
        else:
            plt.title('Running...')
        plt.xlabel('Time in 0.1s Steps')
        plt.ylabel('Count')
        plt.legend()

        # using subplot function and creating plot two
        # row 1, column 2, count 2
        plt.subplot(1, 2, 2)
        for i in range(len(self.agvs_workload)):
            plt.plot(self.agvs_workload[i], label='AGV ' + str(i), linewidth=4-i)
        for i in range(len(self.machines_workload)):
            plt.plot(self.machines_workload[i], label='Machine ' + str(i), linewidth=4-i)
        plt.title('Workload')
        plt.xlabel('Time in 0.1s Steps')
        plt.ylabel('Count')
        plt.legend()

        plt.tight_layout(pad=1.0)
        plt.pause(0.001)  # pause a bit so that plots are updated
        if is_ipython:
            if not show_result:
                display.display(plt.gcf())
                display.clear_output(wait=True)
            else:
                display.display(plt.gcf())

    def collect_train_data(self, reward):
        self.system_stock_data.append(len(self.factory.warehouses[0].end_product_store))
        self.system_transport_data.append(reward)

    def plot_training(self, show_result=False):
        plt.figure(1)
        if show_result:
            plt.clf()
            plt.title('Result')
        else:
            plt.clf()
            plt.title('Running...')
        plt.xlabel('Time in 0.1s Steps')
        plt.ylabel('Products')
        plt.plot(self.system_stock_data, label='Finished Products', color='b', linewidth=3, linestyle=':')
        plt.plot(self.system_transport_data, label='Reward', color='g', linewidth=2)
        plt.legend()
        plt.pause(0.001)  # pause a bit so that plots are updated
        if is_ipython:
            if not show_result:
                display.display(plt.gcf())
                display.clear_output(wait=True)
            else:
                display.display(plt.gcf())

    def write_csv(self):
        data = pandas.DataFrame({'system stock': self.system_transport_data,
                                 'transport stock': self.system_stock_data})
        for i in range(len(self.agvs_workload)):
            data['AGV ' + str(i)] = self.agvs_workload[i]
        for i in range(len(self.machines_workload)):
            data['Machine ' + str(i)] = self.machines_workload[i]
        data.to_csv('C:/Users/Fengler/Downloads/ZellFTFData.csv', index=False, sep=';', decimal=',')


if __name__ == '__main__':
    LoopTest().run_display()
    # LoopTest().run()


'''
    # LoopTest().run_deep_learning_fast()
    # LoopTest().run_deep_learning_display()

    def run_deep_learning_fast(self):
        self.mle = MachineLearningEnvironment(self.factory)
        for e in range(10):
            self.mle.reset()
            self.factory.reset()
            self.step_counter = 0
            done = False
            while not done:
                self.step_counter += 1
                self.mle.perform_action()
                self.simulate_factory_objects()
                if self.step_counter > 2000:
                    done = True
                reward = self.mle.train(done)
                self.collect_train_data(reward)
                if self.step_counter % 100 == 0:
                    self.plot_training()
            print("Reset End Products:", self.system_stock_data[-1])
        # self.mle.save()
        print("Done")
        self.plot_training(True)
        plt.ioff()
        plt.show()
        self.factory.shout_down()

    def run_deep_learning_display(self):
        self.mle = MachineLearningEnvironment(self.factory)
        pygame.init()
        # Calculate window width and height based on color_data dimensions and pixel size
        self.screen = pygame.display.set_mode((self.width * self.pixel_size, self.height * self.pixel_size))
        pygame.display.set_caption('Color Data Display')
        color_grid = self.factory.get_color_grid()
        self.display_colors(color_grid)
        self.simulation_speed = 5

        real_time_lapsed = 0
        start_time = time.time()
        last_time = start_time
        self.step_counter = 0
        speed_time_step = self.time_step / self.simulation_speed
        speed_sleep_time = speed_time_step / 4

        for e in range(10):
            start_time = time.time()
            last_time = start_time
            self.factory.reset()
            self.mle.reset()
            done = False
            while not done:
                time.sleep(speed_sleep_time)
                current_time = time.time()
                delta_sim_time = (current_time - last_time)
                if delta_sim_time < speed_time_step:
                    continue
                last_time += speed_time_step
                real_time_lapsed = current_time - start_time
                self.mle.perform_action()
                self.simulate_factory_objects()
                if real_time_lapsed > 180:
                    done = True
                self.mle.train(done)
                #self.collect_data()
                if (self.step_counter % self.simulation_speed) == 0:
                    self.display_colors(color_grid)
                    # self.plot_durations()
                    self.time_convert(real_time_lapsed)
                self.step_counter += 1
            #self.mle.save()

        self.plot_durations(True)
        plt.ioff()
        plt.show()
        self.factory.shout_down()

'''