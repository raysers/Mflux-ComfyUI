import os
from PIL import Image
import folder_paths
import numpy as np
import torch

from mflux.controlnet.controlnet_util import ControlnetUtil

class MfluxControlNetPipeline:
    def __init__(self, image_path, model_selection, strength, save_canny=False):
        self.image_path = image_path
        self.model_selection = model_selection
        self.strength = strength
        self.save_canny = save_canny

    def clear_cache(self):
        self.image_path = None
        self.model_selection = None
        self.strength = None
        self.save_canny = False

class MfluxControlNetLoader:
    @classmethod
    def INPUT_TYPES(cls):
        input_dir = folder_paths.get_input_directory()
        files = [f for f in os.listdir(input_dir) if os.path.isfile(os.path.join(input_dir, f))]

        controlnet_models = [
            "InstantX/FLUX.1-dev-Controlnet-Canny",
        ]

        return {
            "required": {
                "image": (sorted(files), {"image_upload": True}),
                "model_selection": (controlnet_models, {"default": "InstantX/FLUX.1-dev-Controlnet-Canny"}),
                "strength": ("FLOAT", {"default": 0.4, "min": 0.0, "max": 1.0}),
                "save_canny": (["true", "false"], {"default": "false"}),
            }
        }

    CATEGORY = "Mflux/Pro"
    RETURN_TYPES = ("MfluxControlNetPipeline", "INT", "INT", "IMAGE")
    RETURN_NAMES = ("ControlNet", "width", "height", "canny_image")
    FUNCTION = "load_and_select"

    def load_and_select(self, image, model_selection, strength, save_canny):
        save_canny_bool = save_canny == "true"
        image_path = folder_paths.get_annotated_filepath(image)
        print(f"Loading image from path: {image_path}")

        with Image.open(image_path) as img:
            width, height = img.size
            canny_image = ControlnetUtil.preprocess_canny(img)
            canny_image_np = np.array(canny_image).astype(np.float32) / 255.0
            canny_tensor = torch.from_numpy(canny_image_np)

            if canny_tensor.dim() == 3:
                canny_tensor = canny_tensor.unsqueeze(0)

        print(f"Model selection: {model_selection}")
        print(f"Strength: {strength}")
        print(f"Save Canny: {save_canny_bool}")

        return MfluxControlNetPipeline(image_path, model_selection, strength, save_canny_bool), width, height, canny_tensor

    @classmethod
    def IS_CHANGED(cls, image, model_selection, strength, save_canny):
        return str(image) + str(model_selection) + str(strength) + str(save_canny)

    @classmethod
    def VALIDATE_INPUTS(cls, image, model_selection, strength, save_canny):
        if not folder_paths.exists_annotated_filepath(image):
            return "Invalid image file: {}".format(image)

        available_models = [
            "InstantX/FLUX.1-dev-Controlnet-Canny",
        ]
        if model_selection not in available_models:
            return f"Invalid model selection: {model_selection}"

        if not isinstance(strength, (int, float)):
            return "Strength must be a number"

        if save_canny not in ["true", "false"]:
            return "save_canny must be 'true' or 'false'"

        return True