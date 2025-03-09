from .ComfyMflux import QuickMfluxNode, MfluxModelsLoader, MfluxModelsDownloader, MfluxCustomModels, MfluxImg2Img, MfluxLorasLoader, MfluxControlNetLoader

NODE_CLASS_MAPPINGS = {
    "QuickMfluxNode": QuickMfluxNode,
    "MfluxModelsLoader": MfluxModelsLoader,
    "MfluxModelsDownloader": MfluxModelsDownloader,
    "MfluxCustomModels": MfluxCustomModels,
    "MfluxLorasLoader": MfluxLorasLoader,
    "MfluxImg2Img": MfluxImg2Img,
    "MfluxControlNetLoader": MfluxControlNetLoader,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "QuickMfluxNode": "Quick MFlux Generation",
    "MfluxModelsLoader": "MFlux Models Loader",
    "MfluxModelsDownloader": "MFlux Models Downloader",
    "MfluxCustomModels": "MFlux Custom Models",
    "MfluxLorasLoader": "MFlux Loras Loader",
    "MfluxImg2Img": "MFlux Image2Image",
    "MfluxControlNetLoader": "MFlux ControlNet Loader",
}