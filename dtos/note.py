from pydantic import BaseModel, Field

from dtos.permissions import Role


class Note(BaseModel):
    note_id: str
    tenant_id: str
    user_id: str
    content: str



class NoteCreateRequest(BaseModel):
    content: str
