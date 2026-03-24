# CareerLens n8n Workflows

Automated workflow definitions for CareerLens batch processing, notifications, and reporting tasks.

## Overview

n8n is an open-source workflow automation tool that enables complex integrations between CareerLens API and external systems like:
- Database operations (MySQL)
- Email notifications
- Slack alerts
- Scheduled tasks
- API orchestration

## Workflows

### 1. Batch Resume Analysis
**File:** `n8n-batch-analysis.json`

**Purpose:** Automatically processes pending resumes through the CareerLens analysis pipeline

**Flow:**
1. Fetch pending resumes from database
2. Run hybrid analysis (ESCO + O*NET) for each resume
3. Get ML fit probability score using trained model
4. Save analysis results to database
5. Send Slack notification upon completion

**Trigger:** Manual or scheduled (daily 2 AM)

**Configuration needed:**
- CareerLens API endpoint URL
- MySQL connection credentials
- Slack webhook URL (for notifications)

**Usage:**
```bash
# Import workflow into n8n UI
1. Go to Workflows → Import
2. Select this JSON file
3. Configure credentials
4. Enable workflow
```

### 2. Recruiter Fit Notifications
**File:** `n8n-recruiter-notifications.json`

**Purpose:** Notify recruiters when high-fit candidates are identified

**Flow:**
1. Trigger on new high-fit analysis result (fit_probability > 0.75)
2. Fetch candidate resume details
3. Find recruiters subscribed to that job role
4. Send personalized email notification
5. Log notification in database

**Trigger:** Automatic (database trigger on insertion)

**Configuration needed:**
- MySQL connection
- Email service credentials (SMTP or SES)
- Recruiter subscription list

**Usage:**
```bash
# After importing:
1. Configure email credentials
2. Set up recruiter subscription mechanism
3. Enable trigger
```

## Installation & Setup

### Local Development

1. **Start n8n with docker-compose**
   ```bash
   docker-compose --profile workflows up -d n8n
   ```

2. **Access n8n**
   - URL: http://localhost:5678
   - Username: admin
   - Password: careerlens123 (change in production!)

3. **Import workflows**
   ```bash
   # Option A: Auto-import (workflows in ./workflows/)
   # Option B: Manual UI import
   # Go to Workflows → Import → select JSON file
   ```

### Production Setup

#### Option 1: n8n Cloud (Recommended for managed service)
1. Sign up at https://n8n.cloud
2. Create new workspace for CareerLens
3. Upload workflow JSONs through UI
4. Configure credentials securely

#### Option 2: Self-hosted on VPS/Docker
```bash
# Deploy with persistent MySQL backend
docker-compose --profile workflows up -d n8n

# Configure environment
export N8N_USER=admin
export N8N_PASSWORD=<strong_password>
export N8N_HOST=workflow.careerlens.com
export DB_MYSQLDB_HOST=mysql-prod.example.com
```

## Workflow Configuration

### Prerequisites

Before importing workflows, ensure:
1. ✅ CareerLens backend is running
2. ✅ MySQL database is accessible
3. ✅ Required credentials are available

### Credentials to Configure

#### MySQL Credentials
```
Host: localhost (or MySQL server)
Port: 3306
Username: careerlens_user
Password: careerlens_pass
Database: careerlens_db
```

#### CareerLens API
```
Base URL: http://localhost:8000
Endpoints needed:
  - POST /analyze/hybrid
  - POST /ml-fit/score
  - GET /resumes/{id}
```

#### Email (for notifications)
```
Service: SMTP or AWS SES
From: notifications@careerlens.com
SMTP Server: smtp.example.com:587
Username/Password: (your email provider)
```

#### Slack (optional)
```
Webhook URL: https://hooks.slack.com/services/YOUR/WEBHOOK/URL
Channel: #careerlens-notifications
```

## Running Workflows

### Manual Execution
1. Open n8n UI
2. Select workflow
3. Click "Execute Workflow" button
4. Monitor execution in real-time

### Scheduled Execution
Workflows support multiple trigger types:

**Daily Schedule (Batch Analysis)**
```
Time: 2:00 AM UTC
Frequency: Every day
```

**Event-Based (Recruiter Notifications)**
```
Trigger: New insert into analysis_results table
Condition: fit_probability > 0.75
```

### API Webhook Triggers
The workflows can also be triggered via HTTP webhooks:

```bash
# Example webhook trigger
curl -X POST http://localhost:5678/webhook/careerlens-batch \
  -H "Content-Type: application/json" \
  -d '{"action": "start_analysis"}'
```

## Monitoring & Debugging

### View Execution Logs
```
n8n UI → Workflows → [Select Workflow] → Execution History
```

### Common Issues

**Connection failures**
- Verify MySQL server is running: `docker ps | grep mysql`
- Test API connectivity: `curl http://localhost:8000/docs`
- Check network connectivity between containers

**Workflow hangs**
- Check for circular references in flow
- Review timeout settings (default: 300s)
- Check database connection pool

**Email not sent**
- Verify SMTP credentials
- Check "From" email address is valid
- Review email logs in n8n execution history

## Best Practices

### Security
- 🔐 Use strong passwords for n8n admin
- 🔐 Store credentials in n8n vault (not in workflow JSON)
- 🔐 Use environment variables for sensitive values
- 🔐 Enable HTTPS in production

### Performance
- ⚡ Batch process up to 500 resumes per run
- ⚡ Schedule non-urgent workflows during off-peak hours
- ⚡ Use database indexes for fast queries
- ⚡ Monitor execution times and optimize as needed

### Maintenance
- 📋 Keep workflow documentation updated
- 📋 Version control workflow JSONs
- 📋 Test workflows after database schema changes
- 📋 Regularly backup workflow definitions

## Extending Workflows

### Add New Notification Type

1. Clone an existing workflow
2. Modify the notification node:
   ```json
   {
     "name": "Send Webhook",
     "type": "n8n-nodes-base.webhook",
     "url": "https://external-service.com/notify",
     "method": "POST"
   }
   ```
3. Test with sample data
4. Deploy to production

### Add Conditional Logic

```json
{
  "name": "If-Else Check",
  "type": "n8n-nodes-base.if",
  "conditions": {
    "condition": "fit_probability > 0.8"
  }
}
```

## API Reference

### Workflow Execution
```
GET  /api/workflows              - List all workflows
GET  /api/workflows/{id}          - Get workflow details
POST /api/workflows/{id}/execute  - Execute workflow
GET  /api/workflows/{id}/history  - View execution history
```

### Credentials
```
GET  /api/credentials             - List credentials
POST /api/credentials             - Create credential
```

## Support

- **n8n Documentation**: https://docs.n8n.io
- **CareerLens API Docs**: http://localhost:8000/docs
- **GitHub Issues**: https://github.com/your-org/careerlens/issues

## License

These workflow definitions are part of CareerLens project and follow the same license terms.
