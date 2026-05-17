import os
from pathlib import Path

from flask import Flask, render_template, request, send_file

from main import generate_reflective_journal


app = Flask(__name__)


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/generate")
def generate():
    if not request.form.get("topic", "").strip():
        return render_template(
            "index.html",
            error="Topic is required to generate the journal.",
            form_data=request.form,
        ), 400

    try:
        output_path = generate_reflective_journal(
            {
                "student_name": request.form.get("student_name", "").strip(),
                "course_name": request.form.get("course_name", "").strip(),
                "instructor": request.form.get("instructor", "").strip(),
                "assessment": request.form.get("assessment", "").strip(),
                "date": request.form.get("date", "").strip(),
                "topic": request.form.get("topic", "").strip(),
                "document_name": request.form.get("document_name", "").strip(),
            }
        )
    except Exception as exc:
        return render_template(
            "index.html",
            error=str(exc),
            form_data=request.form,
        ), 500

    download_name = Path(output_path).name
    return send_file(output_path, as_attachment=True, download_name=download_name)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    debug_mode = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug_mode)