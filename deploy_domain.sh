#!/bin/bash
# =============================================================================
#  Leoxur Employee Management Portal — Custom Domain & SSL Deployment Script
#  Run this script on the server to configure a domain name and SSL (HTTPS).
#  Usage: sudo bash deploy_domain.sh
# =============================================================================

set -e

# Make sure the script is run as root or with sudo
if [ "$EUID" -ne 0 ]; then
    echo "  ❌  Error: Please run this script with sudo or as root."
    exit 1
fi

echo ""
echo "============================================================"
echo "  Employee Time & Management Portal — Domain & SSL Setup"
echo "============================================================"
echo ""

# --- Prompt for Domain Name ---
while true; do
    read -p "  Enter your domain name (e.g. employee.leoxur.com): " DOMAIN
    DOMAIN="$(echo "$DOMAIN" | xargs | tr '[:upper:]' '[:lower:]')" # trim and lowercase
    if [ -n "$DOMAIN" ]; then
        break
    fi
    echo "  ⚠️  Domain name cannot be empty. Please try again."
done

# --- Prompt for SSL Email ---
while true; do
    read -p "  Enter email address for SSL certificate renewal alerts: " EMAIL
    EMAIL="$(echo "$EMAIL" | xargs)"
    if [ -n "$EMAIL" ]; then
        break
    fi
    echo "  ⚠️  Email address cannot be empty. Please try again."
done

echo ""
echo "  ✅  Domain Name: $DOMAIN"
echo "  ✅  Admin Email: $EMAIL"
echo ""

# --- Check/Install Nginx & Certbot ---
echo "  📦  Checking for Nginx and Certbot dependencies..."
if ! command -v nginx >/dev/null 2>&1; then
    echo "  ... Nginx not found. Installing Nginx..."
    apt-get update
    apt-get install -y nginx
fi
if ! command -v certbot >/dev/null 2>&1; then
    echo "  ... Certbot not found. Installing Certbot and python3-certbot-nginx..."
    apt-get update
    apt-get install -y certbot python3-certbot-nginx
fi
echo "  ✅  Dependencies verified."
echo ""

# --- Modify docker-compose.yml to free up Port 80 ---
echo "  🐳  Adjusting Docker container port mapping to free up port 80 for Nginx..."
if [ -f docker-compose.yml ]; then
    # We want to replace "- \"80:8000\"" or "- 80:8000" with "- \"127.0.0.1:8000:8000\""
    # This maps container 8000 to host localhost:8000 so Nginx can proxy to it
    if grep -q '"80:8000"' docker-compose.yml || grep -q ' - 80:8000' docker-compose.yml || grep -q ' - "80:8000"' docker-compose.yml; then
        sed -i.bak -E 's/- ("?)80:8000("?)/- "127.0.0.1:8000:8000"/g' docker-compose.yml
        echo "  ✅  docker-compose.yml port mappings updated to 127.0.0.1:8000:8000."
    else
        echo "  ℹ️   Port 80 mapping not found or already modified in docker-compose.yml. Skipping replacement."
    fi
else
    echo "  ❌  Error: docker-compose.yml not found in the current directory."
    exit 1
fi

# --- Add domain to .env as ALLOWED_HOSTS ---
echo "  📄  Configuring environment variables..."
if [ -f .env ]; then
    # Remove existing ALLOWED_HOSTS line if present
    sed -i.bak '/^ALLOWED_HOSTS=/d' .env
    echo "ALLOWED_HOSTS=localhost,127.0.0.1,$DOMAIN" >> .env
    echo "  ✅  .env file updated with ALLOWED_HOSTS."
else
    echo "ALLOWED_HOSTS=localhost,127.0.0.1,$DOMAIN" > .env
    echo "  ✅  .env file created with ALLOWED_HOSTS."
fi
echo ""

# --- Apply Nginx Configuration ---
echo "  🔧  Creating Nginx reverse proxy configuration..."
NGINX_CONF="/etc/nginx/sites-available/employee_management"

cat > "$NGINX_CONF" <<EOF
server {
    listen 80;
    server_name $DOMAIN;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        client_max_body_size 20M;
    }
}
EOF

# Enable the configuration
ln -sf "$NGINX_CONF" /etc/nginx/sites-enabled/
# Remove default nginx config if active to avoid conflicts
rm -f /etc/nginx/sites-enabled/default

# Test Nginx config
nginx -t

# Reload Nginx to apply changes
systemctl reload nginx
echo "  ✅  Nginx proxy for HTTP established."
echo ""

# --- Restart Docker Containers ---
echo "  🔄  Restarting docker containers with new port configuration..."
if command -v docker-compose >/dev/null 2>&1; then
    docker-compose down || true
    docker-compose up -d --build
elif docker compose version >/dev/null 2>&1; then
    docker compose down || true
    docker compose up -d --build
else
    echo "  ⚠️   docker-compose command not found. Please restart your containers manually."
fi
echo "  ✅  Docker containers restarted."
echo ""

# --- Request SSL Certificate using Certbot ---
echo "  🔒  Securing your domain with Let's Encrypt SSL certificate..."
# Run certbot with nginx plugin
certbot --nginx -d "$DOMAIN" --email "$EMAIL" --agree-tos --no-eff-email --non-interactive --redirect

echo ""
echo "============================================================"
echo "  ✅  Setup complete!"
echo "  Your site is now securely running at: https://$DOMAIN"
echo "============================================================"
echo ""
