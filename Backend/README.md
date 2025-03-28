# TimeWell Backend

This is the backend service for the TimeWell application built with FastAPI.

## Project Structure

```
Backend/
├── app/
│   ├── core/           # Core functionality, database, config
│   ├── models/         # Data models
│   ├── routers/        # API routes
│   ├── schemas/        # Pydantic models
│   ├── services/       # Business logic
│   └── main.py        # FastAPI application initialization
├── tests/             # Test suite
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

3. Set up MongoDB:
   - Install MongoDB or use MongoDB Atlas
   - Create a `.env` file with your MongoDB connection string:
   ```
   MONGODB_URL=mongodb://localhost:27017
   MONGODB_DATABASE_NAME=timewell
   ```

## Database Collections

### Users Collection

The `users` collection stores user information with the following structure:

```json
{
  "_id": ObjectId,
  "email": String,
  "username": String,
  "hashed_password": String,
  "is_active": Boolean,
  "preferences": {
    "coach_voice": String,
    "theme": String,
    "notifications_enabled": Boolean,
    "daily_reminder_time": String,
    "weekly_summary_day": Integer
  },
  "created_at": DateTime,
  "updated_at": DateTime
}
```

### Coach Voice Options

The app supports five different coaching styles:

- `motivational`: Energetic and encouraging
- `supportive`: Warm and nurturing
- `direct`: Clear and concise
- `analytical`: Fact-based and logical
- `friendly`: Conversational and casual

### Goals Collection

The `goals` collection stores user goals with the following structure:

```json
{
  "_id": ObjectId,
  "user_id": ObjectId,
  "title": String,
  "description": String,
  "target_date": DateTime,
  "is_completed": Boolean,
  "created_at": DateTime,
  "updated_at": DateTime
}
```

## API Endpoints

### Users

- `GET /users/me` - Get current user
- `GET /users` - Get all users
- `POST /users` - Create new user
- `GET /users/{user_id}` - Get user by ID
- `PATCH /users/{user_id}` - Update user
- `DELETE /users/{user_id}` - Delete user
- `GET /users/{user_id}/goals` - Get user's goals
- `POST /users/{user_id}/goals` - Create a goal for a specific user
- `GET /users/{user_id}/preferences` - Get user preferences
- `PATCH /users/{user_id}/preferences` - Update user preferences
- `PATCH /users/{user_id}/preferences/coach-voice` - Update coach voice preference

### Goals

- `POST /goals` - Create a new goal
- `GET /goals/{goal_id}` - Get goal by ID
- `PATCH /goals/{goal_id}` - Update goal
- `DELETE /goals/{goal_id}` - Delete goal

## Running the Application

To run the application in development mode:

```bash
uvicorn app.main:app --reload
```

The API will be available at http://localhost:8000

API documentation will be available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Running Tests

To run the tests:

```bash
pytest
``` 