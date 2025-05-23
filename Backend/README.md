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

### Events Collection

The `events` collection stores user time events with the following structure:

```json
{
  "_id": ObjectId,
  "user_id": ObjectId,
  "goal_id": ObjectId,
  "title": String,
  "description": String,
  "start_time": DateTime,
  "end_time": DateTime,
  "is_completed": Boolean,
  "created_at": DateTime,
  "updated_at": DateTime
}
```

### Suggestions Collection

The `suggestions` collection stores AI-generated suggestions for event-goal alignment with the following structure:

```json
{
  "_id": ObjectId,
  "user_id": ObjectId,
  "event_id": ObjectId,
  "score": Integer,
  "aligned_goals": [ObjectId],
  "analysis": String,
  "suggestion": String,
  "new_goal_suggestion": String,
  "created_at": DateTime,
  "is_applied": Boolean,
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

### Events

- `POST /events` - Create a new event
- `GET /events` - Get all events for the current user
- `GET /events/user/{user_id}` - Get all events for a specific user
- `GET /events/{event_id}` - Get event by ID
- `PATCH /events/{event_id}` - Update event
- `DELETE /events/{event_id}` - Delete event
- `POST /events/analyze` - Analyze event alignment with goals using GPT-4 (accepts voice_style parameter)

### Suggestions

- `GET /suggestions` - Get all suggestions for the current user
- `GET /suggestions/event/{event_id}` - Get all suggestions for a specific event
- `GET /suggestions/{suggestion_id}` - Get a specific suggestion
- `PATCH /suggestions/{suggestion_id}/apply` - Mark a suggestion as applied
- `PATCH /suggestions/{suggestion_id}/unapply` - Mark a suggestion as not applied

### Coach

- `POST /coach/reflect` - Create a personalized reflection using the user's preferred coach voice
- `POST /coach/feedback` - Generate personalized feedback using the user's preferred coach voice
- `POST /coach/encourage` - Generate personalized encouragement using the user's preferred coach voice
- `POST /coach/ask` - Ask the TimeWell coach a question with specified voice style
- `GET /coach/weekly-review` - Get a personalized weekly review with specified voice style
- `POST /coach/action-plan` - Generate an action plan with specified voice style

### Voice Styles

- `GET /voice-styles` - Get a list of all available voice styles for AI interactions

## AI-Powered Coaching Features

The TimeWell backend includes several AI-powered coaching features:

### Event Analysis
The `/events/analyze` endpoint allows users to get AI-powered analysis of their events in relation to their goals. This feature uses LangChain with GPT-4 to analyze how well an event aligns with the user's goals and provides suggestions for improvement.

### Culturally Relevant Voice Styles

TimeWell provides AI coaching with culturally relevant voice styles specifically designed for the African American community:

- `cool_cousin`: Young, hip mentor who keeps it real with contemporary language, using African American cultural references and modern slang appropriately.
- `og_big_bro`: Experienced, protective guide with street wisdom who balances tough love with deep encouragement, using occasional AAVE naturally.
- `oracle`: Wise, spiritual advisor connected to ancestral knowledge, drawing on African and African American spiritual traditions.
- `motivator`: Energetic, passionate coach focused on empowerment, channeling the energy of motivational speakers in Black churches and communities.
- `wise_elder`: Patient, nuanced mentor with deep historical perspective who provides context from historical struggles and achievements of Black Americans.

### Voice Style Integration

The voice styles are integrated throughout the TimeWell system:

- `GET /voice-styles` - Get a list of all available voice styles
- All AI-powered coaching responses can be customized with a voice style parameter

### LangChain Implementation

TimeWell uses LangChain for structured AI interactions using a flexible chain factory pattern:

- **ChainFactory Service**: Centralizes chain creation logic with support for different models and voice styles
- **PromptTemplateManager**: Manages culturally relevant prompt templates for different voice styles
- **Structured Output Parsing**: Uses LangChain's output parsers to ensure consistent response formats

Example:
```python
# Creating a chain with a specific voice style and output parser
chain_config = chain_factory.create_parser_chain(
    human_template="Answer this question: {question}",
    response_schemas=response_schemas,
    voice_style="cool_cousin"
)
```

### Direct OpenAI API Integration

For specific use cases, TimeWell also offers direct OpenAI API integration through the CoachService:

- `POST /coach/ask` - Ask the coach a direct question with specified voice style
- `GET /coach/weekly-review` - Get a personalized weekly review with specified voice style
- `POST /coach/action-plan` - Generate an action plan with specified voice style using structured JSON output

### Culturally Relevant Fallback Messages

TimeWell includes a robust fallback message system to ensure the application remains functional even when AI services are unavailable:

- **Voice-Style Consistency**: Fallback messages maintain the same culturally relevant voice styles as the AI responses
- **Context-Aware Fallbacks**: Different types of fallback messages for different use cases (analysis, suggestions, weekly reviews, etc.)
- **Automatic Recovery**: Services automatically switch to fallback messages when AI calls fail
- **Transparency**: Responses include a `fallback` flag so the frontend can indicate when a fallback was used

Example of a fallback message from the "Oracle" voice style:
```
Though the analysis is veiled from me now, I feel the intentionality in your actions.
Listen to the wisdom that already resides within you.
```

### Coach Reflections
The `/coach/reflect` endpoint creates personalized reflections for users based on their data and specified time period. The reflections can be:
- Weekly reflections
- Monthly reflections
- Current status updates

### Personalized Feedback and Encouragement
The coach provides personalized feedback and encouragement using the user's preferred coaching style:

- `/coach/feedback` - Generates feedback on specific areas with suggestions for improvement
- `/coach/encourage` - Generates encouraging messages for user achievements

All coach communications are tailored to match the user's preferred coaching style:
- Motivational: Energetic and encouraging
- Supportive: Warm and nurturing
- Direct: Clear and concise
- Analytical: Fact-based and logical
- Friendly: Conversational and casual

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

## AI Event Analysis

The `/events/analyze` endpoint allows users to get AI-powered analysis of their events in relation to their goals. This feature uses LangChain with GPT-4 to analyze how well an event aligns with the user's goals and provides suggestions for improvement.

### How it works

1. The user sends a POST request to `/events/analyze` with an event ID
2. The system retrieves the event details and the user's goals
3. LangChain processes the data through a structured prompt template
4. GPT-4 analyzes the alignment between the event and goals using the template
5. The output is parsed using LangChain's structured output parser
6. The analysis is saved to the `suggestions` collection for future reference
7. The API returns an analysis including:
   - Alignment score (1-10)
   - Which goals are aligned with the event
   - Brief analysis of the alignment
   - Suggestion to improve alignment
   - Potential new goal suggestion if no alignment is found

### LangChain Integration Benefits

- **Structured prompts**: Uses ChatPromptTemplate with system and human message components
- **Type-safe outputs**: Implements ResponseSchema and StructuredOutputParser for consistent response format
- **Reusable chain**: The LLMChain can be easily extended or modified for other analysis needs
- **Efficient processing**: Handles the prompt templating and response parsing in a streamlined way

### Setup Requirements

To use this feature, you need to:

1. Add a valid OpenAI API key to your `.env` file:
```
OPENAI_API_KEY=your_openai_api_key_here
```

2. Make an authenticated POST request to `/events/analyze` with the event ID:
```json
{
  "event_id": "your_event_id_here"
}
```

3. The response will include the analysis in JSON format and the suggestion will be saved to the database for future reference.

### Suggestion Management

Users can view and manage their suggestions using the `/suggestions` endpoints:

- Use `GET /suggestions` to retrieve all suggestions
- Mark a suggestion as applied with `PATCH /suggestions/{id}/apply`
- View suggestions for a specific event with `GET /suggestions/event/{event_id}` 