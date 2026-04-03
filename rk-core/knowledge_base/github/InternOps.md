# InternOps

- **Repository:** https://github.com/rajat-wyrm/InternOps
- **Description:** 
- **Primary language:** JavaScript
- **Stars:** 0
- **Forks:** 48
- **Topics:** None
- **Homepage:** N/A
- **Created:** 2026-05-31
- **Last updated:** 2026-06-16
- **Archived:** No

## README

# InternOps

Enterprise Workforce Management and Intern Operations Platform

[![License](https://img.shields.io/badge/License-Proprietary-blue?style=for-the-badge)](LICENSE)
[![Node.js](https://img.shields.io/badge/Node.js-18+-339933?style=for-the-badge&logo=node.js&logoColor=white)](https://nodejs.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-14+-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Fastify](https://img.shields.io/badge/Fastify-4.x-000000?style=for-the-badge&logo=fastify&logoColor=white)](https://fastify.dev/)
[![React](https://img.shields.io/badge/React-18.x-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev/)

## Table of Contents

- Executive Summary
- Key Features
- System Architecture
- Technology Stack
- Design Principles
- Backend Architecture
- Frontend Architecture
- Authentication Flow
- Authorization Model
- Hierarchy Model
- Database Design
- Database Schema Tables
- Security Architecture
- API Overview
- Major Modules
- Reports and Analytics
- Session Management
- Audit Logging
- Notifications
- Deployment Architecture
- Environment Variables
- Installation
- Quick Start
- Database Migration
- Seed Data
- Running Backend
- Running Frontend
- Testing
- API Documentation
- Performance Considerations
- Scalability Considerations
- Future Integrations
- Production Checklist
- Troubleshooting
- Contributing
- License
- Maintainer

## Executive Summary

InternOps is a production-grade workforce management platform designed to streamline intern operations within structured hierarchies. It provides a full suite of tools for attendance tracking, performance ratings, social task assignments, proof verification, team meetings, notifications, and comprehensive audit logging. The system enforces strict role-based access control with ownership validation, ensuring data integrity and security across all levels of the organization.

Built with a modern Node.js/Fastify backend and a React/Vite frontend, InternOps follows enterprise design patterns such as repository abstraction, middleware-based authorization, and raw SQL queries for optimal database performance. The platform is ready for integration with the Uptoskills ecosystem, with dedicated placeholder modules for future synchronization.

## Key Features

- **Five-tier role hierarchy** - Admin, Senior TL, TL, Captain, Intern with rigid access controls.
- **Attendance management** - Single and bulk attendance marking with monthly statistics and audit trails.
- **Ratings system** - Permanent, immutable rating history with hierarchical rating permissions.
- **Social task management** - Task creation, screenshot proof uploads, and multi-level verification with auto-cleanup of files after 24 hours.
- **Meeting scheduling** - Team meetings with attendee management and hierarchy-aware visibility.
- **Notifications** - Real-time in-app notifications with pagination and read/unread tracking.
- **Reports and analytics** - Attendance summaries, rating trends, task completion stats, CSV exports.
- **Session management** - View active sessions, revoke individual or all user sessions (admin).
- **Audit logging** - Immutable log of every sensitive action (login, attendance, rating, user changes).
- **Security** - JWT authentication, refresh token rotation, Argon2 hashing, CSRF, rate limiting, input sanitization, Helmet headers.
- **RBAC + Ownership validation** - Every API request is validated for both role and hierarchical access.
- **Database** - PostgreSQL with raw SQL (no ORM), UUIDs, foreign keys, indexes, soft deletes.
- **Future integration** - Uptoskills placeholder modules ready for syncing users, attendance, projects.

## System Architecture

InternOps follows a monolithic backend with a separate React frontend, communicating via REST APIs. The backend is built on Fastify and uses raw SQL queries through the `pg` driver. Redis is optionally used for refresh token storage and can be enabled for production scaling.

The architecture emphasizes:

- Clear separation of concerns (routes, services, repositories, middleware)
- Centralized error handling and request logging
- Idempotent database migrations
- BOM-free source files for reliable cross-platform execution

## Technology Stack

| Component       | Technology                         |
| --------------- | ---------------------------------- |
| Backend runtime | Node.js (>=18)                     |
| Framework       | Fastify v4                         |
| Frontend        | React 18, Vite, TailwindCSS, Axios |
| Database        | PostgreSQL (via `pg` driver)       |
| Authentication  | JWT, Argon2                        |
| Caching         | Redis (optional)                   |
| Documentation   | Swagger (OpenAPI)                  |
| Security        | Helmet, CORS, CSRF, Rate Limiting  |
| Validation      | Zod                                |
| Logging         | Pino                               |
| DevOps          | Git, GitHub, PowerShell scripts    |

## Design Principles

- **Security First** - Every endpoint is guarded with authentication, RBAC, and ownership checks.
- **Raw SQL over ORM** - Maximum performance and control with handwritten parameterized queries.
- **Immutability** - Attendance and ratings are never overwritten; changes generate new records or audit logs.
- **Idempotency** - Migration and seed scripts can be safely re-executed.
- **Separation of Concerns** - Routes -> Service -> Repository pattern with clear boundaries.
- **Environment-based Configuration** - All secrets and URLs loaded from `.env`.

## Backend Architecture

The backend follows a modular monolith pattern. Each business module (auth, users, attendance, etc.) is self-contained with its own routes, repository, and optional service layer. Middleware is composed globally or per-route.

- Routes - Define Fastify endpoints, validate input with Zod, delegate to services/repositories.
- Repository - Encapsulates all database queries; no raw SQL in routes.
- Middleware - Auth, RBAC, ownership, CSRF, brute force, and input sanitization.
- Database - PostgreSQL accessed via `pg` with connection pooling and statement timeout.

## Frontend Architecture

The frontend is a React SPA with Vite as build tool and TailwindCSS for styling. State management is handled by Zustand, server state by TanStack Query, and HTTP requests by Axios with automatic token refresh.

- **Protected routes** - Implemented via a PrivateRoute component checking JWT presence.
- **API layer** - Axios instance with interceptors for auth headers and token refresh.
- **UI components** - Built with Shadcn UI primitives, Tailwind utility classes.

## Authentication Flow

1. Client sends `POST /api/auth/login` with email and password.
2. Server verifies Argon2 hash, generates 15-minute access token and 7-day refresh token.
3. Refresh token is hashed and stored in `refresh_tokens` table.
4. Access token is returned in response body; refresh token in HTTP-only cookie.
5. Client stores access token in memory and attaches it via `Authorization` header.
6. On 401, client calls `POST /api/auth/refresh` with the refresh token to obtain a new pair.
7. Old refresh token is revoked server-side.

## Authorization Model

Two layers of authorization are enforced on every protected route:

1. **Role-Based Access Control (RBAC)** - Middleware checks user.role against a list of allowed roles.
2. **Ownership Validation** - Additional middleware ensures the requesting user is in the hierarchy chain of the target resource (e.g., a TL cannot access interns not in their team).

## Hierarchy Model

- Admin - Full access to all resources and users.
- Senior TL - Manages TLs, Captains, and Interns within assigned departments.
- TL - Manages Captains and Interns.
- Captain - Manages Interns directly.
- Intern - Can view own data, upload proof submissions.

Ownership is validated recursively using a `WITH RECURSIVE` cte that walks the manager
