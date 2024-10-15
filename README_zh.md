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

## 更新声明

本次更新为了支持Lora，重新设计了模型加载和量化机制，保持与Mflux官方一致，使用完整模型+量化参数，可能导致之前版本机制中下载的4BIT模型变得多余，然而：

**我建议保留。**

因为我个人的机器是老态龙钟的M1 pro 16GB，使用完整版模型的时候虽然选择了量化参数为4，但这机子有时也难免后继乏力。

在这次模型机制的变更中需要顾及到以下问题：

1、mflux老用户们终端运行mflux生图的时候，大部分人已经从Huggingface下载过完整版的黑森林团队原生dev和schnell模型，一般存储在用户目录.cache中，如果他们只是想来ComfyUI体验一把，此时重新下载就显得多余；

2.有些ComfyUI用户之前可能也下载过完整版的原生模型，也许在ComfyUI的models/checkpoint中，此时重新下载同样显得多余。

为了解决这些资源浪费的问题，我只能想出新造节点的法子，这个版本中添加了一个加载本地模型的节点**Mflux Models Loader**，既然插件过往版本的4BIT量化模型被默认机制存储到了models/mflux中，那么这个节点的主要功能就是检索models/Mflux下的模型，如果用户ComfyUI中已经有过完整版的原生dev和schnell模型，不妨可以将其移动至models/Mflux中，它们将被自动检索，避免从Huggingface再次下载。

那么为何我们需要完整版的dev和schnell？量化不行吗？

是的，在当前的实现中，只有完整版的模型能够实现利用LORA调整权重，能做的补救方法就是利用mflux的量化参数，我们可以设置成4或者8.

至于以前下载的4BIT版本该不该保留，我个人是选择了保留，因为比起完整模型加量化参数方式，直接加载4BIT的显存消耗似乎更少，不知是否心理作用。

当然配置高的用户可以忽视这些，用户们可以自行选择是否删除多余模型以节省硬盘空间。

————以上是本次更新可能带来的混乱，在这里致个歉。

## 使用说明

节点列表：

**Mflux/Air**下：

**Quick MFlux Generation**
**Mflux Models Loader**

**Mflux/Pro**下：

**Mflux Loras Loader**
**Mflux ControlNet Loader**

或者双击画板空白处调出节点搜索框，直接搜索节点名称，搜索关键字“Mflux”

### 流程

**Mflux Air：**

![text2img](examples/Air.png)



这个流程将会从Huggingface下载完整版的dev或schnell到.cache里。

如果你的完整版dev或schnell已经移动到models/Mflux，此时外接一个**Mflux Loras Loader**选择你的完整版dev或schnell，那么不会触发下载，会直接使用你本地的完整版模型。

或者外接的节点可以用来继续加载4BIT量化模型，比如：

![text2img](examples/Air_Local_models.png)


**Mflux Pro：**

![Loras](examples/Pro_Loras.png)

图中使用了两个**Mflux Loras Loader**节点，只是为了说明它们是客户串接的，也就是说，理论上可以加载无数Lora...

注意使用Lora的时候不能串接本地模型，那样将会报错。



![ControlNet](examples/Pro_ControlNet.png)

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

下一步的目标是mflux的最后一块拼图，保存专属模型。

## 贡献
我是编码新手，这是我的第一个GitHub项目。我原本的规划十分宏大，比如实现mflux的Lora以及ControlNet功能（目前已实现Mflux ControNet仅Canny，还有Lora），以及实现ComfyUI的精髓理念——即拆分节点以让用户能够深入了解flux的底层逻辑……但我粗浅的代码能力限制了我的蓝图。如果有高手能够帮忙实现这些，我十分感谢。在此问好。

## 许可证
我想采用和mflux项目一致的MIT麻省理工许可，也算为开源贡献一份心力吧。