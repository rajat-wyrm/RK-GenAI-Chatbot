# Projects

## InternOps — Enterprise Workforce Management Platform
**Stack:** React, Fastify, PostgreSQL, Redis, Socket.IO, Docker

**Overview:** Built a workforce management platform that replaced spreadsheet-based operations
with centralized tracking, reporting, and access control. Used by UptoSkills to manage hundreds
of interns across multiple projects.

**Key Features:**
- Hierarchical **role-based access control (RBAC)** with team, department, and org-level permissions
- **Attendance tracking** with daily logs, late marks, and exception handling
- **Ratings & performance reviews** with structured criteria
- **Meetings** module with scheduling, agendas, and minutes
- **Task workflows** with assignment, status tracking, and validation rules
- **Notifications** system (in-app, email, real-time)
- **Audit logging** for all sensitive operations
- **Analytics dashboards** for team leads and management

**Technical Highlights:**
- Real-time workforce visibility through Socket.IO live updates
- Bulk management features for admin operations
- Automated notification triggers based on business rules
- **Security hardening:**
  - CSRF protection
  - Refresh token rotation
  - Brute force prevention
  - Secure session management
  - Comprehensive audit trails
- **Performance:**
  - Redis caching layer
  - AI-generated reports
  - Automated media cleanup workflows
  - Performance monitoring and metrics

---

## AI Compliance Copilot
**Stack:** FastAPI, Next.js, FAISS, Redis, Docker, Google Cloud

**Overview:** Developed a compliance assistant for document retrieval, clause analysis,
and risk assessment. Helps compliance teams quickly find relevant policies and assess
regulatory risk across large document corpora.

**Key Features:**
- **Document retrieval** with semantic search over compliance documents
- **Clause analysis** that surfaces relevant regulatory text
- **Risk assessment** with contextual reasoning over retrieved content
- **Conversational interface** for natural-language compliance queries

**Technical Highlights:**
- Implemented **semantic search workflows** using FAISS vector store
- Contextual response generation grounded in retrieved documents
- **Caching layer** with Redis for frequently accessed queries
- **Containerized deployment** on Google Cloud for reliability
- **FastAPI** backend with async streaming responses

---

## Apogee — Multi-Tenant SaaS Platform
**Stack:** React, Node.js, PostgreSQL, Socket.IO, Stripe, Docker

**Overview:** Built a multi-tenant platform for project management, collaboration, task
tracking, and analytics. Each organization gets an isolated workspace with custom
permissions and billing.

**Key Features:**
- **Workspace isolation** — strict tenant boundaries for data security
- **Role-based permissions** within and across workspaces
- **Real-time notifications** via Socket.IO
- **Billing workflows** with Stripe integration
- **Activity monitoring** with audit logs
- **Project management** with task tracking and team collaboration
- **Analytics** for workspace-level insights

**Technical Highlights:**
- **Scalable deployment** with Docker and CI/CD automation
- **Cloud integrations** for storage, auth, and monitoring
- **CI/CD pipeline** for automated testing and deployment
- Stripe-powered subscription and billing management
