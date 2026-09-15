"""Conversion logic shared by the desktop UI and automated tests."""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from PIL import Image
from etdx_generator import ETDXGenerator

Progress = Callable[[int, str], None]


@dataclass(frozen=True)
class ConversionOptions:
    source: Path
    destination: Path
    source_type: str = "pdf"
    portrait: bool = False
    front_only: bool = False
    make_etdx: bool = True


@dataclass(frozen=True)
class ConversionResult:
    image_count: int
    image_files: list[Path]
    etdx_files: list[Path]


def resource_path(name: str) -> Path:
    root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return root / name


def natural_key(path: Path) -> list[object]:
    return [int(part) if part.isdigit() else part.lower() for part in re.split(r"(\d+)", path.name)]


def _pdf_to_png(source: Path, destination: Path, portrait: bool, progress: Progress) -> list[Path]:
    try:
        import pymupdf as fitz
    except ImportError as exc:
        raise RuntimeError("PDF support is missing. Reinstall the app or run: pip install PyMuPDF") from exc
    document = fitz.open(source)
    if document.page_count == 0:
        document.close()
        raise ValueError("The selected PDF contains no pages.")
    files: list[Path] = []
    try:
        matrix = fitz.Matrix(300 / 72, 300 / 72)
        for index, page in enumerate(document):
            progress(5 + round(55 * index / document.page_count), f"Rendering page {index + 1} of {document.page_count}…")
            pixmap = page.get_pixmap(matrix=matrix, alpha=False)
            output = destination / f"{source.stem}_page_{index + 1}.png"
            pixmap.save(output)
            if portrait:
                with Image.open(output) as image:
                    image.rotate(90, expand=True).save(output, "PNG")
            files.append(output)
    finally:
        document.close()
    return files


def _prepare_images(source: Path, destination: Path, portrait: bool, progress: Progress) -> list[Path]:
    files = sorted((p for p in source.iterdir() if p.is_file() and p.suffix.lower() == ".png"), key=natural_key)
    if not files:
        raise ValueError("No PNG images were found in the selected folder.")
    if not portrait:
        return files
    rotated_dir = destination / "rotated_images"
    rotated_dir.mkdir(exist_ok=True)
    rotated: list[Path] = []
    for index, path in enumerate(files):
        progress(5 + round(55 * index / len(files)), f"Rotating image {index + 1} of {len(files)}…")
        output = rotated_dir / path.name
        with Image.open(path) as image:
            image.rotate(90, expand=True).save(output, "PNG")
        rotated.append(output)
    return rotated


def _pad_images(files: list[Path], group_size: int) -> list[Path]:
    padded = files.copy()
    missing = (-len(padded)) % group_size
    minimum = 1 if group_size == 2 else 2
    if missing and len(padded) < minimum:
        raise ValueError(f"At least {minimum} image(s) are required for this template type.")
    repeat = padded[-1:] if group_size == 2 else padded[-2:]
    for index in range(missing):
        padded.append(repeat[index % len(repeat)])
    return padded


def convert(options: ConversionOptions, progress: Progress | None = None) -> ConversionResult:
    report = progress or (lambda _value, _text: None)
    if options.source_type not in {"pdf", "images"}:
        raise ValueError("Source type must be 'pdf' or 'images'.")
    if options.source_type == "pdf" and (not options.source.is_file() or options.source.suffix.lower() != ".pdf"):
        raise ValueError("Please select a valid PDF file.")
    if options.source_type == "images" and not options.source.is_dir():
        raise ValueError("Please select a valid image folder.")
    options.destination.mkdir(parents=True, exist_ok=True)
    if options.source_type == "pdf":
        images = _pdf_to_png(options.source, options.destination, options.portrait, report)
        base_name = options.source.stem
    else:
        images = _prepare_images(options.source, options.destination, options.portrait, report)
        base_name = options.source.name or "template"
    etdx_files: list[Path] = []
    if options.make_etdx:
        report(65, "Building Epson Photo+ templates…")
        grouped = _pad_images(images, 2 if options.front_only else 4)
        generator = ETDXGenerator(str(resource_path("template_base")))
        generated = generator.batch_generate([str(p) for p in grouped], str(options.destination), base_name, options.front_only)
        etdx_files = [Path(path) for path in generated]
    report(100, "Conversion complete")
    return ConversionResult(len(images), images, etdx_files)


if __name__ == "__main__":
    import argparse
    import socket

    parser = argparse.ArgumentParser(description="Epson EcoTank ID converter")
    parser.add_argument("--serve", action="store_true", help="share the converter through a web browser")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8080)
    arguments = parser.parse_args()
    if not arguments.serve:
        parser.error("use --serve to start the network interface")
    from web_app import run_server

    try:
        address = socket.gethostbyname(socket.gethostname())
    except OSError:
        address = "this-computer's-IP"
    print(f"Epson converter is available at http://{address}:{arguments.port}")
    print("Press Ctrl+C to stop it.")
    run_server(arguments.host, arguments.port)
