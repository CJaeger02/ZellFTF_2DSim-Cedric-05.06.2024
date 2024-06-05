import gc
import random
import threading

import numpy
import torch

from MachineLearning.Buffer import DiscreteBuffer
from MachineLearning.OutputRandomizer import RandomAction


def net_builder(layer_sizes, layer_activations):
    layers = []
    for i in range(len(layer_sizes) - 1):
        layers += [torch.nn.Linear(layer_sizes[i], layer_sizes[i + 1]), layer_activations[i]()]
    return torch.nn.Sequential(*layers)


class ActorNet(torch.nn.Module):
    def __init__(self, layer_sizes, layer_activations):
        super(ActorNet, self).__init__()
        self.lin = net_builder(layer_sizes, layer_activations)

    def forward(self, x):
        x = self.lin(x)
        return torch.nn.functional.softmax(x, dim=1)


class CriticNet(torch.nn.Module):
    def __init__(self, layer_sizes, layer_activations):
        super(CriticNet, self).__init__()
        self.q_net1 = net_builder(layer_sizes, layer_activations)
        self.q_net2 = net_builder(layer_sizes, layer_activations)

    def forward(self, x):
        q1 = self.q_net1(x)
        q2 = self.q_net2(x)
        return q1, q2


class ActorCritic:
    def __init__(self, state_d=2, action_d=2, net=None, lr=1e-3, gamma=0.95, batch_size=1000, eps_start=0.60,
                 eps_steps=100, eps_end=0.0, eps_step_by_done=False):
        # if net is None:
        #    raise ValueError('Error: Got no neural net class!')
        self.action_d = action_d
        self.lr = lr
        self.gamma = gamma
        self.tau = 0.01
        self.epsilon = 0
        # self.device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
        self.device = torch.device("cpu")
        self.batch_size, self.max_memory = batch_size, 100000
        self.eps_step_by_done = eps_step_by_done
        self.random_action = RandomAction(eps_start, eps_steps, eps_end, self.eps_step_by_done)
        self.memory = DiscreteBuffer(self.max_memory, state_d, self.device)
        self.actor = ActorNet([state_d, 100, action_d], [torch.nn.LeakyReLU, torch.nn.Identity]).to(self.device)
        self.critic = CriticNet([state_d, 100, action_d], [torch.nn.LeakyReLU, torch.nn.Identity]).to(self.device)
        self.critic_target = CriticNet([state_d, 100, action_d], [torch.nn.LeakyReLU, torch.nn.Identity]).to(
            self.device).train()
        self.critic_target.load_state_dict(self.critic.state_dict())
        self.optimizer_actor = torch.optim.Adam(self.actor.parameters(), lr=self.lr)
        self.optimizer_critic = torch.optim.Adam(self.critic.parameters(), lr=self.lr)
        self.criterion_actor = torch.nn.SmoothL1Loss()
        self.criterion_critic = torch.nn.SmoothL1Loss()

        self.alpha = 0.2
        self.h_mean = 0
        self.target_entropy = 0.6 * (-numpy.log(1 / self.action_d))
        self.log_alpha = torch.tensor(numpy.log(self.alpha), dtype=torch.float, requires_grad=True, device=self.device)
        self.alpha_optim = torch.optim.Adam([self.log_alpha], lr=self.lr)

        self.action = 0
        self.state = torch.FloatTensor([0.5, 0.5]).to(self.device)
        self.train_thread = None

    def set_state(self, state):
        self.state = torch.FloatTensor([state], device=self.device)

    def set_state_from_numpy(self, state):
        self.state = torch.unsqueeze(torch.from_numpy(state).to(self.device).to(torch.float), 0)

    def get_action(self, state, use_random_action=True):
        self.state = torch.FloatTensor([state]).to(self.device)
        return self.get_action_without_state(use_random_action)

    def get_action_from_numpy(self, state, use_action_noise=True):
        self.state = torch.unsqueeze(torch.from_numpy(state).to(self.device).to(torch.float), 0)
        return self.get_action_without_state(use_action_noise)

    def get_action_without_state(self, use_random_action=True):
        if use_random_action and self.random_action.get():
            self.action = int(random.random() * self.action_d)
            # action = torch.distributions.categorical.Categorical(probabilities).sample().item()
        else:
            with torch.no_grad():
                self.actor.eval()
                probability = self.actor(self.state)
                self.actor.train()
            self.action = torch.argmax(probability).item()
        return self.action

    def add_memory_data(self, next_state, reward, done, single_train=False, action=None):
        next_state = numpy.array(next_state)
        self.short_learning_step(next_state, reward, done, single_train, action)

    def add_memory_data_from_numpy(self, next_state, reward, done, single_train=False, action=None):
        self.short_learning_step(next_state, reward, done, single_train, action)

    def short_learning_step(self, next_state, reward, done, single_train=False, action=None):
        if action is None:
            action = self.action
        self.memory.add(self.state.cpu().numpy(), action, reward, next_state, done)  # popleft if MAX_MEMORY is reached
        next_state = torch.unsqueeze(torch.from_numpy(next_state).to(self.device).to(torch.float), 0)
        if single_train:
            self.learning_single(self.state, action, reward, next_state, done)
        self.state = next_state
        if self.eps_step_by_done and done:
            self.random_action.increment_done()

    def train(self, batch_size=None):
        if batch_size is None:
            batch_size = self.batch_size
        states, actions, rewards, next_states, dones = self.memory.sample(batch_size)
        if self.train_thread is not None:
            if self.train_thread.is_alive():
                self.train_thread.join()
        self.train_thread = threading.Thread(target=self.train_algorithm,
                                             args=(states, actions, rewards, next_states, dones))
        self.train_thread.start()
        #self.train_algorithm(states, actions, rewards, next_states, dones)

    def learning_single(self, state, action, reward, next_state, done):
        action = torch.LongTensor([[action]]).to(self.device)
        reward = torch.FloatTensor([[reward]]).to(self.device)
        done = torch.LongTensor([[done]]).to(self.device)
        if self.train_thread is not None:
            if self.train_thread.is_alive():
                self.train_thread.join()
        self.train_thread = threading.Thread(target=self.train_algorithm,
                                             args=(state, action, reward, next_state, done))
        self.train_thread.start()
        #self.train_algorithm(state, action, reward, next_state, done)

    def train_algorithm(self, states, actions, rewards, next_states, dones):
        with torch.no_grad():
            next_probabilities = self.actor(next_states)
            next_log_probabilities = torch.log(next_probabilities + 1e-8)
            next_q1, next_q2 = self.critic_target(next_states)
            min_next_q = torch.min(next_q1, next_q2)
            next_values = torch.sum(next_probabilities * (min_next_q - self.alpha * next_log_probabilities), dim=1,
                                    keepdim=True)
            target_q = rewards + (~dones) * self.gamma * next_values

        q1, q2 = self.critic(states)
        q1, q2 = q1.gather(1, actions), q2.gather(1, actions)
        critic_loss = self.criterion_critic(q1, target_q) + self.criterion_critic(q2, target_q)
        self.optimizer_critic.zero_grad()
        critic_loss.backward()
        self.optimizer_critic.step()

        for params in self.critic.parameters():
            params.requires_grad = False
        probabilities = self.actor(states)
        log_probabilities = torch.log(probabilities + 1e-8)
        with torch.no_grad():
            q1, q2 = self.critic(states)
        min_q = torch.min(q1, q2)
        actor_loss = torch.sum(probabilities * (self.alpha * log_probabilities - min_q), dim=1, keepdim=True)
        self.optimizer_actor.zero_grad()
        actor_loss.mean().backward()
        self.optimizer_actor.step()
        for params in self.critic.parameters():
            params.requires_grad = True

        with torch.no_grad():
            self.h_mean = -torch.sum(probabilities * log_probabilities, dim=1).mean()
        alpha_loss = self.log_alpha * (self.h_mean - self.target_entropy)
        self.alpha_optim.zero_grad()
        alpha_loss.backward()
        self.alpha_optim.step()
        self.alpha = self.log_alpha.exp().item()

        del states, actions, rewards, next_states, dones, next_probabilities, next_log_probabilities, next_q1, next_q2
        del min_next_q, next_values, target_q, q1, critic_loss, probabilities, log_probabilities, min_q, actor_loss, alpha_loss
        gc.collect()

        self.soft_target_update()

    def soft_target_update(self):
        # Soft update of the target network's weights
        # θ′ ← τ θ + (1 −τ )θ′
        critic_target_net_state_dict = self.critic_target.state_dict()
        critic_net_state_dict = self.critic.state_dict()
        for key in critic_net_state_dict:
            critic_target_net_state_dict[key] = critic_net_state_dict[key] * self.tau + \
                                                critic_target_net_state_dict[key] * (1 - self.tau)
        self.critic_target.load_state_dict(critic_target_net_state_dict)

    def load(self, name):
        self.actor.load(name)
        self.critic.load(name)
        self.critic_target.load_state_dict(self.critic.state_dict())

    def save(self, name):
        # self.actor.save(name)
        # self.critic.save(name)
        pass
