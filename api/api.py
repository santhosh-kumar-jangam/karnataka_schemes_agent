from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google.adk.sessions import DatabaseSessionService
from google.adk.runners import Runner
from google.genai.types import Content, Part
from fastapi.responses import FileResponse
from agent import root_agent
import os
import json

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
print("db_path:", SESSIONS_DB_PATH)
session_service = DatabaseSessionService(db_url="sqlite:///" + SESSIONS_DB_PATH)

APP_NAME = "gov-scheme-app"
USER_ID = "User123"

# request body model
class AgentRequest(BaseModel):
    query: str
    session_id: str

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
            if session is None:
                session = await session_service.create_session(
                    app_name=APP_NAME,
                    user_id=USER_ID,
                    session_id=body.session_id
                )
                
        print("session object:", session)

        content = Content(role="user", parts=[Part(text=body.query)])

        events = runner.run_async(
            user_id=USER_ID,
            session_id=session.id,
            new_message=content
        )

        full_response_text = "No final response was received from the agent."
        pdf_download_url = None
        async for event in events:
            print("\n--- NEW AGENT EVENT ---")
            print(f"Author: {event.author}")
            
            if hasattr(event, 'content') and event.content:
                print(f"Content Parts: {[part.text for part in event.content.parts]}")
            print("-----------------------\n")
            print(f"Event received from: {event.author}")
            if not (event.content and event.content.parts):
                continue

            for part in event.content.parts:
                if hasattr(part, 'function_response') and part.function_response is not None:
                    
                    func_response = part.function_response
                    
                    # Now, safely check if this response object has a name and if it matches our target.
                    if hasattr(func_response, 'name') and func_response.name == 'generate_application_pdf':
                        
                        print(">>> INTERCEPTED 'generate_application_pdf' function response! <<<")
                        
                        # The tool's return value is in the 'response' attribute
                        tool_result = func_response.response
                        
                        if isinstance(tool_result, dict) and "filename" in tool_result:
                            filename = tool_result.get("filename")
                            if filename:
                                pdf_download_url = f"/download/application/{filename}"
                                print(f"Successfully constructed download URL: {pdf_download_url}")
                            else:
                                print("Warning: Tool output was valid, but 'filename' was empty.")
                        else:
                            print(f"Warning: Tool output was not a valid dict with 'filename' key. Got: {tool_result}")
            if event.is_final_response():
                if event.content and event.content.parts:
                    full_response_text = "".join(
                        part.text for part in event.content.parts
                    )
                else:
                    full_response_text = "Final response event had no content."
                break

        return {"response": full_response_text, "session_id": session.id, "download_url": pdf_download_url}

    except Exception as e:
        return {"error": str(e)}

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
    
@app.get("/download/application/{filename}")
async def download_application_pdf(filename: str):
    """ Serves a PDF file"""

    API_FOLDER_PATH = os.getenv("API_FOLDER_PATH")
    PROJECT_ROOT_PATH = os.getenv("PROJECT_ROOT_PATH")
    try:
        if ".." in filename or "/" in filename or "\\" in filename:
            raise HTTPException(status_code=400, detail="Invalid filename format.")

        # --- Create a list of paths to check ---
        # Path 1: Inside the 'api' folder
        path_in_api = os.path.join(API_FOLDER_PATH, filename)
        # Path 2: In the project's root folder
        path_in_root = os.path.join(PROJECT_ROOT_PATH, filename)

        possible_paths = [path_in_api, path_in_root]
        
        print(f"--- New Download Request for '{filename}' ---")

        # --- Loop through the possible paths and check if the file exists ---
        for file_path in possible_paths:
            print(f"Checking path: {file_path}")
            if os.path.exists(file_path):
                print(f"SUCCESS: File found at {file_path}")
                return FileResponse(path=file_path, filename=filename, media_type='application/pdf')
        
        # --- If the loop finishes and we haven't found the file ---
        print(f"ERROR: File '{filename}' not found in any of the checked locations.")
        raise HTTPException(status_code=404, detail=f"File not found.")
            
    except Exception as e:
        # This will print the REAL error to your console
        print("\n--- UNEXPECTED SERVER ERROR ---")
        import traceback
        traceback.print_exc()
        print("-----------------------------\n")
        raise HTTPException(status_code=500, detail=f"An internal error occurred: {str(e)}")