# AI-Based Smart Attendance & Student Analytics System

An enterprise-grade, end-to-end academic attendance and predictive risk analytics platform powered by AI face recognition, real-time notifications, ReportLab PDF generation, and system audit trail monitoring.

---

## System Architecture Overview

- **Step 1 — Foundation**: MongoDB Atlas persistence, database manager, environment configuration, system health checks.
- **Step 2 — Authentication & Academic Structure**: JWT authentication, role authorization (ADMIN, TEACHER, STUDENT), user management, student/teacher profiles, subject catalog, class section management.
- **Step 3 — AI Face Registration & Recognition**: InsightFace embedding extraction, single face detection, image quality validation, cross-student duplicate face rejection, face recognition API.
- **Step 4 — Smart Attendance Management**: Attendance session lifecycle (OPEN, CLOSED, CANCELLED), face recognition attendance marking, manual/bulk marking, derived absence calculations, explicit attendance corrections, attendance history.
- **Step 5 — Student Analytics & Predictive Risk Analysis**: Deterministic risk score engine (0–100), risk levels (LOW, MEDIUM, HIGH, CRITICAL), trend analysis (daily/weekly/monthly), subject-wise analytics, class-level analytics, role-aware dashboards.
- **Step 6 — Smart Alerts, Notifications & Reporting**: In-app notification bell widget, unread counter badge, automated alert triggers (`ATTENDANCE_LOW`, `RISK_HIGH`, `RISK_CRITICAL`, `ATTENDANCE_SESSION`, `REPORT_READY`, `SYSTEM`), ReportLab PDF transcript engine, secure PDF download.
- **Step 7 — System Administration, Audit Trail & Operational Monitoring**: Failure-safe `audit_logs` collection, security event logging (`AUTH_LOGIN_FAILED`, `UNAUTHORIZED_ACCESS_ATTEMPT`, `IDOR_ATTEMPT`), Admin audit trail workspace, system health & database latency metrics, audit retention cleanup.
- **Step 8 — Production Hardening, Security, Performance & Deployment Readiness**: Rate limiting middleware, dynamic CORS origins, safe global exception handling (zero secret/stack trace leakage), path traversal protection, biometric privacy audit, full test regression, `DEPLOYMENT.md` & `SECURITY.md`.

---

## Quick Start Commands

### Backend Startup
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .\.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend Startup
```bash
cd frontend
npm install
npm run dev
```

### Test Suite Execution
```bash
cd backend
.\.venv\Scripts\python.exe tests/test_step3_face.py
.\.venv\Scripts\python.exe tests/test_step4_attendance.py
.\.venv\Scripts\python.exe tests/test_step5_analytics.py
.\.venv\Scripts\python.exe tests/test_step6_notifications_reports.py
.\.venv\Scripts\python.exe tests/test_step7_audit_monitoring.py
.\.venv\Scripts\python.exe tests/test_step8_production_hardening.py
```
