# 🕰️ TimeWell

**TimeWell** is an Afro-futuristic AI-powered life coach app that helps users—especially from underserved communities—align their time, habits, and goals with their purpose. Powered by GPT-4 and cultural intelligence, TimeWell is your soulful guide to reclaiming your time.

---

## 🌟 Mission

Empower people to stay focused, grow in purpose, and feel seen by technology that speaks their language.

---

## 📲 Core Features

| Category       | Features                                                                 |
|----------------|--------------------------------------------------------------------------|
| Smart Calendar | Sync with Apple/Google Calendar, check event alignment with goals        |
| AI Time Coach  | GPT-4 powered suggestions for optimized, purposeful time use             |
| Goal System    | Track goals in Fitness, Productivity, Wealth, and Learning               |
| Habit Tracker  | Build and maintain streaks for custom or template habits                 |
| Cultural Voices| Select AI coach tone: Cool Cousin, OG Big Bro, Oracle, etc.              |
| Motivation Feed| Daily cultural quotes, affirmations, and videos                          |
| Weekly Reports | View alignment %, habit data, and receive AI insights                    |

---

## 🎨 Design Style

- **Colors**: Charcoal Black, Rich Gold, Emerald Green, Sunset Red  
- **Fonts**: DM Serif / Jua (Headlines), Inter / Poppins (Body)  
- **Voice**: Affirming, soulful, culturally rooted  
- **UX Tone**: Like a trusted cousin, not a drill sergeant

---

## ⚙️ Tech Stack

| Layer       | Tech Stack                                         |
|-------------|----------------------------------------------------|
| Frontend    | React Native + Expo, Zustand/Redux, Tailwind       |
| Backend     | FastAPI (Python)                                   |
| Auth        | Firebase Auth or JWT                               |
| Database    | MongoDB Atlas                                      |
| AI Engine   | OpenAI GPT-4 via LangChain                         |
| Calendar API| EventKit (Apple), Google Calendar API              |
| Storage     | Firebase / Cloudinary                              |
| Hosting     | Render / Railway                                   |

---

## 🧠 AI Behavior

Coach voices are stored in the user profile and affect GPT prompt tone:
- **Cool Cousin**: “Chill and supportive”
- **OG Big Bro**: “Straight talk with love”
- **Oracle**: “Poetic wisdom”
- **Chill Therapist**: “Affirming and calm”

Example Prompt:
> “The user scheduled 2 hours of Netflix. Their goals are fitness and learning. Based on ‘cool_cousin’, suggest a better use of time.”

Example Response:
> “Yo, not sayin’ you can’t chill, but maybe cut Netflix by an hour and slide in 15 mins of reading. Stack those wins, you got this.”

---

## 🗃️ MongoDB Collections

- `users`
- `events`
- `habits`
- `suggestions`

Each collection ties to key user interactions, including goal alignment and AI coaching history.

---

## 🔌 API Routes

| Method | Route                    | Description                             |
|--------|--------------------------|-----------------------------------------|
| POST   | /auth/signup             | Register a user                         |
| POST   | /auth/login              | User login                              |
| POST   | /events                  | Add an event                            |
| GET    | /events/:user_id         | Fetch user’s calendar                   |
| POST   | /events/analyze          | AI analyzes event alignment             |
| POST   | /habits                  | Create a new habit                      |
| PUT    | /habits/:id              | Mark habit complete                     |
| GET    | /habits/:user_id         | Fetch user habits                       |
| GET    | /users/:id/goals         | Fetch user goals                        |
| POST   | /users/:id/goals         | Update user goals                       |
| GET    | /suggestions/:user_id    | View past AI feedback                   |
| POST   | /coach/reflect           | Submit a weekly reflection              |

---

## 🧱 Folder Structure (Recommended)

### Backend (`/backend`)
app/ ├── main.py ├── routers/ ├── models/ ├── schemas/ ├── services/ ├── core/ ├── utils/


### Frontend (`/frontend`)
/src ├── screens/ ├── components/ ├── context/ ├── hooks/ ├── services/


---

## 🚧 Development Checklist

### ✅ Backend
- [ ] Setup FastAPI project & MongoDB connection
- [ ] JWT/Firebase authentication
- [ ] Build out `/auth`, `/events`, `/habits`, `/suggestions`, `/coach` routes
- [ ] Integrate GPT-4 via LangChain
- [ ] Optional: Celery for reminders/summaries

### ✅ Frontend
- [ ] Initialize React Native project via Expo
- [ ] Implement screens: Onboarding, Home, Calendar, Goals, Coach, Reports
- [ ] Connect to backend APIs
- [ ] Animate components with culturally rich feedback
- [ ] Secure auth + token storage

---

## 🚀 Deployment

- FastAPI deployed via Railway or Render
- Mobile builds via EAS (Expo)
- Environment config via `.env`
- Documentation at `/docs` (FastAPI Swagger UI)


---

## 🗣️ License

This project is licensed under the **MIT License**.

