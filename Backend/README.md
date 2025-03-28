# TimeWell Backend

This is the backend service for the TimeWell application built with FastAPI.

## Project Structure

```
Backend/
├── app/
│   ├── core/           # Core functionality, database, config
│   ├── models/         # SQLAlchemy models
│   ├── routers/        # API routes
│   ├── schemas/        # Pydantic models
│   ├── services/       # Business logic
│   └── main.py        # FastAPI application initialization
├── requirements.txt    # Project dependencies
└── README.md          # This file
```

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Application

To run the application in development mode:

```bash
uvicorn app.main:app --reload
```

The API will be available at http://localhost:8000

API documentation will be available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc 