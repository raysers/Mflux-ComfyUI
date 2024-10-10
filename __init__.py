from .MfluxAir import QuickMfluxNode
from .MfluxPro import MfluxControlNetLoader

# 节点类映射
NODE_CLASS_MAPPINGS = {
    "QuickMfluxNode": QuickMfluxNode,
    "MfluxControlNetLoader": MfluxControlNetLoader,  # 映射新节点
}

# 节点显示名称映射
NODE_DISPLAY_NAME_MAPPINGS = {
    "QuickMfluxNode": "Quick MFlux Generation",
    "MfluxControlNetLoader": "Mflux ControlNet Loader",  # 添加显示名称
}
