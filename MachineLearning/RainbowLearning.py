import gc
import random

import torch
from torch.nn.modules import loss

from MachineLearning.Buffer import PrioritizedReplayBuffer, NStepDiscreteBuffer


class RainbowLearning:
    """DQN Agent interacting with environment.

        Attribute:
            state_d (int): size of state space
            action_d (int): size of action space
            net (nn.Module): neural network
            lr (float): learning rate
            gamma (float): discount factor
            memory (PrioritizedReplayBuffer): replay memory to store transitions
            memory_size (int): max memory for the batches
            batch_size (int): batch size for sampling
            alpha (float): alpha parameter for prioritized replay buffer for max priorities
            beta (float): beta parameter for prioritized replay buffer for sample weights
            prior_eps (float): prior eps parameter for prioritized replay buffer for updating priorities
            target_update (int): period for target model's hard update
            std_init (float): standard deviation for the noisy net
            n_step (int): step number to calculate n-step td error
            v_min (float): min value of support in the net
            v_max (float): max value of support in the net
            atom_size (int): the unit number of support in the net
        """

    def __init__(self, state_d: int, action_d: int, net=None, lr=1e-3, gamma: float = 0.95,
                 memory_size: int = 1024, batch_size: int = 256, alpha: float = 0.2, beta: float = 0.6,
                 prior_eps: float = 1e-6, target_update: int = 100, std_init: float = 0.5, n_step: int = 2,
                 v_min: float = 0.0, v_max: float = 200.0, atom_size: int = 20):
        if net is None:
            raise ValueError('Error: Got no neural net class!')

        self.gamma = gamma
        self.batch_size = batch_size
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

        # categorical
        self.v_min = v_min
        self.v_max = v_max
        self.atom_size = atom_size
        self.support = torch.linspace(self.v_min, self.v_max, self.atom_size).to(self.device)

        self.target_update = target_update
        self.target_update_counter = 0

        self.memory = PrioritizedReplayBuffer(memory_size, self.batch_size, state_d, self.device, n_step, self.gamma, alpha)
        self.policy_net = net(state_d, action_d, atom_size, self.support, std_init).to(self.device)
        self.target_net = net(state_d, action_d, atom_size, self.support, std_init).to(self.device)
        self.target_net.load_state_dict(self.policy_net.state_dict())
        self.target_net.eval()
        self.optimizer = torch.optim.AdamW(self.policy_net.parameters(), lr=lr)
        self.action = 0
        self.state = torch.FloatTensor([0.5, 0.5]).to(self.device)
        self.train_thread = None

        self.beta = beta
        self.prior_eps = prior_eps
        self.memory = PrioritizedReplayBuffer(
            memory_size, batch_size, state_d, self.device, n_step, gamma, alpha
        )

        self.use_n_step = True if n_step > 1 else False
        if self.use_n_step:
            self.n_step = n_step
            self.memory_n = NStepDiscreteBuffer(memory_size, self.batch_size, state_d, self.device, n_step, self.gamma)

    def set_state(self, state):
        self.state = torch.tensor([state], device=self.device, dtype=torch.float)

    def set_state_from_numpy(self, state):
        self.state = torch.unsqueeze(torch.from_numpy(state).to(self.device).to(torch.float), 0)

    def get_action(self, state):
        self.state = torch.tensor([state], device=self.device, dtype=torch.float)
        return self.get_action_without_state()

    def get_action_from_numpy(self, state):
        self.state = torch.unsqueeze(torch.from_numpy(state).to(self.device).to(torch.float), 0)
        return self.get_action_without_state()

    def get_action_without_state(self):
        with torch.no_grad():
            probability = self.policy_net(self.state)
        self.action = torch.argmax(probability).item()
        return self.action

    def add_memory_data(self, next_state, reward, done, action=None):
        next_state = torch.tensor([next_state], device=self.device, dtype=torch.float)
        self.add_data_to_memories(next_state, reward, done, action)

    def add_memory_data_from_numpy(self, next_state, reward, done, action=None):
        next_state = torch.unsqueeze(torch.from_numpy(next_state).to(self.device).to(torch.float), 0)
        self.add_data_to_memories(next_state, reward, done, action)

    def add_data_to_memories(self, next_state, reward, done, action=None):
        if action is None:
            action = self.action

            # N-step transition
            if self.use_n_step:
                one_step_transition = self.memory_n.add(self.state, action, reward, next_state, done)
            # 1-step transition
            else:
                one_step_transition = (self.state, action, reward, next_state, done)

            # add a single step transition
            if one_step_transition:
                self.memory.add(*one_step_transition)
        else:
            print("action error")
        self.state = next_state


    def train(self):
        states, actions, rewards, next_states, dones, weights, indices = self.memory.sample_batch(self.beta)
        if states is not None:
            self.q_learning_batch(states, actions, rewards, next_states, dones, weights, indices)

    def q_learning_batch(self, states, actions, rewards, next_states, dones, weights, indices):
        elementwise_loss = self.compute_loss(states, actions, rewards, next_states, dones, self.gamma)

        loss_rain = torch.mean(elementwise_loss * weights)

        if self.use_n_step:
            n_gamma = self.gamma ** self.n_step
            n_states, n_action, n_rewards, n_next_states, n_dones = self.memory_n.sample_batch_from_indices(indices)
            elementwise_n_loss = self.compute_loss(n_states, n_action, n_rewards, n_next_states, n_dones, n_gamma)
            elementwise_loss += elementwise_n_loss
            loss_rain = torch.mean(elementwise_loss * weights)

        self.optimizer.zero_grad()
        loss_rain.backward()
        torch.nn.utils.clip_grad_norm_(self.policy_net.parameters(), 10.0)
        self.optimizer.step()

        loss_for_prior = elementwise_loss.detach().cpu().numpy()
        new_priorities = loss_for_prior + self.prior_eps
        self.memory.update_priorities(indices, new_priorities)

        self.target_update_counter += 1
        if self.target_update_counter > self.target_update:
            self._target_hard_update()
            self.target_update_counter = 0

        self.reset_noise()
        loss_number = loss_rain.detach().item()

        del states, actions, rewards, next_states, dones, weights, indices
        del elementwise_loss, loss_rain, n_gamma, n_states, n_action, n_rewards, n_next_states, n_dones
        del elementwise_n_loss
        gc.collect()

        return loss_number

    def _target_hard_update(self, tau=1.0):
        # Soft update of the target network's weights
        # θ′ ← τ θ + (1 −τ )θ′
        target_net_state_dict = self.target_net.state_dict()
        policy_net_state_dict = self.policy_net.state_dict()
        for key in policy_net_state_dict:
            target_net_state_dict[key] = policy_net_state_dict[key] * tau + target_net_state_dict[key] * (1 - tau)
        self.target_net.load_state_dict(target_net_state_dict)

    def reset_noise(self):
        self.policy_net.reset_noise()
        self.target_net.reset_noise()

    def load(self, name):
        self.policy_net.load(name)
        self.target_net.load_state_dict(self.policy_net.state_dict())

    def save(self, name):
        self.policy_net.save(name)

    def compute_loss(self, states, actions, rewards, next_states, dones, gamma):
        delta_z = float(self.v_max - self.v_min) / (self.atom_size - 1)

        with torch.no_grad():
            next_action = self.policy_net(next_states).argmax(1)
            next_dist = self.target_net.dist(next_states)
            next_dist = next_dist[range(self.batch_size), next_action]

            t_z = rewards + (1 - dones) * gamma * self.support
            t_z = t_z.clamp(self.v_min, self.v_max)
            bound = (t_z - self.v_min) / delta_z
            lower = bound.floor().long()
            upper = bound.ceil().long()

            offset = torch.linspace(0, (self.batch_size - 1) * self.atom_size, self.batch_size
                                    ).long().unsqueeze(1).expand(self.batch_size, self.atom_size).to(self.device)
            proj_dist = torch.zeros(next_dist.size(), device=self.device)
            proj_dist.view(-1).index_add_(0, (lower + offset).view(-1), (next_dist * (upper.float() - bound)).view(-1))
            proj_dist.view(-1).index_add_(0, (upper + offset).view(-1), (next_dist * (bound - lower.float())).view(-1))

        dist = self.policy_net.dist(states)
        log_p = torch.log(dist[range(self.batch_size), actions.squeeze()])  # + 1e-6 ???

        elementwise_loss = -(proj_dist * log_p).sum(1)

        del delta_z, next_action, next_dist, t_z, bound, lower, upper, offset, proj_dist, dist, log_p
        return elementwise_loss
