import torch

from MachineLearning.MachineLearningEnvironment import MachineLearningEnvironment


def run_test():
    print("Start")
    mle = MachineLearningEnvironment()
    mle.some_method()
    print("Stop")


if __name__ == '__main__':
    run_test()

data = torch.Tensor([[0.1, 0.5, -0.9]])
softmax = torch.nn.Softmax(dim=1)
action_probs = softmax(data)

print(action_probs)
