"""Generate Epson Photo+ 4.x ID-card template packages."""
from __future__ import annotations

import json
import os
import secrets
import shutil
import string
import tempfile
import zipfile
from copy import deepcopy
from pathlib import Path
from typing import List

from PIL import Image


PROJECT_INFO = {
    "appVersion": "4.0.4.0",
    "editInfo": {"pageEditInfo": {"canAddPage": True, "canCopyPage": True, "canRemovePage": True}},
    "formatInfo": {"saveFormat": 0},
}

PAPER = {
    "paperSizeId": "IC",
    "size": [764, 1218],
    "orientation": 0,
    "topleft": [0, 0],
    "defaultAddTextFontSize": 15.0,
    "backgroundData": {
        "backgroundImage": "",
        "backgroundPattern": {
            "type": "C", "size": "S", "patternColor": [255, 255, 255, 255],
            "patternName": "", "layout": "T", "angle": 0.0, "scale": 1.0, "density": 50,
        },
    },
    "vergeData": {
        "borderType": "BL", "isEquablePhotoSize": True,
        "defaultWidth": 42, "maxWidth": 162, "width": 42,
    },
    "workData": {"maxWorkSpaceCount": 2, "enableWorkSpaces": [1, 2]},
    "imageFrames": [],
    "cliparts": [],
    "messages": [],
}


def _frame(index: int) -> dict:
    return {
        "topleft": [-10.0, -10.0], "size": [784, 1238], "index": index,
        "imagePositionXIndexList": [index], "imagePositionYIndexList": [index],
        "workSpaceNumber": index,
    }


def _master_template() -> dict:
    paper = deepcopy(PAPER)
    paper["imageFrames"] = [{
        "topleft": [-10, -10], "size": [784, 1238],
        "defaultTopleft": [-10, -10], "defaultSize": [784, 1238],
        "imagePositionXIndexList": [], "imagePositionYIndexList": [],
        "angle": 0.0, "fitting": "fit", "index": 1, "workSpaceNumber": 1,
    }]
    return {
        "id": "IC_002", "version": 3, "thumbnail": "IC_002.png",
        "update": True, "function": "IC", "borderType": 0,
        "paperSizeList": [paper],
    }


def _token(length: int = 10) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


class ETDXGenerator:
    """Build Photo+ 4.x packages matching templates created on Windows."""

    def __init__(self, base_template_dir: str | None = None):
        # Kept for compatibility with existing callers. Photo+ 4.x metadata is
        # generated here so stale template files cannot reintroduce old layouts.
        self.base_template_dir = Path(base_template_dir) if base_template_dir else None

    @staticmethod
    def _photo(image_path: str, filename: str, frame_index: int) -> dict:
        with Image.open(image_path) as image:
            width, height = image.size
        landscape = width >= height
        angle = 90.0 if landscape else 0.0
        placed_width, placed_height = (height, width) if landscape else (width, height)
        scale = max(784 / placed_width, 1238 / placed_height)
        return {
            "imagepath": filename.replace("/", "\\"),
            "originalsize": [width, height],
            "center": [0.0, 0.0],
            "angle": angle,
            "scale": scale,
            "crop": {},
            "effectInfo": {},
            "apfInfo": {"mode": "standard", "level": 5},
            "frameIndex": frame_index,
            "workSpaceNumber": frame_index,
            "zindex": 100,
        }

    def _page_info(self, images: List[str], relative_names: List[str]) -> dict:
        paper = deepcopy(PAPER)
        paper["imageFrames"] = [_frame(1), _frame(2)]
        paper["photos"] = [
            self._photo(images[0], relative_names[0], 1),
            self._photo(images[1], relative_names[1], 2),
        ]
        stored_paper = deepcopy(PAPER)
        stored_paper["imageFrames"] = [_frame(1), _frame(2)]
        for frame in stored_paper["imageFrames"]:
            frame["imagePositionXIndexList"] = []
            frame["imagePositionYIndexList"] = []
        return {
            "version": 3, "id": "IC_002", "thumbnail": "IC_002.png",
            "update": True, "function": "IC", "editedPaperSize": paper,
            "paperSizeList": [stored_paper],
        }

    def generate_etdx(self, images: List[str], output_path: str,
                      template_name: str = "template", front_only: bool = False) -> str:
        expected = 2 if front_only else 4
        if len(images) != expected:
            raise ValueError(f"Expected {expected} images, got {len(images)}")
        output_dir = Path(output_path)
        output_dir.mkdir(parents=True, exist_ok=True)

        page_groups = [images] if front_only else [images[0::2], images[1::2]]
        with tempfile.TemporaryDirectory(prefix="epson-etdx-", dir=output_dir) as temporary:
            root = Path(temporary)
            (root / "MasterTemplate").mkdir()
            (root / "projectInfo.json").write_text(json.dumps(PROJECT_INFO), encoding="utf-8")
            (root / "MasterTemplate" / "_info.json").write_text(
                json.dumps(_master_template()), encoding="utf-8"
            )
            page_ids: list[str] = []
            for group in page_groups:
                page_id = _token()
                page_ids.append(page_id)
                page_dir = root / page_id
                page_dir.mkdir()
                relative_names: list[str] = []
                for source in group:
                    image_id = _token()
                    image_dir = page_dir / image_id
                    image_dir.mkdir()
                    safe_name = Path(source).name
                    shutil.copy2(source, image_dir / safe_name)
                    relative_names.append(f"{image_id}\\{safe_name}")
                info = self._page_info(group, relative_names)
                (page_dir / "_info.json").write_text(json.dumps(info), encoding="utf-8")
            (root / "page.json").write_text(json.dumps(page_ids), encoding="utf-8")

            target = output_dir / f"{template_name}.etdx"
            with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
                for current_root, _directories, files in os.walk(root):
                    for filename in files:
                        path = Path(current_root) / filename
                        archive.write(path, path.relative_to(root))
            return str(target)

    def batch_generate(self, pdf_images: List[str], output_dir: str,
                       base_name: str = "template", front_only: bool = False) -> List[str]:
        group_size = 2 if front_only else 4
        if len(pdf_images) % group_size:
            raise ValueError(f"Expected multiple of {group_size} images, got {len(pdf_images)}")
        return [
            self.generate_etdx(
                pdf_images[index:index + group_size], output_dir,
                f"{base_name}{index // group_size + 1}", front_only,
            )
            for index in range(0, len(pdf_images), group_size)
        ]
