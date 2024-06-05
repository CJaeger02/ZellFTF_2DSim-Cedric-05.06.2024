import os
import torch
from MachineLearning.NoisyNetwork import NoisyLinear


class RainbowNetwork(torch.nn.Module):
    def __init__(self, in_dim: int, out_dim: int,  atom_size: int = 20, support=1, std_init: float = 0.5):
        """Initialization."""
        super(RainbowNetwork, self).__init__()
        self.out_dim = out_dim
        self.support = support
        self.atom_size = atom_size

        # set common feature layer
        self.feature_layers = torch.nn.Sequential(
            torch.nn.Linear(in_dim, 128),
            torch.nn.LeakyReLU(),
            torch.nn.Linear(128, 256),
        )

        # set advantage layer
        self.advantage_hidden_layer = NoisyLinear(256, 256, std_init)
        self.advantage_layer = NoisyLinear(256, self.out_dim * self.atom_size)

        # set value layer
        self.value_hidden_layer = NoisyLinear(256, 256, std_init)
        self.value_layer = NoisyLinear(256, self.atom_size)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward method implementation."""
        q = self.dist(x)
        q = torch.sum(q * self.support, dim=2)
        return q

    def dist(self, x: torch.Tensor) -> torch.Tensor:
        """Get distribution for atoms."""
        feature = self.feature_layers(x)
        adv = torch.nn.functional.relu(self.advantage_hidden_layer(feature))
        val = torch.nn.functional.relu(self.value_hidden_layer(feature))

        adv = self.advantage_layer(adv).view(
            -1, self.out_dim, self.atom_size)
        val = self.value_layer(val).view(-1, 1, self.atom_size)
        q = val + adv - adv.mean(dim=1, keepdim=True)

        q = torch.nn.functional.softmax(q, dim=-1)
        q = q.clamp(min=1e-3)  # for avoiding nans
        del x, feature, adv, val
        return q

    def reset_noise(self):
        self.advantage_hidden_layer.reset_noise()
        self.advantage_layer.reset_noise()
        self.value_hidden_layer.reset_noise()
        self.value_layer.reset_noise()

    def save(self, file_name='model'):
        file_name = file_name + '.pth'
        model_folder_path = './models'
        if not os.path.exists(model_folder_path):
            os.makedirs(model_folder_path)
        file_name = os.path.join(model_folder_path, file_name)
        torch.save(self.state_dict(), file_name)

    def load(self, file_name='model'):
        file_name = file_name + '.pth'
        model_folder_path = './models'
        file_name = os.path.join(model_folder_path, file_name)
        if os.path.exists(file_name):
            self.load_state_dict(torch.load(file_name))


class RainbowNetworkMid(RainbowNetwork):
    def __init__(self, in_dim: int, out_dim: int, atom_size: int = 20, support=1, std_init: float = 0.5):
        super(RainbowNetworkMid, self).__init__(in_dim, out_dim, atom_size, support, std_init)

        # set common feature layer
        self.feature_layers = torch.nn.Sequential(
            torch.nn.Linear(in_dim, 128),
            torch.nn.LeakyReLU(),
            torch.nn.Linear(128, 256),
            torch.nn.LeakyReLU(),
            torch.nn.Linear(256, 512),
            torch.nn.LeakyReLU(),
            torch.nn.Linear(512, 256),
        )


class RainbowNetworkLarge(RainbowNetwork):
    def __init__(self, in_dim: int, out_dim: int, atom_size: int = 20, support=1, std_init: float = 0.5):
        super(RainbowNetworkLarge, self).__init__(in_dim, out_dim, atom_size, support, std_init)

        # set common feature layer
        self.feature_layers = torch.nn.Sequential(
            torch.nn.Linear(in_dim, 128),
            torch.nn.LeakyReLU(),
            torch.nn.Linear(128, 256),
            torch.nn.LeakyReLU(),
            torch.nn.Linear(256, 512),
            torch.nn.LeakyReLU(),
            torch.nn.Linear(512, 1024),
            torch.nn.LeakyReLU(),
            torch.nn.Linear(1024, 1024),
            torch.nn.LeakyReLU(),
            torch.nn.Linear(1024, 512),
            torch.nn.LeakyReLU(),
            torch.nn.Linear(512, 256),
        )


class RainbowCnnNetwork(torch.nn.Module):
    def __init__(self, in_dim: int, out_dim: int, support=1, atom_size=20):
        """Initialization."""
        super(RainbowCnnNetwork, self).__init__()
        self.out_dim = out_dim
        self.support = support
        self.atom_size = atom_size
        self.support = torch.linspace(0.0, 200.0, self.atom_size).to(torch.device('cuda:0'))

        self.cnn = torch.nn.Sequential(
            torch.nn.Conv2d(4, 64, kernel_size=5, stride=2, padding=0),
            torch.nn.LeakyReLU(),
            # torch.nn.MaxPool2d(2),
            torch.nn.Conv2d(64, 128, kernel_size=5, stride=2, padding=0),
            torch.nn.BatchNorm2d(128),
            torch.nn.LeakyReLU(),
            torch.nn.Conv2d(128, 128, kernel_size=7, stride=3, padding=0),
            torch.nn.LeakyReLU(),
            torch.nn.Conv2d(128, 128, kernel_size=7, stride=3, padding=0),
            torch.nn.BatchNorm2d(128),
            torch.nn.LeakyReLU()
        )

        self.flat = torch.nn.Flatten(start_dim=1, end_dim=-1)
        observation_space = torch.zeros(in_dim).unsqueeze(0)
        with torch.no_grad():
            in_dim = self.flat(self.cnn(observation_space)).shape[1]
        print("CNN output size:", in_dim)

        # set common feature layer
        self.feature_layers = torch.nn.Sequential(
            torch.nn.Linear(in_dim, 1024),
            torch.nn.LeakyReLU(),
            torch.nn.Linear(1024, 512),
            torch.nn.LeakyReLU(),
            torch.nn.Linear(512, 256),
            torch.nn.LeakyReLU(),
            torch.nn.Linear(256, 128),
            torch.nn.LeakyReLU(),
            torch.nn.Linear(128, 128),
        )

        # set advantage layer
        self.advantage_hidden_layer = NoisyLinear(128, 128)
        self.advantage_layer = NoisyLinear(128, self.out_dim * self.atom_size)

        # set value layer
        self.value_hidden_layer = NoisyLinear(128, 128)
        self.value_layer = NoisyLinear(128, self.atom_size)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward method implementation."""
        # x = x.unsqueeze(0)
        x = self.cnn(x)
        x = self.flat(x)

        q = self.dist(x)
        q = torch.sum(q * self.support, dim=2)
        return q

    def dist(self, x: torch.Tensor) -> torch.Tensor:
        """Get distribution for atoms."""
        feature = self.feature_layers(x)
        adv = torch.nn.functional.leaky_relu(self.advantage_hidden_layer(feature))
        val = torch.nn.functional.leaky_relu(self.value_hidden_layer(feature))

        adv = self.advantage_layer(adv).view(
            -1, self.out_dim, self.atom_size)
        val = self.value_layer(val).view(-1, 1, self.atom_size)
        q = val + adv - adv.mean(dim=1, keepdim=True)

        q = torch.nn.functional.softmax(q, dim=-1)
        q = q.clamp(min=1e-3)  # for avoiding nans
        del x, feature, adv, val
        return q

    def reset_noise(self):
        self.advantage_hidden_layer.reset_noise()
        self.advantage_layer.reset_noise()
        self.value_hidden_layer.reset_noise()
        self.value_layer.reset_noise()

    def save(self, file_name='model'):
        file_name = file_name + '.pth'
        model_folder_path = './models'
        if not os.path.exists(model_folder_path):
            os.makedirs(model_folder_path)
        file_name = os.path.join(model_folder_path, file_name)
        torch.save(self.state_dict(), file_name)

    def load(self, file_name='model'):
        file_name = file_name + '.pth'
        model_folder_path = './models'
        file_name = os.path.join(model_folder_path, file_name)
        if os.path.exists(file_name):
            self.load_state_dict(torch.load(file_name))

