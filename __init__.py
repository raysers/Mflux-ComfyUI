from .Mflux_Comfy.Mflux_Air import QuickMfluxNode, MfluxModelsLoader, MfluxModelsDownloader, MfluxCustomModels
from .Mflux_Comfy.Mflux_Pro import MfluxImg2Img, MfluxLorasLoader, MfluxControlNetLoader  # 仅导入所需的非实验节点

NODE_CLASS_MAPPINGS = {
    "QuickMfluxNode": QuickMfluxNode,
    "MfluxModelsLoader": MfluxModelsLoader,
    "MfluxModelsDownloader": MfluxModelsDownloader,
    "MfluxCustomModels": MfluxCustomModels,
    "MfluxImg2Img": MfluxImg2Img,
    "MfluxLorasLoader": MfluxLorasLoader,
    "MfluxControlNetLoader": MfluxControlNetLoader,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "QuickMfluxNode": "Quick MFlux Generation",
    "MfluxModelsLoader": "MFlux Models Loader",
    "MfluxModelsDownloader": "MFlux Models Downloader",
    "MfluxCustomModels": "MFlux Custom Models",
    "MfluxImg2Img": "Mflux Img2Img",
    "MfluxLorasLoader": "MFlux Loras Loader",
    "MfluxControlNetLoader": "MFlux ControlNet Loader",
}
