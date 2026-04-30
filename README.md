
# AI-First CRM: HCP Interaction Module

This repository contains the end-to-end implementation of an AI-first Customer Relationship Management (CRM) module tailored for Life Sciences and Healthcare Professionals (HCPs). 

It features a dual-interface design where field representatives can log interactions manually via a highly structured form or purely through natural language using an intelligent chat assistant powered by **LangGraph** and **Groq (Gemma 2)**.

## 🚀 Tech Stack

### Frontend
*   **React (Vite)**: Lightning-fast development environment.
*   **Redux Toolkit**: Centralized state management for seamless sync between the AI chat and the form UI.
*   **CSS3**: Custom light-theme styling to match modern enterprise CRM standards, utilizing the **Google Inter** font.

### Backend
*   **Python + FastAPI**: High-performance asynchronous API.
*   **Uvicorn**: ASGI web server.
*   **LangGraph**: State-based orchestration for the AI agent to handle complex, multi-step tool execution safely.
*   **Groq API**: Utilizing the ultra-fast `llama-3.3-70b-versatile` LLM.
*   **SQLAlchemy**: ORM for database persistence (configured with SQLite for instant local setup, easily swappable to PostgreSQL/MySQL).

---

## 🛠️ AI Agent Architecture

The LangGraph agent is equipped with **5 specialized tools** to handle the CRM workflow:

1.  `log_interaction`: Parses natural language (e.g., "Met Dr. Smith, left 2 samples, sentiment was positive") and maps it to the 11-field CRM form.
2.  `edit_interaction`: Targets and updates specific fields if the user asks for a correction (e.g., "Actually, change the sentiment to neutral").
3.  `get_hcp_history`: Retrieves previous meeting notes and HCP specialties to provide context to the agent.
4.  `schedule_followup`: Automatically drafts follow-up calendar events.
5.  `check_compliance`: Verifies that the interaction summary does not violate Pharma medical-legal guidelines (e.g., off-label promotion).

---

## 💻 Installation & Setup

### Prerequisites
*   Python 3.10+
*   Node.js (v16+) & npm
*   A free API key from [Groq Console](https://console.groq.com/)

### 1. Backend Setup
Open a terminal and navigate to the root directory.
```bash
# Create and navigate to the backend folder (if not already there)
cd backend

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows use: .venv\Scripts\activate

# Install dependencies
pip install fastapi uvicorn langgraph langchain-groq pydantic python-dotenv sqlalchemy
```

**Set your Groq API Key:**
Create a `.env` file in the `backend/` directory and add your key:
```env
GROQ_API_KEY=gsk_your_actual_api_key_here
```

**Run the Backend Server:**
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
*The backend will be running at `http://localhost:8000`.*

### 2. Frontend Setup
Open a **new** terminal window and navigate to the root directory.
```bash
# Navigate to the frontend folder
cd frontend

# Install dependencies
npm install @reduxjs/toolkit react-redux axios

# Start the Vite development server
npm run dev
```
*The frontend will be running at `http://localhost:5173` (or the port Vite provides).*

---

## 🧪 How to Test the Application

1. Open the frontend in your browser. You will see the blank CRM form on the left and the AI Assistant on the right.
2. **Do not type in the left form manually.** 
3. In the chat box on the right, type a prompt like:
   > *"I met with Dr. John Doe today at 10:30 AM. We discussed OncoBoost Phase III results. I left 2 boxes of samples. The sentiment was very positive, and we agreed to follow up next week."*
4. Press **AI Log**.
5. Watch as the LangGraph agent parses the text, triggers the `log_interaction` tool, and **instantly populates the corresponding fields in the Redux form on the left**.
6. **Test Editing**: Type *"Actually, change the time to 2:00 PM and the sentiment to Neutral."* The AI will use the `edit_interaction` tool to update just those specific fields without wiping the rest of the form.
7. **Save**: Click the **Save Interaction to Database** button at the bottom of the form to persist the record via SQLAlchemy.

---

## 🗄️ Database Configuration (PostgreSQL / MySQL)

By default, the application uses **SQLite** (`crm.db`) so evaluators can run the project instantly without installing a local database server.

To switch to **PostgreSQL** or **MySQL** (as requested in the assignment requirements):

1. Open `backend/main.py`.
2. Locate the database setup section.
3. Swap the `SQLALCHEMY_DATABASE_URL` string:

**For PostgreSQL:**
```python
# pip install psycopg2-binary
SQLALCHEMY_DATABASE_URL = "postgresql://username:password@localhost/dbname"
```

**For MySQL:**
```python
# pip install pymysql
SQLALCHEMY_DATABASE_URL = "mysql+pymysql://username:password@localhost/dbname"
```

The SQLAlchemy ORM handles the rest automatically and will create the `interactions` table on startup.

---