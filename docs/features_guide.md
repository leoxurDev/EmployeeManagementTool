# 📚 Employee Portal Features & Pages Guide

This document describes the design, functionality, and usage workflows for every page and portal in the Employee Time & Management Portal.

---

## 📑 Portal Features Index

1.  [Home / Landing Page](#1-home--landing-page)
2.  [Employee Time & Expense Kiosk (Grid)](#2-employee-time--expense-kiosk-grid)
3.  [Manager Login & Register](#3-manager-login--register)
4.  [Manager Dashboard](#4-manager-dashboard)
5.  [Add / Edit / Delete Employee Forms](#5-add--edit--delete-employee-forms)
6.  [IT Support Portal — Client View](#6-it-support-portal--client-view)
7.  [IT Support Engineer Console](#7-it-support-engineer-console)
8.  [Engineer Identity & Permissions Manager](#8-engineer-identity--permissions-manager)
9.  [Leoxur Mails & Chat Communication Suite](#9-leoxur-mails--chat-communication-suite)
10. [Developer / Admin Customizer Page](#10-developer--admin-customizer-page)
11. [Django Admin Database Panel](#11-django-admin-database-panel)

---

## 1. Home / Landing Page
*   **URL**: `/`
*   **Template**: `attendance/home.html`
*   **View**: `home()`
*   **Access**: Public (No login required)

The landing page provides a central hub linking to all primary application sections. It features a global **Shift Ticker Bar** at the top of the viewport (injected via `schedule_context_processor`). This bar loops a marquee showing the current active shift details (Morning 🌅, Afternoon ☀️, or Night 🌙), a live timezone-compliant clock, and shift milestones.

---

## 2. Employee Time & Expense Kiosk (Grid)
*   **URL**: `/grid/?classroom=<DepartmentName>`
*   **Template**: `attendance/employee_grid.html`
*   **View**: `employee_grid()`
*   **Access**: Public (Intended for shared tablet/terminal in common area)

A self-service station for employees to record shift check-ins and check-outs.

*   **Department Tabs**: Dynamically filters employees based on active `DepartmentOption` database choices.
*   **Keypad PIN Verification**: Clicking an employee card slides open a secure 6-digit numeric PIN pad. PIN matches are validated via AJAX (`/verify-pin/`).
*   **Check-In Flow**: Verified employees choose a **Work Mode** (🏢 Office, 🏠 Remote, or 🚗 Field) to record their arrival.
*   **Late Detection**: If check-in occurs more than **15 minutes** past the start of the employee's assigned rostered shift, they are automatically marked as **Late ⏰**.
*   **Check-Out Flow**: Already checked-in employees click **Check Out** on validation to calculate and persist `hours_worked`.
*   **Customizable Layouts**: Kiosk block positioning is fully dynamic (read from the `AppLayoutBlock` table) and can be re-ordered or hidden by admins.

---

## 3. Manager Login & Register
*   **URL**: `/login/` (or `/manager/login/`)
*   **Registration URL**: `/manager/register/` (Restricted to staff/superusers)
*   **Template**: `attendance/login.html`
*   **Access**: Authentication required for registration

Allows managers to log in and access scheduling and employee registers. Sessions are configured to automatically expire after **30 minutes of inactivity** (`SESSION_COOKIE_AGE = 1800`) or when the user closes their browser.

---

## 4. Manager Dashboard
*   **URL**: `/manager/`
*   **Template**: `attendance/manager_dashboard.html`
*   **Access**: Authentication required (Manager account)

The command center for administrative and scheduling tasks.

*   **Interactive Scheduler Grid**: Displays a tabular overview of employees and their shift rosters for any chosen date. Selecting `-- Remove Shift --` deletes the roster entry.
*   **Roster Date Picker**: Allows managers to view historical shift sheets or schedule future work rotations.
*   **Export CSV**: Generates and downloads a spreadsheet containing today's attendance logs, check-in/out timestamps, work modes, and total hours logged.
*   **Ticket Integration Panel**: If the manager has support ticket permissions, lists open incident states at the bottom of the dashboard.

---

## 5. Add / Edit / Delete Employee Forms
*   **URLs**: `/manager/add/`, `/manager/edit/<id>/`, `/manager/delete/<id>/`
*   **Templates**: `attendance/employee_form.html`, `attendance/employee_confirm_delete.html`
*   **Access**: Authentication required (Manager account)

Provides full CRUD operations for employee profile management.
*   **Avatar Styles**: Assign custom emoji avatars and background color palettes.
*   **Numeric PIN**: Configures the 6-digit passcode for kiosk sign-ins.
*   **Soft Deletion**: Deleting an employee sets their `is_active` flag to `False` instead of wiping database rows, preserving historical schedules and timesheets.

---

## 6. IT Support Portal — Client View
*   **URL**: `/support/`
*   **Ticket Lookup URL**: `/support/ticket/<TKT######>/`
*   **Templates**: `attendance/support_home.html`, `attendance/support_ticket_detail.html`
*   **Access**: Authentication required (`can_raise_tickets` permission required)

Allows authorized managers to request technical help and monitor response status.
*   **Ticket Creation**: Submit incidents by caller, subject, details, and priority (Low, Moderate, High, Critical). Tickets are assigned a tracking number (`TKT100001`, etc.).
*   **SLA Tracking**: Incidents dynamically compute deadlines based on priority.
*   **Activity Stream**: Shows comments posted by callers and public updates posted by technicians. Callers can post replies directly in this view.

---

## 7. IT Support Engineer Console
*   **Login URL**: `/support/engineer/login/`
*   **Console URL**: `/support/engineer/`
*   **Templates**: `attendance/support/engineer_login.html`, `attendance/support/engineer_dashboard.html`
*   **Access**: Authentication required (Support Engineer credentials)

A ticket management board for IT support teams. Engineers log in using email credentials (stored in `SupportEngineer`), completely independent of the Django auth system.

*   **Incident Queue Filters**: Filter tickets by assigned engineer, assignment group, state, and priority.
*   **SLA Status Indicators**:
    *   🟢 `Active` — Under SLA window.
    *   🟡 `Warning` — Under 25% of the SLA window remains.
    *   🔴 `Breached` — SLA window passed without ticket resolution.
    *   ✅ `Met` — Incident resolved inside SLA window.
*   **Activity Logging**: Post internal **Work Notes** (visible only to support staff) or **Customer Comments** (visible on the client portal).
*   **Engineering CRUD**: Manage engineers and assign them to **Assignment Groups** (L2, L3, L4 support teams).

---

## 8. Engineer Identity & Permissions Manager
*   **URL**: `/support/engineer/identity/`
*   **Template**: `attendance/support/identity_manager.html`
*   **Access**: Authentication required (Support Administrator)

A central console to manage IT staff profiles, toggle their active status, modify group associations, and toggle the `can_raise_tickets` permissions for regular manager accounts.

---

## 9. Leoxur Mails & Chat Communication Suite
*   **URL**: `/leoxur-comm/`
*   **Template**: `attendance/leoxur_comm.html`
*   **Access**: Authentication required (Requires choosing a profile and verifying PIN/password)

A macOS-inspired communication system containing four core SPA modules.

### Workspace Controls
*   **Fullscreen Mode**: Click the `🖥️` button to toggle fullscreen, stripping headers to maximize desktop focus.
*   **Collapsible Navigation**: The sidebar automatically collapses on mobile viewports into a small toggle button (`Menu ☰`), saving vertical space. Clicking a navigation item automatically collapses the menu back.

### 📧 Leoxur Mails (Email Client)
*   Send emails to any registered employee, manager, or engineer.
*   **Carbon Copy (CC)**: Add multiple CC recipients to email lists.
*   **Email Threading**: Reply directly to received emails, nesting follow-ups inline.

### 💬 Leoxur Chat (Real-time Channels & DMs)
*   Participate in team rooms (`#general`, `#support`, `#managers`) or start Direct Messages.
*   **Web Audio synthesizers**: Plays a retro notification sound in the client browser when a new message is received.
*   **Threading**: Reply to individual channel messages to construct clean side-discussions.

### 📝 Leo Notes (Personal Sticky Notes)
*   macOS Notes-style rich notepad with local auto-saving.
*   **Privacy Controls**: Toggle visibility between `🔒 Private` (visible only to you) and `👥 Collaborative` (readable and editable by all members of the team).

### ✅ Tasks (Kanban Board)
*   Manage project flow across Backlog, In Progress, In Review, Done, and Archived columns.
*   **Split details pane**: Clicking a card slides open a responsive inline layout (details on left, status/assignee controls on right) optimized to prevent overlay overflow on small screen resolutions.

---

## 10. Developer / Admin Customizer Page
*   **URL**: `/manager/developer/`
*   **Template**: `attendance/developer_page.html`
*   **Access**: Superusers / staff users only

An administrative utility to override portal settings.

*   **Drag-and-Drop Block Customizer**: Drag to re-order the structural content layout of the public Employee Kiosk page. Toggle block visibilities instantly.
*   **AI Command Prompt**: Instruct the page layout in natural language (e.g. *"hide the stats banner and move the grid to the top"*). Powered by Google Gemini 2.5 Flash API with a robust offline keyword-parsing fallback.
*   **Support Permissions Matrix**: Simple toggle table to grant or revoke support-ticket permissions for manager logins.

---

## 11. Django Admin Database Panel
*   **URL**: `/admin/`
*   **Access**: Superuser accounts only

Django's built-in administration panel. Provides direct database CRUD operations for all 15 database models (Rosters, Attendances, Support Tickets, Chats, Emails, Tasks, and Layout Configurations).
