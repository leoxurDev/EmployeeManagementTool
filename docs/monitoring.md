# 📈 Monitoring Stack Guide

The application includes a fully containerized monitoring suite to track system health, host resource usage, and container performance metrics.

---

## 📑 Stack Components

The monitoring stack is isolated on a bridge network named `monitoring` and consists of:

1.  **Prometheus**: The core metrics database that scrapes and stores time-series metrics.
2.  **Grafana**: The visualization dashboard UI that connects to Prometheus to render graphs and panels.
3.  **cAdvisor**: Google cAdvisor collects and exposes resource usage and performance metrics for all active Docker containers on the host.
4.  **Node Exporter**: Prometheus Node Exporter collects host machine OS metrics (CPU, Memory, Disk, and Network utilization).

---

## 🔗 Port Mappings & Services

| Service | Host Port | Internal Port | Description |
| --- | --- | --- | --- |
| **Grafana** | `3000` | `3000` | Visualization dashboard interface. |
| **Prometheus** | `9090` | `9090` | Time-series query console. |
| **cAdvisor** | `8081` | `8080` | Container resource analytics viewer. |
| **Node Exporter** | `9100` | `9100` | Host metrics exporter. |

---

## 🔑 Access Credentials

*   **Grafana URL**: `http://<SERVER-IP>:3000/`
*   **Grafana Username**: `admin`
*   **Grafana Password**: Refer to the `GF_SECURITY_ADMIN_PASSWORD` variable defined inside the `grafana` service block in `docker-compose.yml`.

---

## 📊 Pre-Provisioned Dashboards

Grafana is pre-configured to automatically load these dashboards from the [`grafana-provisioning/dashboards/json/`](./grafana-provisioning/dashboards/json/) directory:

1.  **Employee Management Tool - Monitoring Dashboard**:
    *   Visualizes core database and application container CPU/RAM resource rates.
    *   Tracks container status and restarts.
2.  **Docker Containers Monitoring Dashboard**:
    *   Provides high-resolution graphs for individual container network throughput, filesystem I/O, memory limit cache consumption, and thread context switches.

---

## 🛠️ Configurations reference

*   **Scraping targets**: Defined inside [`prometheus.yml`](../prometheus.yml) at the project root.
*   **Auto-Datasources**: Registered via [`grafana-provisioning/datasources/datasource.yml`](../grafana-provisioning/datasources/datasource.yml), which binds the Prometheus database to Grafana automatically.
*   **Dashboard Provider**: Registered via [`grafana-provisioning/dashboards/dashboard.yml`](../grafana-provisioning/dashboards/dashboard.yml) to scan for JSON schemas.

---

## 📋 Troubleshooting Commands

To inspect the health and logs of the monitoring services:

```bash
# Check status of monitoring containers
docker-compose ps

# View cAdvisor container logs
docker-compose logs -f cadvisor

# View Prometheus collection logs
docker-compose logs -f prometheus

# View Grafana rendering logs
docker-compose logs -f grafana
```

---

## 🔔 Gmail Alerting Configuration Setup

The monitoring stack includes **Prometheus Alertmanager**, which is pre-configured to send high-priority alerts to your Gmail account when resource thresholds are breached or when a container stops.

### Step-by-Step Gmail Alerting Configuration:
1.  **Generate a Google App Password**:
    Alertmanager cannot log in with your primary Google password. You must generate an App Password:
    *   Go to [Google My Account](https://myaccount.google.com/).
    *   Navigate to **Security** → **2-Step Verification** (ensure 2-step verification is enabled).
    *   Scroll to the bottom, select **App passwords**, and create a new application named `Alertmanager`.
    *   Copy the generated **16-character code** (ignoring spaces).
2.  **Run the Alerts Setup Script**:
    On your cloud VM terminal, run:
    ```bash
    ./setup_alerts.sh
    ```
3.  **Interactive Prompts**:
    *   Enter the sender Gmail address (e.g. `sender@gmail.com`).
    *   Enter the copied 16-character Gmail App Password.
    *   Enter the recipient email address (where you want alerts to be sent).
4.  **What the script does**:
    *   Generates a custom `alertmanager.yml` file from the [template](../alertmanager.yml.template).
    *   Applies a professional, branded HTML layout matching the **EMS Portal** color scheme.
    *   Restarts the Alertmanager container.

---

## 📈 Alert Rules & Thresholds

Alerts are defined inside [`prometheus_rules.yml`](../prometheus_rules.yml) and trigger under the following conditions:

| Alert Name | Metric Expression | Threshold | Duration (`for`) | Severity |
| --- | --- | --- | --- | --- |
| **ContainerCPUHigh** | `sum(rate(container_cpu_usage_seconds_total))` | `>= 80%` of host capacity | `30 seconds` | Warning |
| **ContainerMemoryHigh** | `container_memory_working_set_bytes` | `>= 80%` of host memory | `30 seconds` | Warning |
| **ContainerDown** | `time() - last_over_time(container_last_seen[1h])` | Container missing | `30 seconds` + `10s eval` | Critical |

*Note: The `last_over_time[1h]` function ensures that stopped/absent containers are successfully remembered and alert trigger evaluation remains active even after cAdvisor stops exporting their metrics.*

---

## 🧪 Testing Your Alert Pipeline

To confirm that both alerts and **Resolved** emails are working correctly:

### Test 1 — Triggering a manual alert (Instant)
Run this command from your terminal to post a dummy test alert to the Alertmanager REST API:
```bash
curl -H "Content-Type: application/json" -d '[
  {
    "labels": {
      "alertname": "EMSSystemCheck",
      "severity": "critical"
    },
    "annotations": {
      "summary": "Manual EMS alert system diagnostic check",
      "description": "This is a diagnostic alert to verify that the EMS Portal style and HTML templates are rendering correctly in Alertmanager."
    }
  }
]' http://localhost:9093/api/v2/alerts
```
Check your inbox after 15 seconds. You should receive a clean, styled HTML email with the subject: `[FIRING] EMSSystemCheck — EMS Portal`.

### Test 2 — Triggering a real Container DOWN alert
1.  Stop the phpMyAdmin container:
    ```bash
    docker-compose stop employee_manage_pma
    ```
2.  Wait **45 seconds**. You will receive an email notifying you that `employee_manage_pma` is down.
3.  Start the container back up:
    ```bash
    docker-compose start employee_manage_pma
    ```
4.  Wait **30 seconds**. You will receive an automatic **RESOLVED** email!

