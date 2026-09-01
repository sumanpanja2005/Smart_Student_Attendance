# Smart Attendance System — Production Deployment Guide

This document provides production deployment instructions for the **AI-Based Smart Attendance & Student Analytics System**.

---

## 1. System Requirements & Prerequisites

- **Python**: `3.10` or higher
- **Node.js**: `18.x` or `20.x` LTS
- **MongoDB**: `4.4` or higher (MongoDB Atlas or self-hosted)
- **RAM**: Minimum 2 GB (4 GB recommended for InsightFace AI face analysis)

---

## 2. Environment Configuration

### Backend Setup
1. Navigate to `backend/`:
   ```bash
   cd backend
   ```
2. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
3. Configure `.env` variables:
   ```ini
   ENVIRONMENT=production
   MONGODB_URI=mongodb+srv://<username>:<password>@cluster.mongodb.net/?retryWrites=true&w=majority
   MONGODB_DATABASE=smart_attendance
   FRONTEND_URL=https://your-frontend-domain.com
   CORS_ORIGINS=https://your-frontend-domain.com
   JWT_SECRET_KEY=generate-a-strong-64-character-random-secret-key
   JWT_ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=60
   RATE_LIMIT_LOGIN_PER_MINUTE=10
   RATE_LIMIT_FACE_PER_MINUTE=20
   RATE_LIMIT_REPORT_PER_MINUTE=10
   REPORTS_DIR=reports_storage
   AUDIT_LOG_RETENTION_DAYS=365
   ```

### Frontend Setup
1. Navigate to `frontend/`:
   ```bash
   cd frontend
   ```
2. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
3. Set your production API URL:
   ```ini
   VITE_API_BASE_URL=https://your-api-domain.com/api
   ```

---

## 3. Production Installation & Build

### Backend Build
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .\.venv\Scripts\activate
pip install -r requirements.txt
```

### Frontend Build
```bash
cd frontend
npm install
npm run build
```
The optimized production bundle will be output to `frontend/dist/`.

---

## 4. Running Services in Production

### Production Uvicorn Server Command
```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Nginx Reverse Proxy Configuration (Example)
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        root /path/to/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## 5. Health & Monitoring

- **Public Liveness Endpoint**: `GET /api/health`
- **Admin System Health Endpoint**: `GET /api/admin/system/health`
- **Admin System Metrics Endpoint**: `GET /api/admin/system/metrics`
- **Audit Retention Cleanup**: `DELETE /api/admin/audit-logs/retention?retention_days=365`
