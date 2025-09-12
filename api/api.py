from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google.adk.sessions import DatabaseSessionService
from google.adk.runners import Runner
from google.genai.types import Content, Part
from agent import root_agent
import os
import tempfile
import sqlite3

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
    
@app.get("/download/application/{filename}")
async def download_application_pdf(filename: str):
    """
    Serves a PDF file stored as a BLOB in the database using FileResponse
    """
    try:
        if ".." in filename or "/" in filename or "\\" in filename:
            raise HTTPException(status_code=400, detail="Invalid filename format.")

        # Connect to the SQLite database
        DB_PATH = os.getenv("APPLICATION_DB_PATH")
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Query the PDF blob using filename
        filename = filename[:-4]
        cursor.execute("SELECT application_pdf FROM applications WHERE application_uuid = ?", (filename,))
        result = cursor.fetchone()
        conn.close()

        if result and result[0]:
            pdf_bytes = result[0]

            # Write to a temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                tmp_file.write(pdf_bytes)
                tmp_path = tmp_file.name

            # Serve the file using FileResponse
            return FileResponse(path=tmp_path, filename=filename, media_type='application/pdf')

        else:
            raise HTTPException(status_code=404, detail="PDF not found in database.")

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"An internal error occurred: {str(e)}")

    
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