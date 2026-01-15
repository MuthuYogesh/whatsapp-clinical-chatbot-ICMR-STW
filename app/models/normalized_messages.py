from pydantic import BaseModel

class NormalizedMessage(BaseModel):
    '''
    NormalizedMessage
    ├── channel: "whatsapp"
    ├── sender_id: "asf515151scasc515"
    ├── sender_name: "919715518841
    ├── message_id: "wamid..."
    ├── timestamp: 1767723392
    ├── message_type: "text"
    ├── content: "This is Muthu Yogesh"
    ├── raw_payload (optional, for audit/debug)
    '''

    channel: str
    sender_id: str
    sender_name: str
    message_id: str
    timestamp: int
    message_type: str
    content: str | None
    raw_payload: dict | None
