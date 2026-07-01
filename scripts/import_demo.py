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
import sys
import argparse

# Add root folder to sys.path so we can import app.db
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import db

def clear_db():
    conn = db.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM expenses")
    cursor.execute("DELETE FROM budgets")
    conn.commit()
    conn.close()
    print("Database cleared successfully!")

def load_balanced_june_2026():
    month = "2026-06"
    db.set_budget(month, 2000.00)
    
    # Generate realistic balanced transactions for June 2026
    txs = [
        (800.00, "Rent", "Monthly apartment rent", "2026-06-01"),
        (30.00, "Transportation", "Weekly transit pass", "2026-06-01"),
        (15.20, "Food", "Groceries at supermarket", "2026-06-02"),
        (12.50, "Food", "Lunch at Bento shop", "2026-06-03"),
        (150.00, "Shopping", "New running shoes", "2026-06-05"),
        (25.00, "Food", "Dinner with friend", "2026-06-05"),
        (50.00, "Entertainment", "Movie ticket & snacks", "2026-06-06"),
        (8.50, "Food", "Coffee & pastry", "2026-06-06"),
        (35.00, "Food", "Sunday brunch buffet", "2026-06-07"),
        (40.00, "Transportation", "Gas fill up", "2026-06-08"),
        (14.00, "Food", "Subway sandwich meal", "2026-06-09"),
        (50.00, "Others", "Haircut salon", "2026-06-10"),
        (22.30, "Food", "Supermarket grocery haul", "2026-06-12"),
        (40.00, "Entertainment", "Arcade and bowling night", "2026-06-13"),
        (80.00, "Shopping", "Summer t-shirts", "2026-06-14"),
        (18.90, "Food", "Dinner takeout", "2026-06-15"),
        (120.00, "Utilities", "Electricity & gas bill", "2026-06-15"),
        (30.00, "Transportation", "Weekly transit pass", "2026-06-15"),
        (30.00, "Food", "Sushi lunch", "2026-06-18"),
        (60.00, "Entertainment", "Concert ticket", "2026-06-20"),
        (12.00, "Food", "Breakfast bakery run", "2026-06-20"),
        (45.00, "Food", "Family dinner", "2026-06-22"),
        (30.00, "Transportation", "Weekly transit pass", "2026-06-22"),
        (120.00, "Shopping", "Wireless headphones", "2026-06-23"),
        (16.50, "Food", "Lunch wrap and drink", "2026-06-25"),
        (45.00, "Entertainment", "Board game meetup", "2026-06-27"),
        (28.00, "Food", "Dinner pizza delivery", "2026-06-28"),
        (40.00, "Transportation", "Gas fill up", "2026-06-29"),
        (15.00, "Food", "Coffee beans purchase", "2026-06-30")
    ]
    
    for amount, cat, note, date in txs:
        db.add_expense(amount, cat, note, date)
        
    print(f"Loaded Balanced Spending Demo for {month}:")
    print(f"  - Budget set to $2000.00")
    print(f"  - Loaded {len(txs)} transactions totaling $1975.90 (Within Budget!)")

def load_overbudget_june_2026():
    month = "2026-06"
    db.set_budget(month, 1500.00)
    
    # Overbudget spending demo
    txs = [
        (800.00, "Rent", "Monthly apartment rent", "2026-06-01"),
        (50.00, "Transportation", "Taxi rides", "2026-06-02"),
        (45.00, "Food", "Steak dinner", "2026-06-03"),
        (350.00, "Shopping", "Designer jacket", "2026-06-05"),
        (180.00, "Shopping", "Luxury sunglasses", "2026-06-08"),
        (120.00, "Entertainment", "Amusement park ticket", "2026-06-10"),
        (65.00, "Food", "Fancy wine dinner", "2026-06-12"),
        (150.00, "Utilities", "Summer AC high electricity", "2026-06-15"),
        (220.00, "Shopping", "Mechanical gaming keyboard", "2026-06-18"),
        (110.00, "Entertainment", "Music festival entry pass", "2026-06-20"),
        (85.00, "Food", "High-end sushi platter", "2026-06-25"),
        (50.00, "Others", "Premium streaming subscription", "2026-06-28")
    ]
    
    for amount, cat, note, date in txs:
        db.add_expense(amount, cat, note, date)
        
    print(f"Loaded Over-Budget Spending Demo for {month}:")
    print(f"  - Budget set to $1500.00")
    print(f"  - Loaded {len(txs)} transactions totaling $2225.00 (Over budget by $725.00!)")

def load_july_2026_draft():
    month = "2026-07"
    db.set_budget(month, 2000.00)
    
    # Add initial draft spending for the current month
    txs = [
        (800.00, "Rent", "Monthly rent for July", "2026-07-01"),
        (45.00, "Food", "First grocery trip of the month", "2026-07-01"),
        (15.00, "Transportation", "Metro card reload", "2026-07-01")
    ]
    
    for amount, cat, note, date in txs:
        db.add_expense(amount, cat, note, date)
        
    print(f"Loaded July 2026 (Current Month) initial draft:")
    print(f"  - Budget set to $2000.00")
    print(f"  - Loaded {len(txs)} transactions totaling $860.00")

def main():
    parser = argparse.ArgumentParser(description="Easy Count Demo Data Importer CLI")
    parser.add_argument(
        "--scenario",
        type=str,
        choices=["balanced", "overbudget", "current", "clear"],
        required=True,
        help="The testing scenario to load"
    )
    
    args = parser.parse_args()
    
    if args.scenario == "clear":
        clear_db()
    elif args.scenario == "balanced":
        clear_db()
        load_balanced_june_2026()
    elif args.scenario == "overbudget":
        clear_db()
        load_overbudget_june_2026()
    elif args.scenario == "current":
        load_july_2026_draft()
        
if __name__ == "__main__":
    main()
