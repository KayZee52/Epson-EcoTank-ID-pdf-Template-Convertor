"""Windows desktop interface for the Epson EcoTank ID template converter."""

from __future__ import annotations

import os
import queue
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from converter import ConversionOptions, convert


def open_folder(path: Path) -> None:
    if sys.platform == "win32":
        os.startfile(path)  # type: ignore[attr-defined]
    elif sys.platform == "darwin":
        subprocess.Popen(["open", str(path)])
    else:
        subprocess.Popen(["xdg-open", str(path)])


class ConverterApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Epson EcoTank ID Template Converter")
        self.geometry("680x540")
        self.minsize(640, 520)
        self.source_type = tk.StringVar(value="pdf")
        self.source = tk.StringVar()
        self.destination = tk.StringVar()
        self.orientation = tk.StringVar(value="landscape")
        self.front_only = tk.BooleanVar(value=False)
        self.make_etdx = tk.BooleanVar(value=True)
        self.status = tk.StringVar(value="Ready")
        self.events: queue.Queue[tuple[str, object]] = queue.Queue()
        self._build_ui()
        self.after(100, self._process_events)

    def _build_ui(self) -> None:
        style = ttk.Style(self)
        if "vista" in style.theme_names():
            style.theme_use("vista")
        root = ttk.Frame(self, padding=24)
        root.pack(fill="both", expand=True)
        root.columnconfigure(0, weight=1)
        ttk.Label(root, text="Epson EcoTank ID Converter", font=("Segoe UI", 20, "bold")).grid(row=0, column=0, sticky="w")
        ttk.Label(root, text="Turn ID-card PDFs or PNG pages into Epson Photo+ .etdx templates.").grid(row=1, column=0, sticky="w", pady=(4, 20))

        source_box = ttk.LabelFrame(root, text="1. Choose source", padding=12)
        source_box.grid(row=2, column=0, sticky="ew")
        source_box.columnconfigure(0, weight=1)
        modes = ttk.Frame(source_box)
        modes.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))
        ttk.Radiobutton(modes, text="PDF file", variable=self.source_type, value="pdf", command=self._source_changed).pack(side="left")
        ttk.Radiobutton(modes, text="Folder of PNG images", variable=self.source_type, value="images", command=self._source_changed).pack(side="left", padx=16)
        ttk.Entry(source_box, textvariable=self.source).grid(row=1, column=0, sticky="ew", padx=(0, 8))
        ttk.Button(source_box, text="Browse…", command=self._browse_source).grid(row=1, column=1)

        options = ttk.LabelFrame(root, text="2. Options", padding=12)
        options.grid(row=3, column=0, sticky="ew", pady=12)
        ttk.Label(options, text="Card orientation:").grid(row=0, column=0, sticky="w")
        ttk.Radiobutton(options, text="Landscape (86 × 54 mm)", variable=self.orientation, value="landscape").grid(row=0, column=1, sticky="w", padx=12)
        ttk.Radiobutton(options, text="Portrait (54 × 86 mm)", variable=self.orientation, value="portrait").grid(row=0, column=2, sticky="w")
        ttk.Checkbutton(options, text="Front side only", variable=self.front_only).grid(row=1, column=1, sticky="w", padx=12, pady=(10, 0))
        self.etdx_check = ttk.Checkbutton(options, text="Create Epson Photo+ templates (.etdx)", variable=self.make_etdx)
        self.etdx_check.grid(row=1, column=2, sticky="w", pady=(10, 0))

        output = ttk.LabelFrame(root, text="3. Output folder", padding=12)
        output.grid(row=4, column=0, sticky="ew")
        output.columnconfigure(0, weight=1)
        ttk.Entry(output, textvariable=self.destination).grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ttk.Button(output, text="Browse…", command=self._browse_output).grid(row=0, column=1)
        actions = ttk.Frame(root)
        actions.grid(row=5, column=0, sticky="ew", pady=(18, 8))
        actions.columnconfigure(0, weight=1)
        self.convert_button = ttk.Button(actions, text="Convert", command=self._start)
        self.convert_button.grid(row=0, column=0, sticky="ew")
        self.open_button = ttk.Button(actions, text="Open output", command=self._open_output, state="disabled")
        self.open_button.grid(row=0, column=1, padx=(8, 0))
        self.progress = ttk.Progressbar(root, mode="determinate", maximum=100)
        self.progress.grid(row=6, column=0, sticky="ew", pady=(8, 4))
        ttk.Label(root, textvariable=self.status).grid(row=7, column=0, sticky="w")

    def _source_changed(self) -> None:
        if self.source_type.get() == "images":
            self.make_etdx.set(True)
            self.etdx_check.state(["disabled"])
        else:
            self.etdx_check.state(["!disabled"])
        self.source.set("")

    def _browse_source(self) -> None:
        if self.source_type.get() == "pdf":
            selected = filedialog.askopenfilename(title="Select ID-card PDF", filetypes=[("PDF files", "*.pdf")])
        else:
            selected = filedialog.askdirectory(title="Select folder containing PNG images")
        if selected:
            self.source.set(selected)
            if not self.destination.get():
                path = Path(selected)
                self.destination.set(str(path.parent if path.is_file() else path / "converted"))

    def _browse_output(self) -> None:
        selected = filedialog.askdirectory(title="Select output folder")
        if selected:
            self.destination.set(selected)

    def _start(self) -> None:
        source = Path(self.source.get().strip())
        destination_text = self.destination.get().strip()
        if not source.exists():
            messagebox.showerror("Source not found", "Please choose a valid PDF file or image folder.")
            return
        if not destination_text:
            messagebox.showerror("Output required", "Please choose an output folder.")
            return
        options = ConversionOptions(source, Path(destination_text), self.source_type.get(), self.orientation.get() == "portrait", self.front_only.get(), self.make_etdx.get())
        self.convert_button.state(["disabled"])
        self.open_button.state(["disabled"])
        self.progress["value"] = 0
        self.status.set("Starting…")
        threading.Thread(target=self._worker, args=(options,), daemon=True).start()

    def _worker(self, options: ConversionOptions) -> None:
        try:
            result = convert(options, lambda value, text: self.events.put(("progress", (value, text))))
            self.events.put(("done", result))
        except Exception as exc:
            self.events.put(("error", str(exc)))

    def _process_events(self) -> None:
        try:
            while True:
                event, payload = self.events.get_nowait()
                if event == "progress":
                    value, status_text = payload  # type: ignore[misc]
                    self.progress["value"] = value
                    self.status.set(status_text)
                elif event == "done":
                    self.convert_button.state(["!disabled"])
                    self.open_button.state(["!disabled"])
                    self.progress["value"] = 100
                    self.status.set("Conversion complete")
                    result = payload
                    messagebox.showinfo("Finished", f"Created {result.image_count} image(s) and {len(result.etdx_files)} template(s).")
                elif event == "error":
                    self.convert_button.state(["!disabled"])
                    self.progress["value"] = 0
                    self.status.set("Conversion failed")
                    messagebox.showerror("Conversion failed", str(payload))
        except queue.Empty:
            pass
        self.after(100, self._process_events)

    def _open_output(self) -> None:
        path = Path(self.destination.get())
        if path.exists():
            open_folder(path)


if __name__ == "__main__":
    ConverterApp().mainloop()
