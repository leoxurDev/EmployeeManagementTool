# ☁️ Cloud Deployment & Updates Guide

This guide details how to deploy the Employee Time & Management Portal to cloud providers (AWS EC2, Azure VMs, GCP Compute Engine) from scratch and how to safely update live deployments.

---

## ⚡ Quickstart with deploy.sh

The included script [`deploy.sh`](../deploy.sh) is a fully automated, interactive utility that builds the Gunicorn and MySQL containers, configures the environment, runs migrations, seeds core parameters, and sets up your superuser account.

To deploy the portal from scratch:
```bash
git clone https://github.com/leoxurDev/EmployeeManagementTool.git
cd EmployeeManagementTool
bash deploy.sh
```

**What the script does:**
1.  Prompts for your **Organization Name** (written to `.env` as `APP_NAME`).
2.  Prompts for your preferred **Database Engine** (SQLite or MySQL).
3.  If MySQL is selected, prompts for database hostname (`db`), port (`3306`), database name (`employee_manage`), user (`employee_user`), and password (safely written to `.env`).
4.  Builds the containers and launches them in detached mode (`docker-compose up --build -d`).
5.  Waits for the MySQL database to report socket readiness.
6.  Applies migrations (`migrate`) and seeds configuration data (`seed_configurations`).
7.  Launches the `createsuperuser` wizard.

---

## 🔒 Inbound Firewall Rules (All Cloud Providers)

For the application and monitoring stack to be accessible, you must configure the following inbound ports in your VM's firewall, security group, or network security group:

*   **Port 22 (SSH)**: To access your VM via terminal (restricted to your IP or VPN).
*   **Port 80 (HTTP)**: To allow users to access the main Employee Portal.
*   **Port 8080 (HTTP)**: To allow administrators to access the phpMyAdmin Web UI (restricted to admin IPs).
*   **Port 3000 (HTTP)**: To access the Grafana Metrics Dashboard (restricted to admin IPs).
*   **Port 9090 (HTTP)**: To access Prometheus raw metrics (restricted to admin IPs).

---

### 1. AWS EC2 Setup

#### Step 1 — Launch Instance
1.  Go to **AWS Console → EC2 → Launch Instance**.
2.  Select **Ubuntu Server 22.04 LTS** as the AMI.
3.  Choose `t3.micro` (small teams) or `t3.small` (larger teams).
4.  Create or select an **SSH key pair** (`.pem` file).
5.  In **Security Groups**, add inbound rules:
    *   `SSH` (Port 22) from your IP.
    *   `HTTP` (Port 80) from `0.0.0.0/0`.
    *   `Custom TCP` (Port 8080) from your IP (for database admin tool).

#### Step 2 — Install Docker & Setup
Connect via SSH and install Docker:
```bash
ssh -i "your-key.pem" ubuntu@<EC2-PUBLIC-IP>

sudo apt-get update
sudo apt-get install -y docker.io docker-compose
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker ubuntu
exit # Log out to apply group permissions
```

#### Step 3 — Deploy
Reconnect and deploy:
```bash
ssh -i "your-key.pem" ubuntu@<EC2-PUBLIC-IP>
git clone https://github.com/leoxurDev/EmployeeManagementTool.git
cd EmployeeManagementTool
bash deploy.sh
```

---

### 2. Azure Virtual Machine Setup

#### Step 1 — Create VM
1.  Go to **Azure Portal → Virtual Machines → Create → Azure Virtual Machine**.
2.  Select **Ubuntu Server 22.04 LTS** as the image.
3.  Set VM size (e.g. `Standard_B1s` or `Standard_B2s`).
4.  Under **Administrator account**, set **SSH public key** authentication.

#### Step 2 — Network Security Group (NSG) Inbound Rules
1.  Go to your VM's **Network settings** tab on Azure.
2.  Click **Add inbound port rule** for Port 80:
    *   `Destination port ranges`: `80`
    *   `Protocol`: `TCP`
    *   `Action`: `Allow`
    *   `Name`: `Port_80_HTTP`
3.  Click **Add inbound port rule** for Port 8080 (phpMyAdmin):
    *   `Source`: `IP Addresses` (restricted to your IP for database security)
    *   `Destination port ranges`: `8080`
    *   `Protocol`: `TCP`
    *   `Action`: `Allow`
    *   `Name`: `Port_8080_phpMyAdmin`

#### Step 3 — Install Docker & Deploy
```bash
ssh -i your-azure-key.pem azureuser@<AZURE-VM-PUBLIC-IP>

# Install Docker
sudo apt-get update
sudo apt-get install -y docker.io docker-compose
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker azureuser
exit

# Reconnect and Deploy
ssh -i your-azure-key.pem azureuser@<AZURE-VM-PUBLIC-IP>
git clone https://github.com/leoxurDev/EmployeeManagementTool.git
cd EmployeeManagementTool
bash deploy.sh
```

---

### 3. GCP Compute Engine Setup

#### Step 1 — Create VM Instance
1.  Go to **GCP Console → Compute Engine → VM Instances → Create Instance**.
2.  Set Boot Disk to **Ubuntu 22.04 LTS**.
3.  Under **Firewall**, check **Allow HTTP traffic**.
4.  Go to **VPC Network → Firewall** and create an ingress rule allowing TCP traffic on port `8080` from your administrative IP ranges.

#### Step 2 — Deploy
Connect via `gcloud` or GCP console terminal:
```bash
# Install Docker
sudo apt-get update && sudo apt-get install -y docker.io docker-compose
sudo usermod -aG docker $USER
exit # Reconnect

# Deploy
git clone https://github.com/leoxurDev/EmployeeManagementTool.git
cd EmployeeManagementTool
bash deploy.sh
```

---

## 🌐 Production Domain & SSL Setup (Nginx + Let's Encrypt)

If you want to host your application on a custom domain (e.g. `your-domain.duckdns.org` or `portal.company.com`) with secure HTTPS/SSL, use the automated script [`deploy_domain.sh`](../deploy_domain.sh).

This script configures a host-level Nginx reverse-proxy to route public traffic (Port 80/443) to the containerized Gunicorn application and automates Let's Encrypt SSL registration.

### Step-by-Step Domain and SSL Configuration:
1.  **Configure Inbound Security Rules**:
    *   Open Port `80` (HTTP) and Port `443` (HTTPS) to the public (`0.0.0.0/0`) on your cloud provider.
2.  **Point DNS Record**:
    *   Point your domain name's `A Record` to the public IP address of your VM.
3.  **Run the Domain Setup Script**:
    ```bash
    sudo ./deploy_domain.sh
    ```
4.  **Interactive Prompts**:
    *   Enter your target domain name (e.g. `your-domain.duckdns.org`).
    *   Enter your email address (required by Let's Encrypt for certificate expiration alerts).
5.  **What the script does**:
    *   Updates the `.env` file with `ALLOWED_HOSTS` and security parameters.
    *   Installs Nginx and Certbot on the host system.
    *   Clears Port 80 container mapping to avoid conflict with Nginx.
    *   Generates the Nginx server configuration under `/etc/nginx/sites-available/employee_management`.
    *   Runs Certbot non-interactively to fetch and install Let's Encrypt certificates.
    *   Restarts the Nginx service and Docker containers to apply the configuration.

---

## 🔄 Updating an Existing Live Deployment

Use these steps to roll out updates to your production or staging server without losing database records:

```bash
# 1. Navigate to the project directory on your cloud server
cd EmployeeManagementTool

# 2. Pull the latest commits from GitHub
git pull origin main

# 3. Rebuild and restart Gunicorn / MySQL containers in background
docker-compose up --build -d

# 4. Apply any new database migrations
docker-compose exec web python manage.py migrate

# 5. Refresh default configurations seeding
docker-compose exec web python manage.py seed_configurations
```

### ⚠️ CRITICAL Warning: Changing Database Credentials
If you modify database variables (`DB_USER`, `DB_PASSWORD`, `DB_NAME`) in `deploy.sh` or `.env`, **re-building containers alone will NOT apply them** because MySQL caches credentials on its persistent volume. The Django web container will attempt to connect using the new credentials but will get **`Access denied`** because the database container is still running the old volume.

If you ever change database credentials:
1.  Stop the containers and **wipe the database volume**:
    ```bash
    docker-compose down -v
    ```
2.  Run the deployment script again to re-initialize MySQL:
    ```bash
    bash deploy.sh
    ```

---

## 🔐 Production Security Checklist

Before exposing your cloud VM to public traffic, ensure the following configurations are updated inside [`employee_attendance/settings.py`](../employee_attendance/settings.py):

1.  **Set `DEBUG = False`**: Disables the detailed Django error diagnostics page, which exposes internal environment variables.
2.  **Generate a new `SECRET_KEY`**: Run this command to generate a unique random string:
    ```bash
    python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
    ```
    Paste the output as `SECRET_KEY` in `settings.py` or `.env`.
3.  **Restrict `ALLOWED_HOSTS`**: Set this to your cloud VM public IP or your domain names, e.g.:
    ```python
    ALLOWED_HOSTS = ['20.219.102.29', 'employee.leoxur.com']
    ```
