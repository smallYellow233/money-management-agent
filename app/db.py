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
import sqlite3
from typing import Any, Dict, List, Optional

DB_FILE_PATH = os.environ.get(
    "MONEY_AGENT_DB_PATH",
    os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "expenses.db"
    ),
)


def get_db_connection(db_path: str = DB_FILE_PATH) -> sqlite3.Connection:
    """Gets a connection to the SQLite database."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str = DB_FILE_PATH) -> None:
    """Initializes the database schemas for expenses and budgets."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        # Create expenses table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                note TEXT,
                date TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        # Create budgets table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS budgets (
                month TEXT PRIMARY KEY,
                limit_amount REAL NOT NULL
            )
            """
        )
        conn.commit()


def add_expense(
    amount: float, category: str, note: Optional[str], date: str, db_path: str = DB_FILE_PATH
) -> int:
    """Adds a new expense record to the database."""
    init_db(db_path)
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO expenses (amount, category, note, date) VALUES (?, ?, ?, ?)",
            (amount, category, note, date),
        )
        conn.commit()
        return cursor.lastrowid


def delete_expense(expense_id: int, db_path: str = DB_FILE_PATH) -> bool:
    """Deletes an expense record by its ID."""
    init_db(db_path)
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
        conn.commit()
        return cursor.rowcount > 0


def get_expenses_for_month(month: str, db_path: str = DB_FILE_PATH) -> List[Dict[str, Any]]:
    """Returns all expenses for a given month (format: YYYY-MM)."""
    init_db(db_path)
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        # Filter where date starts with YYYY-MM
        cursor.execute(
            "SELECT * FROM expenses WHERE date LIKE ? ORDER BY date DESC, id DESC",
            (f"{month}%",),
        )
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def get_expenses_summary(month: str, db_path: str = DB_FILE_PATH) -> Dict[str, Any]:
    """Computes category-wise and total expenses for a month, alongside the budget limit."""
    init_db(db_path)
    expenses = get_expenses_for_month(month, db_path)
    total_spent = sum(item["amount"] for item in expenses)
    
    category_totals: Dict[str, float] = {}
    for item in expenses:
        cat = item["category"]
        category_totals[cat] = category_totals.get(cat, 0.0) + item["amount"]
        
    budget = get_budget(month, db_path)
    
    return {
        "month": month,
        "total_spent": total_spent,
        "budget_limit": budget,
        "remaining_budget": budget - total_spent if budget is not None else None,
        "category_breakdown": category_totals,
        "transactions_count": len(expenses),
    }


def set_budget(month: str, limit_amount: float, db_path: str = DB_FILE_PATH) -> None:
    """Sets or updates the monthly budget limit (month format: YYYY-MM)."""
    init_db(db_path)
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO budgets (month, limit_amount) VALUES (?, ?)",
            (month, limit_amount),
        )
        conn.commit()


def get_budget(month: str, db_path: str = DB_FILE_PATH) -> Optional[float]:
    """Gets the budget limit for a specific month (month format: YYYY-MM)."""
    init_db(db_path)
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT limit_amount FROM budgets WHERE month = ?", (month,))
        row = cursor.fetchone()
        return row["limit_amount"] if row else None


def get_all_budgets(db_path: str = DB_FILE_PATH) -> List[Dict[str, Any]]:
    """Gets all budgets."""
    init_db(db_path)
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM budgets ORDER BY month DESC")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
