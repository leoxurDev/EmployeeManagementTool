# 🗄️ SQL Cheat Sheet — Useful Commands & Queries

A step-by-step guide to connecting, exploring, and querying the database for your Employee Management application.

---

## 🔑 1. Login to MySQL Docker Container

Run this command in your main terminal to log in to the MySQL interactive shell:

### A. Login as Application User
```bash
# Note: Replace user, password, and database name if you configured custom ones in deploy.sh
docker exec -it employee_manage_db mysql -u employee_user -pemployeepassword employee_manage
```

### B. Login as Root Administrator
```bash
# Note: Replace the password if you configured a custom one in deploy.sh
docker exec -it employee_manage_db mysql -u root -prootpassword employee_manage
```

---

## 🔍 2. Database Structure Inspection

Once logged in, use these commands to find database tables and understand their fields:

```sql
-- Show all databases on the MySQL server
SHOW DATABASES;

-- Select/switch to the application database
USE employee_manage;

-- List all tables created by the Django application
SHOW TABLES;

-- Describe the structure of the employee table (find field names and types)
DESCRIBE attendance_employee;

-- Describe the structure of the attendance logs table
DESCRIBE attendance_attendance;
```

---

## 📈 3. Data Retrieval (SELECT Queries)

### View All Columns in a Table
```sql
SELECT * FROM attendance_employee;
```

### View Specific Columns (Recommended)
```sql
SELECT id, first_name, last_name, department FROM attendance_employee;
```

### Filter Rows (WHERE Clause)
```sql
-- Find employees in the Engineering department
SELECT first_name, last_name FROM attendance_employee WHERE department = 'Engineering';

-- Find employees with a specific 6-digit login PIN
SELECT first_name, last_name FROM attendance_employee WHERE pin_code = '100001';
```

### Logical Combinations (AND, OR, NOT)
```sql
-- Find active rosters for a specific employee on a specific date
SELECT * FROM attendance_roster WHERE employee_id = 1 AND date = '2026-06-27';

-- Find employees in either HR or Engineering departments
SELECT first_name, last_name, department FROM attendance_employee WHERE department = 'HR' OR department = 'Engineering';
```

### Sorting Results (ORDER BY)
```sql
-- View attendance logs sorted by check-in date (latest first)
SELECT id, date, check_in, check_out FROM attendance_attendance ORDER BY date DESC;

-- List employees alphabetically by last name
SELECT first_name, last_name FROM attendance_employee ORDER BY last_name ASC;
```

### Limit Rows
```sql
-- View the 5 most recent attendance entries
SELECT * FROM attendance_attendance ORDER BY date DESC LIMIT 5;
```

---

## ➕ 4. Inserting Data (INSERT Queries)

### Insert a New Employee Profile
```sql
INSERT INTO attendance_employee (first_name, last_name, department, avatar_emoji, avatar_color, pin_code)
VALUES ('John', 'Doe', 'Engineering', '💻', '#4F46E5', '123456');
```

### Insert a Roster Assignment
```sql
-- Note: Make sure the employee_id matches a real employee's ID
INSERT INTO attendance_roster (date, shift_type, employee_id)
VALUES ('2026-06-28', 'Morning', 1);
```

---

## ✏️ 5. Updating Data (UPDATE Queries)

### Update an Employee's Login PIN
```sql
UPDATE attendance_employee 
SET pin_code = '999999' 
WHERE id = 1;
```

### Update a Shift Roster
```sql
UPDATE attendance_roster 
SET shift_type = 'Night' 
WHERE employee_id = 1 AND date = '2026-06-28';
```

---

## ❌ 6. Deleting Data (DELETE Queries)

> [!WARNING]
> Always use a `WHERE` clause when executing `DELETE` statements. Omitting it will erase all records in the table!

### Delete a Specific Check-in Entry
```sql
DELETE FROM attendance_attendance WHERE id = 10;
```

### Delete a Test Roster Entry
```sql
DELETE FROM attendance_roster WHERE employee_id = 1 AND date = '2026-06-28';
```

---

## 🔗 7. Advanced Joining Queries (JOINS)

Joins allow you to link tables together using matching IDs:

### Link Attendance Logs with Employee Names
```sql
SELECT 
    e.first_name, 
    e.last_name, 
    a.date, 
    a.check_in, 
    a.check_out, 
    a.hours_worked 
FROM attendance_attendance a
INNER JOIN attendance_employee e ON a.employee_id = e.id
ORDER BY a.date DESC;
```

### Link Scheduled Rosters with Employee Profiles
```sql
SELECT 
    e.first_name, 
    e.last_name, 
    r.date, 
    r.shift_type 
FROM attendance_roster r
INNER JOIN attendance_employee e ON r.employee_id = e.id
WHERE r.date = '2026-06-27';
```

---

## 📊 8. Aggregations & Analytics (GROUP BY)

### Count Total Employees in the Database
```sql
SELECT COUNT(*) AS total_employees FROM attendance_employee;
```

### Group Employees by Department
```sql
SELECT department, COUNT(*) AS employee_count 
FROM attendance_employee 
GROUP BY department;
```

### Calculate Average Hours Worked per Attendance Check-in
```sql
SELECT AVG(hours_worked) AS average_hours FROM attendance_attendance;
```

### Sum Total Hours Worked per Employee
```sql
SELECT 
    e.first_name, 
    e.last_name, 
    SUM(a.hours_worked) AS total_hours_logged 
FROM attendance_attendance a
INNER JOIN attendance_employee e ON a.employee_id = e.id
GROUP BY e.id, e.first_name, e.last_name;
```

---

## 💼 9. Transaction Controls (Safety Checkpoint)

If you are modifying sensitive production data, wrap it in a transaction so you can roll back in case of mistakes:

```sql
-- 1. Start a transaction session
START TRANSACTION;

-- 2. Execute your modifications
UPDATE attendance_employee SET pin_code = '111111' WHERE department = 'Engineering';

-- 3. Review your changes
SELECT id, first_name, pin_code FROM attendance_employee WHERE department = 'Engineering';

-- 4. IF everything is correct, save permanently:
COMMIT;

-- 4. OR if you made a mistake, discard changes and revert:
ROLLBACK;
```

---

## 🚪 10. Disconnecting
To leave the interactive MySQL shell:
```sql
EXIT;
```
