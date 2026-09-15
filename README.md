# Epson EcoTank ID Template Converter

A simple Windows desktop app that converts an ID-card PDF (or a folder of PNG pages) into Epson Photo+ `.etdx` templates.

## Build the Windows app

1. On Windows, install Python 3.11 or newer from [python.org](https://www.python.org/downloads/windows/). Enable **Add Python to PATH**.
2. Double-click `build_windows.bat`.
3. Find the standalone app at `dist\Epson EcoTank ID Converter.exe`.

The `.exe` contains the Python dependencies and Epson base template. Poppler is not needed.

## Use it

1. Choose a PDF or folder containing PNG images.
2. Select landscape/portrait and front-and-back/front-only.
3. Choose an output folder and click **Convert**.

Front-and-back pages are ordered `front 1, back 1, front 2, back 2`; every four pages create one template. Front-only mode uses every two pages. An incomplete final set repeats its last card image(s).

## Run from source

```powershell
py -m pip install -r requirements.txt
py main.py
```
