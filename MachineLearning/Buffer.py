import numpy
import torch
import random
from collections import deque
from typing import Deque, List
from MachineLearning.SegmentTree import MinSegmentTree, SumSegmentTree


class ContinuesBuffer:
    def __init__(self, max_size, state_d, action_d, device):
        self.max_size = max_size
        self.index = 0
        self.size = 0

        if type(state_d) is int:
            self.state = numpy.zeros((max_size, state_d))
            self.next_state = numpy.zeros((max_size, state_d))
        else:
            self.state = numpy.zeros(shape=(max_size, state_d[0], state_d[1], state_d[2]))
            self.next_state = numpy.zeros(shape=(max_size, state_d[0], state_d[1], state_d[2]))
        self.action = numpy.zeros((max_size, action_d))
        self.reward = numpy.zeros((max_size, 1))
        self.dones = numpy.zeros((max_size, 1))

        self.device = device

    def add(self, state, action, reward, next_state, done):
        self.state[self.index] = state
        self.action[self.index] = action
        self.reward[self.index] = reward
        self.next_state[self.index] = next_state
        self.dones[self.index] = done  # 0,0,0，...，1

        self.index = (self.index + 1) % self.max_size
        self.size = min(self.size + 1, self.max_size)

    def sample(self, batch_size):
        indices = numpy.random.randint(0, self.size, size=batch_size)

        return (
            torch.tensor(self.state[indices], dtype=torch.float, device=self.device),
            torch.tensor(self.action[indices], dtype=torch.float, device=self.device),
            torch.tensor(self.reward[indices], dtype=torch.float, device=self.device),
            torch.tensor(self.next_state[indices], dtype=torch.float, device=self.device),
            torch.tensor(self.dones[indices], dtype=torch.long, device=self.device)
        )


class DiscreteBuffer:
    def __init__(self, max_size, state_d, device):
        self.max_size = max_size
        self.index = 0
        self.size = 0

        if type(state_d) is int:
            self.state = numpy.zeros((max_size, state_d))
            self.next_state = numpy.zeros((max_size, state_d))
        else:
            self.state = numpy.zeros(shape=(max_size, state_d[0], state_d[1], state_d[2]))
            self.next_state = numpy.zeros(shape=(max_size, state_d[0], state_d[1], state_d[2]))
        self.action_index = numpy.zeros((max_size, 1))
        self.reward = numpy.zeros((max_size, 1))
        self.dones = numpy.zeros((max_size, 1))

        self.device = device

    def add(self, state, action_index, reward, next_state, done):
        self.state[self.index] = state
        self.action_index[self.index] = action_index
        self.reward[self.index] = reward
        self.next_state[self.index] = next_state
        self.dones[self.index] = done  # 0,0,0，...，1

        self.index = (self.index + 1) % self.max_size
        self.size = min(self.size + 1, self.max_size)

    def sample(self, batch_size):
        indices = numpy.random.randint(0, self.size, size=batch_size)

        return (
            torch.tensor(self.state[indices], dtype=torch.float, device=self.device),
            torch.tensor(self.action_index[indices], dtype=torch.long, device=self.device),
            torch.tensor(self.reward[indices], dtype=torch.float, device=self.device),
            torch.tensor(self.next_state[indices], dtype=torch.float, device=self.device),
            torch.tensor(self.dones[indices], dtype=torch.long, device=self.device)
        )


class MultiDiscreteBuffer:
    def __init__(self, max_size, state_d, device, num_discrete=1):
        self.max_size = max_size
        self.index = 0
        self.size = 0
        self.device = device

        if type(state_d) is int:
            self.state = torch.zeros((max_size, state_d), dtype=torch.float, device=torch.device('cpu'))
            self.next_state = torch.zeros((max_size, state_d), dtype=torch.float, device=torch.device('cpu'))
        else:
            self.state = torch.zeros((max_size, state_d[0], state_d[1], state_d[2]), dtype=torch.float,
                                     device=torch.device('cpu'))
            self.next_state = torch.zeros((max_size, state_d[0], state_d[1], state_d[2]), dtype=torch.float,
                                          device=torch.device('cpu'))
        self.action = torch.zeros((max_size, num_discrete), dtype=torch.long, device=torch.device('cpu'))
        self.reward = torch.zeros((max_size, 1), dtype=torch.float, device=torch.device('cpu'))
        self.dones = torch.zeros((max_size, 1), dtype=torch.long, device=torch.device('cpu'))

    def add(self, state, action, reward, next_state, done):

        action = torch.tensor(action, dtype=torch.long, device=torch.device('cpu'))
        reward = torch.tensor(reward, dtype=torch.float, device=torch.device('cpu'))
        done = torch.tensor(done, dtype=torch.long, device=torch.device('cpu'))

        self.state[self.index] = state
        self.action[self.index] = action
        self.reward[self.index] = reward
        self.next_state[self.index] = next_state
        self.dones[self.index] = done

        self.index = (self.index + 1) % self.max_size
        self.size = min(self.size + 1, self.max_size)

    def sample(self, batch_size):
        if batch_size > self.size:
            batch_size = self.size
        indices = numpy.random.randint(0, self.size, size=batch_size)

        return (
            self.state[indices].to(self.device),
            self.action[indices].to(self.device),
            self.reward[indices].to(self.device),
            self.next_state[indices].to(self.device),
            self.dones[indices].to(self.device)
        )


class DiscreteRNNBuffer:
    def __init__(self, max_size, state_d, device, hidden_size, n_layers):
        self.max_size = max_size
        self.index = 0
        self.size = 0
        self.device = device

        if type(state_d) is int:
            self.state = torch.zeros((max_size, 1, state_d), dtype=torch.float, device=self.device)
            self.next_state = torch.zeros((max_size, 1, state_d), dtype=torch.float, device=self.device)
        else:
            self.state = torch.zeros((max_size, state_d[0], state_d[1], state_d[2]), dtype=torch.float,
                                     device=self.device)
            self.next_state = torch.zeros((max_size, state_d[0], state_d[1], state_d[2]), dtype=torch.float,
                                          device=self.device)
        self.action_index = torch.zeros((max_size, 1), dtype=torch.long, device=self.device)
        self.reward = torch.zeros((max_size, 1), dtype=torch.float, device=self.device)
        self.dones = torch.zeros((max_size, 1), dtype=torch.long, device=self.device)
        self.last_hx = torch.zeros((max_size, n_layers, 1, hidden_size), dtype=torch.float, device=self.device)

    def add(self, state, action_index, reward, next_state, done, last_hx):

        action_index = torch.tensor(action_index, dtype=torch.long, device=self.device)
        reward = torch.tensor(reward, dtype=torch.float, device=self.device)
        done = torch.tensor(done, dtype=torch.long, device=self.device)

        self.state[self.index] = state
        self.action_index[self.index] = action_index
        self.reward[self.index] = reward
        self.next_state[self.index] = next_state
        self.dones[self.index] = done
        self.last_hx[self.index] = last_hx

        self.index = (self.index + 1) % self.max_size
        self.size = min(self.size + 1, self.max_size)

    def sample(self, batch_size):
        if batch_size > self.size:
            batch_size = self.size
        indices = numpy.random.randint(0, self.size, size=batch_size)
        # ind = torch.randint(0, self.size, device=self.device, size=(batch_size,))

        hx = self.last_hx[indices]
        hx = hx.squeeze()
        hx = hx.permute(1, 0, 2)

        return (
            self.state[indices].squeeze(1),
            self.state[indices],
            self.action_index[indices],
            self.reward[indices],
            self.next_state[indices].squeeze(1),
            self.next_state[indices],
            self.dones[indices],
            hx
        )


class PrioritizedDiscreteBuffer(DiscreteBuffer):
    def __init__(
            self,
            max_size: int,
            state_d: int,
            device,
    ):
        super(PrioritizedDiscreteBuffer, self).__init__(
            max_size, state_d, device
        )
        self.max_priority, self.tree_ptr = 1.0, 0
        self.alpha = 0.2

        # capacity must be positive and a power of 2.
        tree_capacity = 1
        while tree_capacity < self.max_size:
            tree_capacity *= 2

        #self.sum_tree = SumSegmentTree(tree_capacity)


class NStepDiscreteBuffer:
    def __init__(self, max_size, batch_size, state_d, device, n_step: int = 1, gamma: float = 0.99):
        self.max_size = max_size
        self.batch_size = batch_size
        self.index = 0
        self.size = 0

        if type(state_d) is int:
            self.states = torch.zeros((max_size, state_d), dtype=torch.float, device=torch.device('cpu'))
            self.next_states = torch.zeros((max_size, state_d), dtype=torch.float, device=torch.device('cpu'))
        else:
            self.states = torch.zeros((max_size, state_d[0], state_d[1], state_d[2]), dtype=torch.float,
                                      device=torch.device('cpu'))
            self.next_states = torch.zeros((max_size, state_d[0], state_d[1], state_d[2]), dtype=torch.float,
                                           device=torch.device('cpu'))
        self.actions = torch.zeros((max_size, 1), dtype=torch.long, device=torch.device('cpu'))
        self.rewards = torch.zeros((max_size, 1), dtype=torch.float, device=torch.device('cpu'))
        self.dones = torch.zeros((max_size, 1), dtype=torch.long, device=torch.device('cpu'))

        #N-step
        self.n_step_buffer = deque(maxlen=n_step)
        self.n_step = n_step
        self.gamma = gamma

        self.device = device

    def add(self, state, action, reward, next_state, done):
        action = torch.tensor(action, dtype=torch.long, device=torch.device('cpu'))
        reward = torch.tensor(reward, dtype=torch.float, device=torch.device('cpu'))
        done = torch.tensor(done, dtype=torch.long, device=torch.device('cpu'))
        return self.adding_to_buffer(state, action, reward, next_state, done)

    def adding_to_buffer(self, state, action, reward, next_state, done):
        transition = (state, action, reward, next_state, done)
        self.n_step_buffer.append(transition)

        if len(self.n_step_buffer) < self.n_step:
            return ()

        reward, next_state, done = self._get_n_step_info(self.n_step_buffer, self.gamma)
        state, action = self.n_step_buffer[0][:2]

        self.states[self.index] = state
        self.actions[self.index] = action
        self.rewards[self.index] = reward
        self.next_states[self.index] = next_state
        self.dones[self.index] = done  # 0,0,0，...，1
        self.index = (self.index + 1) % self.max_size
        self.size = min(self.size + 1, self.max_size)
        return self.n_step_buffer[0]

    def sample(self):
        if self.size > 0:
            indices = numpy.random.randint(0, self.size, size=self.batch_size)
        else:
            indices = numpy.random.randint(0, 1, size=self.batch_size)
            # indices = [0]

        return (
            self.states[indices].to(self.device),
            self.actions[indices].to(self.device),
            self.rewards[indices].to(self.device),
            self.next_states[indices].to(self.device),
            self.dones[indices].to(self.device),
            indices  # n-step
        )

    def sample_batch_from_indices(self, indices=None):  # n-step
        # if indices == None:
        #     indices = [self.index]
        return (
            self.states[indices].to(self.device),
            self.actions[indices].to(self.device),
            self.rewards[indices].to(self.device),
            self.next_states[indices].to(self.device),
            self.dones[indices].to(self.device)
        )

    @staticmethod
    def _get_n_step_info(n_step_buffer: Deque, gamma: float):
        reward, next_state, done = n_step_buffer[-1][-3:]

        for transition in reversed(list(n_step_buffer)[:-1]):
            rew, next_s, do = transition[-3:]

            reward = rew + gamma * reward * (1 - do)
            next_state, done = (next_s, do) if do else (next_state, done)

        return reward, next_state, done

    def __len__(self) -> int:
        return self.size


class PrioritizedReplayBuffer(NStepDiscreteBuffer):
    """Prioritized Replay buffer.

    Attributes:
        max_priority (float): max priority
        tree_ptr (int): next index of tree
        alpha (float): alpha parameter for prioritized replay buffer
        sum_tree (SumSegmentTree): sum tree for prior
        min_tree (MinSegmentTree): min tree for min prior to get max weight
    """

    def __init__(
            self,
            max_size: int,
            batch_size: int,
            state_d: int,
            device,
            n_step: int = 1,
            gamma: float = 0.99,
            alpha: float = 0.6
    ):
        """Initialization."""
        assert alpha >= 0

        super(PrioritizedReplayBuffer, self).__init__(
            max_size, batch_size, state_d, device, n_step, gamma
        )
        self.max_priority, self.tree_ptr = 1.0, 0
        self.alpha = alpha

        # capacity must be positive and a power of 2.
        tree_capacity = 1
        while tree_capacity < self.max_size:
            tree_capacity *= 2

        self.sum_tree = SumSegmentTree(tree_capacity)
        self.min_tree = MinSegmentTree(tree_capacity)

    def add(self, state, action, reward, next_state, done):
        """Store experience and priority."""
        transition = super().adding_to_buffer(state, action, reward, next_state, done)

        if transition:
            self.sum_tree[self.tree_ptr] = self.max_priority ** self.alpha
            self.min_tree[self.tree_ptr] = self.max_priority ** self.alpha
            self.tree_ptr = (self.tree_ptr + 1) % self.max_size

        return transition

    def ready_to_sample(self):
        return self.size >= self.batch_size

    def sample_batch(self, beta: float = 0.4):
        """Sample a batch of experiences."""
        if self.size < self.batch_size or beta <= 0.0:
            return None, None, None, None, None, None, None

        indices = self._sample_proportional()
        return (
            self.states[indices].to(self.device),
            self.actions[indices].to(self.device),
            self.rewards[indices].to(self.device),
            self.next_states[indices].to(self.device),
            self.dones[indices].to(self.device),
            torch.tensor([self._calculate_weight(i, beta) for i in indices]).unsqueeze(1).to(self.device),
            indices
        )
    # numpy.array([self._calculate_weight(i, beta) for i in indices])

    def update_priorities(self, indices: List[int], priorities: numpy.ndarray):
        """Update priorities of sampled transiti ons."""
        assert len(indices) == len(priorities)

        for idx, priority in zip(indices, priorities):
            assert priority > 0
            assert 0 <= idx < len(self)

            self.sum_tree[idx] = priority ** self.alpha
            self.min_tree[idx] = priority ** self.alpha

            self.max_priority = max(self.max_priority, priority)

    def _sample_proportional(self) -> List[int]:
        """Sample indices based on proportions."""
        indices = []
        p_total = self.sum_tree.sum(0, self.size - 1)
        segment = p_total / self.batch_size

        for i in range(self.batch_size):
            a = segment * i
            b = segment * (i + 1)
            upperbound = random.uniform(a, b)
            idx = self.sum_tree.retrieve(upperbound)
            indices.append(idx)

        return indices

    def _calculate_weight(self, idx: int, beta: float):
        """Calculate the weight of the experience at idx."""
        # get max weight
        p_min = self.min_tree.min() / self.sum_tree.sum()
        max_weight = (p_min * len(self)) ** (-beta)

        # calculate weights
        p_sample = self.sum_tree[idx] / self.sum_tree.sum()
        weight = (p_sample * len(self)) ** (-beta)
        weight = weight / max_weight

        return weight
