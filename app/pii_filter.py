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

import re
from typing import Optional

# Regex for common PII patterns
EMAIL_REGEX = re.compile(r"[\w\.-]+@[\w\.-]+\.\w+")
PHONE_REGEX = re.compile(r"\+?\b(?:\d{1,3}[-. ]?)?\(?\d{2,4}\)?[-. ]?\d{3,4}[-. ]?\d{4}\b")
CREDIT_CARD_REGEX = re.compile(r"\b(?:\d[ -]*?){13,19}\b")
SSN_OR_ID_REGEX = re.compile(r"\b\d{3}-\d{2}-\d{4}\b|\b\d{9}\b")


def mask_pii(text: Optional[str]) -> Optional[str]:
    """Masks potential PII (emails, phone numbers, credit cards) in the given text.

    Args:
        text: The string to scrub.

    Returns:
        The text with PII masked (e.g., [EMAIL_REDACTED]), or None if input was None.
    """
    if not text:
        return text

    scrubbed = text
    # Redact credit card numbers
    scrubbed = CREDIT_CARD_REGEX.sub("[CARD_REDACTED]", scrubbed)
    # Redact emails
    scrubbed = EMAIL_REGEX.sub("[EMAIL_REDACTED]", scrubbed)
    # Redact phone numbers
    scrubbed = PHONE_REGEX.sub("[PHONE_REDACTED]", scrubbed)
    # Redact SSN or generic 9-digit IDs
    scrubbed = SSN_OR_ID_REGEX.sub("[ID_REDACTED]", scrubbed)

    return scrubbed


def contains_pii(text: Optional[str]) -> bool:
    """Checks if the text contains potential PII patterns.

    Args:
        text: The string to check.

    Returns:
        True if any PII pattern matches, False otherwise.
    """
    if not text:
        return False

    return bool(
        EMAIL_REGEX.search(text)
        or PHONE_REGEX.search(text)
        or CREDIT_CARD_REGEX.search(text)
        or SSN_OR_ID_REGEX.search(text)
    )
