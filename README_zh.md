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

ComfyUI的loras存放路径是**models/loras**，需要手动将LORA文件放进目录里，**Mflux Loras Loader**节点将自动检索。

我的习惯是在**models/loras**下新建Mflux文件夹，用来检测Mflux所能适配的LORA，统一存放其中，因此在我的节点中，检索出来的应该是Mflux/*******.safetensors

**需要注意：**

本次更新为了支持Lora，重新设计了模型加载和量化机制，保持与Mflux官方一致，使用完整模型+量化参数，这导致运行时需要从Huggingface下载几十G的黑森林FLUX原生模型，也许会给部分用户带来负担。

这是目前为了实现Lora功能的无奈之举，因为Lora只对完整版的权重起作用，使用量化模型则会报错，无法绕开。

为了避免重复下载带来的资源浪费，如果之前ComfyUI里已经有FLUX完整模型，可以把模型移动到“**models/Mflux**”目录下并且使用**Mflux Models Loader**节点加载，可以直接使用跳过下载流程。

当然，如果对Lora的需求不大，仍然推荐继续使用之前的4BIT量化模型，只要它还在以前版本的预设路径“**models/Mflux**”目录下，那么就可以在**Mflux Models Loader**节点列表中自由选择。

这里也给出4BIT版本的手动下载地址：

[madroid/flux.1-schnell-mflux-4bit](https://huggingface.co/madroid/flux.1-schnell-mflux-4bit)
[madroid/flux.1-dev-mflux-4bit](https://huggingface.co/madroid/flux.1-dev-mflux-4bit)

## 使用说明

右键新建节点：

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

如果你的完整版dev或schnell已经移动到models/Mflux，此时外接一个**Mflux Models Loader**选择你的完整版dev或schnell，那么不会触发下载，会直接使用你本地的完整版模型。

或者外接的节点可以用来继续加载4BIT量化模型，比如：

![text2img](examples/Air_Local_models.png)


**Mflux Pro：**

![Loras](examples/Pro_Loras.png)

图中使用了两个**Mflux Loras Loader**节点，只是为了说明它们是可以串接的，也就是说，理论上可以加载无数Lora...

注意使用Lora的时候同样可以用**Mflux Models Loader**节点加载本地模型，但仅限完整版模型，如果模型列表中选择了量化模型，那样将会报错。



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
 我个人比较喜欢打开metadata为true，同时连接预览节点而不是保存节点，这样的好处是不会重复保存，而且如果日后要检索某图片的信息，可以直接json文件中查阅，方便复刻图像。

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