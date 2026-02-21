from __future__ import annotations

from pathlib import Path


def mime_from_path(path: Path) -> str:
    ext = path.suffix.lower().lstrip(".")
    if ext in {"png"}:
        return "image/png"
    if ext in {"jpg", "jpeg"}:
        return "image/jpeg"
    if ext in {"webp"}:
        return "image/webp"
    if ext in {"gif"}:
        return "image/gif"
    if ext in {"pdf"}:
        return "application/pdf"
    # blueprints often come as DWG/DXF, but Gemini inline_data supports only some types;
    # keep as octet-stream to at least send bytes.
    return "application/octet-stream"
