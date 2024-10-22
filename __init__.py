from .MfluxAir import QuickMfluxNode, MfluxModelsLoader, MfluxModelsDownloader, MfluxCustomModels
from .MfluxPro import MfluxLorasLoader, MfluxControlNetLoader

NODE_CLASS_MAPPINGS = {
    "QuickMfluxNode": QuickMfluxNode,
    "MfluxModelsLoader": MfluxModelsLoader,
    "MfluxModelsDownloader": MfluxModelsDownloader,
    "MfluxCustomModels": MfluxCustomModels,
    "MfluxLorasLoader": MfluxLorasLoader,
    "MfluxControlNetLoader": MfluxControlNetLoader,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "QuickMfluxNode": "Quick MFlux Generation",
    "MfluxModelsLoader": "Mflux Models Loader",
    "MfluxModelsDownloader": "Mflux Models Downloader",
    "MfluxCustomModels": "Mflux Custom Models",
    "MfluxLorasLoader": "Mflux Loras Loader",
    "MfluxControlNetLoader": "Mflux ControlNet Loader",
}