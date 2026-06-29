#!/bin/bash
# =============================================================================
#  Leoxur Employee Management Portal — Alerts Config Setup
#  Run this script on the server to configure Gmail alerting.
#  Usage: bash setup_alerts.sh
# =============================================================================

set -e

echo ""
echo "============================================================"
echo "  Employee Time & Management Portal — Gmail Alerting Setup"
echo "============================================================"
echo ""
echo "  This script configures Prometheus Alertmanager to send container"
echo "  CPU/Memory alerts (>80%) to your Gmail account."
echo ""
echo "  💡 IMPORTANT: Google requires an 'App Password' for SMTP access."
echo "  To generate one:"
echo "  1. Go to https://myaccount.google.com/"
echo "  2. Go to Security -> 2-Step Verification (must be enabled)."
echo "  3. Scroll to the bottom and select 'App passwords'."
echo "  4. Create a new App Password (e.g., name it 'Alertmanager')."
echo "  5. Copy the 16-character code generated."
echo "============================================================"
echo ""

# --- Prompt for SMTP Email ---
while true; do
    read -p "  Enter your sender Gmail address (e.g. sender@gmail.com): " SMTP_EMAIL
    SMTP_EMAIL="$(echo "$SMTP_EMAIL" | xargs)"
    if [ -n "$SMTP_EMAIL" ]; then
        break
    fi
    echo "  ⚠️  Gmail address cannot be empty. Please try again."
done

# --- Prompt for SMTP App Password ---
while true; do
    read -sp "  Enter your 16-character Gmail App Password: " SMTP_PASSWORD
    echo ""
    SMTP_PASSWORD="$(echo "$SMTP_PASSWORD" | xargs | tr -d ' ')" # remove spaces if copy-pasted
    if [ -n "$SMTP_PASSWORD" ]; then
        break
    fi
    echo "  ⚠️  App Password cannot be empty. Please try again."
done

# --- Prompt for Recipient Email ---
while true; do
    read -p "  Enter recipient email address (where alerts should be sent): " RECIPIENT_EMAIL
    RECIPIENT_EMAIL="$(echo "$RECIPIENT_EMAIL" | xargs)"
    if [ -n "$RECIPIENT_EMAIL" ]; then
        break
    fi
    echo "  ⚠️  Recipient email cannot be empty. Please try again."
done

echo ""
echo "  📄  Generating alertmanager.yml..."
if [ -f alertmanager.yml.template ]; then
    # Create alertmanager.yml replacing placeholders
    cp alertmanager.yml.template alertmanager.yml
    
    # Use different sed delimiter (e.g. |) to avoid slash conflicts with email addresses
    sed -i.bak "s|SMTP_EMAIL_PLACEHOLDER|$SMTP_EMAIL|g" alertmanager.yml
    sed -i.bak "s|SMTP_PASSWORD_PLACEHOLDER|$SMTP_PASSWORD|g" alertmanager.yml
    sed -i.bak "s|RECIPIENT_EMAIL_PLACEHOLDER|$RECIPIENT_EMAIL|g" alertmanager.yml
    rm -f alertmanager.yml.bak
    
    echo "  ✅  Generated alertmanager.yml successfully."
else
    echo "  ❌  Error: alertmanager.yml.template not found in the current directory."
    exit 1
fi

echo ""
echo "  🔄  Restarting Docker containers to apply alert configurations..."
if command -v docker-compose >/dev/null 2>&1; then
    docker-compose down || true
    docker-compose up -d --build
elif docker compose version >/dev/null 2>&1; then
    docker compose down || true
    docker compose up -d --build
else
    echo "  ⚠️  docker-compose not found. Please restart containers manually."
fi

echo ""
echo "============================================================"
echo "  🎉 Gmail alerting system configured successfully!"
echo "  - Alertmanager Web UI: http://localhost:9093"
echo "  - Prometheus Web UI: http://localhost:9090 (check 'Alerts' tab)"
echo "============================================================"
echo ""
