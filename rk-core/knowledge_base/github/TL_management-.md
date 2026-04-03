# TL_management-

- **Repository:** https://github.com/rajat-wyrm/TL_management-
- **Description:** 
- **Primary language:** TypeScript
- **Stars:** 2
- **Forks:** 13
- **Topics:** None
- **Homepage:** N/A
- **Created:** 2026-05-27
- **Last updated:** 2026-06-05
- **Archived:** No

## README

﻿# TL Management & Attendance Tracking System

Enterprise-grade backend engineered with Node.js, Fastify, Neon PostgreSQL, and military-grade security practices. Production-ready for evaluation.

---

## Quick Start

`ash
git clone https://github.com/rajat-wyrm/TL_management-.git
cd TL_management-
pnpm install
cp .env.example .env
pnpm dev
` 

No local database required - connects to cloud Neon PostgreSQL automatically.

---

## API Documentation

**Swagger UI:** http://localhost:5000

### Authentication
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | /api/v1/auth/register | None | Register new user |
| POST | /api/v1/auth/login | None | Login with anomaly detection |
| POST | /api/v1/auth/refresh | None | Refresh token rotation |
| GET | /api/v1/auth/me | JWT | Get current user |
| PUT | /api/v1/auth/change-password | JWT | Change password |
| POST | /api/v1/auth/forgot-password | None | Request password reset |
| POST | /api/v1/auth/reset-password | None | Reset password with token |
| POST | /api/v1/auth/logout | JWT | Logout + token blacklist |

### MFA / TOTP
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | /api/v1/mfa/setup | JWT | Generate TOTP secret + QR code |
| POST | /api/v1/mfa/verify | JWT | Verify and enable MFA |
| POST | /api/v1/mfa/disable | JWT | Disable MFA |

### API Key Management
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | /api/v1/api-keys | JWT | Create scoped API key (SHA-256 hashed) |
| GET | /api/v1/api-keys | JWT | List all API keys |
| DELETE | /api/v1/api-keys/:id | JWT | Revoke API key |

### Canary Tokens
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | /api/v1/canary/deploy | JWT | Deploy honeypot canary |
| GET | /api/v1/canary/registry | JWT | View all active canaries |
| GET | /api/v1/canary/verify/:id | JWT | Check canary status |

### TL Management
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | /api/v1/tls | Admin/Manager | Create Team Lead |
| GET | /api/v1/tls | Any | List all TLs |
| GET | /api/v1/tls/:id | Any | Get TL by ID |
| PUT | /api/v1/tls/:id | Admin/Manager | Update TL |
| DELETE | /api/v1/tls/:id | Admin | Soft-delete TL |

### Attendance Tracking
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | /api/v1/attendance/mark | JWT | Mark daily attendance |
| GET | /api/v1/attendance/my | JWT | View attendance history |
| GET | /api/v1/attendance/today | JWT | Check today status |

### Performance Ratings
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | /api/v1/ratings | TL/Manager/Admin | Create monthly rating |
| GET | /api/v1/ratings/my | Any | View my ratings |

### Audit Logs
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | /api/v1/audit/logs | Admin/Manager | View tamper-proof audit trail |

### DevOps
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | /api/v1/health | None | Health + pool metrics + memory |
| GET | /api/v1/postman | None | Auto-generated Postman collection |

---

## Security Layers (17 Implemented)

1. Helmet CSP Headers
2. CORS Protection
3. Rate Limiting
4. Leaky Bucket Algorithm
5. Brute Force Protection (5 attempts = 15min lockout)
6. Proof of Work (anti-bot challenge)
7. Argon2id Password Hashing
8. JWT httpOnly Cookies
9. Refresh Token Rotation
10. API Key SHA-256 Hashing
11. MFA/TOTP
12. Zero-Knowledge Proofs
13. Cryptographic Canary Tokens
14. Behavioral Anomaly Detection
15. Data Tokenization
16. Quantum-Resistant KEM
17. CSRF Protection

---

## Resilience Patterns

- Circuit Breaker - DB failure isolation
- Idempotency Keys - Safe retries
- Correlation IDs - Request tracing
- HMAC Request Signing - Zero-trust API
- Tamper-Proof Audit Chain - Hash-linked entries
- Exponential Backoff - DB connection retry
- Graceful Shutdown - SIGTERM/SIGINT handlers

---

## Database Schema

`sql
users (id SERIAL PK, email UNIQUE, password_hash, name, role, department, totp_secret, totp_enabled, is_active, created_at, updated_at)
refresh_tokens (id SERIAL PK, token_id UNIQUE, user_id FK, family, revoked_at, created_at)
attendance (id SERIAL PK, user_id FK, date, status, is_late, comment, created_at, updated_at)
ratings (id SERIAL PK, user_id FK, month, score, comment, reviewer_id, created_at, updated_at)
audit_logs (id SERIAL PK, user_id FK, action, resource, detail, ip_address, chain_hash, created_at)
api_keys (id SERIAL PK, user_id FK, name, prefix, key_hash UNIQUE, scopes, last_used, expires_at, is_active, created_at)
` 

---

## Test Accounts

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@company.com | NewPass@123! |
| Team Lead | tl@company.com | TL@123! |
| Employee | employee@company.com | Employee@123! |

---

## Tech Stack

| Category | Technology |
|----------|------------|
| Runtime | Node.js 24+ |
| Language | TypeScript 5.x (strict) |
| Framework | Fastify 5 |
| Database | Neon PostgreSQL (serverless) |
| Driver | pg (node-postgres) raw SQL |
| Auth | JWT + Argon2id + Speakeasy |
| Validation | Zod |
| Docs | Swagger/OpenAPI 4.0 |

---

**Built with military-grade security. Production-ready. Assessment-complete.**

