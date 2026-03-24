# CareerLens Deployment Guide

## Table of Contents
1. [Local Development with Docker](#local-development)
2. [Production Deployment](#production-deployment)
3. [n8n Workflow Setup](#n8n-setup)
4. [Environment Configuration](#environment-configuration)
5. [Database Migrations](#database-migrations)
6. [Monitoring & Troubleshooting](#monitoring)

---

## Local Development

### Prerequisites
- Docker & Docker Compose (v1.29+)
- Python 3.13+ (for direct development)
- Node.js 20+ (for frontend development)

### Quick Start with Docker Compose

1. **Clone and setup**
   ```bash
   git clone https://github.com/your-org/careerlens.git
   cd careerlens
   cp .env.example .env
   ```

2. **Start all services**
   ```bash
   docker-compose up -d
   ```

3. **Access services**
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - Frontend: http://localhost:3000
   - MySQL: localhost:3306

4. **Run migrations** (automatic on startup)
   ```bash
   # Migrations run automatically when backend starts
   # View logs: docker-compose logs backend
   ```

5. **Stop services**
   ```bash
   docker-compose down
   ```

---

## Production Deployment

### Option 1: AWS ECS with Fargate

**Prerequisites:**
- AWS Account with appropriate IAM permissions
- ECR repositories created for backend and frontend

**Steps:**

1. **Build and push Docker images**
   ```bash
   # Backend
   docker build -t careerlens-backend:v1.0 careerlens-backend/
   docker tag careerlens-backend:v1.0 <AWS_ACCOUNT>.dkr.ecr.<REGION>.amazonaws.com/careerlens-backend:v1.0
   docker push <AWS_ACCOUNT>.dkr.ecr.<REGION>.amazonaws.com/careerlens-backend:v1.0
   
   # Frontend
   docker build -t careerlens-frontend:v1.0 careerlens-frontend/
   docker tag careerlens-frontend:v1.0 <AWS_ACCOUNT>.dkr.ecr.<REGION>.amazonaws.com/careerlens-frontend:v1.0
   docker push <AWS_ACCOUNT>.dkr.ecr.<REGION>.amazonaws.com/careerlens-frontend:v1.0
   ```

2. **Create RDS MySQL instance**
   - Instance class: db.t3.small (minimum)
   - Storage: 20GB
   - Multi-AZ: Yes (for production)
   - Backup retention: 7 days

3. **Create ECS Cluster**
   ```bash
   aws ecs create-cluster --cluster-name careerlens-prod
   ```

4. **Create Task Definition**
   ```bash
   aws ecs register-task-definition --cli-input-json file://ecs-task-definition.json
   ```

5. **Create Service**
   ```bash
   aws ecs create-service \
     --cluster careerlens-prod \
     --service-name careerlens-api \
     --task-definition careerlens-api \
     --desired-count 2 \
     --launch-type FARGATE
   ```

### Option 2: DigitalOcean App Platform

1. **Connect GitHub repository**
   - Push code to GitHub
   - Connect DigitalOcean to GitHub account

2. **Create app.yaml**
   ```yaml
   name: careerlens
   services:
   - name: backend
     github:
       repo: your-org/careerlens
       branch: main
     build_command: pip install -r requirements.txt
     run_command: uvicorn app.main:app --host 0.0.0.0 --port 8080
     http_port: 8080
   
   - name: frontend
     github:
       repo: your-org/careerlens
       branch: main
     build_command: npm ci && npm run build
     run_command: npx serve -s dist -l 8080
     http_port: 8080
   
   databases:
   - name: mysql
     engine: MYSQL
     version: "8"
   ```

3. **Deploy**
   ```bash
   doctl apps create --spec app.yaml
   ```

### Option 3: Kubernetes (Self-hosted or GKE)

1. **Create namespace**
   ```bash
   kubectl create namespace careerlens
   ```

2. **Create ConfigMap for environment**
   ```bash
   kubectl create configmap careerlens-config \
     --from-env-file=.env \
     -n careerlens
   ```

3. **Deploy using Helm**
   ```bash
   helm install careerlens ./helm/careerlens \
     --namespace careerlens \
     --values helm/values-prod.yaml
   ```

---

## n8n Setup

### Local Setup (for development/testing)

1. **Start n8n with docker-compose**
   ```bash
   docker-compose --profile workflows up -d n8n
   ```

2. **Access n8n**
   - URL: http://localhost:5678
   - Default credentials: admin / careerlens123

3. **Import workflows**
   ```bash
   # Workflows are auto-loaded from ./workflows directory
   # Or manually import JSON files through the UI
   ```

### Production n8n Deployment

**Option 1: n8n Cloud (Managed)**
1. Sign up at https://n8n.cloud
2. Create workspace for CareerLens
3. Import workflows from `workflows/` directory
4. Configure credentials:
   - CareerLens API URL
   - MySQL connection
   - Slack webhooks (optional)

**Option 2: Self-hosted**
1. Deploy n8n container with MySQL backend
2. Configure webhooks to CareerLens API
3. Set up workflow triggers
4. Configure notifications (email, Slack, etc.)

### Available Workflows

1. **Batch Resume Analysis**
   - Location: `workflows/n8n-batch-analysis.json`
   - Schedule: Daily at 2 AM
   - Processes pending resumes through CareerLens API
   - Saves results to database

2. **Recruiter Notifications**
   - Location: `workflows/n8n-recruiter-notifications.json`
   - Trigger: On high-fit candidate detection (>75% fit)
   - Sends email alerts to subscribed recruiters
   - Logs notification events

---

## Environment Configuration

### Required Variables

```bash
# Database
DATABASE_URL=mysql+pymysql://user:pass@host:3306/careerlens_db
MYSQL_ROOT_PASSWORD=secure_password
MYSQL_PASSWORD=secure_password

# API
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO

# Frontend
VITE_API_BASE_URL=https://api.careerlens.com

# n8n (optional)
N8N_USER=admin
N8N_PASSWORD=strong_password

# Environment
PYTHON_ENV=production
```

### For AWS Deployment

```bash
# Secrets Manager integration
AWS_REGION=us-east-1
AWS_SECRET_NAME=careerlens/prod/db
AWS_SECRETS_MANAGER_ENABLED=true
```

---

## Database Migrations

### Automatic Migrations

Migrations run automatically when the backend starts:

```bash
# Logs show migration status
docker-compose logs backend | grep -i migration
```

### Manual Migration (if needed)

```bash
# From careerlens-backend directory
cd careerlens-backend

# Apply migrations
python -m alembic upgrade head

# Generate new migration
python -m alembic revision --autogenerate -m "Description"

# Rollback
python -m alembic downgrade -1
```

---

## Monitoring & Troubleshooting

### Health Checks

```bash
# Backend API health
curl http://localhost:8000/health

# Frontend health
curl http://localhost:3000

# Database connection
curl -X GET http://localhost:8000/docs
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f mysql

# With timestamp
docker-compose logs -f --timestamps backend
```

### Common Issues

**Issue: Backend can't connect to MySQL**
```bash
# Check MySQL is running
docker-compose ps mysql

# Check connection
docker exec careerlens-backend \
  python -c "from app.core.database import SessionLocal; SessionLocal()"
```

**Issue: Frontend can't reach API**
- Check VITE_API_BASE_URL is correct
- Verify backend is running: `docker-compose logs backend`
- Check CORS settings in `careerlens-backend/app/main.py`

**Issue: Migrations failing**
- Check database schema: `docker exec careerlens-mysql mysql -u careerlens_user -p careerlens_db`
- Review migration files in `careerlens-backend/alembic/versions/`
- Reset database (dev only): `docker-compose down -v && docker-compose up`

### Performance Tuning

**MySQL**
```yaml
# In docker-compose.yml
environment:
  MYSQL_MAX_CONNECTIONS: 500
  MYSQL_QUERY_CACHE_SIZE: 16M
  MYSQL_INNODB_BUFFER_POOL_SIZE: 1G
```

**Backend (Uvicorn workers)**
```bash
# In docker-compose.yml, change CMD to:
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

---

## Backup & Restore

### MySQL Backup

```bash
# Backup
docker exec careerlens-mysql mysqldump \
  -u careerlens_user -p careerlens_db > backup.sql

# Restore
docker exec -i careerlens-mysql mysql \
  -u careerlens_user -p careerlens_db < backup.sql
```

### ML Model Persistence

```bash
# Backup trained models
docker cp careerlens-backend:/app/ml_models ./ml_models_backup

# Restore
docker cp ./ml_models_backup careerlens-backend:/app/ml_models
```

---

## Support & Documentation

- **API Docs**: http://your-domain/docs
- **GitHub Issues**: https://github.com/your-org/careerlens/issues
- **Wiki**: https://github.com/your-org/careerlens/wiki
