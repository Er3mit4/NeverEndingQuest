# SPDX-FileCopyrightText: 2026 MoonlightByte
# SPDX-License-Identifier: Fair-Source-1.0

"""Conversation identity propagated from the game process to provider children."""

import os
import uuid


_ENV_NAME = "NEQ_OPENCODE_CONVERSATION_ID"


def current_conversation_id():
    value = os.environ.get(_ENV_NAME, "")
    try:
        return str(uuid.UUID(value))
    except (ValueError, AttributeError):
        value = str(uuid.uuid4())
        os.environ[_ENV_NAME] = value
        return value


def start_new_conversation():
    """Call when the game owner starts or restores an independent campaign."""
    value = str(uuid.uuid4())
    os.environ[_ENV_NAME] = value
    return value
