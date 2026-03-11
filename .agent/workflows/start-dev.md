---
description: Start the full development environment (backend + frontend)
---

# Start Dev Server

Starts both the backend API server and the frontend Next.js dev server.

// turbo-all

1. Start the backend server:
```
cd "c:\Users\Siddharth\OneDrive\Desktop\AI Outreach System" && .\.venv\Scripts\activate; python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

2. Start the frontend dev server:
```
cd "c:\Users\Siddharth\OneDrive\Desktop\AI Outreach System\frontend" && npm run dev
```

3. Wait 5 seconds for both servers to start, then confirm:
   - Backend is running at http://localhost:8000
   - Frontend is running at http://localhost:3000
