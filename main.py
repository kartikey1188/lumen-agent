from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware 
from models.pydantic.models import AgentInput
from google.adk.sessions import DatabaseSessionService
from google.adk.runners import Runner
from root_agent.agent import root_agent
from google.genai import types
from utils import add_to_history

try:
    load_dotenv() 
except Exception as e:
    raise HTTPException(status_code=500, detail=f"Error loading environment variables: {e}")

api = FastAPI()

# Enabling CORS for all origins
api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

db_url = "sqlite:///./my_agent_data.db"
session_service = DatabaseSessionService(db_url=db_url)

APP_NAME = "LUMEN_SLATE"
        
@api.get("/agent")
async def main(agent_input: AgentInput):
    try:
        initial_state = {
            "user_id": agent_input.user_id,
            "message_history": [],
        }

        existing_sessions = session_service.list_sessions(
        app_name=APP_NAME,
        user_id=agent_input.user_id,
        )

        if existing_sessions and len(existing_sessions.sessions) > 0:
            SESSION_ID = existing_sessions.sessions[0].id
            print(f"Continuing existing session: {SESSION_ID}")
        else:
            new_session = session_service.create_session(
                app_name=APP_NAME,
                user_id=agent_input.user_id,
                state=initial_state,
            )
            SESSION_ID = new_session.id
            print(f"Created new session: {SESSION_ID}")

        runner = Runner(
            agent=root_agent,
            app_name=APP_NAME,
            session_service=session_service,
        )

        user_message = agent_input.query.strip()

        try:
            add_to_history(user_message, 'user_message')
        except Exception as history_error:
            print(f"Error adding user message to history: {history_error}")

        content = types.Content(role="user", parts=[types.Part(text=agent_input.query)])

        try:
            async for event in runner.run_async(user_id=agent_input.user_id, session_id=SESSION_ID, new_message=content):
                if event.is_final_response():
                    if event.content and event.content.parts:
                        response = {
                            "agent_response": event.content.parts[0].text.strip(),
                            "user_id": agent_input.user_id,
                            "session_id": SESSION_ID
                        }

                        agent_message = event.content.parts[0].text.strip()

                        try:
                            add_to_history(agent_message, 'agent_message')
                        except Exception as history_error:
                            print(f"Error adding agent message to history: {history_error}")
                        
                        return  response
                    
        except Exception as e:
            print(f"Error during agent call: {e}")
            raise HTTPException(status_code=500, detail=f"Agent processing error: {str(e)}")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

print("API is running.")











