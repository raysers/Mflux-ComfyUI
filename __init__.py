from .Mflux_Air import QuickMfluxNode, MfluxModelsLoader, MfluxModelsDownloader, MfluxCustomModels
from .Mflux_Pro import MfluxLoadImage, MfluxLorasLoader, MfluxControlNetLoader  # 仅导入所需的非实验节点

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
    "MfluxModelsLoader": "Mflux Models Loader",
    "MfluxModelsDownloader": "Mflux Models Downloader",
    "MfluxCustomModels": "Mflux Custom Models",
    "MfluxLoadImage": "Mflux Load Image",
    "MfluxLorasLoader": "Mflux Loras Loader",
    "MfluxControlNetLoader": "Mflux ControlNet Loader",
}