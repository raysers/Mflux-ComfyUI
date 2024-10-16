from .MfluxAir import QuickMfluxNode, MfluxModelsLoader
from .MfluxPro import MfluxLorasLoader, MfluxControlNetLoader

NODE_CLASS_MAPPINGS = {
    "QuickMfluxNode": QuickMfluxNode,
    "MfluxModelsLoader": MfluxModelsLoader,
    "MfluxLorasLoader": MfluxLorasLoader,
    "MfluxControlNetLoader": MfluxControlNetLoader,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "QuickMfluxNode": "Quick MFlux Generation",
    "MfluxModelsLoader": "Mflux Models Loader",
    "MfluxLorasLoader": "Mflux Loras Loader",
    "MfluxControlNetLoader": "Mflux ControlNet Loader",
}
