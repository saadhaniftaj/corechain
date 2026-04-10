# Deploy Dashboard Fix to AWS

## Problem
The aggregator dashboard at http://54.173.119.88 is showing "Backend not running" error because the frontend code is still using the old hardcoded port 8000 instead of relative paths.

## What Was Fixed
Changed `dashboard/index.html` line 739-741 from:
```javascript
const API_URL = window.location.hostname === 'localhost'
    ? 'http://localhost:8000'
    : `http://${window.location.hostname}:8000`;
```

To:
```javascript
// Use relative paths - nginx on port 80 proxies /api/* to backend
const API_URL = '';
```

## Verification
- ✅ Fix committed to GitHub (commit 76bb227)
- ✅ Pushed to https://github.com/saadhaniftaj/corechain.git
- ❌ Not yet deployed to AWS server

## Deployment Steps

### Option 1: SSH and Update (Recommended)
```bash
# SSH into AWS server
ssh -i /path/to/your-key.pem ubuntu@54.173.119.88

# Navigate to project directory
cd /home/ubuntu/corechain

# Pull latest changes
git pull origin main

# Copy updated dashboard to nginx web root
sudo cp dashboard/index.html /var/www/html/index.html

# Verify the file was updated
grep "Use relative paths" /var/www/html/index.html

# Clear browser cache and reload
# No need to restart nginx - just refresh browser
```

### Option 2: Direct File Copy (If you have SSH key)
```bash
# From your local machine
scp -i /path/to/your-key.pem \
    /Users/applestore/Desktop/corechain/dashboard/index.html \
    ubuntu@54.173.119.88:/tmp/index.html

# Then SSH and move it
ssh -i /path/to/your-key.pem ubuntu@54.173.119.88
sudo mv /tmp/index.html /var/www/html/index.html
```

### Option 3: Docker Container Update (If using Docker)
```bash
# SSH into server
ssh -i /path/to/your-key.pem ubuntu@54.173.119.88

# Update code
cd /home/ubuntu/corechain
git pull origin main

# Rebuild and restart container
docker-compose down
docker-compose build aggregator
docker-compose up -d aggregator
```

## Verification After Deployment

1. **Clear browser cache** (Ctrl+Shift+R or Cmd+Shift+R)
2. Navigate to http://54.173.119.88
3. Dashboard should show:
   - Status: **running** (green badge)
   - Connected Hospitals: **1 / 1**
   - Current Round: **2 / 10**
   - Training status metrics

## Current API Status (Working)
The API is already working correctly:
```json
{
  "status": "running",
  "fl_status": "training",
  "connected_hospitals": 1,
  "total_hospitals": 1,
  "current_round": 2,
  "total_rounds": 10,
  "last_update": "2026-02-08T23:57:46"
}
```

## Next Steps
1. Deploy the fix using one of the options above
2. Clear browser cache
3. Refresh dashboard
4. Verify metrics are displayed correctly
5. Ready for presentation!
