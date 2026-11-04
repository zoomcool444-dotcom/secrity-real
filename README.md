# SecureMail - Secure Email Platform

A fully functional, mobile-responsive email-style security website built with FastAPI, Python, SQLite, HTML, CSS, and JavaScript.

## Features

- **User Authentication**: Secure login and registration system
- **Password Security**: Bcrypt password hashing
- **Session Management**: Secure session-based authentication
- **Password Reset**: Functional password reset feature with tokens
- **Email Validation**: Client and server-side email validation
- **Responsive Design**: Works on mobile, tablet, and desktop
- **Original Branding**: SecureMail - no third-party branding
- **Error Handling**: User-friendly error messages
- **Dashboard**: User dashboard after successful login

## Technology Stack

- **Backend**: FastAPI (Python)
- **Database**: SQLite
- **Frontend**: HTML5, CSS3, JavaScript
- **Authentication**: Session-based with secure cookies
- **Password Hashing**: Passlib with bcrypt

## Project Structure

```
security-demo/
├── main.py              # FastAPI application
├── requirements.txt     # Python dependencies
├── README.md           # Project documentation
├── instance/           # SQLite database storage
├── static/             # Static files
│   ├── css/
│   │   └── style.css   # Main stylesheet
│   ├── js/
│   │   └── main.js     # Client-side JavaScript
│   └── img/            # Images directory
└── templates/          # HTML templates
    ├── index.html      # Landing page
    ├── login.html      # Login page
    ├── signup.html     # Registration page
    ├── dashboard.html  # User dashboard
    ├── reset_password.html      # Password reset request
    └── reset_confirm.html       # Password reset confirmation
```

## Setup and Installation (Kali Linux)

### Step 1: Navigate to the project directory
```bash
cd /home/kali/security-demo
```

### Step 2: Create a virtual environment
```bash
python3 -m venv venv
```

### Step 3: Activate the virtual environment
```bash
source venv/bin/activate
```

### Step 4: Install dependencies
```bash
pip install -r requirements.txt
```

### Step 5: Run the application
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Step 6: Access the website
Open your web browser and navigate to:
```
http://localhost:8000
```

## Usage

1. **Home Page**: Visit the landing page to learn about SecureMail
2. **Sign Up**: Create a new account with full name, username, email, and password (minimum 8 characters)
3. **Login**: Sign in with your email and password
4. **Dashboard**: Access your secure dashboard after login
5. **Password Reset**: Use the "Forgot Password?" link to reset your password
6. **Logout**: Click logout to end your session

## Security Features

- Passwords are hashed using bcrypt before storing in database
- Session cookies are secured with a random secret key
- Email format validation on both client and server side
- Password minimum length requirement (8 characters)
- Protection against duplicate email/username registration
- Secure password reset with time-limited tokens
- SQL injection prevention using parameterized queries

## Notes

- The database (`securemail.db`) will be created automatically in the `instance/` directory on first run
- Password reset tokens are displayed on screen for demonstration purposes (in production, they would be sent via email)
- This is a complete, functional application - not a demo or mockup
- All files are original with custom SecureMail branding
