# Google OAuth 2.0 Login System (FastAPI + Jinja2)

A full-stack login system with Google OAuth 2.0, multi-theme customization (5 Dark & 5 Light themes), auto user registration, and session management built using FastAPI and Jinja2 templates.

## 🚀 Features
- **Google OAuth 2.0 Integration**: Single-click login with Google.
- **Auto User Registration**: Auto-creates account on first login.
- **Session Management**: Protected routes (`/dashboard`) and logout functionality.
- **Theme Customizer**: 5 Dark and 5 Light themes with `localStorage` persistence.
- **Modern UI**: Clean design with responsiveness and dynamic typography.

---

## 🛠️ Setup Google Cloud Console Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project (e.g., `FastAPI-OAuth-App`).
3. Navigate to **APIs & Services** > **OAuth consent screen**:
   - Choose **External**.
   - Fill in app name, user support email, and developer contact info.
   - Add scopes: `openid`, `https://www.googleapis.com/auth/userinfo.email`, `https://www.googleapis.com/auth/userinfo.profile`.
4. Navigate to **APIs & Services** > **Credentials**:
   - Click **Create Credentials** > **OAuth client ID**.
   - Select Application Type: **Web application**.
   - Add **Authorized JavaScript origins**:
     - `http://127.0.0.1:8000` (for local development)
     - `https://your-deployed-app-url.onrender.com` (for production)
   - Add **Authorized redirect URIs**:
     - `http://127.0.0.1:8000/auth/google/callback` (for local development)
     - `https://your-deployed-app-url.onrender.com/auth/google/callback` (for production)
5. Copy your **Client ID** and **Client Secret**.

---

## ⚙️ Local Installation & Run Guide

1. **Clone the Repository**:
   ```bash
   git clone [https://github.com/your-username/google-oauth-fastapi.git](https://github.com/your-username/google-oauth-fastapi.git)
   cd google-oauth-fastapi