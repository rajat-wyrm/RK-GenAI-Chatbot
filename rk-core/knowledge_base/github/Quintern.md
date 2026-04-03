# Quintern

- **Repository:** https://github.com/rajat-wyrm/Quintern
- **Description:** Quintern — 5-tier cohort operations platform with AI-powered assistance. quin (5) + intern.
- **Primary language:** JavaScript
- **Stars:** 0
- **Forks:** 0
- **Topics:** None
- **Homepage:** https://github.com/rajat-wyrm/Quintern
- **Created:** 2026-06-13
- **Last updated:** 2026-06-16
- **Archived:** No

## README

# Quintern

> **quin (five) + intern — a 5-tier cohort operations platform with real-time collaboration and a 7-provider AI assistant.**

[![License: Proprietary](https://img.shields.io/badge/License-Proprietary-1f2937?style=for-the-badge)](#license)
[![Node.js](https://img.shields.io/badge/Node.js-24-339933?style=for-the-badge&logo=nodedotjs&logoColor=white)](https://nodejs.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-18-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Fastify](https://img.shields.io/badge/Fastify-5-000000?style=for-the-badge&logo=fastify&logoColor=white)](https://fastify.dev/)
[![React](https://img.shields.io/badge/React-19-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-6-646CFF?style=for-the-badge&logo=vite&logoColor=white)](https://vitejs.dev/)
[![Socket.IO](https://img.shields.io/badge/Socket.IO-Realtime-010101?style=for-the-badge&logo=socketdotio&logoColor=white)](https://socket.io/)
[![CI](https://img.shields.io/badge/CI-3_checks_passing-22c55e?style=for-the-badge&logo=githubactions&logoColor=white)](#ci--cd)
[![Tests](https://img.shields.io/badge/Tests-44%2F44-22c55e?style=for-the-badge&logo=jest&logoColor=white)](#testing)

---

## Maintainer

**Rajat Kumar** — Project Management, Uptoskills

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [The Quintern Philosophy](#the-quintern-philosophy)
3. [What is Quintern?](#what-is-quintern)
4. [Highlights](#highlights)
5. [System Architecture](#system-architecture)
6. [Technology Stack](#technology-stack)
7. [The 5-Tier Hierarchy](#the-5-tier-hierarchy)
8. [Backend Architecture](#backend-architecture)
9. [Frontend Architecture](#frontend-architecture)
10. [Real-Time Layer (Socket.IO)](#real-time-layer-socketio)
11. [AI Assistant — 7-Provider Fallback Chain](#ai-assistant--7-provider-fallback-chain)
12. [Authentication & Authorization](#authentication--authorization)
13. [Database Design](#database-design)
14. [Module Reference](#module-reference)
15. [API Reference](#api-reference)
16. [Security Architecture](#security-architecture)
17. [File Storage — Cloudinary Integration](#file-storage--cloudinary-integration)
18. [Payments — Stripe Webhook](#payments--stripe-webhook)
19. [Performance & Scalability](#performance--scalability)
20. [Observability](#observability)
21. [CI / CD](#ci--cd)
22. [Deployment](#deployment)
23. [Local Development](#local-development)
24. [Environment Variables](#environment-variables)
25. [Testing Strategy](#testing-strategy)
26. [Project Structure](#project-structure)
27. [Roadmap](#roadmap)
28. [Contributing](#contributing)
29. [License](#license)
30. [Acknowledgements](#acknowledgements)

---

## Executive Summary

**Quintern** is a production-grade workforce and intern operations platform that consolidates the entire intern-program lifecycle — recruitment to retention — into a single, real-time, AI-augmented system.

The platform models the real-world structure of a high-performing internship program as a **5-tier cohort hierarchy** (Admin → Senior TL → TL → Captain → Intern), and enforces it end-to-end at the database, middleware, API, and UI layers. Every action — every attendance mark, every rating, every task assignment, every login — flows through this hierarchy, is validated against it, and is recorded in an immutable audit log.

A 7-provider AI assistant provides natural-language insights, summaries, and recommendations that are **role-aware** (the same question gets a different answer for an Admin versus an Intern). A Socket.IO real-time layer pushes notifications, presence, and live data updates to every connected client in under 10 ms. A Cloudinary-backed upload pipeline handles avatars and proof attachments. A Stripe webhook handles subscription events.

Quintern is built to be deployed as a single Vercel + Render + Neon + Upstash stack, scale horizontally, and survive any single provider going down.

---

## The Quintern Philosophy

1. **Hierarchy is sacred.** A 5-tier cohort structure is a deliberate design choice — it reflects how great intern programs actually run, and it surfaces the right access boundaries naturally.
2. **Real-time is a feature, not a luxury.** When a Captain marks attendance for an Intern, the Intern should _see_ it happen. When a rating is received, the dashboard updates before the user blinks.
3. **The user always gets an answer.** Whether it's from a frontier LLM, a local heuristic, or a role-aware default — the system never returns an empty bubble.
4. **Audit by default.** Every state-changing action is logged immutably. There is no "off the record" mode.
5. **Performance is a feature.** A dashboard that takes 3 seconds to load is broken, no matter how pretty the chart is.
6. **Boring technology wins.** Node, Postgres, Redis, React — all boring, all proven, all excellent.

---

## What is Quintern?

| Module                    | What it does                                                                                  |
| ------------------------- | --------------------------------------------------------------------------------------------- |
| **Auth**                  | JWT access (15 min) + refresh (7 d), CSRF, Argon2 password hashing, forgot/reset/verify flows |
| **Users & Departments**   | 16 seeded users across 5 roles, 3 departments, full profile + avatar management               |
| **Hierarchy**             | `checkHierarchyAccess(userId, targetId)` enforces ancestor/descendant permissions             |
| **Team**                  | Captain+ see only their reports; Senior TL+ see department-wide; Admin sees all               |
| **Attendance**            | 6 states (PRESENT, ABSENT, LEAVE, EXAM_LEAVE, HALF_DAY, WFH), bulk mark, monthly stats        |
| **Ratings**               | 1–10 scale, 7 categories, immutable once written, deep-linked to actor and target             |
| **Social Tasks + Proofs** | Captains assign social tasks; Interns submit text/image proofs; Captain reviews               |
| **Projects**              | Kanban (6 columns), milestones, risks, members, priorities, health                            |
| **Meetings**              | Create, RSVP, attendees, post-meeting notes                                                   |
| **Notifications**         | Real-time, read/unread, in-app badge counter, push on event                                   |
| **Reports & Exports**     | CSV exports of attendance, ratings, tasks — admin only                                        |
| **Analytics**             | Org-wide overview, top performers, attendance trends                                          |
| **Audit Log**             | Append-only, immutable, captures every state-changing action with actor/target/timestamp      |
| **AI Assistant**          | 7-provider fallback chain with role-aware prompts and live platform data                      |
| **Uploads**               | Avatars + files → Cloudinary with local-disk fallback                                         |
| **Stripe**                | Webhook endpoint with HMAC-SHA256 signature verification + event log                          |
| **Realtime**              | Socket.IO with JWT auth, per-user/role/department rooms, presence                             |
| **Sessions**              | View active sessions, revoke any session except current                                       |
| **Uptoskills**            | External skills platform integration with sync status                                         |

---

## Highlights

- 🏛 **5-tier hierarchy enforced end-to-end** — Admin → Senior TL → TL → Captain → Intern
- ⚡ **Socket.IO real-time** — JWT-authenticated, per-user/role/department rooms, presence, 4 ms heartbeat
- 🤖 **7-provider AI chain** — Groq → Gemini → OpenAI → HuggingFace → DeepSeek → Anthropic → FastAPI → heuristic
- 📊 **6 attendance states, 1–10 ratings, 7 r
