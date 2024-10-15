<h1 align="center">Quick Mflux on Comfyui</h1>

<p align="center">
    <br> <font size=5>English | <a href="README_zh.md">中文</a></font>
</p>

# Quick Mflux on Comfyui

## Introduction
Simple use of Mflux in ComfyUI, suitable for users who are not familiar with terminal usage, specifically for MacOS.

## Acknowledgements

Thanks to the developers of the [**mflux**](https://github.com/filipstrand/mflux) project, especially the initiator **@filipstrand** and active contributor **@anthonywu**, for making it easier and more efficient for Mac users to generate flux model images. These contributions are truly delightful—thank you!

mflux:  
https://github.com/filipstrand/mflux

Thanks also to **@CharafChnioune**, the author of [**MFLUX-WEBUI**](https://github.com/CharafChnioune/MFLUX-WEBUI), from whom I partially referenced some code. In compliance with the Apache 2.0 license used in his project, I have added license comments in the referenced sections of my code.

## Installation Guide
1. `cd /path/to/your_ComfyUI`
2. Activate the virtual environment
3. `cd custom_nodes`
4. `git clone https://github.com/raysers/Mflux-ComfyUI.git`
5. `pip install mflux==0.3.0`
6. Restart ComfyUI

Alternatively, you can search for "Mflux-ComfyUI" in ComfyUI-Manager for a quick installation.

Update Statement

This update has redesigned the model loading and quantization mechanism to support Lora, aligning with the official Mflux method. It now uses a full model with quantization parameters, which may make the 4BIT models downloaded in previous versions redundant. However:

I recommend keeping them.

Because my personal machine is an aging M1 Pro with 16GB RAM, even when using the full model with 4-bit quantization, it sometimes struggles to keep up.

There are a few issues to consider with this model mechanism change:

Many long-time Mflux users have already downloaded the full native models (dev and schnell) from the Black Forest team via Huggingface, typically stored in the user’s .cache directory. If they just want to try out ComfyUI, re-downloading these models would be unnecessary.
Some ComfyUI users may have previously downloaded the full native models, possibly stored in ComfyUI's models/checkpoint folder. In that case, re-downloading would also be redundant.
To avoid wasting resources, I came up with the idea of creating a new node. In this version, I’ve added a node called Mflux Models Loader, which loads local models. Since previous versions of the plugin stored the 4BIT quantized models under models/mflux, the main function of this node is to scan the models in models/Mflux. If users already have the full native dev and schnell models in ComfyUI, they can move them to models/Mflux for automatic detection, avoiding the need to download them again from Huggingface.

Why do we need the full dev and schnell models? Can’t we just use the quantized versions?

Yes, but currently only the full models support adjusting weights with LORA. The best compromise is to use Mflux’s quantization parameters, which we can set to 4 or 8.

As for whether to keep the 4BIT models previously downloaded, I personally chose to keep them because, compared to the full model with quantization, directly loading the 4BIT model seems to consume less VRAM—though that might just be a placebo effect.

Of course, users with high-end setups can ignore this. Users are free to decide whether to delete unnecessary models to save disk space.

—Apologies for any confusion this update may cause.

## Usage Instructions

### Create New Nodes

#### Under `Mflux/Air`:
- `Quick MFlux Generation`
- `Mflux Models Loader`

#### Under `Mflux/Pro`:
- `Mflux Loras Loader`
- `Mflux ControlNet Loader`

### Alternative Method

- Double-click on an empty area of the canvas to bring up the node search box.
- Search for nodes using the keyword `Mflux`.

### Workflow

**Mflux Air:**

![text2img](examples/Air.png)

This workflow will download the full dev or schnell models from Huggingface to the `.cache` directory.

If your full dev or schnell models have already been moved to `models/Mflux`, you can connect an external **Mflux Loras Loader** and select your full dev or schnell model. In this case, no download will be triggered, and the local full model will be used directly.

Alternatively, the external node can continue to load 4BIT quantized models, such as:

![text2img](examples/Air_Local_models.png)

**Mflux Pro:**

![Loras](examples/Pro_Loras.png)

In the image above, two **Mflux Loras Loader** nodes are used, simply to illustrate that they can be daisy-chained. This means, in theory, you can load an unlimited number of Loras.

> **Note**: When using Loras, you cannot chain local models, as that will result in an error.

![ControlNet](examples/Pro_ControlNet.png)

Mflux's ControlNet currently only supports Canny.

**Mflux Plus:**

![Translate + Mflux](examples/Plus1.png)

A must-have for users less proficient in English.

![Florence2 + Mflux](examples/Plus2.png)

Reverse image generation, using the `MiaoshouAI/Florence-2-large-PromptGen-v1.5` vision model.

All the above workflows can be directly dragged into ComfyUI from the `workflows` folder.

!!! If a node is highlighted in red, use ComfyUI-Manager's "Install Missing Nodes" feature.

!!! Please note that preview nodes are used at the end of all workflows, so images are not saved automatically. You will need to manually save any generated images you are satisfied with, or replace the preview nodes with save nodes.

In the **Quick MFlux Generation** node, if the `metadata` option is set to `true` (default is `false`), the generated image will be saved in **ComfyUI/output/Mflux**, along with a `.json` file of the same name. This JSON file will contain nearly all the parameters used to generate the image.

### Possible Explorations

**Mflux MAX:**

......

**Mflux Ultra:**

......

I hope the community will share more workflows, embodying the spirit of open collaboration on the internet. Paid knowledge? No thanks, I believe in embracing and sharing what’s freely available.

## Roadmap

The next goal is to complete the final piece of the Mflux puzzle: saving custom models.

## Contribution

I’m a beginner at coding, and this is my first GitHub project. My original plan was quite ambitious, such as implementing Mflux's Lora and ControlNet features (currently, Mflux ControlNet only supports Canny, and Lora is functional), as well as realizing ComfyUI's core philosophy—breaking down nodes to help users deeply understand the underlying logic of Mflux. However, my limited coding skills have constrained my vision. If anyone more experienced could help implement these features, I would be extremely grateful. Greetings to all!

## License

I plan to adopt the MIT License, consistent with the Mflux project, as a small contribution to the open-source community.
