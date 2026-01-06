#!/bin/bash
# Railway QuestDB Setup Script
# Configures QuestDB to work with Railway's HTTP domain

set -e

echo "============================================================"
echo "Railway QuestDB HTTP Access Setup"
echo "============================================================"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "⚠ This script should be run as root on Railway"
    echo "  Run: sudo bash railway_questdb_setup.sh"
    exit 1
fi

# Set JAVA_HOME if not set
if [ -z "$JAVA_HOME" ]; then
    JAVA_PATH=$(readlink -f /usr/bin/java | sed "s:bin/java::")
    export JAVA_HOME=$JAVA_PATH
    echo "export JAVA_HOME=$JAVA_PATH" >> ~/.bashrc
    echo "✓ JAVA_HOME set to: $JAVA_HOME"
fi

# Check if QuestDB is running
if questdb status &> /dev/null; then
    echo "✓ QuestDB is running"
    QUESTDB_RUNNING=true
else
    echo "⚠ QuestDB is not running"
    QUESTDB_RUNNING=false
fi

echo ""
echo "Choose setup method:"
echo "  1) Install nginx reverse proxy (port 80 → 9000) [Recommended]"
echo "  2) Configure QuestDB to listen on port 80"
echo "  3) Just verify current setup"
echo ""
read -p "Enter choice (1-3): " choice

case $choice in
    1)
        echo ""
        echo "Installing nginx reverse proxy..."
        
        # Install nginx
        apt-get update
        apt-get install -y nginx
        
        # Create nginx config
        cat > /etc/nginx/sites-available/default << 'NGINX_EOF'
server {
    listen 80;
    server_name _;
    
    location / {
        proxy_pass http://127.0.0.1:9000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support (if QuestDB uses it)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
NGINX_EOF
        
        # Test nginx config
        nginx -t
        
        # Start nginx
        systemctl enable nginx
        systemctl restart nginx
        
        echo "✓ nginx installed and configured"
        echo ""
        echo "IMPORTANT: Update Railway dashboard:"
        echo "  - Go to Networking → HTTP Domain"
        echo "  - Change port from 9000 to 80"
        echo "  - Save changes"
        echo ""
        echo "Then access: http://dexextractor.up.railway.app"
        ;;
        
    2)
        echo ""
        echo "Configuring QuestDB to listen on port 80..."
        
        # Stop QuestDB if running
        if [ "$QUESTDB_RUNNING" = true ]; then
            questdb stop
            echo "✓ QuestDB stopped"
        fi
        
        # Start QuestDB on port 80
        # Note: QuestDB may need root to bind to port 80, or use setcap
        questdb start -d ~/.questdb -p 80
        
        echo "✓ QuestDB started on port 80"
        echo ""
        echo "IMPORTANT: Update Railway dashboard:"
        echo "  - Go to Networking → HTTP Domain"
        echo "  - Change port from 9000 to 80"
        echo "  - Save changes"
        echo ""
        echo "Then access: http://dexextractor.up.railway.app"
        ;;
        
    3)
        echo ""
        echo "Verifying current setup..."
        echo ""
        
        # Check QuestDB status
        if questdb status &> /dev/null; then
            echo "✓ QuestDB is running"
            questdb status
        else
            echo "✗ QuestDB is not running"
        fi
        
        echo ""
        echo "Checking ports..."
        netstat -tulpn | grep -E ":(80|9000)" || echo "No services listening on ports 80 or 9000"
        
        echo ""
        echo "Current Railway configuration:"
        echo "  HTTP Domain: dexextractor.up.railway.app → Port 9000 (won't work for HTTP)"
        echo "  TCP Proxy: ballast.proxy.rlwy.net:16681 → Port 9000 (TCP only)"
        echo ""
        echo "To fix: Change HTTP domain port to 80 and use one of the options above"
        ;;
        
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "============================================================"




