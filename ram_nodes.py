import torch
import numpy as np
from PIL import Image, ImageOps
import base64
import io
from itertools import cycle
import hashlib

from .server import get_session_key


def xor_cipher(data, key):
    if not key:
        raise ValueError("XOR key cannot be empty")
    return bytes(a ^ b for a, b in zip(data, cycle(key)))


class LoadImageFromUpload:
    @classmethod
    def INPUT_TYPES(s):
        return {"required": {"encrypted_upload": ("STRING", {"multiline": True, "default": ""}),
                             "client_id": ("STRING", {"multiline": False, "default": ""}), }}

    CATEGORY = "image"
    RETURN_TYPES = ("IMAGE", "MASK")
    FUNCTION = "load_image"

    def load_image(self, encrypted_upload, client_id):
        if not encrypted_upload: return (torch.empty(0), torch.empty(0))
        if not client_id: raise Exception("The 'client_id' field on the LoadImage (Privacy) node cannot be empty.")
        obfuscated_data = base64.b64decode(encrypted_upload)
        key = get_session_key(client_id)
        if not key: raise Exception(f"Could not find session key for client_id: {client_id}.")
        image_data = xor_cipher(obfuscated_data, key)
        img = Image.open(io.BytesIO(image_data))
        img = ImageOps.exif_transpose(img)
        output_image = img.convert("RGB")
        output_image = np.array(output_image).astype(np.float32) / 255.0
        output_image = torch.from_numpy(output_image)[None,]
        if 'A' in img.getbands():
            mask = 1. - torch.from_numpy(np.array(img.getchannel('A')).astype(np.float32) / 255.0)
        else:
            mask = torch.ones((img.height, img.width), dtype=torch.float32)
        mask = mask.unsqueeze(0)
        return (output_image, mask)

    @classmethod
    def IS_CHANGED(s, encrypted_upload, client_id):
        return hashlib.sha256((encrypted_upload + client_id).encode()).hexdigest()


class PreviewImageInRAM:
    @classmethod
    def INPUT_TYPES(s):
        return {"required": {"images": ("IMAGE",), "client_id": ("STRING", {"multiline": False, "default": ""}), }}

    RETURN_TYPES = ()
    FUNCTION = "preview_images"
    OUTPUT_NODE = True
    CATEGORY = "image"

    def preview_images(self, images, client_id=None):
        if not client_id: raise Exception("The 'client_id' field on the PreviewImage (Privacy) node cannot be empty.")
        key = get_session_key(client_id)
        if not key: raise Exception(f"Could not find session key for client_id: {client_id}.")
        results = []
        for image_tensor in images:
            i = 255. * image_tensor.cpu().numpy()
            img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8))
            buffer = io.BytesIO()
            img.save(buffer, format="WEBP", lossless=False, quality=95, method=4)
            image_data_bytes = buffer.getvalue()
            obfuscated_data = xor_cipher(image_data_bytes, key)
            img_base64 = base64.b64encode(obfuscated_data).decode('utf-8')
            results.append({"base64": img_base64, "format": "webp", "type": "image"})
        return {"ui": {"previews": results}}


class PreviewVideoInRAM:
    @classmethod
    def INPUT_TYPES(s):
        return {"required": {"video_data": ("VIDEO_BYTES",), "mime_type": ("STRING", {"default": "video/mp4"}),
                             "client_id": ("STRING", {"multiline": False, "default": ""}), }}

    RETURN_TYPES = ()
    FUNCTION = "preview_video"
    OUTPUT_NODE = True
    CATEGORY = "video"

    def preview_video(self, video_data, mime_type, client_id=None):
        if not client_id: raise Exception("The 'client_id' field on the PreviewVideo (Privacy) node cannot be empty.")
        if not video_data: return {"ui": {"previews": []}}
        key = get_session_key(client_id)
        if not key: raise Exception(f"Could not find session key for client_id: {client_id}.")
        video_bytes = video_data
        encrypted_video_bytes = xor_cipher(video_bytes, key)
        video_base64 = base64.b64encode(encrypted_video_bytes).decode('utf-8')
        results = [{"base64": video_base64, "mime_type": mime_type, "type": "video"}]
        return {"ui": {"previews": results}}


class PreviewAnimationAsWebP:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "images": ("IMAGE",),
                "fps": ("FLOAT", {"default": 10.0, "min": 0.1, "max": 60.0, "step": 0.1}),
                "client_id": ("STRING", {"multiline": False, "default": ""}),
            }
        }

    RETURN_TYPES = ()
    FUNCTION = "preview_animation"
    OUTPUT_NODE = True
    CATEGORY = "image"

    def preview_animation(self, images, fps, client_id=None):
        if not client_id: raise Exception("The 'client_id' field on the PreviewAnimationAsWebP node cannot be empty.")
        if images is None or len(images) == 0: return {"ui": {"previews": []}}
        key = get_session_key(client_id)
        if not key: raise Exception(f"Could not find session key for client_id: {client_id}. Please refresh the page.")
        pil_images = [Image.fromarray(np.clip(255. * i.cpu().numpy(), 0, 255).astype(np.uint8)).convert("RGB") for i in
                      images]
        if not pil_images: return {"ui": {"previews": []}}
        buffer = io.BytesIO()
        pil_images[0].save(buffer, format="WEBP", save_all=True, append_images=pil_images[1:], duration=int(1000 / fps),
                           loop=0, lossless=False, quality=95, method=4)
        webp_bytes = buffer.getvalue()
        encrypted_webp_bytes = xor_cipher(webp_bytes, key)
        webp_base64 = base64.b64encode(encrypted_webp_bytes).decode('utf-8')
        results = [{"base64": webp_base64, "format": "webp", "type": "image"}]
        return {"ui": {"previews": results}}


class PrivacyText:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "encrypted_text": ("STRING", {"multiline": True, "default": ""}),
                "client_id": ("STRING", {"multiline": False, "default": ""}),
            }
        }

    CATEGORY = "text"
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("text",)
    FUNCTION = "decrypt_text"

    def decrypt_text(self, encrypted_text, client_id):
        if not encrypted_text:
            return ("",)
        if not client_id:
            raise Exception("The 'client_id' field on the Text (Privacy) node cannot be empty.")

        key = get_session_key(client_id)
        if not key:
            raise Exception(f"Could not find session key for client_id: {client_id}. Please refresh the page.")

        encrypted_data_bytes = base64.b64decode(encrypted_text)
        decrypted_bytes = xor_cipher(encrypted_data_bytes, key)
        decrypted_string = decrypted_bytes.decode('utf-8')
        return (decrypted_string,)

    @classmethod
    def IS_CHANGED(s, encrypted_text, client_id):
        return hashlib.sha256((encrypted_text + client_id).encode()).hexdigest()


class PreviewTextInRAM:
    @classmethod
    def INPUT_TYPES(s):
        return {"required": {
            "text": ("STRING", {"forceInput": True}),
            "client_id": ("STRING", {"multiline": False, "default": ""}),
        }}

    RETURN_TYPES = ()
    FUNCTION = "preview_text"
    OUTPUT_NODE = True
    CATEGORY = "text"

    def preview_text(self, text, client_id=None):
        if not client_id:
            raise Exception("The 'client_id' field on the Preview Text (Privacy) node cannot be empty.")

        if text is None or text == "":
            return {"ui": {"previews": []}}

        key = get_session_key(client_id)
        if not key:
            raise Exception(f"Could not find session key for client_id: {client_id}.")

        text_bytes = text.encode('utf-8')
        encrypted_text_bytes = xor_cipher(text_bytes, key)
        text_base64 = base64.b64encode(encrypted_text_bytes).decode('utf-8')

        results = [{"base64": text_base64, "type": "text"}]

        return {"ui": {"previews": results}}