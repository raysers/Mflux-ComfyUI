import random
import json
import os
import numpy as np
import torch
from tqdm import tqdm
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
    image_path = image.image_path if image else None
    strength = image.strength if image else None

    lora_paths, lora_scales = get_lora_info(Loras)
    if Loras:
        print(f"LoRA paths: {lora_paths}")
        print(f"LoRA scales: {lora_scales}")

    ControlNet_model_selection, save_canny = None, None
    if ControlNet and isinstance(ControlNet, MfluxControlNetPipeline):
        ControlNet_model_selection = ControlNet.model_selection
        save_canny = ControlNet.save_canny

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
            **({"controlnet_strength": strength} if ControlNet else {
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
        control_image = ImageUtil.load_image(image_path)
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