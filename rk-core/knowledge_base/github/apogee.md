# apogee

- **Repository:** https://github.com/rajat-wyrm/apogee
- **Description:** Apogee - The Pinnacle of Productivity (Full-stack PERN application)
- **Primary language:** HTML
- **Stars:** 0
- **Forks:** 0
- **Topics:** None
- **Homepage:** N/A
- **Created:** 2026-03-04
- **Last updated:** 2026-06-07
- **Archived:** No

## README

# Apogee

**Enterprise Multi-Tenant Productivity Platform**

Apogee is a modern enterprise productivity platform designed for teams, startups, and organizations that require secure multi-tenant collaboration, project management, advanced analytics, AI-powered insights, and enterprise-grade administration.

Built with a scalable architecture using Node.js, PostgreSQL, React, and modern cloud-native practices, Apogee provides a unified workspace for managing projects, tasks, teams, files, notifications, analytics, billing, and AI-driven productivity workflows.

---

## Table of Contents

* [Overview](#overview)
* [Key Features](#key-features)
* [Architecture](#architecture)
* [Technology Stack](#technology-stack)
* [System Modules](#system-modules)
* [Project Structure](#project-structure)
* [Getting Started](#getting-started)
* [Environment Variables](#environment-variables)
* [Database Setup](#database-setup)
* [Running the Application](#running-the-application)
* [API Reference](#api-reference)
* [Authentication & Authorization](#authentication--authorization)
* [Testing](#testing)
* [Docker Deployment](#docker-deployment)
* [Production Deployment](#production-deployment)
* [Performance & Reliability](#performance--reliability)
* [Security Features](#security-features)
* [Roadmap](#roadmap)
* [License](#license)

---

# Overview

Apogee is a full-stack SaaS productivity platform that combines:

* Multi-tenant organization management
* Workspace and project collaboration
* Task tracking and workflow management
* Real-time notifications
* AI-powered recommendations and forecasting
* Analytics and reporting
* Subscription billing
* Enterprise administration and audit logging

The platform is designed with a modular architecture, enabling organizations to scale from small teams to enterprise environments while maintaining tenant isolation, security, and performance.

---

# Key Features

## Productivity Management

* Project management with custom workflows
* Task management with priorities, statuses, assignments, and due dates
* Kanban, list, and calendar views
* Subtasks and comments
* File attachments and document storage

## Enterprise Multi-Tenancy

* Organization-level isolation
* Workspace segmentation
* Tenant-aware database operations
* Role-based access control
* Member management

## Authentication & Security

* JWT access tokens
* Refresh token rotation
* Account lockout protection
* Password reset workflow
* Helmet security headers
* Secure middleware architecture

## AI-Powered Productivity

* Task completion prediction
* Productivity forecasting
* Smart recommendations
* Multi-provider AI fallback architecture
* Graceful degradation when providers are unavailable

## Analytics & Reporting

* Task trend analysis
* Productivity scoring
* Weekly activity reports
* Priority distribution metrics
* Project health monitoring

## Collaboration

* Real-time notifications
* Live updates via Socket.IO
* Notification center
* Team activity tracking

## Billing & Subscription Management

* Stripe integration
* Subscription management
* Checkout session generation
* Webhook handling
* Plan-based architecture

## Administration

* User management
* Role administration
* Audit logging
* Feature flag management

## Engineering Quality

* Comprehensive integration testing
* Dockerized deployment
* CI/CD automation
* Progressive Web App support
* Optimized production builds

---

# Architecture

```text
┌───────────────────────────────────────────────┐
│                   Frontend                    │
│        React 19 + Vite + Tailwind CSS         │
└───────────────────────┬───────────────────────┘
                        │
                        ▼
┌───────────────────────────────────────────────┐
│                 REST API Layer                │
│                Node.js + Express              │
└───────────────────────┬───────────────────────┘
                        │
     ┌──────────────────┼──────────────────┐
     ▼                  ▼                  ▼
 Authentication     Business Logic     Realtime Layer
     JWT             Services/Models      Socket.IO

                        │
                        ▼

┌───────────────────────────────────────────────┐
│                 PostgreSQL                    │
│        Multi-Tenant Relational Database       │
└───────────────────────────────────────────────┘

        Optional Integrations
 ┌────────────┬────────────┬────────────┐
 │  OpenAI    │  Stripe    │ Cloudinary │
 │  Gemini    │ Billing    │ File Store │
 │ DeepSeek   │            │            │
 └────────────┴────────────┴────────────┘
```

---

# Technology Stack

| Category         | Technologies             |
| ---------------- | ------------------------ |
| Backend          | Node.js, Express.js      |
| Database         | PostgreSQL               |
| Authentication   | JWT, Bcrypt              |
| Realtime         | Socket.IO                |
| Frontend         | React 19, Vite           |
| Styling          | Tailwind CSS             |
| State Management | Zustand                  |
| Data Fetching    | React Query              |
| Animation        | Framer Motion            |
| Charts           | Recharts                 |
| AI Providers     | OpenAI, Gemini, DeepSeek |
| Billing          | Stripe                   |
| File Storage     | Cloudinary               |
| Testing          | Jest, Supertest          |
| DevOps           | Docker, GitHub Actions   |
| PWA              | Vite Plugin PWA          |

---

# System Modules

## Backend Modules

| Module         | Description                              |
| -------------- | ---------------------------------------- |
| Authentication | User registration, login, refresh tokens |
| Organizations  | Multi-tenant organization management     |
| Workspaces     | Team collaboration spaces                |
| Projects       | Project lifecycle management             |
| Tasks          | Task tracking and assignment             |
| Notifications  | Real-time user notifications             |
| Files          | Cloudinary-based file management         |
| Analytics      | Reporting and productivity insights      |
| AI Services    | Forecasting and recommendations          |
| Billing        | Stripe subscriptions and payments        |
| Administration | User roles, audit logs, feature flags    |

## Frontend Modules

| Module         | Description                    |
| -------------- | ------------------------------ |
| Dashboard      | Productivity overview          |
| Projects       | Project management UI          |
| Tasks          | List and Kanban workflows      |
| Analytics      | Charts and reporting           |
| Notifications  | Notification center            |
| Settings       | User and organization settings |
| Authentication | Login and registration flows   |

---

# Project Structure

```text
apogee/
│
├── apps/
│   └── web/
│       ├── src/
│       ├── public/
│       └── vite.config.js
│
├── src/
│   ├── config/
│   ├── middleware/
│   ├── models/
│   ├── routes/
│   ├── services/
│   ├── utils/
│   └── index.js
│
├── database/
│   ├── migrations/
│   └── seeds/
│
├── scripts/
│   ├── migrate.js
│   └── seed.js
│
├── tests/
│
├── docker-compose.yml
├── Dockerfile
├── package.json
└── README.md
```

---

# Getting Started

## Prerequisites

* Node.js 18+
* PostgreSQL 14+
* npm or pnpm

Optional:

* OpenAI API Key
* Gemini API Key
* DeepSeek API Key
* Stripe Account
* Cloudinary Account

---

# Installation

```bash
git clone https://github.com/rajat-wyrm/apogee.git

cd apogee

npm install
```

---

# Environment Variables

Create a `.env` file in the root directory.

```env
PORT=5000

DATABASE_URL=

JWT_SECRET=
JWT_REFRESH_SECRET=

OPENAI_API_KEY=
GEMINI_API_KEY=
DEEPSEEK_API_KEY=

STRIPE_SECRET_KEY=

CLOUDINARY_CLOUD_NAME=
CLOUDINARY_API_KEY=
CLOUDINARY_API_SECRET=
```

---

# Database Setup

Run migrations:

```bash
npm run migrate
```

Seed demo data:

```bash
npm run s
