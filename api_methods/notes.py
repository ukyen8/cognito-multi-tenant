from fastapi import APIRouter, Depends, HTTPException, status
from dtos.auth import UserClaims
from cognito import get_current_user
import uuid

from dtos.note import Note, NoteCreateRequest
from dtos.permissions import PERMISSION_SCORE

router = APIRouter()

# Using a simple in-memory dictionary as a fake database for this example.
# The key is the tenant_id, and the value is a list of notes for that tenant.
NOTES_DB: dict[str, list[Note]] = {}


@router.post(
    "/notes", response_model=Note, status_code=status.HTTP_201_CREATED
)
def create_note(
    note_request: NoteCreateRequest,
    user: UserClaims = Depends(get_current_user),
) -> Note:
    """Create a new note within the user's tenant."""
    new_note = Note(
        note_id=str(uuid.uuid4()),
        tenant_id=user.tenant_id,
        user_id=user.user_id,
        content=note_request.content,
        permission=user.cognito_groups[0]
    )

    if user.tenant_id not in NOTES_DB:
        NOTES_DB[user.tenant_id] = []
    NOTES_DB[user.tenant_id].append(new_note)

    return new_note


@router.get("/notes/{note_id}", response_model=Note)
def get_note_by_id(
    note_id: str,
    user: UserClaims = Depends(get_current_user),
) -> Note:
    """Retrieve a note by its ID."""
    tenant_notes = NOTES_DB.get(user.tenant_id, [])
    note = next((n for n in tenant_notes if n.note_id == note_id), None)

    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Note not found"
        )
    if PERMISSION_SCORE[user.cognito_groups[0]] < PERMISSION_SCORE[note.permission]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )
    return note


@router.get("/notes", response_model=list[Note])
def list_notes(
    user: UserClaims = Depends(get_current_user),
) -> list[Note]:
    """List all notes for the user's tenant."""
    if user.tenant_id not in NOTES_DB:
        return []

    all_notes = NOTES_DB.get(user.tenant_id)
    notes = []
    for note in all_notes:
        if PERMISSION_SCORE[user.cognito_groups[0]] >= PERMISSION_SCORE[note.permission]:
            notes.append(note)
    return notes
