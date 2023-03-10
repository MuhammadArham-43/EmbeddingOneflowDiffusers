# coding=utf-8
# Copyright 2022 HuggingFace Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest
import numpy as np
import oneflow as torch

from diffusers import OneFlowAutoencoderKL as AutoencoderKL
from diffusers.modeling_oneflow_utils import OneFlowModelMixin as ModelMixin
from diffusers.testing_oneflow_utils import floats_tensor, torch_device

from .test_modeling_common_oneflow import ModelTesterMixin



class AutoencoderKLTests(ModelTesterMixin, unittest.TestCase):
    model_class = AutoencoderKL

    @property
    def dummy_input(self):
        batch_size = 4
        num_channels = 3
        sizes = (32, 32)

        image = floats_tensor((batch_size, num_channels) + sizes).to(torch_device)

        return {"sample": image}

    @property
    def input_shape(self):
        return (3, 32, 32)

    @property
    def output_shape(self):
        return (3, 32, 32)

    def prepare_init_args_and_inputs_for_common(self):
        init_dict = {
            "block_out_channels": [32, 64],
            "in_channels": 3,
            "out_channels": 3,
            "down_block_types": ["DownEncoderBlock2D", "DownEncoderBlock2D"],
            "up_block_types": ["UpDecoderBlock2D", "UpDecoderBlock2D"],
            "latent_channels": 4,
        }
        inputs_dict = self.dummy_input
        return init_dict, inputs_dict

    def test_forward_signature(self):
        pass

    def test_training(self):
        pass

    def test_from_pretrained_hub(self):
        model, loading_info = AutoencoderKL.from_pretrained("fusing/autoencoder-kl-dummy", output_loading_info=True)
        self.assertIsNotNone(model)
        self.assertEqual(len(loading_info["missing_keys"]), 0)

        model.to(torch_device)
        image = model(**self.dummy_input)

        assert image is not None, "Make sure output is not None"

    def test_output_pretrained(self):
        model = AutoencoderKL.from_pretrained("fusing/autoencoder-kl-dummy")
        model = model.to(torch_device)
        model.eval()

        # One-time warmup pass (see #372)
        if torch_device == "mps" and isinstance(model, ModelMixin):
            image = torch.randn(1, model.config.in_channels, model.config.sample_size, model.config.sample_size)
            image = image.to(torch_device)
            with torch.no_grad():
                _ = model(image, sample_posterior=True).sample
            generator = torch.manual_seed(0)
        else:
            generator = torch.Generator(device=torch_device).manual_seed(0)

        image = torch.randn(
            1,
            model.config.in_channels,
            model.config.sample_size,
            model.config.sample_size,
            generator=torch.manual_seed(0),
        )
        image = image.to(torch_device)
        with torch.no_grad():
            output = model(image, sample_posterior=True, generator=generator).sample

        output_slice = output[0, -1, -3:, -3:].flatten().cpu()

        # NOTE: oneflow's random generator is not aligned with pytorch's
        # TODO(oneflow): check if oneflow has identical result to pytorch
        expected_output_slice = torch.tensor(
            [-0.1307,  0.1102,  0.3255, -0.2596, -0.0746, -0.1416, -0.2858, -0.3020, -0.1785]
        )
        self.assertTrue(np.allclose(output_slice.numpy(), expected_output_slice.numpy(), rtol=1e-2))
