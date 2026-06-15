# LabMS — Laboratory Management System

A full-featured, production-ready Django application for managing laboratories, patients, test orders, and automated WhatsApp result notifications.

---

## Features

| Module | Capabilities |
|--------|-------------|
| **Admin Panel** | Full user management, lab approvals, notification logs |
| **Laboratory Management** | Self-registration, admin approval workflow, multi-lab support |
| **Customer / Patient Management** | Patient profiles, medical history, auto-generated Patient IDs |
| **Test Catalog** | Categories, test codes, pricing, sample types, normal ranges |
| **Test Orders** | Multi-test orders, status tracking, payment status |
| **Results Upload** | Per-test result upload (text + file), abnormal flagging |
| **WhatsApp Notifications** | Auto-notify customer via Twilio when all results are ready |
| **Role-Based Access** | Admin / Lab Manager / Customer — each sees only what they need |

---

## Quick Start

### 1. Clone & Install

```bash
git clone <your-repo>
cd labms

python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env` and fill in your values:

```bash
cp .env .env.local
```

**Required `.env` variables:**

```env
SECRET_KEY=your-very-long-random-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Twilio WhatsApp (get from twilio.com)
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886

SITE_URL=http://localhost:8000
```

### 3. Database & Initial Data

```bash
python manage.py migrate
python manage.py create_admin     # Creates admin user + sample test categories
```

### 4. Run Development Server

```bash
python manage.py runserver
```

Visit **http://localhost:8000** — login with `admin / admin123`

---

## User Roles & Workflows

### Admin
- Creates/manages all users and laboratories
- Approves or rejects laboratory registrations
- Views all orders and the WhatsApp notification log
- Can create test categories and tests for any lab

### Lab Manager
- Registers their lab via `/lab/register/` (pending admin approval)
- After approval: manages their lab's test catalog
- Creates patient orders, uploads test results
- WhatsApp notification fires automatically when all results are uploaded

### Customer (Patient)
- Self-registers at `/accounts/register/` OR is created by admin/lab
- Views their own orders and downloads results
- Gets WhatsApp notification when results are ready

---

## WhatsApp Notification Setup (Twilio)

1. Sign up at [twilio.com](https://www.twilio.com)
2. Go to **Messaging → Try it out → Send a WhatsApp message**
3. Follow Twilio's sandbox instructions (customer must opt-in by sending a code first in sandbox)
4. Set credentials in `.env`
5. Customers must have `whatsapp_number` set (with country code, e.g. `+923001234567`)

**For production:** Apply for a Twilio WhatsApp Business number to skip the sandbox opt-in.

---

## Project Structure

```
labms/                    # Django settings & URLs
accounts/                 # Custom User model, login, dashboard, user mgmt
  management/commands/    # create_admin command
lab/                      # Laboratory model, registration, approval
tests_mgmt/               # Tests, orders, results, WhatsApp service
  services.py             # Business logic: WhatsApp notifications
templates/
  base.html               # Sidebar layout
  accounts/               # Login, register, dashboard, profile
  lab/                    # Lab register, list, detail, approve
  tests_mgmt/             # Tests, customers, orders, results, notifications
```

---

## Production Deployment Checklist

- [ ] Set `DEBUG=False` in `.env`
- [ ] Set a strong `SECRET_KEY`
- [ ] Add your domain to `ALLOWED_HOSTS`
- [ ] Configure PostgreSQL (update `DATABASES` in settings)
- [ ] Configure real email backend (SMTP)
- [ ] Set up a proper Twilio WhatsApp number (not sandbox)
- [ ] Use **gunicorn** or **uWSGI** as the WSGI server
- [ ] Set up **Nginx** to serve static/media files
- [ ] Run `python manage.py collectstatic`
- [ ] Use **Let's Encrypt** for HTTPS (required for `SECURE_SSL_REDIRECT=True`)

### Switch to PostgreSQL

```python
# labms/settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
    }
}
```

```bash
pip install psycopg2-binary
```

### Gunicorn + Nginx

```bash
pip install gunicorn
gunicorn labms.wsgi:application --bind 0.0.0.0:8000 --workers 3
```

---

## Default Credentials

| Role | Username | Password |
|------|----------|----------|
| Admin | `admin` | `admin123` |

> ⚠️ **Change the admin password immediately in production!**

---

## Requirements

```
Django>=4.2
pillow
python-decouple
twilio
reportlab
django-crispy-forms
crispy-bootstrap5
```
# labms
# labms
