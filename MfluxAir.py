import os
import time
import random
import json
from pathlib import Path
import numpy as np
import torch
from huggingface_hub import snapshot_download
from folder_paths import get_filename_list, get_output_directory, models_dir
from mflux.config.model_config import ModelConfig
from mflux.config.config import Config, ConfigControlnet
from mflux.flux.flux import Flux1
from mflux.controlnet.flux_controlnet import Flux1Controlnet
from .MfluxPro import MfluxControlNetPipeline

flux_cache = {}

def load_or_create_flux(model, quantize, path, lora_paths, lora_scales, is_controlnet=False):
    key = (model, quantize, path, tuple(lora_paths), tuple(lora_scales), is_controlnet)
    if key not in flux_cache:
        FluxClass = Flux1Controlnet if is_controlnet else Flux1
        flux_cache[key] = FluxClass(
            model_config=ModelConfig.from_alias(model),
            quantize=quantize,
            local_path=path,
            lora_paths=lora_paths,
            lora_scales=lora_scales,
        )
    # This code is licensed under the Apache 2.0 License.
    # Portions of this code are derived from the work of CharafChnioune at https://github.com/CharafChnioune/MFLUX-WEBUI
    return flux_cache[key]

class MfluxModelsLoader:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model_name": (cls.get_model_paths(),)
            }
        }

    RETURN_TYPES = ("PATH",)
    RETURN_NAMES = ("Local_models",)
    CATEGORY = "Mflux/Air"
    FUNCTION = "load"

    @classmethod
    def get_model_paths(cls):
        mflux_dir = os.path.join(models_dir, "Mflux")
        return [p.name for p in Path(mflux_dir).iterdir() if p.is_dir()]

    def load(self, model_name):
        model_paths = self.get_model_paths()
        full_model_path = os.path.join(models_dir, "Mflux", model_name)
        return (full_model_path,) if model_name in model_paths else ("",)

class QuickMfluxNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": ("STRING", {"multiline": True, "dynamicPrompts": True, "tooltip": "The text to be encoded.", "default": "Luxury food photograph"}),
                "model": (["dev", "schnell"], {"default": "schnell"}),
                "quantize": (["None", "4", "8"], {"default": "None"}),
                "seed": ("INT", {"default": -1, "min": -1, "max": 0xffffffffffffffff}),
                "width": ("INT", {"default": 512}),
                "height": ("INT", {"default": 512}),
                "steps": ("INT", {"default": 2, "min": 1}),
                "cfg": ("FLOAT", {"default": 3.5, "min": 0.0}),
                "metadata": (["true", "false"], {"default": "false"}),
            },
            "optional": {
                "Local_models": ("PATH",),
                "Loras": ("MfluxLorasPipeline",),
                "ControlNet": ("MfluxControlNetPipeline",),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    CATEGORY = "Mflux/Air"
    FUNCTION = "generate"

    def generate(self, prompt, model, seed, width, height, steps, cfg, quantize="None", metadata="false", Local_models="", Loras=None, ControlNet=None):
        model = "dev" if "dev" in Local_models.lower() else "schnell" if "schnell" in Local_models.lower() else model
        print(f"Using model: {model}")
        image_path, save_canny, strength = None, None, None
        if ControlNet:
            if isinstance(ControlNet, MfluxControlNetPipeline):
                image_path = ControlNet.image_path
                save_canny = ControlNet.save_canny
                strength = ControlNet.strength
        is_controlnet = ControlNet is not None
        quantize = None if quantize == "None" else int(quantize)
        seed = random.randint(0, 0xffffffffffffffff) if seed == -1 else int(seed)
        print(f"Using seed: {seed}")
        steps = min(max(steps, 2), 4) if model == "schnell" else steps
        lora_paths = Loras.lora_paths if Loras else []
        lora_scales = Loras.lora_scales if Loras else []
        flux = load_or_create_flux(model, quantize, Local_models if Local_models else None, lora_paths, lora_scales, is_controlnet)
        output_image_path = (
            f"{get_output_directory()}/generated_image.png"
            if is_controlnet and save_canny == "true"
            else None
        )
        config_class = ConfigControlnet if is_controlnet else Config
        config = config_class(
            num_inference_steps=steps,
            height=height,
            width=width,
            guidance=cfg,
            **({"controlnet_strength": strength} if is_controlnet else {})
        )
        generate_args = {
            "seed": seed,
            "prompt": prompt,
            "config": config
        }
        if is_controlnet:
            generate_args["controlnet_image_path"] = image_path
            generate_args["controlnet_save_canny"] = save_canny
            if save_canny == "true":
                generate_args["output"] = output_image_path
            else:
                generate_args["output"] = ""
        image = flux.generate_image(**generate_args)
        inner_image = image.image
        tensor_image = torch.from_numpy(np.array(inner_image).astype(np.float32) / 255.0)
        if tensor_image.dim() == 3:
            tensor_image = tensor_image.unsqueeze(0)
        if metadata == "true":
            self.save_images([inner_image], prompt, model, Local_models, seed, height, width, steps, cfg)
        return (tensor_image,)
    
    def save_images(self, images, prompt, model, Local_models, seed, height, width, steps, cfg, filename_prefix="Mflux"):
        output_dir = get_output_directory()
        mflux_dir = os.path.join(output_dir, "Mflux")
        os.makedirs(mflux_dir, exist_ok=True)
        results = []
        existing_files = os.listdir(mflux_dir)
        existing_count = len([f for f in existing_files if f.startswith(filename_prefix)])
        for (batch_number, img) in enumerate(images):
            filename = f"{filename_prefix}_{existing_count + batch_number:05}.png"
            file_path = os.path.join(mflux_dir, filename)
            img.save(file_path)
            metadata = {
                "prompt": prompt,
                "model": model,
                "path": Local_models,
                "seed": seed,
                "height": height,
                "width": width,
                "steps": steps,
                "guidance": cfg,
            }
            metadata_filename = os.path.join(mflux_dir, f"{filename_prefix}_{existing_count + batch_number:05}.json")
            with open(metadata_filename, 'w') as metadata_file:
                json.dump(metadata, metadata_file)
            results.append({
                "filename": filename,
                "path": file_path,
            })
        return results