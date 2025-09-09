from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google.adk.sessions import DatabaseSessionService
from google.adk.runners import Runner
from google.genai.types import Content, Part
from agent import root_agent
import os

from dotenv import load_dotenv
load_dotenv()

app = FastAPI(title="Schemes Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SESSIONS_DB_PATH=os.getenv("SESSIONS_DB_PATH")
session_service = DatabaseSessionService(db_url="sqlite:///" + SESSIONS_DB_PATH)

APP_NAME = "gov-scheme-app"
USER_ID = "User123"

@app.post("/create-new-session")
async def create_new_session():
    try:
        # Create a brand new session
        session = await session_service.create_session(
            app_name=APP_NAME,
            user_id=USER_ID
        )
        return {
            "message": "New session created successfully",
            "session_id": session.id
        }
    except Exception as e:
        return {"error": str(e)}

# request body model
class AgentRequest(BaseModel):
    query: str
    session_id: str | None = None

@app.post("/agent/run")
async def run_agent(body: AgentRequest):
    try:
        # initialize runner
        runner = Runner(
            agent=root_agent,
            app_name=APP_NAME,
            session_service=session_service
        )

        # reuse session if provided, else create a new one
        if body.session_id:
            session = await session_service.get_session(app_name=APP_NAME, user_id=USER_ID ,session_id=body.session_id)
            if not session:
                return {"error": f"Session with id {body.session_id} not found"}
        else:
            session = await session_service.create_session(
                app_name=APP_NAME,
                user_id=USER_ID
            )

        content = Content(role="user", parts=[Part(text=body.query)])

        events = runner.run_async(
            user_id=USER_ID,
            session_id=session.id,
            new_message=content
        )

        full_response_text = "No final response was received from the agent."
        async for event in events:
            print(f"Event received from: {event.author}")
            if event.is_final_response():
                if event.content and event.content.parts:
                    full_response_text = "".join(
                        part.text for part in event.content.parts
                    )
                else:
                    full_response_text = "Final response event had no content."
                break

        return {"response": full_response_text, "session_id": session.id}

    except Exception as e:
        return {"error": str(e)}
    
@app.delete("/delete-session/{session_id}")
async def delete_session(session_id: str):
    try:
        deleted = await session_service.delete_session(
            app_name=APP_NAME,
            user_id=USER_ID,
            session_id=session_id
        )
        if deleted:
            return {"message": f"Session {session_id} deleted successfully"}
        else:
            return {"error": f"Session {session_id} not found"}
    except Exception as e:
        return {"error": str(e)}