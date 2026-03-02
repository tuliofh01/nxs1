# Agents Overview

This project utilizes automated agents to manage development, deployment, and security.

## Core Agents
- **Deployment Agent:** Handles the build process (TS -> JS, SASS -> CSS) and deploys the Cloudflare Worker.
- **Security Agent:** Implements security headers (CSP, HSTS), input validation, and rate limiting logic.
- **Database Agent:** Manages D1 database migrations and query optimization.

## Workflow
1.  **Check TODOs**: All agents must check `TODO.md` for active tasks and priorities.
2.  Frontend source (TS/SCSS) is compiled by the Deployment Agent.
3.  Backend logic (Worker) is consolidated and secured by the Security Agent.
4.  Changes are pushed to Cloudflare's edge network.
