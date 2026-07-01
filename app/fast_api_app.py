# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import os

import google.auth
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from google.adk.cli.fast_api import get_fast_api_app
from google.cloud import logging as google_cloud_logging
from pydantic import BaseModel

from app.app_utils.telemetry import setup_telemetry
from app.app_utils.typing import Feedback

# DB & Agent imports
from app import db
from app.agent import root_agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

setup_telemetry()
try:
    _, project_id = google.auth.default()
except Exception:
    project_id = "mock-project"

try:
    logging_client = google_cloud_logging.Client()
    logger = logging_client.logger(__name__)
except Exception:
    # Local logger fallback if not running on GCP
    import logging
    logger = logging.getLogger(__name__)

allow_origins = (
    os.getenv("ALLOW_ORIGINS", "").split(",") if os.getenv("ALLOW_ORIGINS") else None
)

# Artifact bucket for ADK (created by Terraform, passed via env var)
logs_bucket_name = os.environ.get("LOGS_BUCKET_NAME")

AGENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# In-memory session configuration - no persistent storage
session_service_uri = None

artifact_service_uri = f"gs://{logs_bucket_name}" if logs_bucket_name else None

app: FastAPI = get_fast_api_app(
    agents_dir=AGENT_DIR,
    web=True,
    artifact_service_uri=artifact_service_uri,
    allow_origins=allow_origins,
    session_service_uri=session_service_uri,
    otel_to_cloud=True,
)
app.title = "money-management-agent"
app.description = "API for interacting with the Agent money-management-agent"

# Initialize Global Runner for Agent Chat
session_service = InMemorySessionService()
runner = Runner(
    agent=root_agent,
    app_name="app",
    session_service=session_service,
    auto_create_session=True,
)


# Pydantic Schemas
class BudgetRequest(BaseModel):
    limit_amount: float
    month: str


class ExpenseRequest(BaseModel):
    amount: float
    category: str
    note: str
    date: str


class ChatRequest(BaseModel):
    message: str
    session_id: str


# Custom Routes
@app.get("/dashboard", response_class=HTMLResponse)
def get_dashboard() -> str:
    """Serves the main Money Management Concierge HTML dashboard."""
    template_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "templates", "dashboard.html"
    )
    if not os.path.exists(template_path):
        raise HTTPException(status_code=404, detail="Dashboard template not found")
    with open(template_path, "r", encoding="utf-8") as f:
        return f.read()


@app.get("/api/summary")
def get_summary(month: str) -> dict:
    """Gets the budget and transaction summary for a month."""
    try:
        summary = db.get_expenses_summary(month)
        return {"status": "success", "summary": summary}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/transactions")
def get_transactions(month: str) -> dict:
    """Gets transaction history for a month."""
    try:
        transactions = db.get_expenses_for_month(month)
        return {"status": "success", "transactions": transactions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/budget")
def add_budget(req: BudgetRequest) -> dict:
    """Sets the monthly budget limit."""
    try:
        db.set_budget(req.month, req.limit_amount)
        return {"status": "success", "message": "Budget limit updated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/add-expense")
def add_expense(req: ExpenseRequest) -> dict:
    """Manually records a transaction."""
    try:
        from app.tools import record_expense_tool
        result = record_expense_tool(
            amount=req.amount,
            category=req.category,
            note=req.note,
            date=req.date,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/delete-expense/{expense_id}")
def delete_expense(expense_id: int) -> dict:
    """Deletes a transaction by ID."""
    try:
        from app.tools import delete_expense_tool
        result = delete_expense_tool(expense_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/agent-chat")
async def agent_chat(req: ChatRequest) -> dict:
    """Processes message requests through the ADK agent engine."""
    try:
        # Create session if not already existing
        session = await session_service.get_session(
            app_name="app", user_id="local_user", session_id=req.session_id
        )
        if not session:
            await session_service.create_session(
                app_name="app", user_id="local_user", session_id=req.session_id
            )


        # Dynamically inject current date context to resolve relative terms (today, yesterday, tomorrow)
        import datetime
        local_today = datetime.date.today().strftime("%Y-%m-%d")
        from app.agent import FINANCIAL_AGENT_INSTRUCTION
        root_agent.instruction = (
            f"{FINANCIAL_AGENT_INSTRUCTION}\n\n"
            f"IMPORTANT context: Today is {local_today}. Use this date as reference for relative dates. "
            f"E.g., if today is {local_today}, then 'today' refers to {local_today}, 'yesterday' refers to the day before, "
            f"and 'tomorrow' refers to the day after. Resolve relative terms to specific dates when calling tools."
        )

        new_msg = types.Content(
            role="user", parts=[types.Part.from_text(text=req.message)]
        )

        response_text = ""
        async for event in runner.run_async(
            user_id="local_user",
            session_id=req.session_id,
            new_message=new_msg,
        ):
            if event.is_final_response():
                if event.content and event.content.parts:
                    response_text += "".join(
                        p.text for p in event.content.parts if p.text
                    )

        if not response_text:
            response_text = "Transaction recorded or task updated."

        return {"status": "success", "response": response_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/feedback")
def collect_feedback(feedback: Feedback) -> dict[str, str]:
    """Collect and log feedback.

    Args:
        feedback: The feedback data to log

    Returns:
        Success message
    """
    if hasattr(logger, "log_struct"):
        logger.log_struct(feedback.model_dump(), severity="INFO")
    else:
        logger.info(feedback.model_dump())
    return {"status": "success"}


# Main execution
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.fast_api_app:app", host="0.0.0.0", port=8000, reload=True)
