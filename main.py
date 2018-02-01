import torch
import torch.nn as nn
import torch.utils.data

from layers import ScaleLayer, BinaryDecorator, binarize_model
from metrics import test
from trainer import Trainer
from utils import StepLRClamp


class NetBinary(nn.Module):
    def __init__(self, conv_channels, fc_sizes, conv_kernel=3):
        super().__init__()

        conv_layers = []
        for (in_features, out_features) in zip(conv_channels[:-1], conv_channels[1:]):
            conv_layers.append(nn.BatchNorm2d(in_features))
            layer = nn.Conv2d(in_features, out_features, kernel_size=conv_kernel, padding=0, bias=False)
            layer = BinaryDecorator(layer)
            conv_layers.append(layer)
            conv_layers.append(nn.MaxPool2d(kernel_size=2))
            conv_layers.append(nn.PReLU())
        self.conv_sequential = nn.Sequential(*conv_layers)

        fc_layers = []
        for (in_features, out_features) in zip(fc_sizes[:-1], fc_sizes[1:]):
            fc_layers.append(nn.BatchNorm1d(in_features))
            layer = nn.Linear(in_features, out_features, bias=False)
            layer = BinaryDecorator(layer)
            fc_layers.append(layer)
            fc_layers.append(nn.PReLU())
        self.fc_sequential = nn.Sequential(*fc_layers)
        self.scale_layer = ScaleLayer()

    def forward(self, x):
        x = self.conv_sequential(x)
        x = x.view(x.shape[0], -1)
        x = self.fc_sequential(x)
        x = self.scale_layer(x)
        return x


def train_binary():
    conv_channels = [3, 10, 20]
    fc_sizes = [720, 500, 10]
    model = NetBinary(conv_channels, fc_sizes)
    # for n, p in model.named_parameters():
    #     print(n)
    # quit()
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-2, weight_decay=1e-8)
    scheduler = StepLRClamp(optimizer, step_size=3, gamma=0.5, min_lr=1e-4)
    trainer = Trainer(model, criterion, optimizer, dataset="CIFAR10", scheduler=scheduler)
    trainer.train(n_epoch=200, debug=0)


if __name__ == '__main__':
    train_binary()
    test(train=True)