# 🔗 URL Routes & Static Assets Reference

This document maps out the URL patterns, views, and static assets of the Employee Time & Management Portal.

---

## 🔗 Route Reference Registry

| URL Pattern | View Function | Description |
| --- | --- | --- |
| `/` | `home` | Landing page |
| `/grid/` | `employee_grid` | Employee kiosk tab view |
| `/verify-pin/` | `verify_pin` | AJAX endpoint: verifies employee 6-digit PIN code |
| `/toggle-attendance/` | `toggle_attendance` | AJAX endpoint: registers employee check-in or check-out |
| `/login/` | `manager_login` | Unified manager login page |
| `/manager/login/` | `manager_login` | Manager login alias page |
| `/manager/register/` | `manager_register` | Manager registration page (restricted to staff/superusers) |
| `/manager/logout/` | `manager_logout` | Manager session sign out |
| `/manager/` | `manager_dashboard` | Manager Dashboard (Roster date editor & ticket summaries) |
| `/manager/add/` | `add_employee` | Form to create a new employee profile |
| `/manager/edit/<id>/` | `edit_employee` | Form to update an employee profile |
| `/manager/delete/<id>/` | `delete_employee` | Soft-deletes employee profile (`is_active = False`) |
| `/manager/export/` | `export_attendance_csv` | Downloads today's attendance logs in CSV format |
| `/manager/roster/assign/` | `assign_roster_shift` | AJAX endpoint: schedules or removes employee shift roster |
| `/manager/developer/` | `admin_developer_page` | Developer panel: drag kiosk blocks, AI chat commands |
| `/manager/developer/save/` | `save_layout` | AJAX endpoint: saves block layouts weights & visibilities |
| `/manager/developer/chat/` | `ai_chat_command` | AJAX endpoint: processes Gemini layout chat inputs |
| `/support/` | `support_home` | IT Support client portal and ticket creator |
| `/support/ticket/<num>/` | `support_ticket_view` | Client ticket activity logs and customer comment replies |
| `/support/engineer/login/` | `engineer_login_view` | IT Support Engineer console login page |
| `/support/engineer/logout/` | `engineer_logout_view` | IT Support Engineer console logout |
| `/support/engineer/` | `engineer_dashboard` | IT Support Incident queue dashboard |
| `/support/engineer/ticket/<num>/` | `engineer_ticket_detail` | Incident management detail panel (Work Notes/SLA timers) |
| `/support/engineer/identity/` | `identity_manager` | IT staff manager: active toggles, permissions, groups |
| `/support/engineer/list/` | `engineer_list` | List all support engineers |
| `/support/engineer/create/` | `engineer_create` | Add support engineer profile |
| `/support/engineer/edit/<id>/` | `engineer_edit` | Update support engineer details |
| `/support/engineer/delete/<id>/` | `engineer_delete` | Delete support engineer details |
| `/support/group/list/` | `group_list` | List all IT assignment groups |
| `/support/group/create/` | `group_create` | Add an IT assignment group |
| `/support/group/edit/<id>/` | `group_edit` | Update IT assignment group name/details |
| `/support/group/delete/<id>/` | `group_delete` | Delete assignment group |
| `/leoxur-comm/` | `leoxur_comm_dashboard` | Workspace SPA (Mails, Chat, Tasks, Notes) |
| `/leoxur-comm/auth/` | `leoxur_comm_auth` | Workspace profile login page (checks PIN / password) |
| `/leoxur-comm/logout/` | `leoxur_comm_logout` | Workspace profile session sign out |
| `/leoxur-comm/data/` | `leoxur_comm_data` | AJAX endpoint: polls emails, chat messages, and tasks |
| `/leoxur-comm/send-email/` | `leoxur_send_email` | AJAX endpoint: sends email message |
| `/leoxur-comm/send-chat/` | `leoxur_send_chat` | AJAX endpoint: sends chat channel/direct message |
| `/leoxur-comm/read-email/` | `leoxur_read_email` | AJAX endpoint: flags email as read |
| `/leoxur-comm/create-task/` | `leoxur_create_task` | AJAX endpoint: creates task on Kanban board |
| `/leoxur-comm/update-task/` | `leoxur_update_task` | AJAX endpoint: moves task columns or sets priorities |
| `/leoxur-comm/delete-task/` | `leoxur_delete_task` | AJAX endpoint: deletes task cards |
| `/leoxur-comm/add-task-comment/` | `leoxur_create_task_comment` | AJAX endpoint: posts comments on tasks |
| `/admin/` | `Django Admin` | Django built-in core database admin portal |

---

## 🎨 Static Assets & Stylesheets

### CSS Themes
*   **[`static/css/employee_theme.css`](../static/css/employee_theme.css)**: Core stylesheet for the Employee Portal. Defines dark mode variable tokens, layout alignments, shift ticker loops, keypad elements, and tables.
*   **[`static/css/servicenow_theme.css`](../static/css/servicenow_theme.css)**: Technical stylesheet for IT Support and Incident Management views. Handles ticket state badge coloring, SLA timer alerts, and lists.
*   **[`static/css/leoxur_comm.css`](../static/css/leoxur_comm.css)**: Visual layout for the SPA Communication Suite. Controls direct message bubbles, chat panes, notes autosaver toolbar, and drag-and-drop Kanban columns.

### Frontend Logic
*   **[`static/js/employee_attendance.js`](../static/js/employee_attendance.js)**: Central script handling all browser-side operations:
    *   AJAX calls (check-in, check-out, PIN checks).
    *   Keypad UI animations.
    *   Leoxur Mails composition.
    *   Leoxur Chat DOM renders and Audio notification synthesizer.
    *   Notes localStorage auto-saves.
    *   Kanban task card draggable hooks.
