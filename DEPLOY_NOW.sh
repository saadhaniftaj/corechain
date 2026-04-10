#!/bin/bash
# One-Command Dashboard Deployment
# Just copy and paste this entire command into your terminal

echo "🚀 Deploying dashboard fix to AWS..."
echo ""
echo "Copy and paste this command:"
echo ""
echo "---START COPY HERE---"
cat << 'EOF'
ssh ubuntu@54.173.119.88 'bash -s' << 'ENDSSH'
cd /home/ubuntu/corechain 2>/dev/null || cd /var/www/corechain 2>/dev/null || cd ~/corechain
git pull origin main
sudo cp dashboard/index.html /var/www/html/index.html
echo "✅ Dashboard deployed! Clear browser cache and refresh: http://54.173.119.88"
ENDSSH
EOF
echo "---END COPY HERE---"
echo ""
echo "After running the command above:"
echo "1. Clear browser cache (Ctrl+Shift+R or Cmd+Shift+R)"
echo "2. Refresh http://54.173.119.88"
echo "3. Dashboard will work permanently!"
