from MachineLearning import DQNNetworks
from MachineLearning.ActorCritic import ActorCritic
from MachineLearning.DQNFast import DQNFast


class MachineLearningEnvironment:
    def __init__(self, factory):
        self.agent = DQNFast(state_d=18, action_d=7, net=DQNNetworks.LargeNetActor, lr=1e-3,
                               gamma=0.99,
                               batch_size=1000, memory_size=10_000,
                               eps_start=0.10, eps_steps=50, eps_end=0.0, eps_step_by_done=True)
        #self.agent = ActorCritic(state_d=6, action_d=3, lr=1e-3, gamma=0.95, batch_size=10000,
        #                           eps_start=0.60, eps_steps=100, eps_end=0.0, eps_step_by_done=True)
        # self.agent.load("FTFDQLTestOne")
        self.factory = factory
        self.last_end_product_count = 0
        self.last_critical_conditions = 0

    def reset(self):
        self.last_end_product_count = 0
        self.last_critical_conditions = 0
        state = self.get_state()
        self.agent.set_state(state)

    def train(self, done=False):
        next_state = self.get_state()
        reward = self.get_reward()
        self.agent.add_memory_data(next_state, reward, done)
        self.agent.train()
        return reward

    def get_state(self):
        state = []
        for agv in self.factory.agvs:
            if agv.is_free:
                state.append(1)
            else:
                state.append(0)
            if agv.loaded_product is None:
                state.append(1)
            else:
                state.append(0)
        for machine in self.factory.machines:
            input_priority, output_priority = machine.get_buffer_status()
            state.append(input_priority)
            state.append(output_priority)
        return state

    def perform_action(self):
        action_index = self.agent.get_action_without_state()
        if action_index == 1:
            self.environment_set_action(self.factory.agvs[0], self.factory.warehouses[0], self.factory.machines[0])
        elif action_index == 2:
            self.environment_set_action(self.factory.agvs[0], self.factory.machines[0], self.factory.machines[1])
        elif action_index == 3:
            self.environment_set_action(self.factory.agvs[0], self.factory.machines[1], self.factory.warehouses[0])
        elif action_index == 4:
            self.unload_agv(self.factory.agvs[0], self.factory.warehouses[0])
        elif action_index == 5:
            self.environment_set_action(self.factory.agvs[1], self.factory.warehouses[0], self.factory.machines[0])
        elif action_index == 6:
            self.environment_set_action(self.factory.agvs[1], self.factory.machines[0], self.factory.machines[1])
        elif action_index == 7:
            self.environment_set_action(self.factory.agvs[1], self.factory.machines[1], self.factory.warehouses[0])
        elif action_index == 8:
            self.unload_agv(self.factory.agvs[1], self.factory.warehouses[0])

    @staticmethod
    def environment_set_action(agv, loading, unloading):
        if agv.is_free:
            product = unloading.input_products[0]
            if loading.has_product(product):
                agv.deliver(loading, unloading, product)

    def get_reward(self):
        reward = 0
        critical_conditions = 0
        product_count = len(self.factory.warehouses[0].end_product_store)
        if product_count > self.last_end_product_count:
            self.last_end_product_count = product_count
            reward = 1
        for machine in self.factory.machines:
            input_priority, output_priority = machine.get_buffer_status()
            if input_priority == 4:
                critical_conditions += 1
            if output_priority == 4:
                critical_conditions += 1
        if self.last_critical_conditions > critical_conditions:
            reward += 0.1
        self.last_critical_conditions = critical_conditions
        return reward
        # for product in self.factory.warehouses[0].end_product_store:
        #    if product.name == self.factory.warehouses[0].input_products[0]:
        #        the_count += 1

    @staticmethod
    def unload_agv(agv, unloading):
        agv.unload(unloading)

    def save(self):
        self.agent.save("FTFDQLTestOne")


'''
idle
agv0 - warehouse - factory
agv0 - factory - warehouse 
agv0 - unload
agv1 - warehouse - factory
agv1 - factory - warehouse
agv1 - unload
'''
