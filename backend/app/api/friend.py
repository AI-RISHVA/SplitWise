from fastapi import APIRouter, Depends ,HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.data import get_session
from app.models.user import User
from app.models.friend import Friend, FriendStatus
from app.schemas.friend import FriendRequestRequest, FriendRequestResponse, FriendSearchRequest
from app.api.settlement import get_pairwise_balance
# Security import
from app.api.auth import verify_token

router = APIRouter()

@router.post("/friend/search/")
def search_user_to_add(
    data: FriendSearchRequest,       #  ab query field use hoga
    db: Session = Depends(get_session), 
    username: str = Depends(verify_token)
):
    # ilike = case-insensitive partial match (jaise SQL ka LIKE '%query%')
    matches = db.execute(
        select(User).where(
            User.username.ilike(f"%{data.query}%"),
            User.username != username)).scalars().all()

    if not matches:
        return {"status": "No users found", "data": []}

    result = []
    for u in matches[:10]:      
        result.append({
            "firstname": u.firstname,
            "lastname": u.lastname,
            "username": u.username
        })

    return {"status": "Users found", "data": result}

# SEND FRIEND REQUEST
@router.post("/friend/send_request/")
def send_friend_request(
    data: FriendRequestRequest, 
    db: Session = Depends(get_session), 
    username: str = Depends(verify_token)
):
    # check kare k potane request mokle che?
    if username == data.friend_username:
        return {'error': "You cannot send a friend request to yourself."}

    # jene mokli che request e user register che?
    user_exists = db.execute(select(User).where(User.username == data.friend_username)).scalars().first()
    if not user_exists:
        return {'error': f"User '{data.friend_username}' does not exist."}

    # pending request already chale che bey ni vache?
    existing_relation = db.execute(
    select(Friend).where(
        ((Friend.sender_username == username) & (Friend.receiver_username == data.friend_username)) |
        ((Friend.sender_username == data.friend_username) & (Friend.receiver_username == username))
    )
).scalars().first()

    if existing_relation:
        if existing_relation.status == FriendStatus.REJECTED:
            db.delete(existing_relation)   # purani rejected request hata do, naya bhejne do
            db.flush()
        else:
            return {'error': f" relationship or request already exists with status: '{existing_relation.status}'."}



    db_friend = Friend(
        sender_username=username,
        receiver_username=data.friend_username,
        status=FriendStatus.PENDING
    )
    db.add(db_friend)
    db.commit()
    return {"status": "Success", "msg": f"Friend request sent successfully to '{data.friend_username}'."}


# ACCEPT/REJECT FRIEND REQUEST 
@router.put("/friend/respond_request/")
def respond_friend_request(
    data: FriendRequestResponse, 
    db: Session = Depends(get_session), 
    username: str = Depends(verify_token)
):
    # Database pase thi  pending request gote 
    statement = select(Friend).where(
        (Friend.sender_username == data.friend_username) &
        (Friend.receiver_username == username) &
        (Friend.status == FriendStatus.PENDING)
    )
    db_request = db.execute(statement).scalars().first()
    if not db_request:
        return {'error': f"No pending friend request found from user '{data.friend_username}'"}

    if data.action == FriendStatus.ACCEPTED:
        db_request.status = FriendStatus.ACCEPTED
        msg = f"You are now friends with '{data.friend_username}'"
    elif data.action == FriendStatus.REJECTED:
        db_request.status = FriendStatus.REJECTED
        msg = f"Friend request from '{data.friend_username}' has been rejected"
    else:
        raise HTTPException(status_code=400, detail="Action must be either 'accepted' or 'rejected'.")

    db.add(db_request)
    db.commit()
    return {"status": "Success", "msg": msg}


# # LIST FRIENDS 
@router.get("/friend/list/")
def list_all_friends(
    db: Session = Depends(get_session), 
    username: str = Depends(verify_token)
):
    statement = select(Friend).where(
    (Friend.status == FriendStatus.ACCEPTED) & 
    ((Friend.sender_username == username) | (Friend.receiver_username == username))
    )

    friends_records = db.execute(statement).scalars().all()
    
    friends_list = []
    for record in friends_records:
        actual_friend = record.receiver_username if record.sender_username == username else record.sender_username

        net = get_pairwise_balance(db, username, actual_friend)  

        friends_list.append({
            "username": actual_friend,
            "balance": net
        })

    return {
        "logged_in_user": username,
        "total_friends": len(friends_list),
        "friends": friends_list,
    }


# REMOVE FRIEND 
@router.delete("/friend/remove/")
def remove_friend(
    data: FriendRequestRequest, 
    db: Session = Depends(get_session), 
    username: str = Depends(verify_token)
):
    statement = select(Friend).where(
    (Friend.status == FriendStatus.ACCEPTED) & 
    (
        ((Friend.sender_username == username) & (Friend.receiver_username == data.friend_username)) |
        ((Friend.sender_username == data.friend_username) & (Friend.receiver_username == username))
    )
    )

    db_friend = db.execute(statement).scalars().first()
    if not db_friend:
        return {'error': f"User '{data.friend_username}' is not in your friend list."}

    net = get_pairwise_balance(db, username, data.friend_username)
    if abs(net) > 0.01:      # balance settle nathi to remove nai thava dey
        raise HTTPException(
            status_code=400,
            detail=f"Cannot remove {data.friend_username} — balance is not settled ({net}). Settle up first."
        )

    db.delete(db_friend)
    db.commit()
    return {"status": "Success", "msg": f"User '{data.friend_username}' has been successfully removed from your friend list."}



# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


