from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from dtos.auth import UserClaims
from cognito import get_current_user
import uuid

router = APIRouter()

# In a real application, this DTO would be in a separate file (e.g., dtos/notes.py)
class Note(BaseModel):
    note_id: str
    tenant_id: str
    user_id: str
    content: str

class NoteCreateRequest(BaseModel):
    content: str

# Using a simple in-memory dictionary as a fake database for this example.
# The key is the tenant_id, and the value is a list of notes for that tenant.
NOTES_DB = {}


@router.post("/notes", response_model=Note, status_code=status.HTTP_201_CREATED)
def create_note(
    note_request: NoteCreateRequest,
    user: UserClaims = Depends(get_current_user),
) -> Note:
    """Creates a new note within the user's tenant."""
    if not user.tenant_id or not user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not belong to a tenant",
        )

    new_note = Note(
        note_id=str(uuid.uuid4()),
        tenant_id=user.tenant_id,
        user_id=user.user_id,
        content=note_request.content,
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
    """
    Retrieve a note by its ID.

    This endpoint enforces tenant isolation by ensuring the requested note
    belongs to the tenant ID present in the user's JWT.
    """
    if not user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not belong to a tenant",
        )

    tenant_notes = NOTES_DB.get(user.tenant_id, [])
    note = next((n for n in tenant_notes if n.note_id == note_id), None)

    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Note not found"
        )

    return note


@router.get("/notes", response_model=list[Note])
def list_notes(
    user: UserClaims = Depends(get_current_user),
) -> list[Note]:
    """
    List all notes for the user's tenant.

    The tenant is determined by the `tenant_id` claim in the user's JWT.
    """
    if not user.tenant_id:
        return [] # Or raise HTTPException, depending on desired behavior

    return NOTES_DB.get(user.tenant_id, [])
