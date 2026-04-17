"""
Connector smoke tests — one task per tool.

Exercises the real implementation code via mocked Google API services,
following the same pattern as the rest of the test suite.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from unittest.mock import Mock, patch

# ── impl functions (no decorator unwrapping needed) ──────────────────────────
from gappsscript.apps_script_tools import _list_script_projects_impl


def _unwrap(tool):
    """Unwrap FunctionTool + decorators to the original async function."""
    fn = tool.fn if hasattr(tool, "fn") else tool
    while hasattr(fn, "__wrapped__"):
        fn = fn.__wrapped__
    return fn


# ── imports for decorated tools ───────────────────────────────────────────────
from gmail.gmail_tools import draft_gmail_message
from gdrive.drive_tools import list_drive_items
from gcalendar.calendar_tools import list_calendars
from gdocs.docs_tools import create_doc
from gsheets.sheets_tools import create_spreadsheet
from gslides.slides_tools import create_presentation
from gforms.forms_tools import create_form
from gtasks.tasks_tools import list_task_lists
from gchat.chat_tools import list_spaces


# ─────────────────────────────────────────────────────────────────────────────
# Gmail — draft a simple email
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_gmail_draft_email():
    mock_service = Mock()
    mock_service.users().drafts().create().execute.return_value = {"id": "draft_abc"}

    result = await _unwrap(draft_gmail_message)(
        service=mock_service,
        user_google_email="user@example.com",
        to="colleague@example.com",
        subject="Hello from connector test",
        body="This is a connector smoke test.",
        include_signature=False,
    )

    assert "Draft created" in result
    assert "draft_abc" in result


# ─────────────────────────────────────────────────────────────────────────────
# Drive — list items in root folder
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_drive_list_items():
    mock_service = Mock()
    mock_service.files().list().execute.return_value = {
        "files": [
            {
                "id": "file_001",
                "name": "My Document",
                "mimeType": "application/vnd.google-apps.document",
                "modifiedTime": "2026-01-01T00:00:00Z",
                "webViewLink": "https://docs.google.com/document/d/file_001/edit",
            }
        ]
    }

    # resolve_folder_id returns the folder_id unchanged for plain IDs / "root"
    with patch("gdrive.drive_tools.resolve_folder_id", return_value="root"), \
         patch("gdrive.drive_tools.build_drive_list_params", return_value={
             "q": "'root' in parents and trashed=false",
             "pageSize": 100,
             "fields": "nextPageToken, files(id,name,mimeType,modifiedTime,webViewLink)",
             "supportsAllDrives": True,
             "includeItemsFromAllDrives": True,
         }):
        result = await _unwrap(list_drive_items)(
            service=mock_service,
            user_google_email="user@example.com",
            folder_id="root",
        )

    assert "My Document" in result
    assert "file_001" in result


# ─────────────────────────────────────────────────────────────────────────────
# Calendar — list user's calendars
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_calendar_list_calendars():
    mock_service = Mock()
    mock_service.calendarList().list().execute.return_value = {
        "items": [
            {"id": "primary@example.com", "summary": "My Calendar", "primary": True},
            {"id": "work@example.com", "summary": "Work Calendar"},
        ]
    }

    result = await _unwrap(list_calendars)(
        service=mock_service,
        user_google_email="user@example.com",
    )

    assert "My Calendar" in result
    assert "Work Calendar" in result
    assert "Primary" in result


# ─────────────────────────────────────────────────────────────────────────────
# Docs — create a new document
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_docs_create_doc():
    mock_service = Mock()
    mock_service.documents().create().execute.return_value = {
        "documentId": "doc_xyz",
        "title": "Connector Test Doc",
    }

    result = await _unwrap(create_doc)(
        service=mock_service,
        user_google_email="user@example.com",
        title="Connector Test Doc",
    )

    assert "doc_xyz" in result
    assert "Connector Test Doc" in result


# ─────────────────────────────────────────────────────────────────────────────
# Sheets — create a new spreadsheet
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_sheets_create_spreadsheet():
    mock_service = Mock()
    mock_service.spreadsheets().create().execute.return_value = {
        "spreadsheetId": "sheet_123",
        "spreadsheetUrl": "https://docs.google.com/spreadsheets/d/sheet_123/edit",
        "properties": {"title": "Connector Sheet", "locale": "en_US"},
    }

    result = await _unwrap(create_spreadsheet)(
        service=mock_service,
        user_google_email="user@example.com",
        title="Connector Sheet",
    )

    assert "sheet_123" in result
    assert "Connector Sheet" in result


# ─────────────────────────────────────────────────────────────────────────────
# Apps Script — list script projects
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_appscript_list_projects():
    mock_service = Mock()
    mock_service.files().list().execute.return_value = {
        "files": [
            {
                "id": "script_001",
                "name": "My Automation Script",
                "createdTime": "2025-06-01T09:00:00Z",
                "modifiedTime": "2026-03-15T12:00:00Z",
            }
        ]
    }

    result = await _list_script_projects_impl(
        service=mock_service,
        user_google_email="user@example.com",
    )

    assert "My Automation Script" in result
    assert "script_001" in result


# ─────────────────────────────────────────────────────────────────────────────
# Slides — create a new presentation
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_slides_create_presentation():
    mock_service = Mock()
    mock_service.presentations().create().execute.return_value = {
        "presentationId": "pres_456",
        "title": "Connector Presentation",
        "slides": [{}],
    }

    result = await _unwrap(create_presentation)(
        service=mock_service,
        user_google_email="user@example.com",
        title="Connector Presentation",
    )

    assert "pres_456" in result
    assert "Connector Presentation" in result


# ─────────────────────────────────────────────────────────────────────────────
# Forms — create a new form
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_forms_create_form():
    mock_service = Mock()
    mock_service.forms().create().execute.return_value = {
        "formId": "form_789",
        "info": {"title": "Connector Survey"},
        "responderUri": "https://docs.google.com/forms/d/form_789/viewform",
    }

    result = await _unwrap(create_form)(
        service=mock_service,
        user_google_email="user@example.com",
        title="Connector Survey",
    )

    assert "form_789" in result
    assert "Connector Survey" in result


# ─────────────────────────────────────────────────────────────────────────────
# Tasks — list task lists
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_tasks_list_task_lists():
    mock_service = Mock()
    mock_service.tasklists().list().execute.return_value = {
        "items": [
            {"id": "tasklist_001", "title": "My Tasks", "updated": "2026-04-01T10:00:00Z"},
            {"id": "tasklist_002", "title": "Work Tasks", "updated": "2026-04-10T08:00:00Z"},
        ]
    }

    result = await _unwrap(list_task_lists)(
        service=mock_service,
        user_google_email="user@example.com",
    )

    assert "My Tasks" in result
    assert "Work Tasks" in result
    assert "tasklist_001" in result


# ─────────────────────────────────────────────────────────────────────────────
# Chat — list spaces
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_chat_list_spaces():
    mock_service = Mock()
    mock_service.spaces().list().execute.return_value = {
        "spaces": [
            {"name": "spaces/AAA", "displayName": "Engineering Team", "spaceType": "SPACE"},
            {"name": "spaces/BBB", "displayName": "Direct Message", "spaceType": "DIRECT_MESSAGE"},
        ]
    }

    result = await _unwrap(list_spaces)(
        service=mock_service,
        user_google_email="user@example.com",
    )

    assert "Engineering Team" in result
    assert "Direct Message" in result
    assert "spaces/AAA" in result
