#!/bin/bash
# Setup script to install costume detector as a systemd service

echo "🎃 Halloween Costume Detector - Service Setup"
echo "=============================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Please run with sudo: sudo ./setup-service.sh"
    exit 1
fi

# Copy service file to systemd directory
echo "📋 Copying service file..."
cp costume-detector.service /etc/systemd/system/

# Reload systemd daemon
echo "🔄 Reloading systemd..."
systemctl daemon-reload

# Enable service to start on boot
echo "✅ Enabling service..."
systemctl enable costume-detector.service

echo ""
echo "✅ Setup complete!"
echo ""
echo "📝 Useful commands:"
echo "   Start:   sudo systemctl start costume-detector"
echo "   Stop:    sudo systemctl stop costume-detector"
echo "   Status:  sudo systemctl status costume-detector"
echo "   Logs:    tail -f ~/costume-detector.log"
echo "   Errors:  tail -f ~/costume-detector-error.log"
echo ""
echo "🎃 Ready for Halloween! The service will auto-start on boot and restart if it crashes."
