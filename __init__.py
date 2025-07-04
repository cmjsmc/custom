from . import server
from .ram_nodes import LoadImageFromUpload, PreviewImageInRAM, PreviewVideoInRAM, PreviewAnimationAsWebP, PrivacyText, PreviewTextInRAM

NODE_CLASS_MAPPINGS = {
    "LoadImageFromUpload": LoadImageFromUpload,
    "PreviewImageInRAM": PreviewImageInRAM,
    "PreviewVideoInRAM": PreviewVideoInRAM,
    "PreviewAnimationAsWebP": PreviewAnimationAsWebP,
    "PrivacyText": PrivacyText,
    "PreviewTextInRAM": PreviewTextInRAM,
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "LoadImageFromUpload": "Load Image (Privacy)",
    "PreviewImageInRAM": "Preview Image (Privacy)",
    "PreviewVideoInRAM": "Preview Video (Privacy)",
    "PreviewAnimationAsWebP": "Preview Animation as WebP (Privacy)",
    "PrivacyText": "Text (Privacy)",
    "PreviewTextInRAM": "Preview Text (Privacy)",
}
WEB_DIRECTORY = "./js"
__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]