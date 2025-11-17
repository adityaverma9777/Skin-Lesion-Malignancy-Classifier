import logging
from pathlib import Path
from typing import Dict, Union

import timm
import torch
import torchvision.transforms as T
from PIL import Image

logger = logging.getLogger(__name__)


class SkinLesionModel:
    """Loads EfficientNet-B4 once and serves fast CPU inference."""

    def __init__(self, model_path: Union[str, Path]) -> None:
        self.device = torch.device("cpu")
        self.model = timm.create_model("efficientnet_b4", pretrained=False, num_classes=1)
        self.transform = T.Compose(
            [
                T.Resize((224, 224)),
                T.ToTensor(),
                T.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5]),
            ]
        )

        self._load_weights(model_path)
        self.model.to(self.device)
        self.model.eval()

    def _load_weights(self, model_path: Union[str, Path]) -> None:
        model_path = Path(model_path)
        if not model_path.exists():
            raise FileNotFoundError(f"Model file not found: {model_path}")

        checkpoint = torch.load(model_path, map_location=self.device)
        state_dict = self._extract_state_dict(checkpoint)
        state_dict = self._strip_module_prefix(state_dict)

        try:
            self.model.load_state_dict(state_dict, strict=True)
        except RuntimeError as exc:
            logger.warning("Strict load failed (%s). Retrying with strict=False.", exc)
            self.model.load_state_dict(state_dict, strict=False)

        logger.info("Model loaded from %s", model_path)

    @staticmethod
    def _extract_state_dict(checkpoint: object) -> Dict[str, torch.Tensor]:
        if isinstance(checkpoint, dict):
            if "state_dict" in checkpoint and isinstance(checkpoint["state_dict"], dict):
                return checkpoint["state_dict"]
            if "model_state_dict" in checkpoint and isinstance(checkpoint["model_state_dict"], dict):
                return checkpoint["model_state_dict"]
            if all(isinstance(v, torch.Tensor) for v in checkpoint.values()):
                return checkpoint

        if hasattr(checkpoint, "state_dict"):
            return checkpoint.state_dict()

        raise ValueError("Unsupported checkpoint format. Expected a state_dict or checkpoint dict.")

    @staticmethod
    def _strip_module_prefix(state_dict: Dict[str, torch.Tensor]) -> Dict[str, torch.Tensor]:
        if not any(key.startswith("module.") for key in state_dict):
            return state_dict
        return {key.replace("module.", "", 1): value for key, value in state_dict.items()}

    def preprocess(self, image: Image.Image) -> torch.Tensor:
        rgb_image = image.convert("RGB")
        tensor = self.transform(rgb_image).unsqueeze(0)
        return tensor.to(self.device)

    def predict_proba(self, input_tensor: torch.Tensor) -> float:
        with torch.no_grad():
            logits = self.model(input_tensor)
            probability = torch.sigmoid(logits).squeeze().item()
        return float(probability)
