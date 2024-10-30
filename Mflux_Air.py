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
from .Mflux_Pro import MfluxControlNetPipeline

flux_cache = {}

def load_or_create_flux(model, quantize, path, lora_paths, lora_scales, is_controlnet=False):
    key = (model, quantize, path, tuple(lora_paths), tuple(lora_scales), is_controlnet)
    if key not in flux_cache:
        flux_cache.clear()  
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

def create_directory(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)
    return directory

mflux_dir = os.path.join(models_dir, "Mflux")
create_directory(mflux_dir)

def get_full_model_path(model_dir, model_name):
    return os.path.join(model_dir, model_name)

def get_lora_info(Loras):
    if Loras:
        return Loras.lora_paths, Loras.lora_scales
    return [], []

def download_hg_model(model_version):
    repo_id = f"madroid/{model_version}" if "4bit" in model_version else f"AITRADER/{model_version}"
    model_checkpoint = get_full_model_path(mflux_dir, model_version)  
    if not os.path.exists(model_checkpoint):
        print(f"Downloading model {model_version} to {model_checkpoint}...")
        try:
            snapshot_download(repo_id=repo_id, local_dir=model_checkpoint)
        except Exception as e:
            print(f"Error downloading model {model_version}: {e}")
            return None
    else:
        print(f"Model {model_version} already exists at {model_checkpoint}. Skipping download.")
    return model_checkpoint

class MfluxModelsDownloader:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model_version": (["flux.1-schnell-mflux-4bit", "flux.1-dev-mflux-4bit", "MFLUX.1-schnell-8-bit", "MFLUX.1-dev-8-bit"], {"default": "flux.1-schnell-mflux-4bit"}),
            }
        }

    RETURN_TYPES = ("PATH",)
    RETURN_NAMES = ("Downloaded_model",)
    CATEGORY = "Mflux/Air"
    FUNCTION = "download_model"

    def download_model(self, model_version):
        model_path = download_hg_model(model_version)
        if model_path:
            return (model_path,)  
        return (None,)
    
class MfluxCustomModels:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model": (["dev", "schnell"], {"default": "schnell"}),
                "quantize": (["4", "8"], {"default": "4"}),
            },
            "optional": {
                "Loras": ("MfluxLorasPipeline",),
                "custom_identifier": ("STRING", {"default": "", "tooltip": "Custom identifier for the model."}),
            }
        }

    RETURN_TYPES = ("PATH",)
    RETURN_NAMES = ("Custom_model",)
    CATEGORY = "Mflux/Air"
    FUNCTION = "save_model"

    def save_model(self, model, quantize, Loras=None, custom_identifier=""):
        identifier = custom_identifier if custom_identifier else "default"
        save_dir = get_full_model_path(mflux_dir, f"Mflux-{model}-{quantize}bit-{identifier}")
        create_directory(save_dir)
        print(f"Saving model: {model}, quantize: {quantize}, save_dir: {save_dir}")
        lora_paths, lora_scales = get_lora_info(Loras)
        if lora_paths:
            print(f"LoRA paths: {lora_paths}")
            print(f"LoRA scales: {lora_scales}")
        model_config = ModelConfig.from_alias(model)
        flux = Flux1(model_config=model_config, quantize=int(quantize), lora_paths=lora_paths, lora_scales=lora_scales)
        flux.save_model(save_dir)
        print(f"Model saved to {save_dir}")
        return (save_dir,)

class MfluxModelsLoader:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model_name": (cls.get_sorted_model_paths(),)
            }
        }

    RETURN_TYPES = ("PATH",)
    RETURN_NAMES = ("Local_model",)
    CATEGORY = "Mflux/Air"
    FUNCTION = "load"

    @classmethod
    def get_sorted_model_paths(cls):
        model_paths = [p.name for p in Path(mflux_dir).iterdir() if p.is_dir()]
        return sorted(model_paths, key=lambda x: x.lower())

    def load(self, model_name):
        full_model_path = get_full_model_path(mflux_dir, model_name)
        return (full_model_path,)

class QuickMfluxNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": ("STRING", {"multiline": True, "dynamicPrompts": True, "tooltip": "The text to be encoded.", "default": "Luxury food photograph"}),
                "model": (["dev", "schnell"], {"default": "schnell"}),
                "quantize": (["None", "4", "8"], {"default": "4"}),
                "seed": ("INT", {"default": -1, "min": -1, "max": 0xffffffffffffffff}),
                "width": ("INT", {"default": 512}),
                "height": ("INT", {"default": 512}),
                "steps": ("INT", {"default": 2, "min": 1}),
                "guidance": ("FLOAT", {"default": 3.5, "min": 0.0}),
                "metadata": ("BOOLEAN", {"default": True, "label_on": "True", "label_off": "False"}),
            },
            "optional": {
                "Local_model": ("PATH",),
                "image": ("MfluxImagePipeline",), 
                "Loras": ("MfluxLorasPipeline",),
                "ControlNet": ("MfluxControlNetPipeline",),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    CATEGORY = "Mflux/Air"
    FUNCTION = "generate"

    def generate(self, prompt, model, seed, width, height, steps, guidance, quantize="None", metadata=True, Local_model="", image=None, Loras=None, ControlNet=None):
        model = "dev" if "dev" in Local_model.lower() else "schnell" if "schnell" in Local_model.lower() else model
        print(f"Using model: {model}")

        if image:
            image_path = image.image_path
            strength = image.strength
        else:
            image_path, strength = None, None

        lora_paths, lora_scales = get_lora_info(Loras)
        if Loras:
            print(f"LoRA paths: {Loras.lora_paths}")
            print(f"LoRA scales: {Loras.lora_scales}")

        ControlNet_model_selection, save_canny = None, None
        if ControlNet and isinstance(ControlNet, MfluxControlNetPipeline):
            ControlNet_model_selection = ControlNet.model_selection
            save_canny = ControlNet.save_canny

        quantize = None if quantize == "None" else int(quantize)
        seed = random.randint(0, 0xffffffffffffffff) if seed == -1 else int(seed)
        print(f"Using seed: {seed}")
        steps = min(max(steps, 2), 4) if model == "schnell" else steps
        
        flux = load_or_create_flux(model, quantize, Local_model if Local_model else None, lora_paths, lora_scales, ControlNet is not None)

        output_image_path = (
            f"{get_output_directory()}/canny_image.png"
            if ControlNet and save_canny == "true"
            else None
        )

        config_class = ConfigControlnet if ControlNet else Config
        config = config_class(
            num_inference_steps=steps,
            height=height,
            width=width,
            guidance=guidance,
            **({"controlnet_strength": strength} if ControlNet else {
                "init_image_path": image_path, 
                "init_image_strength": strength
            })
        )

        generate_args = {
            "seed": seed,
            "prompt": prompt,
            "config": config
        }

        if ControlNet:
            if image_path is None:
                raise ValueError("ControlNet image path is None, please check if the path is valid.")
            generate_args["controlnet_image_path"] = image_path
            generate_args["controlnet_save_canny"] = save_canny

            if save_canny == "true":
                generate_args["output"] = output_image_path
            else:
                generate_args["output"] = ""

        generated_image = flux.generate_image(**generate_args)
        inner_image = generated_image.image
        tensor_image = torch.from_numpy(np.array(inner_image).astype(np.float32) / 255.0)
        if tensor_image.dim() == 3:
            tensor_image = tensor_image.unsqueeze(0)

        if metadata:
            self.save_images([inner_image], prompt, model, Local_model, seed, height, width, steps, guidance, 
                             lora_paths=lora_paths, lora_scales=lora_scales, image_path=image_path, strength=strength, controlnet_model=ControlNet_model_selection)

        return (tensor_image,)
    
    def save_images(self, images, prompt, model, Local_model, seed, height, width, steps, guidance, 
                    lora_paths=None, lora_scales=None, image_path=None, strength=None, controlnet_model=None, filename_prefix="Mflux"):
        output_dir = get_output_directory()
        mflux_output_dir = os.path.join(output_dir, "Mflux")
        create_directory(mflux_output_dir)

        results = []
        existing_files = os.listdir(mflux_output_dir)
        
        existing_indices = [
            int(f.split('_')[-1].split('.')[0]) 
            for f in existing_files 
            if f.startswith(filename_prefix) and f.endswith(('.png', '.json'))
        ]

        next_index = max(existing_indices, default=0) + 1

        for batch_number, img in enumerate(images):
            filename = f"{filename_prefix}_{next_index:05}.png"
            file_path = os.path.join(mflux_output_dir, filename)
            img.save(file_path)

            metadata = {
                "prompt": prompt,
                "model": model,
                "Local_model": os.path.basename(Local_model),
                "seed": seed,
                "height": height,
                "width": width,
                "steps": steps,
                "guidance": guidance,
                "lora_paths": [os.path.basename(path) for path in lora_paths],
                "lora_scales": lora_scales,
                "image_path": image_path,
                "strength": strength,
                "controlnet_model": controlnet_model
            }

            metadata_filename = get_full_model_path(mflux_output_dir, f"{filename_prefix}_{next_index:05}.json")
            with open(metadata_filename, 'w') as metadata_file:
                json.dump(metadata, metadata_file, indent=4)

            results.append({
                "filename": filename,
                "path": file_path,
            })

            next_index += 1

        return results