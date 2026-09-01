# Smart Attendance System — Security & Privacy Architecture

This document describes the security controls, privacy safeguards, and compliance posture implemented in the **Smart Attendance System**.

---

## 1. Authentication & JWT Hardening

- **Stateless JWT Tokens**: Signed with `HS256` and cryptographically validated on every protected API call using strong `JWT_SECRET_KEY`.
- **Password Hashing**: Passwords stored as `bcrypt` / `PBKDF2` salted password hashes. Passwords are never stored or logged in plain text.
- **Deactivated Account Defense**: Deactivated user accounts (`is_active: false`) are rejected at the authentication layer (`401 Unauthorized`).

---

## 2. Server-Side Role & Resource Authorization (IDOR Defense)

- **Role Authorization**: Endpoints are strictly guarded with server-side dependencies (`require_admin`, `require_teacher`, `require_role`).
- **Student Resource Isolation**: Students can access ONLY their own attendance history, personal analytics, notifications, and generated reports. Attempting to pass another student's ID returns `403 Forbidden` and triggers a `CRITICAL` security audit event (`IDOR_ATTEMPT`).
- **Teacher Class Roster Isolation**: Teachers can view analytics, take attendance, and generate reports ONLY for their assigned classes and subjects.

---

## 3. Biometric & Data Privacy Protection

- **Zero Secret Exposure**: Database audit records, operational logs, API error payloads, and PDF reports strictly omit password hashes, JWT tokens, face embeddings, raw camera frames, or database credentials.
- **Path Traversal Protection**: PDF file download endpoints enforce strict directory confinement checking (`os.path.abspath(file_path).startswith(REPORTS_DIR)`).
- **Failure-Safe Audit Reliability**: Audit event logging is wrapped in failure-safe handlers. An audit persistence error will NEVER crash or interrupt a user's primary login, face recognition, or attendance request.

---

## 4. Abuse Protection & Rate Limiting

- **Endpoint Rate Limiting**: In-memory sliding window rate limiting limits login (`10 requests/min`), face recognition (`20 requests/min`), and PDF report generation (`10 requests/min`) to prevent automated brute-force attacks.
- **Safe Error Response Handling**: Unhandled 500 server errors return standardized, sanitized JSON messages without exposing internal stack traces.
