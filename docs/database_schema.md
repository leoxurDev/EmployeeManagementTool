# 🗄️ Database Schema & Migration Guide

This document describes the database schema, models, shift business rules, SLA timers, and steps to migrate data from SQLite to MySQL.

---

## 🗄️ Database Models Reference

The application contains 15 database models defined in [`attendance/models.py`](../attendance/models.py):

| Model Name | Table Name | Purpose & Description |
| --- | --- | --- |
| `DepartmentOption` | `attendance_departmentoption` | Active departments displayed as tabs on the Employee Kiosk. Stores department name, visual emoji icon, and ordering weight. |
| `AvatarEmoji` | `attendance_avataremoji` | Registered choices of emojis that employees can choose for their profile picture avatar. |
| `AvatarColor` | `attendance_avatarcolor` | Hex colors that can be selected for employee avatar background cards. |
| `Employee` | `attendance_employee` | Primary profiles of employees. Records name, department connection, visual avatar emoji/color, and the hashed/encrypted 6-digit access PIN. |
| `Roster` | `attendance_roster` | Scheduled shift placements for employees on specific calendar dates. Links to employee profiles and stores shift types (Morning, Afternoon, Night). |
| `Attendance` | `attendance_attendance` | Daily check-in/out records. Tracks check-in/out times, work modes (Office, Remote, Field), statuses (Present, Late, Absent), and calculated total hours worked. |
| `AppLayoutBlock` | `attendance_applayoutblock` | Stores layout block configuration (order index and visibility) for the Employee Kiosk page (Header, Tabs, Stats, Grid). |
| `AssignmentGroup` | `attendance_assignmentgroup` | IT Incident assignment groups (e.g. L2 Support, Networking, Hardware Teams) for ticketing workflows. |
| `SupportEngineer` | `attendance_supportengineer` | Technical staff logins. Stores name, email, hashed credentials, and toggle statuses for access control. |
| `SupportTicket` | `attendance_supportticket` | IT Incident tickets. Tracks generate IDs (`TKT100001`), state lifecycle, priorities, caller name, assignment group, and assigned engineer. |
| `TicketActivity` | `attendance_ticketactivity` | Communication logs on tickets. Distinguishes between internal **Work Notes** and public **Customer Comments**. |
| `EmployeeSupportPermission` | `attendance_employeesupportpermission` | Map association granting specific managers the ability to raise help desk tickets. |
| `LeoxurEmail` | `attendance_leoxuremail` | Emails composed inside the workspace portal. Links sender/recipient, subject, body, read flags, and carbon copies. |
| `LeoxurMessage` | `attendance_leoxurmessage` | Communication chat messages. Maps to channel tags (general, support, managers, announcements) or direct user message connections. Supports threading. |
| `LeoxurTask` | `attendance_leoxurtask` | Kanban cards. Tracks task title, description, priority weight, status column, creator, and assignee. |
| `LeoxurTaskComment` | `attendance_leoxurtaskcomment` | Comments posted inside task cards on the Kanban board. |

---

## ⏰ Shift & SLA Rules

### Shift Time Definitions
The portal defaults to **Asia/Kolkata (IST — UTC+5:30)**:
*   🌅 **Morning Shift**: 06:00 AM – 02:00 PM
*   ☀️ **Afternoon Shift**: 02:00 PM – 10:00 PM
*   🌙 **Night Shift**: 10:00 PM – 06:00 AM

> **Late Check-In Rule**: If an employee checks in more than **15 minutes** after their assigned shift start time, the attendance status is automatically flagged as **Late ⏰**.

### SLA Durations by Incident Priority
IT support incidents are bounded by Service Level Agreement (SLA) response windows based on priority level:
*   **Critical**: 1 hour response window
*   **High**: 4 hours response window
*   **Moderate**: 8 hours response window
*   **Low**: 24 hours response window

---

## 🔄 SQLite to MySQL Database Migration

Follow these steps to migrate your existing local SQLite data into the production MySQL database container:

### Step 1 — Dump Current SQLite Data
Export your local SQLite tables into a standardized JSON data dump (excluding Django content types and permission rules to prevent unique constraints failures):
```bash
python manage.py dumpdata --natural-foreign --natural-primary -e contenttypes -e auth.Permission --indent 4 > datadump.json
```

### Step 2 — Configure Environment Variables
Ensure your `.env` file is configured with the MySQL connection variables:
```ini
DB_ENGINE=mysql
DB_NAME=employee_manage
DB_USER=admin_db_user
DB_PASSWORD=your_secure_password
DB_HOST=db
DB_PORT=3306
```

### Step 3 — Apply Schema Migrations on MySQL
Start your container stack and apply Django migrations to create the table structure in MySQL:
```bash
docker-compose exec web python manage.py migrate
```

### Step 4 — Clear Default Content Types
Before loading the data dump, you must clear the automatically generated `ContentType` entries to avoid conflicts:
```bash
docker-compose exec web python manage.py shell -c "from django.contrib.contenttypes.models import ContentType; ContentType.objects.all().delete()"
```

### Step 5 — Import the Data Dump
Load the data dump file into the MySQL database container:
```bash
# Copy the dump file to the container if needed (Compose mounts local workspace so it's already present in /app)
docker-compose exec web python manage.py loaddata datadump.json
```

If starting fresh (without importing a database dump), run the seeding command to populate initial kiosk blocks and departments:
```bash
docker-compose exec web python manage.py seed_configurations
```
