import os
from PIL import Image
import folder_paths
import numpy as np
import torch

from mflux.controlnet.controlnet_util import ControlnetUtil

class MfluxLorasPipeline:
    def __init__(self, lora_paths, lora_scales):
        self.lora_paths = lora_paths
        self.lora_scales = lora_scales

    def clear_cache(self):
        self.lora_paths = []
        self.lora_scales = []

class MfluxLorasLoader:
    @classmethod
    def INPUT_TYPES(cls):
        lora_base_path = folder_paths.models_dir
        loras_relative = ["None"] + folder_paths.get_filename_list("loras")

        inputs = {
            "required": {
                "Lora1": (loras_relative,),
                "scale1": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 1.0, "step": 0.01}),
                "Lora2": (loras_relative,),
                "scale2": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 1.0, "step": 0.01}),
                "Lora3": (loras_relative,),
                "scale3": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 1.0, "step": 0.01}),
            },
            "optional": {
                "Loras": ("MfluxLorasPipeline",)
            }
        }

        return inputs

    RETURN_TYPES = ("MfluxLorasPipeline",)
    RETURN_NAMES = ("Loras",)
    FUNCTION = "lora_stacker"
    CATEGORY = "Mflux/Pro"

    def lora_stacker(self, Loras=None, **kwargs):
        lora_base_path = folder_paths.models_dir
        lora_models = [
            (os.path.join(lora_base_path, "loras", kwargs.get(f"Lora{i}")), kwargs.get(f"scale{i}"))
            for i in range(1, 4) if kwargs.get(f"Lora{i}") != "None"
        ]
        
        if Loras is not None and isinstance(Loras, MfluxLorasPipeline):
            lora_paths = Loras.lora_paths
            lora_scales = Loras.lora_scales

            if lora_paths and lora_scales:
                lora_models.extend(zip(lora_paths, lora_scales))

        if lora_models:
            lora_paths, lora_scales = zip(*lora_models)
        else:
            lora_paths, lora_scales = [], []

        return (MfluxLorasPipeline(list(lora_paths), list(lora_scales)),)

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
                "save_canny": ("BOOLEAN", {"default": False, "label_on": "True", "label_off": "False"}),
            }
        }

    CATEGORY = "Mflux/Pro"
    RETURN_TYPES = ("MfluxControlNetPipeline", "INT", "INT", "IMAGE")
    RETURN_NAMES = ("ControlNet", "width", "height", "canny_image")
    FUNCTION = "load_and_select"

    def load_and_select(self, image, model_selection, strength, save_canny):
        image_path = folder_paths.get_annotated_filepath(image)

        with Image.open(image_path) as img:
            width, height = img.size
            canny_image = ControlnetUtil.preprocess_canny(img)
            canny_image_np = np.array(canny_image).astype(np.float32) / 255.0
            canny_tensor = torch.from_numpy(canny_image_np)
            
            if canny_tensor.dim() == 3:
                canny_tensor = canny_tensor.unsqueeze(0)

        return MfluxControlNetPipeline(image_path, model_selection, strength, save_canny), width, height, canny_tensor

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

        if not isinstance(save_canny, bool):
            return "save_canny must be a boolean value"

        return True