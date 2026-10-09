# SmartTrendTracer Deployment Guide

## Development Setup

### Prerequisites

- Python 3.10+ (tested with 3.12)
- Node.js 16+
- SQLite3
- Git

### Environment Variables

Create `backend/.env`:
```bash
# Twitter API
TWITTER_BEARER_TOKEN=your_twitter_bearer_token_here

# OpenAI API
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_ORG_ID=optional_org_id

# Application Settings
DATABASE_URL=sqlite:///data/tweets.db
LOG_LEVEL=INFO
ENVIRONMENT=development

# Server Settings
HOST=0.0.0.0
PORT=8000
RELOAD=true
```

## Local Development

### Using the Setup Script

```bash
# Make setup script executable
chmod +x setup_python.sh

# Run setup
./setup_python.sh
```

### Manual Setup

1. **Backend Setup**
```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Initialize database
python -m app.models.database

# Run migrations (if any)
alembic upgrade head
```

2. **Frontend Setup**
```bash
cd frontend

# Install dependencies
npm install --legacy-peer-deps

# Build for production
npm run build
```

## Production Deployment

### Option 1: Docker Deployment

Create `docker-compose.yml`:
```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=sqlite:///data/tweets.db
      - ENVIRONMENT=production
    volumes:
      - ./data:/app/data
      - ./backend/.env:/app/.env
    restart: unless-stopped

  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - backend
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - frontend
      - backend
    restart: unless-stopped
```

Create `backend/Dockerfile`:
```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directory
RUN mkdir -p /app/data

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Create `frontend/Dockerfile`:
```dockerfile
FROM node:18-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./
RUN npm ci --legacy-peer-deps

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built files
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

### Option 2: systemd Service (Linux)

Create `/etc/systemd/system/smarttrendtracer.service`:
```ini
[Unit]
Description=SmartTrendTracer Backend
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/smarttrendtracer/backend
Environment="PATH=/opt/smarttrendtracer/backend/venv/bin"
ExecStart=/opt/smarttrendtracer/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable smarttrendtracer
sudo systemctl start smarttrendtracer
sudo systemctl status smarttrendtracer
```

### Option 3: PM2 Process Manager

```bash
# Install PM2
npm install -g pm2

# Start backend
cd backend
pm2 start "uvicorn app.main:app --host 0.0.0.0 --port 8000" --name smarttrendtracer-backend

# Start frontend
cd ../frontend
pm2 start "npm run preview" --name smarttrendtracer-frontend

# Save PM2 configuration
pm2 save
pm2 startup
```

## Nginx Configuration

Create `/etc/nginx/sites-available/smarttrendtracer`:
```nginx
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket support
    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/smarttrendtracer /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## SSL Certificate

Using Let's Encrypt:
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

## Database Management

### Backup

```bash
# Create backup
sqlite3 data/tweets.db ".backup data/backup/tweets_$(date +%Y%m%d).db"

# Automated daily backup (crontab)
0 2 * * * sqlite3 /opt/smarttrendtracer/data/tweets.db ".backup /opt/smarttrendtracer/data/backup/tweets_$(date +\%Y\%m\%d).db"
```

### Restore

```bash
# Restore from backup
sqlite3 data/tweets.db ".restore data/backup/tweets_20250108.db"
```

### Migration

```bash
# Generate new migration
cd backend
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Monitoring

### Health Checks

```bash
# Check backend health
curl http://localhost:8000/api/health

# Check frontend
curl http://localhost:3000

# Check database size
du -h data/tweets.db
```

### Logging

Configure logging in `backend/app/main.py`:
```python
import logging
from logging.handlers import RotatingFileHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler('logs/app.log', maxBytes=10485760, backupCount=5),
        logging.StreamHandler()
    ]
)
```

### Monitoring with Prometheus

Add to `backend/requirements.txt`:
```
prometheus-fastapi-instrumentator==5.9.1
```

Add to `backend/app/main.py`:
```python
from prometheus_fastapi_instrumentator import Instrumentator

# Add after app creation
Instrumentator().instrument(app).expose(app)
```

## Performance Optimization

### Database Optimization

```sql
-- Create indexes for common queries
CREATE INDEX idx_tweets_created_at ON tweets(created_at);
CREATE INDEX idx_tweets_author ON tweets(author_username);
CREATE INDEX idx_tags_name ON tags(name);
CREATE INDEX idx_tweet_tags_tweet_id ON tweet_tags(tweet_id);

-- Vacuum and analyze
VACUUM;
ANALYZE;
```

### Caching

Add Redis for caching:
```bash
# Install Redis
sudo apt install redis-server

# Add to requirements.txt
redis==5.0.1
```

Configure in backend:
```python
import redis
from functools import lru_cache

# Redis connection
redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)

# Cache decorator
def cache_result(ttl=3600):
    def decorator(func):
        def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
            result = func(*args, **kwargs)
            redis_client.setex(cache_key, ttl, json.dumps(result))
            return result
        return wrapper
    return decorator
```

## Scheduled Tasks

### Cron Jobs

```bash
# Edit crontab
crontab -e

# Collect tweets every hour
0 * * * * cd /opt/smarttrendtracer/backend && /opt/smarttrendtracer/backend/venv/bin/python -m app.collectors.smart_collector

# Generate trends every 6 hours
0 */6 * * * cd /opt/smarttrendtracer/backend && /opt/smarttrendtracer/backend/venv/bin/python -m app.analyzers.trend_analyzer

# Daily backup at 2 AM
0 2 * * * sqlite3 /opt/smarttrendtracer/data/tweets.db ".backup /opt/smarttrendtracer/data/backup/tweets_$(date +\%Y\%m\%d).db"

# Weekly cleanup of old logs
0 3 * * 0 find /opt/smarttrendtracer/logs -name "*.log" -mtime +30 -delete
```

### Using APScheduler

Already included in requirements. Configure in `backend/app/scheduler.py`:
```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

scheduler = AsyncIOScheduler()

# Add jobs
scheduler.add_job(
    collect_tweets,
    trigger=IntervalTrigger(hours=1),
    id='collect_tweets',
    name='Collect new tweets',
    replace_existing=True
)

scheduler.add_job(
    analyze_trends,
    trigger=IntervalTrigger(hours=6),
    id='analyze_trends',
    name='Analyze trends',
    replace_existing=True
)

# Start scheduler
scheduler.start()
```

## Security

### Environment Variables

Never commit `.env` files. Use environment-specific configs:
```bash
# Production
cp .env.production .env

# Development
cp .env.development .env
```

### API Rate Limiting

Add to `backend/app/main.py`:
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

app.state.limiter = limiter
app.add_exception_handler(429, _rate_limit_exceeded_handler)
```

### CORS Configuration

```python
from fastapi.middleware.cors import CORSMiddleware

# Production CORS settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-domain.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
```

## Troubleshooting

### Common Issues

1. **Port already in use**
```bash
# Find process using port 8000
lsof -i :8000
# Kill process
kill -9 <PID>
```

2. **Database locked**
```bash
# Check for locks
fuser data/tweets.db
# Remove stale lock files
rm data/tweets.db-journal
rm data/tweets.db-wal
```

3. **Memory issues**
```bash
# Check memory usage
free -h
# Clear cache
sync && echo 3 > /proc/sys/vm/drop_caches
```

4. **Disk space**
```bash
# Check disk usage
df -h
# Find large files
du -ah data/ | sort -rh | head -20
```

### Logs Location

- Backend logs: `logs/app.log`
- Frontend logs: Check browser console
- Nginx logs: `/var/log/nginx/`
- System logs: `journalctl -u smarttrendtracer`

## Scaling

### Horizontal Scaling

Use a load balancer (HAProxy, Nginx) with multiple backend instances:
```nginx
upstream backend {
    server 127.0.0.1:8000;
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
}

location /api {
    proxy_pass http://backend;
}
```

### Database Scaling

For high volume, migrate to PostgreSQL:
```python
# Update DATABASE_URL in .env
DATABASE_URL=postgresql://user:password@localhost/smarttrendtracer

# Update requirements.txt
psycopg2-binary==2.9.9
```

## Maintenance

### Regular Tasks

1. **Weekly**: Check disk space, review logs
2. **Monthly**: Update dependencies, review API usage
3. **Quarterly**: Security updates, performance review

### Update Procedure

```bash
# Backup first
./scripts/backup.sh

# Pull latest code
git pull origin main

# Update backend
cd backend
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head

# Update frontend
cd ../frontend
npm install --legacy-peer-deps
npm run build

# Restart services
sudo systemctl restart smarttrendtracer
sudo systemctl restart nginx
```