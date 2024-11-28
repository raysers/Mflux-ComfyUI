import os
import json
from pathlib import Path 
from huggingface_hub import snapshot_download
from folder_paths import get_filename_list, get_output_directory, models_dir
from mflux.config.model_config import ModelConfig
from mflux.flux.flux import Flux1
from .Mflux_Core import get_lora_info, generate_image, save_images_with_metadata

def create_directory(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)
    return directory

mflux_dir = os.path.join(models_dir, "Mflux")
create_directory(mflux_dir)

def get_full_model_path(model_dir, model_name):
    return os.path.join(model_dir, model_name)

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
    CATEGORY = "MFlux/Air"
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
    CATEGORY = "MFlux/Air"
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
                "model_name": (cls.get_sorted_model_paths() or ["None"], {"default": cls.get_sorted_model_paths()[0] if cls.get_sorted_model_paths() else "None"}),  
            },
            "optional": {
                "free_path": ("STRING", {"default": "", "tooltip": "Free model path. If provided, this will override the model_name."}),
            }
        }

    RETURN_TYPES = ("PATH",)
    RETURN_NAMES = ("Local_model",)
    CATEGORY = "MFlux/Air"
    FUNCTION = "load"

    @classmethod
    def get_sorted_model_paths(cls):
        model_paths = [p.name for p in Path(mflux_dir).iterdir() if p.is_dir()]
        return sorted(model_paths, key=lambda x: x.lower())

    def load(self, model_name="", free_path=""):
        if free_path:
            full_model_path = free_path
            if not os.path.exists(full_model_path):
                raise ValueError(f"Provided custom path does not exist: {full_model_path}")
        elif model_name and model_name != "None":  
            full_model_path = get_full_model_path(mflux_dir, model_name)
        else:
            raise ValueError("Either 'model_name' must be provided or 'free_path' must be used.")

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
                "img2img": ("MfluxImg2ImgPipeline",),
                "Loras": ("MfluxLorasPipeline",),
                "ControlNet": ("MfluxControlNetPipeline",),
            },
            "hidden": {
                "full_prompt": "PROMPT", 
                "extra_pnginfo": "EXTRA_PNGINFO"
            }
        }

    RETURN_TYPES = ("IMAGE",)
    CATEGORY = "MFlux/Air"
    FUNCTION = "generate"

    def generate(self, prompt, model, seed, width, height, steps, guidance, quantize="None", metadata=True, Local_model="", img2img=None, Loras=None, ControlNet=None, full_prompt=None, extra_pnginfo=None):
        generated_images = generate_image(
            prompt, model, seed, width, height, steps, guidance, quantize, metadata, Local_model, img2img, Loras, ControlNet
        )

        image_path = img2img.image_path if img2img else None
        image_strength = img2img.image_strength if img2img else None
        lora_paths, lora_scales = get_lora_info(Loras)

        if metadata:
            save_images_params = {
                "images": generated_images,
                "prompt": prompt,
                "model": "dev" if "dev" in Local_model.lower() else "schnell" if "schnell" in Local_model.lower() else model,
                "quantize": quantize,
                "Local_model": Local_model,
                "seed": seed,
                "height": height,
                "width": width,
                "steps": steps,
                "guidance": guidance,
                "image_path": image_path,
                "image_strength": image_strength,
                "lora_paths": lora_paths,
                "lora_scales": lora_scales,
                "filename_prefix": "Mflux",
                "full_prompt": full_prompt,
                "extra_pnginfo": extra_pnginfo,
            }

            result = save_images_with_metadata(**save_images_params)
            counter = result["counter"]

        return generated_images
