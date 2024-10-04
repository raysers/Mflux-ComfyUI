<h1 align="center">Quick Mflux on Comfyui</h1>

<p align="center">
    <br> <font size=5>中文 | <a href="README.md">English</a></font>
</p>


# Quick Mflux on Comfyui

## 简介
Mflux在ComfyUI中的简单使用，适合不太懂得使用终端的用户。

## 特别鸣谢

感谢[**mflux**](https://github.com/filipstrand/mflux)项目的开发者们，特别是项目发起人 **@filipstrand** 和活跃贡献者 **@anthonywu**，是他们让Mac用户实现了更方便高效的flux模型生图，这些贡献着实令人轻松愉悦，谢谢他们！

同时感谢[**MFLUX-WEBUI**](https://github.com/CharafChnioune/MFLUX-WEBUI)的作者 **@CharafChnioune**，我部分参考了他的代码，基于他的项目所使用的Apache 2.0许可证的要求，我在代码中的引用段落添加了许可证注释。

## 安装指南
1. cd /path/to/your_ComfyUI
2. 激活虚拟环境
3. cd custom_nodes
4. `git clone https://github.com/raysers/Mflux-ComfyUI.git`
5. pip install mflux==0.3.0
6. 重启ComfyUI

## 使用说明
由于目前的功能相对简单，仅仅实现了文生图，因此只需要新建节点 **Quick MFlux Generation**（在 **Mflux/Quick** 下），再连接ComfyUI自带的预览图像或保存图像节点即可。如果 **Quick MFlux Generation** 连接的是预览图像节点，最终生成结果需要右键手动保存；如果是保存图像节点，任何生成图片都将被ComfyUI的机制自动保存到 **ComfyUI/output** 下。需要注意的是 **Quick MFlux Generation** 节点中的metadata选项，如果它是true值（默认false），那么生成的图像将被保存到 **ComfyUI/output/Mflux** 中，同时带有图像同名的json文件，里面包含了该图像的几乎一切生成参数。

或者，您可以直接将本项目中的JSON或PNG工作流拖入ComfyUI，它们将自动加载。

## 贡献
我是编码新手，这是我的第一个GitHub项目。我原本的规划十分宏大，比如实现mflux的Lora以及ControlNet功能，以及实现ComfyUI的精髓理念——即拆分节点以让用户能够深入了解flux的底层逻辑……但我粗浅的代码能力限制了我的蓝图。如果有高手能够帮忙实现这些，我十分感谢。在此问好。

## 许可证
我想采用和mflux项目一致的MIT麻省理工许可，也算为开源贡献一份心力吧。