from flask import Flask, request, send_from_directory, abort, url_for
from pathlib import Path
import sqlite3
import re
import os
import tempfile

BASE_DIR = Path(__file__).resolve().parent

# Automatically determine directory containing index.html
if (BASE_DIR / "index.html").is_file():
    SITE_DIR = BASE_DIR
elif (BASE_DIR.parent / "index.html").is_file():
    SITE_DIR = BASE_DIR.parent
elif (BASE_DIR / "website" / "index.html").is_file():
    SITE_DIR = BASE_DIR / "website"
else:
    SITE_DIR = BASE_DIR

# Determine writable database path for serverless (Vercel) and local environments
if os.environ.get("VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
    DB_PATH = Path(tempfile.gettempdir()) / "school_messages.db"
else:
    try:
        test_file = BASE_DIR / ".write_test"
        test_file.touch()
        test_file.unlink()
        DB_PATH = BASE_DIR / "school_messages.db"
    except (PermissionError, OSError):
        DB_PATH = Path(tempfile.gettempdir()) / "school_messages.db"

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 1 * 1024 * 1024  # 1 MB per form post


def get_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    try:
        with get_db() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                form_type TEXT NOT NULL CHECK(form_type IN ('contact','enquiry','feedback')),
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                phone TEXT DEFAULT '',
                student_class TEXT DEFAULT '',
                subject TEXT DEFAULT '',
                message TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )""")
    except Exception as exc:
        print(f"Database initialization notice: {exc}")


# Ensure DB is initialized before handling requests
@app.before_request
def ensure_db():
    if not getattr(app, "_db_initialized", False):
        init_db()
        app._db_initialized = True


@app.route("/", methods=["GET"])
def home():
    index_file = SITE_DIR / "index.html"
    if index_file.is_file():
        return send_from_directory(SITE_DIR, "index.html")
    abort(404, description=f"index.html not found in {SITE_DIR}")


@app.route("/health", methods=["GET"])
@app.route("/api/health", methods=["GET"])
def health():
    return {"status": "ok", "database": str(DB_PATH.name)}


@app.route("/submit/<form_type>", methods=["POST"])
@app.route("/api/submit/<form_type>", methods=["POST"])
def submit(form_type):
    if form_type not in ("contact", "enquiry", "feedback"):
        abort(404)

    # Spam trap: real visitors leave this hidden field blank.
    if request.form.get("website", "").strip():
        return thank_you(form_type)

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    phone = request.form.get("phone", "").strip()
    student_class = request.form.get("studentClass", "").strip()
    subject = request.form.get("subject", "").strip()
    message = request.form.get("message", "").strip()

    if not name or not email or not message:
        return error_page("Please fill in your name, email and message.", form_type), 400
    if len(name) > 120 or len(email) > 254 or len(phone) > 40 or len(student_class) > 120 or len(subject) > 200 or len(message) > 10000:
        return error_page("One or more fields are too long. Please go back and shorten them.", form_type), 400
    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
        return error_page("Please enter a valid email address.", form_type), 400

    with get_db() as db:
        db.execute("""INSERT INTO messages
            (form_type, name, email, phone, student_class, subject, message)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (form_type, name, email, phone, student_class, subject, message))

    return thank_you(form_type)


def page(title, message, form_type, is_error=False):
    back = "/contact.html" if form_type == "contact" else "/enquiry-and-feedback.html"
    color = "#b42318" if is_error else "#087b45"
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title><style>
body{{font-family:Arial,sans-serif;background:#f4f6f8;margin:0;min-height:100vh;display:grid;place-items:center;color:#222}}
main{{background:white;padding:32px;border-radius:12px;max-width:520px;margin:20px;text-align:center;box-shadow:0 4px 22px #0001}}
h1{{color:{color}}}a{{display:inline-block;margin:8px;padding:12px 18px;background:#087b45;color:white;text-decoration:none;border-radius:6px}}
a.secondary{{background:#555}}
</style></head><body><main><h1>{title}</h1><p>{message}</p>
<a href="/">Home</a><a class="secondary" href="{back}">Back to form</a></main></body></html>'''


def thank_you(form_type):
    label = {"contact": "contact message", "enquiry": "enquiry", "feedback": "feedback"}[form_type]
    return page("Thank you!", f"Your {label} has been received and saved successfully.", form_type)


def error_page(message, form_type):
    return page("Please check your form", message, form_type, True)


@app.route("/<path:filename>", methods=["GET"])
def website_files(filename):
    # Support clean URLs: if requested filename without .html exists with .html, serve it
    target = (SITE_DIR / filename).resolve()
    if not target.is_file() and not filename.endswith(".html"):
        alt_target = (SITE_DIR / f"{filename}.html").resolve()
        if alt_target.is_file():
            target = alt_target
            filename = f"{filename}.html"

    if not target.is_relative_to(SITE_DIR.resolve()) or not target.is_file():
        abort(404)
    return send_from_directory(SITE_DIR, filename)


class VercelPathMiddleware:
    """Ensures WSGI PATH_INFO reflects rewritten paths if Vercel headers are present."""
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        matched_path = environ.get("HTTP_X_MATCHED_PATH") or environ.get("HTTP_X_VERCEL_MATCHED_PATH")
        if matched_path and not matched_path.startswith("/api/"):
            environ["PATH_INFO"] = matched_path
        return self.wsgi_app(environ, start_response)


app.wsgi_app = VercelPathMiddleware(app.wsgi_app)

# Initialize the database table on startup
init_db()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
