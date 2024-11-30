import os
import json
import random
import folder_paths
import numpy as np
import torch
from pathlib import Path 
from huggingface_hub import snapshot_download
from folder_paths import get_filename_list, get_output_directory, models_dir
from PIL import Image
from PIL.PngImagePlugin import PngInfo
from tqdm import tqdm

import comfy.utils as utils
import mlx.core as mx

from mflux.config.model_config import ModelConfig
from mflux.config.config import Config, ConfigControlnet
from mflux.flux.flux import Flux1
from mflux.controlnet.controlnet_util import ControlnetUtil
from mflux.controlnet.flux_controlnet import Flux1Controlnet
from mflux.config.runtime_config import RuntimeConfig
from mflux.post_processing.array_util import ArrayUtil
from mflux.post_processing.image_util import ImageUtil
from mflux.post_processing.generated_image import GeneratedImage
from mflux.latent_creator.latent_creator import LatentCreator
from mflux.post_processing.stepwise_handler import StepwiseHandler
from mflux.controlnet.controlnet_util import ControlnetUtil
from mflux.models.vae.vae import VAE

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

def get_lora_info(Loras):
    if Loras:
        return Loras.lora_paths, Loras.lora_scales
    return [], []

def generate_image(prompt, model, seed, width, height, steps, guidance, quantize="None", metadata=True, Local_model="", image=None, Loras=None, ControlNet=None):
    model = "dev" if "dev" in Local_model.lower() else "schnell" if "schnell" in Local_model.lower() else model
    print(f"Using model: {model}")
    image_path = image.image_path if image else None
    strength = image.strength if image else None

    lora_paths, lora_scales = get_lora_info(Loras)
    if Loras:
        print(f"LoRA paths: {lora_paths}")
        print(f"LoRA scales: {lora_scales}")

    ControlNet_model_selection, control_image_path, controlnet_strength, save_canny = None, None, None, None
    if ControlNet and isinstance(ControlNet, MfluxControlNetPipeline):
        ControlNet_model_selection = ControlNet.model_selection
        save_canny = ControlNet.save_canny
        control_strength = ControlNet.control_strength
        control_image_path = ControlNet.control_image_path

    quantize = None if quantize == "None" else int(quantize)
    seed = random.randint(0, 0xffffffffffffffff) if seed == -1 else int(seed)
    print(f"Using seed: {seed}")
    steps = min(max(steps, 2), 4) if model == "schnell" else steps

    flux = load_or_create_flux(model, quantize, Local_model if Local_model else None, lora_paths, lora_scales, ControlNet is not None)

    config_class = ConfigControlnet if ControlNet else Config
    config = RuntimeConfig(
        config=config_class(
            num_inference_steps=steps,
            height=height,
            width=width,
            guidance=guidance,
            **({"controlnet_strength": control_strength} if ControlNet else {
                "init_image_path": image_path,
                "init_image_strength": strength
            })
        ),
        model_config=flux.model_config
    )

    time_steps = tqdm(range(config.init_time_step if not ControlNet else 0, config.num_inference_steps))

    stepwise_handler = StepwiseHandler(
        flux=flux,
        config=config,
        seed=seed,
        prompt=prompt,
        time_steps=time_steps,
        output_dir=None
    )

    t5_tokens = flux.t5_tokenizer.tokenize(prompt)
    clip_tokens = flux.clip_tokenizer.tokenize(prompt)
    prompt_embeds = flux.t5_text_encoder.forward(t5_tokens)
    pooled_prompt_embeds = flux.clip_text_encoder.forward(clip_tokens)

    if ControlNet:
        control_image = ImageUtil.load_image(control_image_path)
        control_image = ControlnetUtil.scale_image(config.height, config.width, control_image)
        control_image = ControlnetUtil.preprocess_canny(control_image)
        controlnet_cond = ImageUtil.to_array(control_image)
        controlnet_cond = flux.vae.encode(controlnet_cond)
        controlnet_cond = (controlnet_cond / flux.vae.scaling_factor) + flux.vae.shift_factor
        controlnet_cond = ArrayUtil.pack_latents(latents=controlnet_cond, height=config.height, width=config.width)

        latents = LatentCreator.create(seed=seed, height=config.height, width=config.width)
    else:
        latents = LatentCreator.create_for_txt2img_or_img2img(seed, config, flux.vae)

    pbar = None
    for gen_step, t in enumerate(time_steps, 1):
        if gen_step == 2:
            pbar = utils.ProgressBar(total=steps)

        predict_args = {
            't': t,
            'prompt_embeds': prompt_embeds,
            'pooled_prompt_embeds': pooled_prompt_embeds,
            'hidden_states': latents,
            'config': config,
        }

        if ControlNet:
            controlnet_block_samples, controlnet_single_block_samples = flux.transformer_controlnet.forward(
                t=t,
                prompt_embeds=prompt_embeds,
                pooled_prompt_embeds=pooled_prompt_embeds,
                hidden_states=latents,
                controlnet_cond=controlnet_cond,
                config=config,
            )

            predict_args['controlnet_block_samples'] = controlnet_block_samples
            predict_args['controlnet_single_block_samples'] = controlnet_single_block_samples

        noise = flux.transformer.predict(**predict_args)
        dt = config.sigmas[t + 1] - config.sigmas[t]
        latents += noise * dt

        stepwise_handler.process_step(gen_step, latents)

        if pbar:
            pbar.update(1)

        mx.eval(latents)

    if pbar:
        pbar.update(1)

    latents = ArrayUtil.unpack_latents(latents=latents, height=config.height, width=config.width)
    decoded = flux.vae.decode(latents)
    normalized_latents = ImageUtil._denormalize(decoded)

    numpy_image = ImageUtil._to_numpy(normalized_latents)
    tensor_image = torch.from_numpy(numpy_image)

    if tensor_image.dim() == 3:
        tensor_image = tensor_image.unsqueeze(0)

    return (tensor_image,)

def save_images_with_metadata(images, prompt, model, quantize, Local_model, seed, height, width, steps, guidance, lora_paths, lora_scales, image_path, strength, filename_prefix="Mflux", full_prompt=None, extra_pnginfo=None):
    
    output_dir = folder_paths.get_output_directory()
    full_output_folder, filename, counter, subfolder, filename_prefix = folder_paths.get_save_image_path(
        filename_prefix, output_dir, images[0].shape[1], images[0].shape[0])
    mflux_output_folder = os.path.join(full_output_folder, "MFlux")
    os.makedirs(mflux_output_folder, exist_ok=True)
    existing_files = os.listdir(mflux_output_folder)
    existing_counters = [
        int(f.split("_")[-1].split(".")[0])
        for f in existing_files
        if f.startswith(filename_prefix) and f.endswith(".png")
    ]
    counter = max(existing_counters, default=0) + 1

    results = list()
    for image in images:
        i = 255. * image.cpu().numpy().squeeze()
        img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8))
        metadata = None
        if full_prompt is not None or extra_pnginfo is not None:
            metadata = PngInfo()
            if full_prompt is not None:
                metadata.add_text("full_prompt", json.dumps(full_prompt))
            if extra_pnginfo is not None:
                for x in extra_pnginfo:
                    metadata.add_text(x, json.dumps(extra_pnginfo[x]))
        image_file = f"{filename_prefix}_{counter:05}.png"
        img.save(os.path.join(mflux_output_folder, image_file), pnginfo=metadata, compress_level=4)
        results.append({
            "filename": image_file,
            "subfolder": subfolder,
            "type": "output"
        })

        metadata_jsonfile = os.path.join(mflux_output_folder, f"{filename_prefix}_{counter:05}.json")
        json_dict = {
            "prompt": prompt,
            "model": model,
            "quantize": quantize,
            "seed": seed,
            "height": height,
            "width": width,
            "steps": steps,
            "guidance": guidance if model == "dev" else None,
            "Local_model": Local_model,
            "init_image_path": image_path,
            "init_image_strength": strength,
            "lora_paths": lora_paths,
            "lora_scales": lora_scales,
        }
        with open(metadata_jsonfile, 'w') as metadata_file:
            json.dump(json_dict, metadata_file, indent=4)
        counter += 1
    return {"ui": {"images": results}, "counter": counter}

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
    CATEGORY = "MFlux"
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
    CATEGORY = "MFlux"
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
    CATEGORY = "MFlux"
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
                "image": ("MfluxImagePipeline",),
                "Loras": ("MfluxLorasPipeline",),
                "ControlNet": ("MfluxControlNetPipeline",),
            },
            "hidden": {
                "full_prompt": "PROMPT", 
                "extra_pnginfo": "EXTRA_PNGINFO"
            }
        }

    RETURN_TYPES = ("IMAGE",)
    CATEGORY = "MFlux"
    FUNCTION = "generate"

    def generate(self, prompt, model, seed, width, height, steps, guidance, quantize="None", metadata=True, Local_model="", image=None, Loras=None, ControlNet=None, full_prompt=None, extra_pnginfo=None):
        generated_images = generate_image(
            prompt, model, seed, width, height, steps, guidance, quantize, metadata, Local_model, image, Loras, ControlNet
        )

        image_path = image.image_path if image else None
        strength = image.strength if image else None
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
                "strength": strength,
                "lora_paths": lora_paths,
                "lora_scales": lora_scales,
                "filename_prefix": "Mflux",
                "full_prompt": full_prompt,
                "extra_pnginfo": extra_pnginfo,
            }

            result = save_images_with_metadata(**save_images_params)
            counter = result["counter"]

        return generated_images

class MfluxImagePipeline:
    def __init__(self, image_path, strength):
        self.image_path = image_path
        self.strength = strength

    def clear_cache(self):
        self.image_path = None
        self.strength = None

class MfluxLoadImg2Img:
    @classmethod
    def INPUT_TYPES(cls):
        input_dir = folder_paths.get_input_directory()
        files = [f for f in os.listdir(input_dir) if os.path.isfile(os.path.join(input_dir, f))]

        return {
            "required": {
                "image": (sorted(files), {"image_upload": True}),
                "strength": ("FLOAT", {"default": 0.4, "min": 0.0, "max": 1.0, "step": 0.01}),
            }
        }

    CATEGORY = "MFlux"
    RETURN_TYPES = ("MfluxImagePipeline", "INT", "INT")
    RETURN_NAMES = ("image", "width", "height")
    FUNCTION = "load_and_process"

    def load_and_process(self, image, strength):
        image_path = folder_paths.get_annotated_filepath(image)

        with Image.open(image_path) as img:
            width, height = img.size

        return MfluxImagePipeline(image_path, strength), width, height

    @classmethod
    def IS_CHANGED(cls, image, strength):
        image_hash = hash(image)
        strength_rounded = round(float(strength), 2)
        return (image_hash, strength_rounded)

    @classmethod
    def VALIDATE_INPUTS(cls, image, strength):
        if not folder_paths.exists_annotated_filepath(image):
            return "Invalid image file: {}".format(image)

        if not isinstance(strength, (int, float)):
            return "Strength must be a number"

        return True

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
    CATEGORY = "MFlux"

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
    def __init__(self, model_selection, control_image_path, control_strength, save_canny=False):
        self.model_selection = model_selection
        self.control_image_path = control_image_path
        self.control_strength = control_strength
        self.save_canny = save_canny
 

    def clear_cache(self):
        self.model_selection = None
        self.control_image_path = None
        self.control_strength = None
        self.save_canny = False


class MfluxControlNetLoader:
    @classmethod
    def INPUT_TYPES(cls):
        controlnet_models = [
            "InstantX/FLUX.1-dev-Controlnet-Canny",
        ]

        input_dir = folder_paths.get_input_directory()
        files = [f for f in os.listdir(input_dir) if os.path.isfile(os.path.join(input_dir, f))]

        return {
            "required": {
                "model_selection": (controlnet_models, {"default": "InstantX/FLUX.1-dev-Controlnet-Canny"}),
                "image": (sorted(files), {"image_upload": True}),
                "control_strength": ("FLOAT", {"default": 0.5, "min": 0.0, "max": 1.0, "step": 0.01}),
                "save_canny": ("BOOLEAN", {"default": False, "label_on": "True", "label_off": "False"}),
            }

        }

    CATEGORY = "MFlux"
    RETURN_TYPES = ("MfluxControlNetPipeline", "INT", "INT", "IMAGE",)
    RETURN_NAMES = ("ControlNet", "width", "height", "preprocessed_image")
    FUNCTION = "load_and_select"

    def load_and_select(self, model_selection, image, control_strength, save_canny):
        
        control_image_path = folder_paths.get_annotated_filepath(image)

        with Image.open(control_image_path) as img:
            width, height = img.size

        with Image.open(control_image_path) as img:
            canny_image = ControlnetUtil.preprocess_canny(img)
            canny_image_np = np.array(canny_image).astype(np.float32) / 255.0
            canny_tensor = torch.from_numpy(canny_image_np)

            if canny_tensor.dim() == 3:
                canny_tensor = canny_tensor.unsqueeze(0)

        return MfluxControlNetPipeline(model_selection, control_image_path, control_strength, save_canny), width, height, canny_tensor

    @classmethod
    def IS_CHANGED(cls, model_selection, image, control_strength, save_canny):
        control_image_path = folder_paths.get_annotated_filepath(image)
        control_strength = round(float(control_strength), 2)
        control_image_hash = hash(image)
        return str(control_image_hash) + str(model_selection) + str(control_strength) + str(save_canny)

    @classmethod
    def VALIDATE_INPUTS(cls, image, model_selection, control_strength, save_canny):

        available_models = [
            "InstantX/FLUX.1-dev-Controlnet-Canny",
        ]
        if model_selection not in available_models:
            return f"Invalid model selection: {model_selection}"

        if not folder_paths.exists_annotated_filepath(image):
            return "Invalid control image file: {}".format(image)

        if not isinstance(control_strength, (int, float)):
            return "Strength must be a number"

        if not isinstance(save_canny, bool):
            return "save_canny must be a boolean value"


        return True