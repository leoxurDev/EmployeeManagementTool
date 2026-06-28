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
