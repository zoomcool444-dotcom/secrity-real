from fastapi import FastAPI, Request, Form, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from passlib.context import CryptContext
import sqlite3
import os
import secrets
import hashlib
from datetime import datetime, timedelta
import re

app = FastAPI(title="SecureMail - Secure Email Platform")

# Session middleware
app.add_middleware(SessionMiddleware, secret_key=secrets.token_urlsafe(32))

# Static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Database setup
DB_PATH = "instance/securemail.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        full_name TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS password_reset_tokens (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        token TEXT UNIQUE NOT NULL,
        expires_at TIMESTAMP NOT NULL,
        used BOOLEAN DEFAULT 0,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )''')
    conn.commit()
    conn.close()

init_db()

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def get_current_user(request: Request, db: sqlite3.Connection = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    cur = db.cursor()
    cur.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cur.fetchone()
    return user

def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    user = get_current_user(request)
    if user:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse("index.html", {"request": request, "user": None})

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    user = get_current_user(request)
    if user:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse("login.html", {"request": request, "error": None})

@app.post("/login")
async def login(request: Request, email: str = Form(...), password: str = Form(...), db: sqlite3.Connection = Depends(get_db)):
    if not validate_email(email):
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid email format"})
    
    cur = db.cursor()
    cur.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = cur.fetchone()
    
    if not user or not pwd_context.verify(password, user["password_hash"]):
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid email or password"})
    
    request.session["user_id"] = user["id"]
    return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)

@app.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request):
    user = get_current_user(request)
    if user:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse("signup.html", {"request": request, "error": None})

@app.post("/signup")
async def signup(request: Request, full_name: str = Form(...), username: str = Form(...), email: str = Form(...), password: str = Form(...), confirm_password: str = Form(...), db: sqlite3.Connection = Depends(get_db)):
    if not validate_email(email):
        return templates.TemplateResponse("signup.html", {"request": request, "error": "Invalid email format"})
    
    if len(password) < 8:
        return templates.TemplateResponse("signup.html", {"request": request, "error": "Password must be at least 8 characters long"})
    
    if password != confirm_password:
        return templates.TemplateResponse("signup.html", {"request": request, "error": "Passwords do not match"})
    
    if len(username) < 3:
        return templates.TemplateResponse("signup.html", {"request": request, "error": "Username must be at least 3 characters long"})
    
    cur = db.cursor()
    cur.execute("SELECT * FROM users WHERE email = ? OR username = ?", (email, username))
    existing = cur.fetchone()
    
    if existing:
        return templates.TemplateResponse("signup.html", {"request": request, "error": "Email or username already exists"})
    
    password_hash = pwd_context.hash(password)
    cur.execute("INSERT INTO users (username, email, password_hash, full_name) VALUES (?, ?, ?, ?)",
                (username, email, password_hash, full_name))
    db.commit()
    
    cur.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = cur.fetchone()
    request.session["user_id"] = user["id"]
    
    return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, db: sqlite3.Connection = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse("dashboard.html", {"request": request, "user": user})

@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)

@app.get("/reset-password", response_class=HTMLResponse)
async def reset_password_page(request: Request):
    return templates.TemplateResponse("reset_password.html", {"request": request, "error": None, "success": None})

@app.post("/reset-password")
async def reset_password(request: Request, email: str = Form(...), db: sqlite3.Connection = Depends(get_db)):
    if not validate_email(email):
        return templates.TemplateResponse("reset_password.html", {"request": request, "error": "Invalid email format", "success": None})
    
    cur = db.cursor()
    cur.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = cur.fetchone()
    
    if user:
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now() + timedelta(hours=1)
        cur.execute("INSERT INTO password_reset_tokens (user_id, token, expires_at) VALUES (?, ?, ?)",
                    (user["id"], token, expires_at))
        db.commit()
        return templates.TemplateResponse("reset_password.html", {"request": request, "error": None, "success": f"Password reset link sent to {email} (Token: {token})"})
    
    return templates.TemplateResponse("reset_password.html", {"request": request, "error": None, "success": f"Password reset link sent to {email} (if account exists)"})

@app.get("/reset-password/confirm/{token}", response_class=HTMLResponse)
async def reset_confirm_page(request: Request, token: str, db: sqlite3.Connection = Depends(get_db)):
    cur = db.cursor()
    cur.execute("SELECT * FROM password_reset_tokens WHERE token = ? AND used = 0 AND expires_at > ?", 
                (token, datetime.now()))
    reset_token = cur.fetchone()
    
    if not reset_token:
        return templates.TemplateResponse("reset_confirm.html", {"request": request, "error": "Invalid or expired token", "token": token})
    
    return templates.TemplateResponse("reset_confirm.html", {"request": request, "error": None, "token": token})

@app.post("/reset-password/confirm/{token}")
async def reset_confirm(request: Request, token: str, password: str = Form(...), confirm_password: str = Form(...), db: sqlite3.Connection = Depends(get_db)):
    if len(password) < 8:
        return templates.TemplateResponse("reset_confirm.html", {"request": request, "error": "Password must be at least 8 characters long", "token": token})
    
    if password != confirm_password:
        return templates.TemplateResponse("reset_confirm.html", {"request": request, "error": "Passwords do not match", "token": token})
    
    cur = db.cursor()
    cur.execute("SELECT * FROM password_reset_tokens WHERE token = ? AND used = 0 AND expires_at > ?", 
                (token, datetime.now()))
    reset_token = cur.fetchone()
    
    if not reset_token:
        return templates.TemplateResponse("reset_confirm.html", {"request": request, "error": "Invalid or expired token", "token": token})
    
    password_hash = pwd_context.hash(password)
    cur.execute("UPDATE users SET password_hash = ? WHERE id = ?", (password_hash, reset_token["user_id"]))
    cur.execute("UPDATE password_reset_tokens SET used = 1 WHERE token = ?", (token,))
    db.commit()
    
    return templates.TemplateResponse("reset_confirm.html", {"request": request, "error": None, "success": "Password reset successful! You can now login.", "token": token})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
