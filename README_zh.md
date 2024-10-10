<h1 align="center">Quick Mflux on Comfyui</h1>

<p align="center">
    <br> <font size=5>中文 | <a href="README.md">English</a></font>
</p>


# Quick Mflux on Comfyui

## 简介
Mflux在ComfyUI中的简单使用，适合不太懂得使用终端的用户，仅MacOS。

## 特别鸣谢

感谢[**mflux**](https://github.com/filipstrand/mflux)项目的开发者们，特别是项目发起人 **@filipstrand** 和活跃贡献者 **@anthonywu**，是他们让Mac用户实现了更方便高效的flux模型生图，这些贡献着实令人轻松愉悦，谢谢他们！

mflux:
https://github.com/filipstrand/mflux

同时感谢[**MFLUX-WEBUI**](https://github.com/CharafChnioune/MFLUX-WEBUI)的作者 **@CharafChnioune**，我部分参考了他的代码，基于他的项目所使用的Apache 2.0许可证的要求，我在代码中的引用段落添加了许可证注释。

## 安装指南
1. cd /path/to/your_ComfyUI
2. 激活虚拟环境
3. cd custom_nodes
4. `git clone https://github.com/raysers/Mflux-ComfyUI.git`
5. pip install mflux==0.3.0
6. 重启ComfyUI

或者，从ComfyUI-Manager中直接搜索“Mflux-ComfyUI”来快速安装。

## 使用说明

节点，当右键新建时：

**Quick MFlux Generation** 在**Mflux/Air**下
**Mflux ControlNet Loader** 在**Mflux/Pro**下

或者双击画板空白处调出节点搜索框，直接搜索节点名称，搜索关键字“Mflux”

### 流程

**Mflux Air：**

![text2img](examples/Air.png)

**Mflux Pro：**

![ControlNet](examples/Pro.png)
Mflux的ControlNet，目前仅支持Canny

**Mflux Plus：**

![Translate + Mflux](examples/Plus1.png)
英文小白们必备

![Florence2 + Mflux](examples/Plus2.png)
图像反推再生成，这里使用MiaoshouAI/Florence-2-large-PromptGen-v1.5视觉模型

以上流程均可从workflows文件夹中直接拖入ComfyUI.

！！！节点报红色的话使用ComfyUI-Manager的“一键安装缺失节点”。
！！！请注意流程末端全部使用的是预览节点，不会自动保存，需要自己挑选满意的生成图片手动保存，或者干脆把预览节点换成保存节点。

 **Quick MFlux Generation** 节点中的metadata选项，如果它是true值（默认false），那么生成的图像将被保存到 **ComfyUI/output/Mflux** 中，同时带有图像同名的json文件，里面包含了该图像的几乎一切生成参数。

### 可能的探索

**Mflux MAX:**

......

**Mflux Ultra:**

......

这里还是希望大佬们多分享工作流程，充分发扬互联网的共享精神，知识付费？不，我要拿来主义。

## 规划

下一步的目标是Lora，尽量吧。

## 贡献
我是编码新手，这是我的第一个GitHub项目。我原本的规划十分宏大，比如实现mflux的Lora以及ControlNet功能（目前已实现Mflux ControNet仅Canny），以及实现ComfyUI的精髓理念——即拆分节点以让用户能够深入了解flux的底层逻辑……但我粗浅的代码能力限制了我的蓝图。如果有高手能够帮忙实现这些，我十分感谢。在此问好。

## 许可证
我想采用和mflux项目一致的MIT麻省理工许可，也算为开源贡献一份心力吧。