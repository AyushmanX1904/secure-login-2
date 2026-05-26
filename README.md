# Secure Login Web App

This is a minimal secure login web app built with Flask featuring:

- Registration & login with Argon2-hashed passwords
- Input validation with WTForms
- SQL injection protection using SQLAlchemy ORM (parameterized queries)
- Session management with Flask-Login and logout
- Optional TOTP 2FA using `pyotp` and QR code provisioning

Location: secure-login-2

Quick start (Windows):

```powershell
cd d:/thiranex-5/secure-login-2
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python init_db.py
python app.py
```

Open http://127.0.0.1:5000

To push to your GitHub repo and create a Pages-style link for the repository (frontend only), run:

```powershell
git init
git add .
git commit -m "Initial secure-login app"
git remote add origin https://github.com/AyushmanX1904/secure-login-2.git
git branch -M main
git push -u origin main
```

Note: This app is a dynamic Flask backend — GitHub Pages only serves static sites. To make the app publicly accessible, deploy the repository to a platform that supports Python web apps (Render, Fly, Heroku, Azure Web Apps, etc.).

If you want a static demo hosted at GitHub Pages, create a `gh-pages` branch with a small static frontend that calls a hosted API.

Publishing the bundled static demo to GitHub Pages
------------------------------------------------

This repository includes a ready static demo in the `static-demo` folder. To publish it to the `gh-pages` branch (so GitHub Pages serves it at https://AyushmanX1904.github.io/secure-login-2/), you can use one of these methods from the project root:

1) Using `git subtree` (easy):

```powershell
git add static-demo
git commit -m "Add static demo"
git subtree push --prefix static-demo origin gh-pages
```

2) Using an orphan branch (works everywhere):

```powershell
git checkout --orphan gh-pages
git rm -rf .
robocopy static-demo . /E
git add .
git commit -m "Deploy static demo to gh-pages"
git push -u origin gh-pages --force
git checkout main
```

After pushing, GitHub Pages will normally publish the site at:

https://AyushmanX1904.github.io/secure-login-2/

