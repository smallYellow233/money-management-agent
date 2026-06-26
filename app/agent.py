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

import datetime
from zoneinfo import ZoneInfo

from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.genai import types

import os
import dotenv

# Load local .env variables
dotenv.load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

# Disable Vertex AI to use AI Studio API key
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "False"


from app.tools import (
    record_expense_tool,
    delete_expense_tool,
    get_monthly_summary_tool,
    set_monthly_budget_tool,
    get_historical_data_for_advice,
)

# Core instruction for the money management concierge
FINANCIAL_AGENT_INSTRUCTION = """
You are a Money Management Concierge, a helpful, secure, and friendly AI assistant designed to help users record, track, and summarize their personal expenses and budgets.

Your main tasks:
1. Help the user record their expenses using the `record_expense_tool`. Recommend categories like Food, Transportation, Shopping, Entertainment, Utilities, Rent, Others.
2. Help the user delete transactions when requested using `delete_expense_tool`.
3. Set monthly spending budgets using `set_monthly_budget_tool`.
4. Provide summaries of monthly budgets and spending via `get_monthly_summary_tool`.
5. Retrieve historical transaction data using `get_historical_data_for_advice` and provide smart saving recommendations or analysis for the incoming month.

Rules and Security Constraints:
- PII and Security: NEVER request or repeat passwords, bank account credentials, SSNs, or other sensitive personal info. If the user mentions them, acknowledge the input but redact or ignore the sensitive information.
- Scope: Restrict your advice to budget optimizations, savings tips, and expense trends. Avoid providing professional investment, stock, tax, or legal advice.
- Financial Disclaimer: At the end of any advice, recommendation, or spending summary, ALWAYS append the following exact disclaimer:
  "*Disclaimer: The suggestions provided are for informational purposes only and do not constitute professional financial advice.*"
"""

root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model="gemini-2.5-flash",  # Using the latest Gemini model as per operational guidelines
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=FINANCIAL_AGENT_INSTRUCTION,
    tools=[
        record_expense_tool,
        delete_expense_tool,
        get_monthly_summary_tool,
        set_monthly_budget_tool,
        get_historical_data_for_advice,
    ],
)

app = App(
    root_agent=root_agent,
    name="app",
)
