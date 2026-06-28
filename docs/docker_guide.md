# 🐳 Running in Docker & Containers Guide

This guide details how to build, run, and manage the Employee Time & Management Portal using Docker and Docker Compose.

---

## 🐳 Method 1: Docker Compose (Recommended)

Using Docker Compose is the recommended way to run the application in a multi-container stack (application container + MySQL database container + phpMyAdmin container).

### 1. Build and Start Services
```bash
docker-compose up --build -d
```
*   `--build` ensures the Docker image is rebuilt with any code updates.
*   `-d` runs the container stack in the background (detached mode).

### 2. Apply Database Migrations
Run migrations inside the running `web` container:
```bash
docker-compose exec web python manage.py migrate
```

### 3. Seed Default Configuration Data
Seed default departments, avatar options, and background colors:
```bash
docker-compose exec web python manage.py seed_configurations
```

### 4. Create a Superuser Account
```bash
docker-compose exec web python manage.py createsuperuser
```

Open your browser and navigate to:
*   **Web Portal**: `http://localhost/` (Port 80 mapped to container port 8000)
*   **phpMyAdmin (Database Web UI)**: `http://localhost:8080/` (Port 8080 mapped to container port 80)

---

## 🚨 Crucial: Resetting & Wiping Database Volumes

MySQL stores all databases and users inside a persistent volume. **MySQL Docker containers only initialize database tables and user credentials the very first time the volume is created.**

If you run `deploy.sh` (or modify `.env`/`docker-compose.yml`) and change database variables such as `DB_USER`, `DB_PASSWORD`, or `DB_NAME`, the changes will be **ignored** by the running MySQL container, leading to `Access denied` database connection errors.

### To completely reset and wipe the database volume:
1.  **Stop the containers and delete the volume**:
    ```bash
    docker-compose down -v
    ```
    *The `-v` (volume) flag is critical. It deletes the persistent MySQL storage volume, allowing it to be recreated fresh.*
2.  **Re-run your setup script or build command**:
    ```bash
    bash deploy.sh
    # OR:
    # docker-compose up --build -d
    ```
3.  **Apply migrations, seeding, and superuser commands** (see steps 2, 3, 4 under Docker Compose above).

---

## 🧪 Running Tests inside Docker

To run the automated tests suite inside the Docker container:
```bash
docker-compose exec web python manage.py test
```

---

## 🐳 Method 2: Raw Docker Commands (Single Container)

If you wish to run the portal inside a standalone container using local SQLite database:

### 1. Build the Image
```bash
docker build -t employee-attendance-app .
```

### 2. Run the Container
Mount `db.sqlite3` from your host directory to persist database data, and set `APP_NAME`:
```bash
# macOS / Linux
docker run -d -p 8000:8000 \
  -e APP_NAME="Acme Corp" \
  -v $(pwd)/db.sqlite3:/app/db.sqlite3 \
  --name employee-attendance-container \
  employee-attendance-app

# Windows (Command Prompt)
# docker run -d -p 8000:8000 -e APP_NAME="Acme Corp" -v %cd%/db.sqlite3:/app/db.sqlite3 --name employee-attendance-container employee-attendance-app
```

### 3. Run Setup Commands Inside the Container
```bash
# Apply migrations
docker exec -it employee-attendance-container python manage.py migrate

# Seed configuration options
docker exec -it employee-attendance-container python manage.py seed_configurations

# Create superuser
docker exec -it employee-attendance-container python manage.py createsuperuser
```

Access the portal at `http://localhost:8000/`.

---

## 📈 Monitoring & Logs Cheatsheet

| Command | Purpose |
| --- | --- |
| `docker-compose ps` | List status of all active stack containers |
| `docker-compose logs -f` | View and follow real-time logs for all services |
| `docker-compose logs web --tail=50` | View the last 50 log lines for the Django web container |
| `docker-compose logs db` | View MySQL database container logs |
| `docker-compose down` | Stop and remove stack containers (keeps volumes/data) |
| `docker-compose down -v` | Stop containers and **delete all volumes and data** |
| `docker exec -it employee_manage_db bash` | Open an interactive terminal shell inside the MySQL database container |
