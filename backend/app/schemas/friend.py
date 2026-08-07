from pydantic import BaseModel
from app.models.friend import FriendStatus # Database se Enum classes ko import kiya

class FriendRequestRequest(BaseModel):
    friend_username: str

class FriendSearchRequest(BaseModel):
    query: str   # LIKE search ke liye


class FriendRequestResponse(BaseModel):
    friend_username: str
    
    action: FriendStatus
    # YAHAN ENUM USE KIYA: Isse Swagger UI par dropdown menu automatic ban jayega
    # User ko 'pending', 'accepted', 'rejected' likhna nahi padega, chunnna padega
    