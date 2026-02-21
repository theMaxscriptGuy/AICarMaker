from __future__ import annotations

import base64
import datetime as dt
from dataclasses import dataclass
from pathlib import Path

from aicarmaker_app.services.gemini_client import GeminiClient
from aicarmaker_app.utils.file_utils import mime_from_path


@dataclass
class CameraAngle:
    name: str
    description: str


class RenderService:
    def __init__(self, *, gemini: GeminiClient, output_dir: Path):
        self.gemini = gemini
        self.output_dir = output_dir

    def generate_renders(
        self,
        *,
        project_name: str,
        model_name: str,
        car_prompt: str,
        blueprint_files: list[Path],
        camera_angles: list[CameraAngle],
    ) -> Path:
        ts = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        out = self.output_dir / f"{project_name or 'Project'}" / ts
        out.mkdir(parents=True, exist_ok=True)

        inline_files = [_inline_file_dict(p) for p in blueprint_files]

        for idx, angle in enumerate(camera_angles, start=1):
            prompt = _build_prompt(car_prompt=car_prompt, angle=angle)
            resp = self.gemini.generate_image(model=model_name, prompt=prompt, inline_files=inline_files)
            if not resp.images_b64:
                _write_debug(resp.raw, out, f"debug_{idx:03d}_{_safe(angle.name)}.json")
                continue

            # Write first image as PNG (common); Gemini may return other formats but b64 is opaque.
            img_path = out / f"{idx:03d}_{_safe(angle.name)}.png"
            img_path.write_bytes(base64.b64decode(resp.images_b64[0]))

        return out


def _build_prompt(*, car_prompt: str, angle: CameraAngle) -> str:
    return (
        "You are a product visualization renderer.\n"
        "Generate a photorealistic render of a car based on the provided blueprint/reference files.\n\n"
        f"Car description (user prompt):\n{car_prompt.strip()}\n\n"
        f"Camera angle name: {angle.name}\n"
        f"Camera angle description: {angle.description}\n\n"
        "Output: a single high-quality image render."
    )


def _inline_file_dict(p: Path) -> dict[str, str]:
    b = p.read_bytes()
    return {
        "mime_type": mime_from_path(p),
        "data_b64": base64.b64encode(b).decode("utf-8"),
    }


def _write_debug(data: dict, out_dir: Path, filename: str) -> None:
    import json

    p = out_dir / filename
    p.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _safe(name: str) -> str:
    s = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in (name or "angle"))
    return s[:60] if len(s) > 60 else s
