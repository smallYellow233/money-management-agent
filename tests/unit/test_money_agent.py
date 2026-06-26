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
import tempfile
import pytest

from app import db
from app import pii_filter


@pytest.fixture
def temp_db():
    """Fixture that initializes a temporary database file and cleans it up afterward."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    
    # Initialize schema
    db.init_db(db_path=path)
    
    yield path
    
    # Clean up file
    if os.path.exists(path):
        os.remove(path)


def test_pii_filtering():
    # Test emails
    assert pii_filter.mask_pii("my email is test@domain.com") == "my email is [EMAIL_REDACTED]"
    
    # Test phone numbers
    assert pii_filter.mask_pii("call me at +1-555-019-2834") == "call me at [PHONE_REDACTED]"
    
    # Test credit card numbers
    assert pii_filter.mask_pii("cc number 1234-5678-9012-3456 here") == "cc number [CARD_REDACTED] here"
    
    # Check boolean functions
    assert pii_filter.contains_pii("test@domain.com") is True
    assert pii_filter.contains_pii("normal text note") is False


def test_db_operations(temp_db):
    # Test budget limit setting and retrieval
    db.set_budget("2026-06", 1000.0, db_path=temp_db)
    assert db.get_budget("2026-06", db_path=temp_db) == 1000.0
    
    # Test adding expenses
    exp_id1 = db.add_expense(amount=50.0, category="Food", note="Lunch", date="2026-06-15", db_path=temp_db)
    exp_id2 = db.add_expense(amount=200.0, category="Shopping", note="Shoes", date="2026-06-16", db_path=temp_db)
    
    assert exp_id1 > 0
    assert exp_id2 > 0
    
    # Test listing expenses for month
    expenses = db.get_expenses_for_month("2026-06", db_path=temp_db)
    assert len(expenses) == 2
    
    # Test summary logic
    summary = db.get_expenses_summary("2026-06", db_path=temp_db)
    assert summary["total_spent"] == 250.0
    assert summary["budget_limit"] == 1000.0
    assert summary["remaining_budget"] == 750.0
    assert summary["category_breakdown"]["Food"] == 50.0
    assert summary["category_breakdown"]["Shopping"] == 200.0
    
    # Test deleting expense
    delete_success = db.delete_expense(exp_id1, db_path=temp_db)
    assert delete_success is True
    
    expenses_after = db.get_expenses_for_month("2026-06", db_path=temp_db)
    assert len(expenses_after) == 1
    assert expenses_after[0]["id"] == exp_id2
