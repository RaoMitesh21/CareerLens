# CareerLens

<p align="center">
  <img src="careerlens-backend/app/static/careerlens-logo.png" alt="CareerLens Logo" width="280"/>
</p>

<p align="center">
  AI-powered resume intelligence platform for skill-gap analysis, role-fit scoring, and personalized career roadmaps.
</p>

## Overview

CareerLens is a production-ready full-stack platform that analyzes a candidate resume against occupational skill standards and returns:

- Role match scores (core, secondary, bonus)
- Missing skill priorities
- Confidence-calibrated analysis
- Personalized learning roadmap
- Optional ML fit probability for recruiter use cases

The platform is built around a modular backend architecture, a modern React frontend, and optional workflow automation for batch operations.

## Quick Links

- Full documentation: [DOCUMENTATION.md](DOCUMENTATION.md)
- Deployment guide: [DEPLOYMENT.md](DEPLOYMENT.md)
- Backend guide: [careerlens-backend/README.md](careerlens-backend/README.md)
- Frontend guide: [careerlens-frontend/README.md](careerlens-frontend/README.md)
- Workflow automation: [workflows/README.md](workflows/README.md)

## Core Capabilities

- Resume parsing and text-based role analysis
- Hybrid scoring pipeline with confidence calibration
- ML fit scoring endpoint for candidate ranking
- Skill-gap prioritization and roadmap generation
- Recruiter-focused shortlist and dashboard support
- Containerized deployment with CI-ready structure

## System Architecture

```text
┌───────────────────────────────────────────────────────────┐
│ Frontend (React + Vite)                                  │
│ - Landing, Upload, Results, Recruiter, Auth, Dashboard   │
└───────────────────────────────────────────────────────────┘
                          │
                          │ HTTPS / JSON
                          ▼
┌───────────────────────────────────────────────────────────┐
│ Backend API (FastAPI)                                    │
│ - Routers: analyze, roadmap, ml-fit, auth, resume, user  │
│ - Services: scoring, analyzer, classifier, generators     │
│ - Schemas: request/response contracts                     │
└───────────────────────────────────────────────────────────┘
                          │
                          │ SQLAlchemy ORM
                          ▼
┌───────────────────────────────────────────────────────────┐
│ Data Layer                                                │
│ - Relational DB (MySQL-compatible)                        │
│ - Occupations, skills, mappings, users, resumes, results  │
└───────────────────────────────────────────────────────────┘
                          │
                          ▼
┌───────────────────────────────────────────────────────────┐
│ Optional Automation                                       │
│ - n8n workflows for batch scoring and notifications       │
└───────────────────────────────────────────────────────────┘
```

## Component Structure

### Backend Components

- API entrypoint: [careerlens-backend/app/main.py](careerlens-backend/app/main.py)
- Routing layer: [careerlens-backend/app/routers](careerlens-backend/app/routers)
- Service layer: [careerlens-backend/app/services](careerlens-backend/app/services)
- Data models: [careerlens-backend/app/models](careerlens-backend/app/models)
- Schema contracts: [careerlens-backend/app/schemas](careerlens-backend/app/schemas)
- DB configuration: [careerlens-backend/app/core/database.py](careerlens-backend/app/core/database.py)

### Frontend Components

- App bootstrap: [careerlens-frontend/src/main.jsx](careerlens-frontend/src/main.jsx)
- Routing shell: [careerlens-frontend/src/App.jsx](careerlens-frontend/src/App.jsx)
- Pages: [careerlens-frontend/src/pages](careerlens-frontend/src/pages)
- Reusable UI: [careerlens-frontend/src/components](careerlens-frontend/src/components)
- API client layer: [careerlens-frontend/src/services/api.js](careerlens-frontend/src/services/api.js)
- Theme and styles: [careerlens-frontend/src/theme](careerlens-frontend/src/theme)

### Infrastructure Components

- Compose stack: [docker-compose.yml](docker-compose.yml)
- Backend container: [careerlens-backend/Dockerfile](careerlens-backend/Dockerfile)
- Frontend container: [careerlens-frontend/Dockerfile](careerlens-frontend/Dockerfile)
- CI workflows: [.github/workflows/backend.yml](.github/workflows/backend.yml), [.github/workflows/frontend.yml](.github/workflows/frontend.yml)

## Development Approach

### 1) Product Strategy

- Problem-first design: align candidate skills with real role requirements
- Explainability-first scoring: deterministic outputs with traceable skill evidence
- Incremental enhancement: base scoring, then calibration, then ML fit

### 2) Backend Engineering Approach

- API-first implementation using FastAPI and Pydantic schemas
- Layered architecture to separate routes, business logic, and persistence
- Config-driven behavior for portability across local, staging, and cloud
- Defensive coding around parsing/scoring to reduce runtime failures

### 3) Frontend Engineering Approach

- Component-driven design with clear page/component/service boundaries
- UX flow focused on candidate journey: upload -> analyze -> roadmap
- Structured service calls and typed payload contracts from backend schemas
- Dashboard-oriented layouts for recruiter and student experiences

### 4) Data and Scoring Approach

- Occupation-skill mapping as the base truth layer
- Tier-based scoring for core/secondary/bonus signals
- Confidence calibration to reduce false confidence on sparse resumes
- ML fit scoring as a complementary ranking signal (not a black box replacement)

### 5) Delivery and Operations Approach

- Dockerized runtime for consistent deployment
- CI workflows for repeatable quality gates
- Environment-based configuration for secrets and external services
- Optional workflow automation for batch pipelines and notifications

## Local Setup

### Quick Start

```bash
cd "/Users/miteshrao/Desktop/Capstone Project"
chmod +x quickstart.sh
./quickstart.sh
```

### Manual Start

```bash
# Backend
cd careerlens-backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend (new terminal)
cd careerlens-frontend
npm install
npm run dev
```

## API Surface (Highlights)

- `/analyze` and `/analyze/hybrid` for role analysis
- `/roadmap` for learning path generation
- `/ml-fit/score` and `/ml-fit/score-batch` for recruiter fit predictions
- `/resumes/*` for resume upload and management
- `/auth/*` for authentication workflows

Interactive docs are available at `http://localhost:8000/docs` in local mode.

## Production Readiness

- Containerized backend and frontend
- Environment template included ([.env.example](.env.example))
- Deployment playbook included ([DEPLOYMENT.md](DEPLOYMENT.md))
- Workflow automation templates included ([workflows](workflows))
- Production-focused repository policy via [.gitignore](.gitignore)

## Security and Quality Practices

- Secrets kept out of version control
- Schema validation at API boundaries
- Authentication and password hashing support in backend auth modules
- Structured project layout to reduce duplicate logic
- Commit discipline for production-only artifacts

## Roadmap

- Improve multilingual role and skill normalization
- Expand recruiter analytics and candidate comparison tooling
- Introduce advanced model evaluation and model governance pipeline
- Add managed observability stack for production telemetry

## Author

Mitesh Rao

## License

MIT (add a LICENSE file if not already present).
