# Contributing to AI Outreach System

Thank you for considering contributing! This guide will help you get started.

## Development Setup

1. **Clone the repo**

   ```bash
   git clone https://github.com/Wrathsid/AI_Outreach_System.git
   cd AI_Outreach_System
   ```

2. **Backend**

   ```bash
   cd backend
   python -m venv venv
   .\venv\Scripts\activate  # Windows
   pip install -r requirements.txt
   cp ../.env.example .env   # Fill in your API keys
   python -m backend.main
   ```

3. **Frontend**

   ```bash
   cd frontend
   npm install
   cp .env.example .env.local  # Fill in your keys
   npm run dev
   ```

## Code Guidelines

### Backend (Python)

- Use **type hints** on all function signatures
- Follow **PEP 8** formatting
- Add docstrings to all public functions
- Use **Pydantic models** for request/response validation
- Handle errors with proper HTTP status codes

### Frontend (TypeScript)

- Use **TypeScript** strictly (no `any` unless unavoidable)
- Keep components focused and reusable
- Maintain the **glassmorphism design language** — translucent panels, subtle gradients, smooth animations
- Use **Framer Motion** for all animations (no raw CSS transitions)
- All API calls go through `src/lib/api.ts`

### Commits

- Use [Conventional Commits](https://www.conventionalcommits.org/):
  - `feat:` — New feature
  - `fix:` — Bug fix
  - `docs:` — Documentation
  - `chore:` — Maintenance
  - `refactor:` — Code restructuring

## Pull Request Process

1. Create a feature branch from `main`
2. Make your changes with clear, atomic commits
3. Ensure the backend starts without errors
4. Ensure `npm run build` passes for the frontend
5. Open a PR with a clear description of changes
6. Request review

## Reporting Issues

- Use GitHub Issues
- Include steps to reproduce, expected behavior, and actual behavior
- Add screenshots for UI issues

## Questions?

Open a GitHub Discussion or reach out to the maintainer.
