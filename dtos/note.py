from pydantic import BaseModel, Field

from dtos.permissions import Role


class Note(BaseModel):
    note_id: str
    tenant_id: str
    user_id: str
    content: str
    permission: Role = Field(description="Permission for the note")


class NoteCreateRequest(BaseModel):
    content: str
