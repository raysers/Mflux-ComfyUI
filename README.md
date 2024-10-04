<h1 align="center">Quick Mflux on Comfyui</h1>

<p align="center">
    <br> <font size=5>English | <a href="README_zh.md">中文</a></font>
</p>

## Introduction
Simple use of Mflux in ComfyUI, suitable for users who are not familiar with terminal usage.

## Acknowledgements

Special thanks to the developers of the [**mflux**](https://github.com/filipstrand/mflux) project, especially the initiator **@filipstrand** and active contributor **@anthonywu**, for making it easier and more efficient for Mac users to generate flux model images. Their contributions are truly delightful; appreciate them!

I also want to thank **@CharafChnioune**, the author of [**MFLUX-WEBUI**](https://github.com/CharafChnioune/MFLUX-WEBUI). I have partially referenced his code, and in accordance with the Apache 2.0 license used in his project, I have added license comments in the referenced sections of my code.

MFLUX-WEBUI:https://github.com/CharafChnioune/MFLUX-WEBUI

## Installation Guide
1. cd /path/to/your_ComfyUI
2. Activate your virtual environment
3. cd custom_nodes
4. `git clone https://github.com/raysers/Mflux-ComfyUI.git`
5. pip install mflux==0.3.0
6. Restart ComfyUI

## Usage Instructions
Currently, the functionality is relatively simple and only implements text-to-image generation. To use it, simply create a node named **Quick MFlux Generation** (found under **Mflux/Quick**), and then connect it to the built-in preview or save image nodes in ComfyUI. If the Quick MFlux Generation node is connected to a preview node and you are satisfied with the generated image, you will need to right-click to manually save the final result. If it is connected to a save image node, any generated images will be automatically saved to **ComfyUI/output** by the ComfyUI mechanism. Note that in the Quick MFlux Generation node, the metadata option should be set to true (default is false); if true, the generated image will be saved to **ComfyUI/output/Mflux** along with a JSON file of the same name, containing almost all the generation parameters of that image.

PS: Alternatively, you can directly drag the JSON or PNG workflows from this project into ComfyUI, and they will load automatically.

## Contributions
I am a novice coder, and this is my first GitHub project. I initially had grand plans, such as implementing mflux's Lora and ControlNet functionalities, and realizing the essence of ComfyUI—splitting nodes to allow users to delve into the underlying logic of flux. However, my limited coding skills have constrained my vision. If anyone with expertise could help implement these, I would be very grateful. Greetings to all!

## License
I would like to adopt the MIT license, consistent with the mflux project, as a contribution to open source.