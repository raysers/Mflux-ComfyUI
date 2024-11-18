from .Mflux_Comfy.Mflux_Air import QuickMfluxNode, MfluxModelsLoader, MfluxModelsDownloader, MfluxCustomModels
from .Mflux_Comfy.Mflux_Pro import MfluxLoadImage, MfluxLorasLoader, MfluxControlNetLoader  # 仅导入所需的非实验节点

NODE_CLASS_MAPPINGS = {
    "QuickMfluxNode": QuickMfluxNode,
    "MfluxModelsLoader": MfluxModelsLoader,
    "MfluxModelsDownloader": MfluxModelsDownloader,
    "MfluxCustomModels": MfluxCustomModels,
    "MfluxLoadImage": MfluxLoadImage,
    "MfluxLorasLoader": MfluxLorasLoader,
    "MfluxControlNetLoader": MfluxControlNetLoader,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "QuickMfluxNode": "Quick MFlux Generation",
    "MfluxModelsLoader": "MFlux Models Loader",
    "MfluxModelsDownloader": "MFlux Models Downloader",
    "MfluxCustomModels": "MFlux Custom Models",
    "MfluxLoadImage": "MFlux Load Image",
    "MfluxLorasLoader": "MFlux Loras Loader",
    "MfluxControlNetLoader": "MFlux ControlNet Loader",
}