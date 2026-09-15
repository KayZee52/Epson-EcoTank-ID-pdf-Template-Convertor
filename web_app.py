"""Browser interface for sharing the converter on a trusted local network."""
from __future__ import annotations

import io
import tempfile
import zipfile
from pathlib import Path

from flask import Flask, render_template_string, request, send_file
from werkzeug.utils import secure_filename

from converter import ConversionOptions, convert

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 200 * 1024 * 1024

PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Epson EcoTank ID Converter</title>
<style>
*{box-sizing:border-box}body{margin:0;background:#f3f6fa;color:#172033;font:16px system-ui,-apple-system,"Segoe UI",sans-serif}
main{max-width:700px;margin:48px auto;padding:28px;background:#fff;border-radius:16px;box-shadow:0 8px 30px #18315318}
h1{margin:0 0 6px;font-size:28px}.sub{color:#637087;margin:0 0 26px}fieldset{border:1px solid #d9e0e9;border-radius:10px;margin:0 0 18px;padding:16px}
legend{font-weight:650;padding:0 7px}label{display:block;margin:9px 0}.inline{display:inline-block;margin-right:22px}
input[type=file]{display:block;width:100%;padding:12px;border:1px dashed #9ba9bb;border-radius:8px;background:#f8fafc}
button{width:100%;border:0;border-radius:9px;background:#1261d7;color:#fff;padding:13px;font-weight:700;font-size:16px;cursor:pointer}
.hint{font-size:13px;color:#68758a;margin-top:16px}.error{background:#fff0f0;color:#a11919;padding:12px;border-radius:8px;margin-bottom:16px}
</style></head><body><main>
<h1>Epson EcoTank ID Converter</h1><p class="sub">Upload card pages and download Epson Photo+ templates.</p>
{% if error %}<div class="error">{{ error }}</div>{% endif %}
<form method="post" enctype="multipart/form-data">
<fieldset><legend>Source</legend>
<label class="inline"><input type="radio" name="source_type" value="pdf" checked onchange="pick.accept='.pdf';pick.multiple=false"> PDF file</label>
<label class="inline"><input type="radio" name="source_type" value="images" onchange="pick.accept='.png';pick.multiple=true"> PNG images</label>
<input id="pick" type="file" name="files" accept=".pdf" required>
</fieldset>
<fieldset><legend>Options</legend>
<label class="inline"><input type="radio" name="orientation" value="landscape" checked> Landscape</label>
<label class="inline"><input type="radio" name="orientation" value="portrait"> Portrait</label>
<label><input type="checkbox" name="front_only"> Front side only</label>
</fieldset>
<button type="submit">Convert and download</button>
</form><p class="hint">Front/back order: front 1, back 1, front 2, back 2. Maximum upload: 200 MB.</p>
</main></body></html>"""


@app.get("/")
def index():
    return render_template_string(PAGE, error=None)


@app.post("/")
def upload():
    source_type = request.form.get("source_type", "pdf")
    uploads = [item for item in request.files.getlist("files") if item.filename]
    if not uploads:
        return render_template_string(PAGE, error="Choose a PDF or one or more PNG files."), 400
    if source_type == "pdf" and (len(uploads) != 1 or not uploads[0].filename.lower().endswith(".pdf")):
        return render_template_string(PAGE, error="PDF mode accepts one .pdf file."), 400
    if source_type == "images" and any(not item.filename.lower().endswith(".png") for item in uploads):
        return render_template_string(PAGE, error="Image mode accepts PNG files only."), 400

    try:
        with tempfile.TemporaryDirectory(prefix="epson-web-") as temporary:
            root = Path(temporary)
            incoming, output = root / "uploads", root / "output"
            incoming.mkdir()
            saved: list[Path] = []
            for number, item in enumerate(uploads, 1):
                name = secure_filename(item.filename) or f"upload_{number}.png"
                path = incoming / name
                item.save(path)
                saved.append(path)
            source = saved[0] if source_type == "pdf" else incoming
            result = convert(ConversionOptions(
                source=source,
                destination=output,
                source_type=source_type,
                portrait=request.form.get("orientation") == "portrait",
                front_only="front_only" in request.form,
                make_etdx=True,
            ))
            archive_data = io.BytesIO()
            with zipfile.ZipFile(archive_data, "w", zipfile.ZIP_DEFLATED) as archive:
                for path in result.etdx_files:
                    archive.write(path, path.name)
                if source_type == "pdf":
                    for path in result.image_files:
                        archive.write(path, f"images/{path.name}")
            archive_data.seek(0)
        return send_file(archive_data, mimetype="application/zip", as_attachment=True, download_name="epson-templates.zip")
    except Exception as error:
        return render_template_string(PAGE, error=str(error)), 400


@app.errorhandler(413)
def too_large(_error):
    return render_template_string(PAGE, error="Upload is larger than the 200 MB limit."), 413


def run_server(host: str = "0.0.0.0", port: int = 8080) -> None:
    from waitress import serve
    serve(app, host=host, port=port, threads=4)
