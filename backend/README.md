# Smart Attendance System - FastAPI Backend

Modern, modular FastAPI backend providing application services, JWT role-based authentication, database management via MongoDB Atlas (PyMongo), and academic management routes.

## Directory Structure

```text
backend/
├── app/
│   ├── api/
│   │   ├── deps.py       # Authentication & authorization dependencies (OAuth2/JWT)
│   │   └── routes/       # Modular API route controllers
│   ├── cli/
│   │   └── create_admin.py # CLI Bootstrap tool for initial administrator creation
│   ├── core/             # Centralized pydantic-settings & security configuration
│   ├── db/               # PyMongo client lifecycle & unique collection index management
│   ├── models/           # MongoDB collection schemas & specifications
│   ├── schemas/          # Pydantic request & response models
│   ├── services/         # Atomic business logic & academic operations
│   ├── utils/            # Helper functions
│   └── main.py           # FastAPI application entry point & lifespan handlers
├── requirements.txt      # Python dependencies
├── .env.example          # Environment variable template
└── README.md             # Backend documentation
```

## Setup & Running locally

```bash
# 1. Activate Virtual Environment
source .venv/bin/activate  # or .\.venv\Scripts\Activate.ps1 on Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create initial Admin Account (CLI Bootstrap Tool)
python -m app.cli.create_admin

# 4. Launch dev server
uvicorn app.main:app --reload --port 8000
```
