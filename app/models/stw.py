from pydantic import BaseModel

class STWMetadata(BaseModel):
    id: str
    name: str
    description: str | None = None
