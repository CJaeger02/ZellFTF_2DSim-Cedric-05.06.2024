import math
import time
import config

import threading


class AGV:
    def __init__(self, start_position=None):
        if start_position is None:
            self.start_position = [0, 0]
        else:
            self.start_position = start_position
        self.max_speed = config.agv['max_speed']
        self.load_speed = config.agv['load_speed']
        self.couple_speed = config.agv['couple_speed']
        self.length = config.agv['length']
        self.width = config.agv['width']
        self.payload = config.agv['payload']
        self.pos_x = self.start_position[0]
        self.pos_y = self.start_position[1]
        self.factory = None
        self.is_free = True  # True when AGV can receive new command
        self.command = 'idle'  # there are 5 commands: 'idle', 'move', 'deliver', 'coupling', 'follow_master'
        self.status = 'idle'  # there are 8 statuses: 'idle', 'move_to_input', 'move_to_output', 'load_product',
                        # 'unload_product', 'move_to_coupling_position', 'master_slave_decision', 'wait_for_coupling'
        self.idle_time = 0
        self.max_idle_time = 10  # seconds
        self.move_target = [0, 0]
        self.output_object = None
        self.input_object = None
        self.loaded_product = None
        self.target_product = None
        self.coupling_master = None
        self.agv_couple_count = 0
        self.coupling_time_max = 2.0
        self.coupling_time = 0.0
        self.coupling_position = [3, 3]
        self.coupling_formation_position = [0, 0]

        self.task_number = 0      # added for NN observation    - 0 represents 'no task'

        # Threading !!! There is a possibility of an asynchronous behavior. If this is happening implement frame counter
        # TODO integrate a threading attribute (related to 'def run_with_threads(self):'-TODO)
        self.thread_running = True
        self.thread_waiting = True
        self.time_step = 0.0
        self.waited_time = 0.0
        self.sleep_time = 0.00001
        # self.run_thread = threading.Thread(target=self.run_with_threads)
        # self.run_thread.start()
        self.step_counter_last = 0
        self.step_counter_next = 1  # was once initialized with 0
        self.coupled_size = [1, 1]

        self.is_slave = False
        self.unload_stucked_agvs = False
        self.is_moving = False

    def reload_settings(self):
        self.max_speed = config.agv['max_speed']
        self.length = config.agv['length']
        self.width = config.agv['width']
        self.payload = config.agv['payload']
        self.pos_x = self.start_position[0]
        self.pos_y = self.start_position[1]

    def reset(self):
        self.is_free = True
        self.step_counter_last = 0
        self.step_counter_next = 1  # was once initialized with 0
        self.thread_waiting = True
        self.command = 'idle'
        self.status = 'idle'
        self.output_object = None
        self.input_object = None
        self.loaded_product = None
        self.target_product = None
        self.pos_x = self.start_position[0]
        self.pos_y = self.start_position[1]
        self.coupling_master = None
        self.agv_couple_count = 0

        self.task_number = 0
        self.move_target = [self.pos_x, self.pos_y]  # relevant for is_moving() function

        self.is_slave = False
        self.is_moving = False
        self.unload_stucked_agvs = False

    def set_target(self, target):
        self.move_target = target
        self.command = 'move'

    def unload(self, input_object):
        if self.loaded_product is None:
            self.command = 'idle'
            self.status = 'idle'
            self.is_free = True
            self.task_number = 0
            self.move_to_loading_station()
            return
        self.input_object = input_object
        self.move_target = input_object.pos_input
        self.is_free = False
        self.command = 'deliver'
        self.status = 'move_to_input'

    def deliver(self, output_object, input_object, product_name):
        self.output_object = output_object
        self.input_object = input_object
        self.target_product = product_name
        self.is_free = False
        self.command = 'deliver'

    def coupling(self, coupling_master, paring_formation_position, agv_couple_count=1, output_object=None,
                 input_object=None, product_name=None, coupled_size=None):
        self.is_free = False
        if coupled_size is None:
            coupled_size = [1, 1]
        self.output_object = output_object
        self.input_object = input_object
        self.target_product = product_name
        self.command = 'coupling'
        self.coupling_master = coupling_master
        self.coupling_formation_position = paring_formation_position
        self.agv_couple_count = agv_couple_count
        self.coupled_size = coupled_size

    def run_with_threads(self):     # !CAUTION! compare _simulate_factory_objects in StableBaselinesLearningTest.py
        while self.thread_running:
            time.sleep(0.0005)    # allows up to roughly 1000 fps (1/0.0005/2)
            if not self.thread_waiting:
                self.step_command()
                self.thread_waiting = True
                self.step_counter_last = self.step_counter_next
    # TODO create a solution with one run function (test for threading)

    def run_without_threads(self):  # !CAUTION! compare _simulate_factory_objects in StableBaselinesLearningTest.py
        self.step_command()
        self.step_counter_last = self.step_counter_next

    def step(self, time_step, step_counter):
        self.step_counter_next = step_counter
        self.time_step = time_step
        self.thread_waiting = False

    def step_command(self):
        if self.command == 'move':
            if self.move_state():
                self.command = 'idle'
        elif self.command == 'deliver':  # master_agvs (includes solo) only
            self.deliver_state()
        elif self.command == 'coupling':
            self.coupling_agv()
        elif self.command == 'follow_master':
            self.follow_master()
        if self.command == 'idle':
            self.is_moving = False
            self.idle_time += self.time_step
        else:
            self.idle_time = 0

    def move_state(self):
        self.is_moving = True
        move_vector = [self.move_target[0] - self.pos_x, self.move_target[1] - self.pos_y]
        distance = math.sqrt(math.pow(move_vector[0], 2) + math.pow(move_vector[1], 2))
        if distance < 1:    # TODO [inelegant] value has to equal time_step of main prog. (1 m/s * t = VALUE(t) m)
            self.pos_x = self.move_target[0]
            self.pos_y = self.move_target[1]
            return True
        norm = 1 / distance
        move_vector = [norm * move_vector[0], norm * move_vector[1]]
        if self.coupling_master == self:
            speed = self.couple_speed
        elif self.loaded_product is not None:
            speed = self.load_speed
        else:
            speed = self.max_speed
        distance_vector = [move_vector[0] * speed * self.time_step, move_vector[1] * speed * self.time_step]
        self.pos_x += distance_vector[0]
        self.pos_y += distance_vector[1]
        return False

    def deliver_state(self):
        if self.status == 'idle':
            self.move_target = self.output_object.pos_output
            self.move_state()
            self.status = 'move_to_output'
        elif self.status == 'move_to_output':
            if self.move_state():
                self.status = 'load_product'
        elif self.status == 'load_product':
            self.is_moving = False
            product = self.output_object.handover_output_product(self.target_product)
            if self.load_product(product):
                # added for RL
                self.is_free = False
                # For RL AGVs become locked
                for agv in self.factory.agvs:
                    if agv.coupling_master == self:
                        agv.is_free = False
                self.move_target = self.input_object.pos_input
                self.status = 'move_to_input'
            else:
                # added for RL
                self.is_free = True
                # For RL AGVs become locked
                for agv in self.factory.agvs:
                    if agv.coupling_master == self:
                        agv.is_free = True
        elif self.status == 'move_to_input':
            if self.move_state():
                self.status = 'unload_product'
                self.waited_time = 0.0
        elif self.status == 'unload_product':
            self.is_moving = False
            if self.input_object.handover_input_product(self.loaded_product):
                self.loaded_product = None
                self.decouple()
                self.is_free = True
                self.task_number = 0
                self.command = 'idle'
                self.status = 'idle'
            else:
                self.unload_if_stuck()  # TODO (find better solution for NN)

    def load_product(self, product):
        if self.loaded_product is None and product is not None:
            if (product.width > self.width * self.coupled_size[0]
                    or product.length > self.length * self.coupled_size[1]
                    or product.weight > self.payload * (self.agv_couple_count+1)):  # slaves + master
                return False
            self.loaded_product = product
            self.loaded_product.stored_in = self
            return True
        return False

    def move_to_loading_station(self):
        for loading_station in self.factory.loading_stations:
            if loading_station.register_agv(self):
                self.set_target([loading_station.pos_x, loading_station.pos_y])
                return

    def unload_if_stuck(self):
        # self.waited_time += self.time_step
        # if self.waited_time > self.input_object.process_time:
        # TODO not elegant
        if self.unload_stucked_agvs:        # same every step for every agv - True for the 0 actions else False
            self.input_object = self.factory.warehouses[0]
            self.move_target = self.input_object.pos_input
            self.status = 'move_to_input'

    def coupling_agv(self):
        if self.status == 'idle':
            self.move_target = [self.output_object.pos_output[0] + self.coupling_formation_position[0]/2,
                                self.output_object.pos_output[1] + self.coupling_formation_position[1]/2]
            self.move_state()
            self.status = 'move_to_coupling_position'
        elif self.status == 'move_to_coupling_position':
            if self.move_state():
                self.status = 'master_slave_decision'
        elif self.status == 'master_slave_decision':
            self.is_moving = False
            if self.coupling_master == self:
                self.status = 'wait_for_coupling'
                # for RL
                self.is_free = True  # enables NN to direct AGVs somewhere else HAS TO BE AFTER 'waiting_for_coupling'
            else:
                self.command = 'follow_master'
                # for RL
                self.is_free = True  # enables NN to direct AGVs somewhere else HAS TO BE AFTER 'following_master'
                self.status = 'idle'
        elif self.status == 'wait_for_coupling':
            if self.is_coupling_complete():  # only master
                self.command = 'deliver'
                # self.status = 'idle'  # TODO reactivate if possible (does this line break anything?)
                self.status = 'load_product'

    def will_coupling_be_complete(self):
        slave_count = 0
        for agv in self.factory.agvs:
            if agv != self and agv.coupling_master == self:
                slave_count += 1
        if self.agv_couple_count == slave_count:
            return True
        elif self.agv_couple_count < slave_count:
            print("AGV", str(self), "has more assigned slaves than mandatory")
        return False

    def is_coupling_complete(self):
        slave_count = 0
        for agv in self.factory.agvs:
            if agv != self and agv.coupling_master == self:
                if agv.command == 'follow_master':      # necessary ?
                    slave_count += 1
        if self.agv_couple_count == slave_count:
            # For RL AGVs become locked (coupling_process)
            for agv in self.factory.agvs:
                if agv.coupling_master == self:
                    agv.is_free = False
            self.coupling_time += self.time_step
            if self.coupling_time >= self.coupling_time_max:
                self.coupling_time = 0
                return True
        elif self.agv_couple_count < slave_count:
            print("AGV", str(self), "has more assigned slaves than mandatory")
        return False

    def decouple(self):
        if self.coupling_master is not None:
            for agv in self.factory.agvs:
                if agv != self and agv.coupling_master == self:     # effects slaves
                    agv.is_slave = False
                    agv.command = 'idle'        # status of slaves is 'idle' (already)
                    agv.is_free = True
                    agv.task_number = 0         # nothing task
                    agv.coupling_master = None
                    agv.is_moving = False
            self.coupling_master = None
            self.coupled_size = [1, 1]
            self.agv_couple_count = 0

    def follow_master(self):
        if self.coupling_master is not None:
            # The following is obsolete
            # [why would the coupling master vanish and how do time_step relations matter (synchronization is ensured)]
            '''
            for _ in range(1000):
                time.sleep(self.sleep_time)
                 # QUESTION: How does the time_step comparison work?
                if self.coupling_master is None or self.coupling_master.step_counter_last == self.step_counter_next:   
                    break
            if self.coupling_master is None:
                self.task_number = 0
                return
            '''
            # unless master is still moving to coupling position slaves should follow him
            if self.coupling_master.status != 'move_to_coupling_position':
                self.move_target = [self.coupling_master.pos_x + self.coupling_formation_position[0] * self.width / (
                        self.factory.cell_size * 1000),
                                    self.coupling_master.pos_y + self.coupling_formation_position[1] * self.length / (
                                            self.factory.cell_size * 1000)]

            if self.coupling_master.is_moving:
                if self.coupling_master.status not in ['move_to_coupling_position', 'master_slave_decision']:
                    self.move_state()
        else:
            print("MISTAKE: AGV is following a none existing master")

    def get_middle_position(self):
        return [self.pos_x, self.pos_y]

    def is_moving_(self):   # not needed after implementation of self.is_moving boolean
        if self.move_target != [self.pos_x, self.pos_y]:
            return True
        elif self.coupling_master:
            if self.command == 'follow_master':
                if self.coupling_master.move_target != [self.coupling_master.pos_x, self.coupling_master.pos_y]:
                    return True
        return False

    def free_from_coupling(self):   # CAUTION WHEN USING THIS - make sure the right task_number is assigned afterwards
        self.is_slave = False
        self.command = 'idle'
        self.status = 'idle'
        self.is_free = True
        self.task_number = 0
        self.coupling_master = None
        self.coupled_size = [1, 1]
        self.agv_couple_count = 0

        self.task_number = 0
        self.move_target = [self.pos_x, self.pos_y]
        self.is_moving = False

        self.output_object = None
        self.input_object = None
        self.loaded_product = None
        self.target_product = None
