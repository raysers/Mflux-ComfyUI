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

def download_hg_model(model_id, path, exDir="mflux"):
    model_checkpoint = os.path.join(models_dir, exDir, path)
    if not os.path.exists(model_checkpoint):
        print(f"Downloading model {model_id} to {model_checkpoint}...")
        try:
            snapshot_download(repo_id=model_id, local_dir=model_checkpoint, local_dir_use_symlinks=False)
        except Exception as e:
            print(f"Error downloading model {model_id}: {e}")
            return None
    else:
        print(f"Model {model_id} already exists at {model_checkpoint}. Skipping download.")
    return model_checkpoint

def load_or_create_flux(model, path, lora_paths, lora_scales, is_controlnet=False):
    key = (model, path, tuple(lora_paths), tuple(lora_scales), is_controlnet)
    if key not in flux_cache:
        FluxClass = Flux1Controlnet if is_controlnet else Flux1
        flux_cache[key] = FluxClass(
            model_config=ModelConfig.from_alias(model),
            local_path=path,
            lora_paths=lora_paths,
            lora_scales=lora_scales,
        )
    # This code is licensed under the Apache 2.0 License.
    # Portions of this code are derived from the work of CharafChnioune at https://github.com/CharafChnioune/MFLUX-WEBUI
    return flux_cache[key]

class QuickMfluxNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": ("STRING", {"multiline": True, "dynamicPrompts": True, "tooltip": "The text to be encoded.", "default": "Luxury food photograph"}),
                "model": (["dev", "schnell"], {"default": "schnell"}),
                "path": (["flux.1-schnell-mflux-4bit", "flux.1-dev-mflux-4bit"], {"default": "flux.1-schnell-mflux-4bit"}),
                "seed": ("INT", {"default": -1, "min": -1, "max": 0xffffffffffffffff}),
                "width": ("INT", {"default": 512}),
                "height": ("INT", {"default": 512}),
                "steps": ("INT", {"default": 2, "min": 1}),
                "cfg": ("FLOAT", {"default": 3.5, "min": 0.0}),
                "metadata": (["true", "false"], {"default": "false"}),
            },
            "optional": {
                "lora_files": ("LIST", {"default": []}),
                "lora_scales": ("STRING", {"default": ""}),
                "ControlNet": ("MfluxControlNetPipeline",),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    CATEGORY = "Mflux/Air"
    FUNCTION = "generate"

    def generate(self, prompt, model, path, seed, width, height, steps, cfg, metadata="false", lora_files=[], lora_scales="", ControlNet=None):
        image_path, save_canny = None, None
        strength = None
        
        if ControlNet:
            if isinstance(ControlNet, MfluxControlNetPipeline):
                image_path = ControlNet.image_path
                save_canny = ControlNet.save_canny
                strength = ControlNet.strength
            else:
                print("Unexpected format for ControlNet.")
        else:
            print("Non-ControlNet")

        model_id = f"madroid/{path}"  
        full_model_path = download_hg_model(model_id, path)

        if model == "dev":
            steps = max(steps, 14)
        elif model == "schnell":
            steps = min(max(steps, 2), 4)

        lora_paths = lora_files if lora_files else []
        lora_scales = [float(s.strip()) for s in lora_scales.split(",")] if lora_scales else []

        is_controlnet = ControlNet is not None
        flux = load_or_create_flux(model, full_model_path, lora_paths, lora_scales, is_controlnet)

        seed = random.randint(0, 0xffffffffffffffff) if seed == -1 else int(seed)
        print(f"Using seed: {seed}")

        output_image_path = None
        if is_controlnet and save_canny == "true":
            output_directory = get_output_directory()
            output_image_path = f"{output_directory}/generated_image.png"

        if is_controlnet:
            config = ConfigControlnet(
                num_inference_steps=steps,
                height=height,
                width=width,
                guidance=cfg,
                controlnet_strength=strength
            )
        else:
            config = Config(
                num_inference_steps=steps,
                height=height,
                width=width,
                guidance=cfg
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
            self.save_images([inner_image], prompt, model, path, seed, height, width, steps, cfg)

        print(f"Generated tensor image with shape: {tensor_image.shape}, dtype: {tensor_image.dtype}")
        return (tensor_image,)

    def save_images(self, images, prompt, model, path, seed, height, width, steps, cfg, filename_prefix="Mflux"):
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
                "path": path,
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