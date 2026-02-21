from __future__ import annotations

# NOTE: Copied/adapted from archviz_desktop_tool (our reference implementation).

import json
from dataclasses import dataclass
from typing import Any

import requests


@dataclass
class GeminiResponse:
    images_b64: list[str]
    raw: dict[str, Any]


class GeminiClient:
    """Gemini wrapper.

    Supports two backends:
    1) **google-genai SDK** (recommended for image-capable models)
    2) **REST** fallback (best-effort)
    """

    def __init__(self, *, api_key: str, endpoint: str | None = None, timeout_s: int = 180):
        self.api_key = api_key
        self.endpoint = endpoint or "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        self.timeout_s = timeout_s

    def list_models_rest(self) -> dict[str, Any]:
        url = "https://generativelanguage.googleapis.com/v1beta/models"
        r = requests.get(url, params={"key": self.api_key}, timeout=self.timeout_s)
        r.raise_for_status()
        return r.json()

    def generate_image(
        self,
        *,
        model: str,
        prompt: str,
        inline_files: list[dict[str, str]] | None = None,
        fallback_imagen_model: str | None = "imagen-4.0-generate-001",
    ) -> GeminiResponse:
        try:
            resp = self._generate_image_sdk(model=model, prompt=prompt, inline_files=inline_files)
            if resp.images_b64 or not fallback_imagen_model:
                return resp
            return self._generate_image_imagen_sdk(model=fallback_imagen_model, prompt=prompt)
        except ModuleNotFoundError:
            return self._generate_image_rest(model=model, prompt=prompt, inline_files=inline_files)

    def _generate_image_sdk(
        self,
        *,
        model: str,
        prompt: str,
        inline_files: list[dict[str, str]] | None = None,
    ) -> GeminiResponse:
        from google import genai  # type: ignore

        client = genai.Client(api_key=self.api_key)

        contents: list[Any] = [prompt]

        for f in inline_files or []:
            mime = f.get("mime_type", "")
            b = _b64decode(f["data_b64"])
            if isinstance(mime, str) and mime.startswith("image/"):
                try:
                    from PIL import Image  # type: ignore
                    from io import BytesIO

                    contents.append(Image.open(BytesIO(b)))
                    continue
                except Exception:
                    pass
            try:
                from google.genai import types  # type: ignore

                contents.append(types.Part.from_bytes(data=b, mime_type=mime))
            except Exception:
                return self._generate_image_rest(model=model, prompt=prompt, inline_files=inline_files)

        model_sdk = model if model.startswith("models/") else f"models/{model}"
        try:
            from google.genai import types  # type: ignore

            cfg = types.GenerateContentConfig(response_modalities=["IMAGE", "TEXT"])
            resp = client.models.generate_content(model=model_sdk, contents=contents, config=cfg)
        except Exception:
            resp = client.models.generate_content(model=model_sdk, contents=contents)

        images_b64: list[str] = []
        try:
            for cand in getattr(resp, "candidates", []) or []:
                content = getattr(cand, "content", None)
                parts = getattr(content, "parts", []) if content is not None else []
                for part in parts or []:
                    inline = getattr(part, "inline_data", None)
                    if inline is None:
                        continue
                    data_bytes = getattr(inline, "data", None)
                    if data_bytes:
                        import base64

                        images_b64.append(base64.b64encode(data_bytes).decode("utf-8"))
        except Exception:
            pass

        raw = _to_raw_dict(resp)
        if not images_b64:
            images_b64 = _extract_images_b64(raw)
        return GeminiResponse(images_b64=images_b64, raw=raw)

    def _generate_image_imagen_sdk(self, *, model: str, prompt: str) -> GeminiResponse:
        from google import genai  # type: ignore
        from google.genai import types  # type: ignore

        client = genai.Client(api_key=self.api_key)
        model_sdk = model if model.startswith("models/") else f"models/{model}"

        cfg = types.GenerateImagesConfig(number_of_images=1)
        resp = client.models.generate_images(model=model_sdk, prompt=prompt, config=cfg)

        raw = _to_raw_dict(resp)
        images_b64 = _extract_images_b64(raw)
        return GeminiResponse(images_b64=images_b64, raw=raw)

    def _generate_image_rest(
        self,
        *,
        model: str,
        prompt: str,
        inline_files: list[dict[str, str]] | None = None,
    ) -> GeminiResponse:
        url = self.endpoint.format(model=model)
        headers = {"Content-Type": "application/json"}
        params = {"key": self.api_key}

        parts: list[dict[str, Any]] = [{"text": prompt}]
        for f in inline_files or []:
            parts.append({"inline_data": {"mime_type": f["mime_type"], "data": f["data_b64"]}})

        payload = {"contents": [{"parts": parts}]}

        r = requests.post(url, headers=headers, params=params, data=json.dumps(payload), timeout=self.timeout_s)
        if r.status_code == 404:
            raise RuntimeError(
                "Gemini returned 404 (model not found or endpoint not supported). "
                "Fix by choosing a model name that exists for your API key."
            )
        r.raise_for_status()
        data = r.json()

        images = _extract_images_b64(data)
        return GeminiResponse(images_b64=images, raw=data)


def _extract_images_b64(data: Any) -> list[str]:
    images: list[str] = []

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            inline = node.get("inline_data") or node.get("inlineData")
            if isinstance(inline, dict):
                mime = inline.get("mime_type") or inline.get("mimeType") or ""
                b64 = inline.get("data")
                if isinstance(mime, str) and mime.startswith("image/") and isinstance(b64, str) and b64:
                    images.append(b64)

            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for it in node:
                walk(it)

    walk(data)
    return images


def _to_raw_dict(resp: Any) -> dict[str, Any]:
    if hasattr(resp, "model_dump"):
        return resp.model_dump()
    if hasattr(resp, "to_dict"):
        return resp.to_dict()
    try:
        return json.loads(json.dumps(resp, default=str))
    except Exception:
        return {"repr": repr(resp)}


def _b64decode(s: str) -> bytes:
    import base64

    return base64.b64decode(s)
