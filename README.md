# Diamond Pricing Intelligence Platform

## Quick Start (Minimal Deploy)

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

## Environment Variables
Copy `.env.example` to `.env` and configure as needed.
By default, the system uses mock API adapters for VDB and Diamax.
