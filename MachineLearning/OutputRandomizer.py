import math
import random
import numpy
import torch


class RandomAction:
    def __init__(self, eps_start=0.95, eps_steps=1000, eps_end=0.02, eps_step_by_done=False):
        self.eps_start = eps_start
        self.eps_steps = eps_steps
        self.eps_end = eps_end
        self.eps_step_by_done = eps_step_by_done
        self.done = 0

    def get(self):
        epsilon = random.random()
        threshold = self.eps_end + (self.eps_start - self.eps_end) * math.exp(-1. * self.done / self.eps_steps)
        if not self.eps_step_by_done:
            self.done += 1
        return epsilon < threshold

    def increment_done(self):
        self.done += 1

    def reset(self):
        self.done = 0


class SimpleActionNoise:
    def __init__(self, action_d, sigma):
        self.sigma = sigma
        device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
        self.dimensions = torch.zeros(action_d, device=device)

    def noise(self):
        return torch.randn_like(self.dimensions) * self.sigma

    def decay_sigma(self):
        pass

    def reset(self):
        pass


class OrnsteinUhlenbeckActionNoise:
    def __init__(self, action_d, sigma_start, sigma_steps=0, mu=0, theta=0.15, dt=0.01, x0=None):
        self.x_prev = 0
        self.action_d = action_d
        self.sigma_start = sigma_start
        self.sigma_end = 0.0
        self.sigma_steps = sigma_steps
        self.done = 0
        self.sigma = float(self.sigma_start) * numpy.ones(self.action_d)
        if mu == 0:
            self.mu = numpy.zeros(self.action_d)
        else:
            self.mu = float(mu) * numpy.ones(self.action_d)
        self.theta = theta
        self.dt = dt
        self.x0 = x0
        self.reset()

    def noise(self, actions=0):
        x = self.x_prev + self.theta * (self.mu - self.x_prev) * self.dt \
            + self.sigma * numpy.sqrt(self.dt) * numpy.random.normal(size=self.mu.shape)
        self.x_prev = x
        return x

    def batch_noise(self, length):
        noise_array = numpy.zeros(length)
        for i in range(length):
            noise_array[i] = self.noise()
        return noise_array

    def decay_sigma(self):
        if self.sigma_steps != 0:
            self.done += 1
            self.sigma = float(
                self.sigma_end + (self.sigma_start - self.sigma_end) *
                math.exp(-1. * self.done / self.sigma_steps)) * numpy.ones(self.action_d)

    def reset(self):
        self.x_prev = self.x0 if self.x0 is not None else numpy.zeros_like(self.mu)

    def __repr__(self):
        return 'OrnsteinUhlenbeckActionNoise(mu={}, sigma={})'.format(self.mu, self.sigma)


class NormalActionNoise:
    def __init__(self, sigma_start, sigma_steps=0, mu=0):
        self.sigma_start = sigma_start
        self.sigma_end = 0.0
        self.sigma_steps = sigma_steps
        self.done = 0
        self.sigma = float(self.sigma_start)
        self.mu = mu
        self.d_type = numpy.float32

    def noise(self, actions):
        noise = actions.clone().data.normal_(0, self.sigma).clamp(-2 * self.sigma, 2 * self.sigma)
        return noise

    def batch_noise(self, actions):
        noise = actions.clone().data.normal_(0, self.sigma).clamp(-2*self.sigma, 2*self.sigma)
        return noise

    def decay_sigma(self):
        if self.sigma_steps != 0:
            self.done += 1
            self.sigma = float(
                self.sigma_end + (self.sigma_start - self.sigma_end) *
                math.exp(-1. * self.done / self.sigma_steps))

    def reset(self):
        self.done = 0
