import random
import json
import os
import numpy as np
import torch
from tqdm import tqdm
from PIL import Image
from PIL.PngImagePlugin import PngInfo
import comfy.utils as utils
import folder_paths

import mlx.core as mx
from mflux.config.model_config import ModelConfig
from mflux.config.config import Config, ConfigControlnet
from mflux.flux.flux import Flux1
from mflux.controlnet.flux_controlnet import Flux1Controlnet
from mflux.config.runtime_config import RuntimeConfig
from mflux.post_processing.array_util import ArrayUtil
from mflux.post_processing.image_util import ImageUtil
from mflux.post_processing.generated_image import GeneratedImage
from mflux.latent_creator.latent_creator import LatentCreator
from mflux.post_processing.stepwise_handler import StepwiseHandler
from mflux.controlnet.controlnet_util import ControlnetUtil
from mflux.models.vae.vae import VAE
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

def get_lora_info(Loras):
    if Loras:
        return Loras.lora_paths, Loras.lora_scales
    return [], []

def generate_image(prompt, model, seed, width, height, steps, guidance, quantize="None", metadata=True, Local_model="", image=None, Loras=None, ControlNet=None):
    model = "dev" if "dev" in Local_model.lower() else "schnell" if "schnell" in Local_model.lower() else model
    print(f"Using model: {model}")
    image_path = image.image_path if image else None
    image_strength = image.image_strength if image else None

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
                "init_image_strength": image_strength
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
