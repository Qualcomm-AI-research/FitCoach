"""
MIT License

Copyright (c) 2020 Twenty Billion Neurons GmbH

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
from typing import Tuple
import numpy as np
import torch.nn as nn


class RealtimeNeuralNet(nn.Module):
    """
    RealtimeNeuralNet is the abstract class for all neural networks used in InferenceEngine.

    Subclasses should overwrite the methods in RealtimeNeuralNet.
    """
    def __init__(self):
        super().__init__()

    def preprocess(self, clip: np.ndarray):
        """
        Pre-process a clip from a video source.
        """
        raise NotImplementedError

    @property
    def step_size(self) -> int:
        """
        Return the step size of the neural network.
        """
        raise NotImplementedError

    @property
    def fps(self) -> int:
        """
        Return the frame per second rate of the neural network.
        """
        raise NotImplementedError

    @property
    def expected_frame_size(self) -> Tuple[int, int]:
        """
        Return the expected frame size of the neural network.
        """
        raise NotImplementedError


class Pipe(RealtimeNeuralNet):

    def __init__(self, feature_extractor, feature_converter):
        super().__init__()
        self.feature_extractor = feature_extractor
        self.feature_converter = feature_converter

    def forward(self, input_tensor):
        feature = self.feature_extractor(input_tensor)
        if isinstance(self.feature_converter, list):
            return [convert(feature) for convert in self.feature_converter]
        return self.feature_converter(feature)

    @property
    def expected_frame_size(self) -> Tuple[int, int]:
        return self.feature_extractor.expected_frame_size

    @property
    def fps(self) -> int:
        return self.feature_extractor.fps

    @property
    def step_size(self) -> int:
        return self.feature_extractor.step_size

    def preprocess(self, clip: np.ndarray):
        return self.feature_extractor.preprocess(clip)


class LogisticRegression(nn.Sequential):

    def __init__(self, num_in, num_out, use_softmax=True, global_average_pooling=True):
        layers = [nn.Linear(num_in, num_out)]
        if use_softmax:
            layers.append(nn.Softmax(dim=-1))
        super(LogisticRegression, self).__init__(*layers)
        self.global_average_pooling = global_average_pooling

    def forward(self, input_tensor):
        if self.global_average_pooling:
            input_tensor = input_tensor.mean(dim=-1).mean(dim=-1)
        return super().forward(input_tensor)


class LogisticRegressionSigmoid(LogisticRegression):

    def __init__(self, **kwargs):
        super().__init__(use_softmax=False, **kwargs)
        self.add_module(str(len(self)), nn.Sigmoid())
