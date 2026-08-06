from pydantic import BaseModel

class RefreshTokenInput(BaseModel):
    refresh_token: str