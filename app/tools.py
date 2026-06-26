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

from typing import Dict, Any
from app import db
from app.pii_filter import mask_pii


def record_expense_tool(amount: float, category: str, note: str, date: str) -> Dict[str, Any]:
    """Records a new expense.

    Args:
        amount: The monetary amount spent. Must be positive.
        category: The expense category (e.g., Food, Transportation, Shopping, Entertainment, Utilities, Rent, Others).
        note: A short note describing the expense. Any potential PII (emails, phone numbers, etc.) will be masked.
        date: The date of the expense in YYYY-MM-DD format.

    Returns:
        A dictionary indicating the status and the recorded expense ID.
    """
    if amount <= 0:
        return {"status": "error", "message": "Amount must be greater than zero."}

    # Mask PII in the note
    masked_note = mask_pii(note)

    expense_id = db.add_expense(
        amount=amount,
        category=category,
        note=masked_note,
        date=date,
    )

    return {
        "status": "success",
        "message": f"Expense of ${amount:.2f} under category '{category}' recorded successfully.",
        "expense_id": expense_id,
    }


def delete_expense_tool(expense_id: int) -> Dict[str, Any]:
    """Deletes an existing expense record by ID.

    Args:
        expense_id: The unique integer ID of the expense record.

    Returns:
        A dictionary showing the status of the deletion.
    """
    success = db.delete_expense(expense_id)
    if success:
        return {"status": "success", "message": f"Expense ID {expense_id} deleted."}
    return {"status": "error", "message": f"Expense ID {expense_id} not found."}


def get_monthly_summary_tool(month: str) -> Dict[str, Any]:
    """Retrieves the spending summary and budget status for a specific month.

    Args:
        month: The target month in YYYY-MM format (e.g., 2026-06).

    Returns:
        A dictionary with total spending, remaining budget, and category-wise totals.
    """
    summary = db.get_expenses_summary(month)
    return {"status": "success", "summary": summary}


def set_monthly_budget_tool(limit_amount: float, month: str) -> Dict[str, Any]:
    """Sets or updates the spending budget limit for a specific month.

    Args:
        limit_amount: The maximum budget limit amount. Must be positive.
        month: The target month in YYYY-MM format (e.g., 2026-06).

    Returns:
        A dictionary indicating the status of setting the budget.
    """
    if limit_amount <= 0:
        return {"status": "error", "message": "Budget limit must be greater than zero."}

    db.set_budget(month, limit_amount)
    return {
        "status": "success",
        "message": f"Budget of ${limit_amount:.2f} set successfully for {month}.",
    }


def get_historical_data_for_advice() -> Dict[str, Any]:
    """Retrieves all budget and expense data to provide comprehensive advice.

    Returns:
        A dictionary containing all configured budgets and a listing of recent expenses.
    """
    all_budgets = db.get_all_budgets()
    
    # We fetch summaries for all months that have budgets configured
    summaries = []
    for b in all_budgets:
        month = b["month"]
        summary = db.get_expenses_summary(month)
        summaries.append(summary)
        
    return {
        "status": "success",
        "monthly_summaries": summaries,
    }
