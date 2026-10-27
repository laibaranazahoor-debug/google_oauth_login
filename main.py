import os
import re
import logging
from pathlib import Path
from authlib.integrations.starlette_client import OAuth
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from pwdlib import PasswordHash

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("google_oauth")

# Environment Setup
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.getenv("SECRET_KEY")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv(
    "GOOGLE_REDIRECT_URI",
    "http://127.0.0.1:8000/auth/google/callback",
)

if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY is missing from .env")
if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
    raise RuntimeError("GOOGLE_CLIENT_ID or GOOGLE_CLIENT_SECRET is missing from .env")

app = FastAPI(title="Google OAuth Login System")

app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    session_cookie="login_session",
    max_age=3600,
    same_site="lax",
    https_only=os.getenv("COOKIE_SECURE", "false").lower() == "true",
)

# Static and Uploads mounting
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
password_hasher = PasswordHash.recommended()

users = {}

oauth = OAuth()
oauth.register(
    name="google",
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)

def valid_email(email: str) -> bool:
    pattern = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
    return bool(re.fullmatch(pattern, email))

def current_user(request: Request):
    email = request.session.get("user_email")
    if not email:
        return None
    return users.get(email)

def render(request: Request, page: str, **context):
    return templates.TemplateResponse(
        request=request,
        name=page,
        context=context,
    )

@app.get("/")
async def home(request: Request):
    destination = "/dashboard" if current_user(request) else "/login"
    return RedirectResponse(destination, status_code=303)

@app.get("/register")
async def register_page(request: Request):
    if current_user(request):
        return RedirectResponse("/dashboard", status_code=303)
    return render(request, "register.html", error=None)

@app.post("/register")
async def register(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
):
    name = name.strip()
    email = email.strip().lower()
    if not name or len(name) > 80:
        return render(request, "register.html", error="Name must contain 1 to 80 characters.")
    if len(email) > 254 or not valid_email(email):
        return render(request, "register.html", error="Please enter a valid email address.")
    if email in users:
        return render(request, "register.html", error="An account with this email already exists.")
    if not 8 <= len(password) <= 128:
        return render(request, "register.html", error="Password must be between 8 and 128 characters.")
    if password != confirm_password:
        return render(request, "register.html", error="Passwords do not match.")

    users[email] = {
        "name": name,
        "email": email,
        "password_hash": password_hasher.hash(password),
        "google_id": None,
        "picture": None,
    }
    return RedirectResponse("/login?registered=1", status_code=303)

@app.get("/login")
async def login_page(request: Request, registered: int = 0):
    if current_user(request):
        return RedirectResponse("/dashboard", status_code=303)
    message = "Registration successful! Please log in." if registered == 1 else None
    return render(request, "login.html", error=None, message=message)

@app.post("/login")
async def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
):
    email = email.strip().lower()
    user = users.get(email)
    if (
        not user
        or not user.get("password_hash")
        or not password_hasher.verify(password, user["password_hash"])
    ):
        return render(request, "login.html", error="Invalid email or password.", message=None)

    request.session.clear()
    request.session["user_email"] = email
    return RedirectResponse("/dashboard", status_code=303)

@app.get("/auth/google/login")
async def google_login(request: Request):
    try:
        return await oauth.google.authorize_redirect(request, GOOGLE_REDIRECT_URI)
    except Exception as exc:
        logger.exception("Could not start Google OAuth: %s", type(exc).__name__)
        return render(request, "login.html", error="Could not start Google login.", message=None)

@app.get("/auth/google/callback")
async def google_callback(request: Request):
    try:
        token = await oauth.google.authorize_access_token(request)
        profile = token.get("userinfo")
        if not profile:
            return render(request, "login.html", error="Google did not return a profile.", message=None)

        google_id = profile.get("sub")
        name = (profile.get("name") or "").strip()
        email = (profile.get("email") or "").strip().lower()
        picture = profile.get("picture")
        verified = profile.get("email_verified")

        if not google_id or not email or not valid_email(email) or verified not in (True, "true"):
            return render(request, "login.html", error="Google account email could not be verified.", message=None)

        user = users.get(email)
        if user is None:
            user = {
                "google_id": google_id,
                "name": name or email.split("@")[0],
                "email": email,
                "picture": picture,
                "password_hash": None,
            }
            users[email] = user
        else:
            user["google_id"] = google_id
            user["name"] = name or user.get("name") or email.split("@")[0]
            user["picture"] = picture

        request.session.clear()
        request.session["user_email"] = email
        return RedirectResponse("/dashboard", status_code=303)
    except Exception as exc:
        logger.exception("Google OAuth callback failed: %s", type(exc).__name__)
        return render(request, "login.html", error="Google login failed.", message=None)

@app.get("/dashboard")
async def dashboard(request: Request):
    user = current_user(request)
    if not user:
        return RedirectResponse("/login", status_code=303)
    return render(request, "dashboard.html", user=user)

@app.post("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=303)