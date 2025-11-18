from typing import Optional
from threading import Lock

import numpy as np
import torch
from PIL import Image


class GradCAM:
    """Grad-CAM for convolutional models with single-logit output."""

    def __init__(self, model: torch.nn.Module, target_layer: Optional[torch.nn.Module] = None) -> None:
        self.model = model
        self.target_layer = target_layer or self._find_last_conv_layer(model)
        self.activations: Optional[torch.Tensor] = None
        self.gradients: Optional[torch.Tensor] = None
        self._lock = Lock()

        self._forward_handle = self.target_layer.register_forward_hook(self._forward_hook)
        self._backward_handle = self.target_layer.register_full_backward_hook(self._backward_hook)

    def _forward_hook(self, _module: torch.nn.Module, _inputs: tuple, output: torch.Tensor) -> None:
        self.activations = output.detach()

    def _backward_hook(
        self,
        _module: torch.nn.Module,
        _grad_input: tuple,
        grad_output: tuple,
    ) -> None:
        self.gradients = grad_output[0].detach()

    @staticmethod
    def _find_last_conv_layer(model: torch.nn.Module) -> torch.nn.Module:
        for module in reversed(list(model.modules())):
            if isinstance(module, torch.nn.Conv2d):
                return module
        raise RuntimeError("No Conv2d layer found for Grad-CAM target layer.")

    def generate(self, input_tensor: torch.Tensor, original_image: Image.Image) -> Image.Image:
        with self._lock:
            self.model.zero_grad(set_to_none=True)

            output = self.model(input_tensor)
            score = output.squeeze()
            score.backward(retain_graph=False)

            if self.activations is None or self.gradients is None:
                raise RuntimeError("Grad-CAM hooks did not capture activations/gradients.")

            weights = self.gradients.mean(dim=(2, 3), keepdim=True)
            cam = (weights * self.activations).sum(dim=1)
            cam = torch.relu(cam).squeeze(0)

            max_val = cam.max()
            if max_val > 0:
                cam = cam / max_val

            cam_np = cam.detach().cpu().numpy()
        cam_image = Image.fromarray(np.uint8(cam_np * 255)).resize(original_image.size, Image.BILINEAR)
        cam_resized = np.array(cam_image, dtype=np.float32) / 255.0

        return self._overlay(original_image.convert("RGB"), cam_resized, alpha=0.45)

    @staticmethod
    def _overlay(image: Image.Image, cam: np.ndarray, alpha: float = 0.45) -> Image.Image:
        base = np.asarray(image, dtype=np.float32)
        heatmap = GradCAM._simple_colormap(cam)
        blended = np.clip((1.0 - alpha) * base + alpha * heatmap, 0, 255).astype(np.uint8)
        return Image.fromarray(blended)

    @staticmethod
    def _simple_colormap(cam: np.ndarray) -> np.ndarray:
        cam = np.clip(cam, 0.0, 1.0)

        red = np.clip(2.0 * cam, 0.0, 1.0)
        green = np.clip(2.0 * (1.0 - np.abs(cam - 0.5) * 2.0), 0.0, 1.0)
        blue = np.clip(2.0 * (1.0 - cam), 0.0, 1.0)

        return (np.stack([red, green, blue], axis=-1) * 255.0).astype(np.float32)

    def close(self) -> None:
        self._forward_handle.remove()
        self._backward_handle.remove()
