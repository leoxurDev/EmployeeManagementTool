# 💻 Local Development Setup (Virtualenv)

This guide provides instructions for setting up the Employee Time & Management Portal on your local machine for development, testing, and debugging.

---

## ⚙️ Step-by-Step Setup

Follow these steps to set up a Python virtual environment and run the application locally with the default SQLite database:

### 1. Clone the Repository
```bash
git clone https://github.com/leoxurDev/EmployeeManagementTool.git
cd EmployeeManagementTool
```

### 2. Create and Activate a Python Virtual Environment
```bash
# Create the environment
python3 -m venv venv

# Activate (macOS / Linux)
source venv/bin/activate

# Activate (Windows CMD)
# venv\Scripts\activate.bat

# Activate (Windows PowerShell)
# venv\Scripts\Activate.ps1
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Apply Database Migrations
```bash
python manage.py migrate
```

### 5. Seed Default Configuration Data
Before starting the application, you must seed the database with the default departments, avatar emojis, and color palettes:
```bash
python manage.py seed_configurations
```
*Note: This command runs the Django management command defined in `attendance/management/commands/seed_configurations.py`.*

### 6. Create a Superuser Account
Create an administrative account to access the Django Admin interface (`/admin/`) and manage layouts/permissions:
```bash
python manage.py createsuperuser
```

### 7. Run the Development Server
Specify an optional `APP_NAME` environment variable to customize the organization's display name:
```bash
# macOS / Linux
APP_NAME="Acme Corp" python manage.py runserver

# Windows (CMD)
# set APP_NAME=Acme Corp
# python manage.py runserver
```

Open your browser and navigate to **`http://127.0.0.1:8000/`**.

---

## 🗄️ Resetting and Wiping local Database Data

### A. Clear database records (keep schema)
If you want to clear all data (employees, attendance logs, emails, etc.) but keep the database structure, tables, and superuser accounts:
```bash
python manage.py flush --noinput
```

### B. Start from a completely fresh database file
To wipe the SQLite database file entirely and re-create it:
```bash
# Delete the SQLite file (macOS / Linux)
rm db.sqlite3

# Delete the SQLite file (Windows)
# del db.sqlite3

# Re-run migrations and setup
python manage.py migrate
python manage.py seed_configurations
python manage.py createsuperuser
```

---

## 🧪 Running Automated Tests

The application features a unified test suite in [`attendance/tests.py`](../attendance/tests.py) covering PIN verification, dashboard authorization, layouts API, SLA calculations, and support tickets logic.

To run the tests in your local environment, ensure your virtual environment is active and run:
```bash
python manage.py test
```
