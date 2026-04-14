# taskflow

- **Repository:** https://github.com/rajat-wyrm/taskflow
- **Description:** 
- **Primary language:** JavaScript
- **Stars:** 0
- **Forks:** 0
- **Topics:** None
- **Homepage:** N/A
- **Created:** 2026-03-03
- **Last updated:** 2026-06-15
- **Archived:** No

## README


# Task Flow Project

A powerful and intuitive task management system designed to streamline your team's workflow. Visualize, track, and optimize task progress from start to finish.

![Task Flow Demo](https://via.placeholder.com/800x400.png?text=Task+Flow+Screenshot)

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Configuration](#configuration)
- [Usage](#usage)
  - [Creating Tasks](#creating-tasks)
  - [Task States](#task-states)
  - [Board View](#board-view)
  - [Analytics](#analytics)
- [API Reference](#api-reference)
- [Testing](#testing)
- [Deployment](#deployment)
- [Contributing](#contributing)
- [License](#license)

## Overview

Task Flow is a full-stack application that helps teams manage their work using a flexible, board‑based approach. Tasks move through customizable stages (Backlog, In Progress, Review, Done) with real‑time updates and rich collaboration features.

Built for modern development teams, Task Flow reduces context switching and provides actionable metrics to identify bottlenecks.

## Features

- **Drag‑and‑drop board** – Intuitive Kanban-style interface
- **Task lifecycle** – Define custom statuses and transitions
- **User assignments** – Assign tasks to team members
- **Due dates & priorities** – Set deadlines and priority levels (Low, Medium, High, Critical)
- **Comments & activity logs** – Full audit trail for each task
- **File attachments** – Upload images, documents, or screenshots
- **Real‑time notifications** – In-app and email alerts
- **Dashboard analytics** – Cycle time, throughput, and cumulative flow diagrams
- **RESTful API** – Integrate with external tools
- **Role‑based access** – Admin, Manager, Member views

## Tech Stack

| Layer       | Technology                               |
|-------------|------------------------------------------|
| Frontend    | React 18, Redux Toolkit, Tailwind CSS    |
| Backend     | Node.js, Express, Socket.io              |
| Database    | PostgreSQL (primary), Redis (caching)    |
| Auth        | JWT, bcrypt, OAuth2 (Google/GitHub)      |
| Testing     | Jest, React Testing Library, Supertest   |
| Deployment  | Docker, Nginx, AWS ECS (or your choice)  |

## Getting Started

Follow these instructions to get a copy of the project running on your local machine for development and testing.

### Prerequisites

- Node.js (v18 or later)
- PostgreSQL (v14+)
- Redis (optional, but recommended for production)
- npm or yarn

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-org/task-flow.git
   cd task-flow
   ```

2. **Install dependencies for both server and client**
   ```bash
   # Backend
   cd backend
   npm install

   # Frontend
   cd ../frontend
   npm install
   ```

3. **Set up the database**
   ```bash
   # Create PostgreSQL database (adjust credentials as needed)
   createdb taskflow_db

   # Run migrations (example using Sequelize or Knex)
   cd ../backend
   npm run migrate:up
   ```

4. **Seed initial data (optional)**
   ```bash
   npm run seed
   ```

### Configuration

Create a `.env` file in the `backend` directory with the following variables:

```env
# Server
PORT=5000
NODE_ENV=development

# Database
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=yourpassword
DB_NAME=taskflow_db

# JWT
JWT_SECRET=your_super_secret_key_change_me
JWT_EXPIRES_IN=7d

# Redis (optional)
REDIS_URL=redis://localhost:6379

# Email (for notifications)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=yourapp@gmail.com
SMTP_PASS=your_app_password
```

For the frontend, create `.env` in the `frontend` folder:

```env
REACT_APP_API_URL=http://localhost:5000/api
REACT_APP_SOCKET_URL=http://localhost:5000
```

## Usage

Start both servers (from the project root):

```bash
# Terminal 1: Backend
cd backend
npm run dev

# Terminal 2: Frontend
cd frontend
npm start
```

Open [http://localhost:3000](http://localhost:3000) in your browser.  
The default admin credentials (after seeding) are:

- Email: `admin@taskflow.com`
- Password: `admin123`

### Creating Tasks

1. Click the **+ New Task** button on the board.
2. Fill in title, description, assignee, priority, due date.
3. The task appears in the **Backlog** column by default.
4. Drag the task to any other column to change its status.

### Task States

Default workflow stages – you can customize them later:

- **Backlog** – newly created, not yet scheduled
- **To Do** – ready to be worked on
- **In Progress** – actively being developed
- **In Review** – awaiting feedback or QA
- **Done** – completed and verified

### Board View

- Cards show task title, assignee avatar, priority badge, and due date.
- Real‑time updates: when a team member moves a task, everyone sees it instantly.
- Filter by assignee, priority, or due date.

### Analytics

Navigate to the **Reports** tab to see:

- **Cumulative Flow Diagram** – visualize work in progress across stages
- **Cycle Time** – average time from "To Do" to "Done"
- **Throughput** – number of tasks completed per day/week

## API Reference

The REST API is available at `http://localhost:5000/api`.  
All endpoints (except login/register) require a Bearer token.

### Authentication

| Method | Endpoint            | Description               |
|--------|---------------------|---------------------------|
| POST   | `/auth/register`    | Create a new user         |
| POST   | `/auth/login`       | Login, returns JWT        |
| GET    | `/auth/me`          | Get current user profile  |

### Tasks

| Method | Endpoint               | Description                     |
|--------|------------------------|---------------------------------|
| GET    | `/tasks`               | List all tasks (with filters)   |
| POST   | `/tasks`               | Create a new task               |
| GET    | `/tasks/:id`           | Get task details                |
| PUT    | `/tasks/:id`           | Update task                     |
| DELETE | `/tasks/:id`           | Delete task                     |
| PATCH  | `/tasks/:id/status`    | Change task status (e.g., move) |

### Boards & Columns

| Method | Endpoint               | Description                     |
|--------|------------------------|---------------------------------|
| GET    | `/boards`              | Get boards for current team     |
| POST   | `/boards`              | Create a new board              |
| PUT    | `/boards/:id/columns`  | Reorder / rename columns        |

For full API documentation, run the server and visit `http://localhost:5000/api-docs` (Swagger UI).

## Testing

Run unit and integration tests:

```bash
# Backend tests
cd backend
npm test

# Frontend tests
cd ../frontend
npm test
```

To run end‑to‑end tests (Cypress):

```bash
cd frontend
npm run cypress:open
```

## Deployment

### Using Docker (recommended)

A `docker-compose.yml` file is provided:

```bash
# Build and start all services
docker-compose up -d --build
```

Services: Nginx (reverse proxy), backend (Node.js), frontend (static build), PostgreSQL, Redis.

### Manual deployment to a VPS

1. Build the frontend: `cd frontend && npm run build`
2. Set up a process manager (PM2) for the backend: `pm start backend/src/server.js`
3. Configure Nginx to serve the static frontend and proxy API requests.

Refer to the `deployment` folder for example configurations.

## Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository.
2. Create a feature branch: `git checkout -b feature/amazing-idea`
3. Commit your changes: `git commit -m 'Add some amazing feature'`
4. Push to the branch: `git push origin feature/amazing-idea`
5. Open a Pull Request.

See [CONTRIBUTING.md](CONTRIBUTING.md) for code style, commit conventions, and testing guidelines.

## License

This project is licensed under the MIT License – see the [LICENSE](LICENSE) file for details.

---

