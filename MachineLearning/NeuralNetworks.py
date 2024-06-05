import os
import torch


class MidNetActor(torch.nn.Module):
    def __init__(self, state_d, action_d):
        super(MidNetActor, self).__init__()
        self.lin1 = torch.nn.Sequential(
            torch.nn.Linear(state_d, 128),
            torch.nn.LeakyReLU())
        self.lin2 = torch.nn.Sequential(
            torch.nn.Linear(128, 128),
            torch.nn.LeakyReLU())
        self.lin3 = torch.nn.Sequential(
            torch.nn.Linear(128, action_d),
            torch.nn.LeakyReLU())

    def forward(self, x):
        x = self.lin1(x)
        x = self.lin2(x)
        return self.lin3(x)

    def save(self, file_name='MidNetActor'):
        file_name = file_name + '.pth'
        model_folder_path = './models'
        if not os.path.exists(model_folder_path):
            os.makedirs(model_folder_path)
        file_name = os.path.join(model_folder_path, file_name)
        torch.save(self.state_dict(), file_name)

    def load(self, file_name='MidNetActor'):
        file_name = file_name + '.pth'
        model_folder_path = './models'
        file_name = os.path.join(model_folder_path, file_name)
        if os.path.exists(file_name):
            self.load_state_dict(torch.load(file_name))
            self.eval()
        else:
            print(file_name + " NOT found!")


class DuelingNetwork(torch.nn.Module):
    def __init__(self, in_dim: int, out_dim: int):
        super(DuelingNetwork, self).__init__()
        print("Using Dueling Network")

        # set common feature layer
        self.feature_layer = torch.nn.Sequential(
            torch.nn.Linear(in_dim, 32),
            torch.nn.LeakyReLU(),
            torch.nn.Linear(32, 64),
            torch.nn.LeakyReLU(),
            torch.nn.Linear(64, 128),
            torch.nn.LeakyReLU()
        )

        # set advantage layer
        self.advantage_layer = torch.nn.Sequential(
            torch.nn.Linear(128, 128),
            torch.nn.LeakyReLU(),
            torch.nn.Linear(128, out_dim),
        )

        # set value layer
        self.value_layer = torch.nn.Sequential(
            torch.nn.Linear(128, 128),
            torch.nn.LeakyReLU(),
            torch.nn.Linear(128, 1),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward method implementation."""
        feature = self.feature_layer(x)

        value = self.value_layer(feature)
        advantage = self.advantage_layer(feature)

        q = value + advantage - advantage.mean(dim=-1, keepdim=True)

        return q
