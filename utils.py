from models.sqlite import get_db
from models.sqlite.models import UnalteredHistory, Role
from datetime import datetime
import logging
import os
import google.generativeai as genai

genai.configure(api_key=os.getenv("GOOGLE_GENAI_API_KEY"))
model = genai.GenerativeModel("gemini-2.0-flash")

def create_summary(messages):
    input = f"""
    You are a helpful assistant that summarizes conversations.
    Please summarize the following messages in a concise manner, focusing on the main points and key information.
    Here are the messages:

    {messages}

    Please provide a summary that captures the essence of the conversation without losing important details.
    Do NOT say anything else or extra, just provide the summary.
    The summary should be in a single paragraph and should not exceed 100 words.
    """
    response = model.generate_content(input)
    return response.text.strip() if response and response.text else None

async def add_to_history(message: str, role: str, user_id: str, session_id: str, app_name: str, session_service):
    db_gen = get_db()     
    db = next(db_gen)     
    try:
        # adding the message to the database
        role = role.lower()
        db_message = UnalteredHistory(user_id= user_id, message = message, role=Role(role))
        db.add(db_message)
        db.commit()

        # adding the message to the session state
        session = session_service.get_session(
            app_name=app_name, user_id=user_id, session_id=session_id
        )

        message_history = session.state.get("message_history", [])

        if len(message_history) > 11:
            older_message_history = message_history[:8]
            newer_message_history = message_history[8:]

            summary = create_summary(older_message_history)

            if not summary:
                logging.warning("No summary created for older_message_history.")
                summary = "No summary available for messages prior to the latest ones."

            logging.info(f"Created summary of older_message_history: {summary}")

            summary_message = {
                "role": "prior_messages_summary",  
                "message": f"""
                The following message is a summary of the entire prior conversation, before the newest messages.
                {summary}
                """
            }

            final_message_history = [summary_message] + newer_message_history

            latest_message = {
                "role": role,
                "message": message,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

            final_message_history.append(latest_message)

            logging.info(f"Adding message to history: {message_history}")

            updated_state = session.state.copy()

            updated_state["message_history"] = final_message_history

            session_service.create_session(
                app_name=app_name,
                user_id=user_id,
                session_id=session_id,
                state=updated_state,
            )
        else:
            latest_message = {
                "role": role,
                "message": message,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            message_history.append(latest_message)

            logging.info(f"Adding message to history:\n{latest_message}")

            updated_state = session.state.copy()
            updated_state["message_history"] = message_history

            session_service.create_session(
                app_name=app_name,
                user_id=user_id,
                session_id=session_id,
                state=updated_state,
            )
    finally:
        db_gen.close()    


