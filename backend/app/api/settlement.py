from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.db.data import get_session

# table import
from app.models.group import Group
from app.models.user import User
from app.models.expense import Expense
from app.models.settlement import Settlement

# schema import
from app.schemas.settlement import SettlementCreate

# security import
from app.api.auth import verify_token


router = APIRouter()
# ------------------------------------------------------------------------------------

@router.post("/settle/", status_code=201)
def record_settlement(settle_data: SettlementCreate, db: Session = Depends(get_session), username: str = Depends(verify_token)):

    if settle_data.paid_to == username:
        raise HTTPException(status_code=400, detail="You cannot settle payment with yourself.")

    if settle_data.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be greater than zero.")

    group_record = db.execute(select(Group).where(Group.group_name == settle_data.group_name)).scalars().first() #group check karse
    receiver_record = db.execute(select(User).where(User.username == settle_data.paid_to)).scalars().first()  #group ni andar member che k nai a check karse

    if not group_record:
        raise HTTPException(status_code=404, detail=f"Group '{settle_data.group_name}' does not exist.")
    if not receiver_record:
        raise HTTPException(status_code=404, detail=f"User '{settle_data.paid_to}' does not exist.")

    if username not in group_record.groupmember or settle_data.paid_to not in group_record.groupmember:  
        raise HTTPException(status_code=400, detail="Both users must be members of this group.")

    db_settlement = Settlement(
        group_name=settle_data.group_name,
        paid_by=username,
        paid_to=settle_data.paid_to,
        amount=settle_data.amount
    )

    db.add(db_settlement)
    db.commit()
    db.refresh(db_settlement)

    return {
        "status": "Success",
        "msg": f"{username} paid {settle_data.amount} to {settle_data.paid_to}",
        "data": {
            "group_name": db_settlement.group_name,
            "paid_by": db_settlement.paid_by,
            "paid_to": db_settlement.paid_to,
            "amount": db_settlement.amount,
            "date": db_settlement.date
        }
    }


# ============ HELPER FUNCTIONS (inhe koi bhi file import karke use kar sakti hai) ============

def get_group_balances(db: Session, group_name: str):
    
    group_record = db.execute(select(Group).where(Group.group_name == group_name)).scalars().first()
    if not group_record:
        return {'msg':"group not exists"}

    balance = {member: 0.0 for member in group_record.groupmember}

    expense_records = db.execute(select(Expense).where(Expense.group_name == group_name, Expense.is_deleted == False)).scalars().all()

    for i in expense_records:
        if i.paid_by_name in balance:
            balance[i.paid_by_name] += i.amount
        for member, share in i.split_details.items():
            if member in balance:
                balance[member] -= share

    settlement_records = db.execute(select(Settlement).where(Settlement.group_name == group_name)).scalars().all()
    for stl in settlement_records:
        if stl.paid_by in balance:
            balance[stl.paid_by] += stl.amount
        if stl.paid_to in balance:
            balance[stl.paid_to] -= stl.amount

    return {member: round(bal, 2) for member, bal in balance.items()}


def get_pairwise_balance(db: Session, user_a: str, user_b: str):
   
    net = 0.0

    all_groups = db.execute(select(Group)).scalars().all()
    shared_group_names = [
        g.group_name for g in all_groups
        if user_a in g.groupmember and user_b in g.groupmember
    ]

    if not shared_group_names:
        return 0.0

    expense_records = db.execute(
        select(Expense).where(
            Expense.group_name.in_(shared_group_names),
            Expense.is_deleted == False
        )
    ).scalars().all()

    for exp in expense_records:
        if exp.paid_by_name == user_a and user_b in exp.split_details:
            net += exp.split_details[user_b]
        elif exp.paid_by_name == user_b and user_a in exp.split_details:
            net -= exp.split_details[user_a]

    settlement_records = db.execute(
        select(Settlement).where(Settlement.group_name.in_(shared_group_names))
    ).scalars().all()

    for stl in settlement_records:
        if stl.paid_by == user_a and stl.paid_to == user_b:
            net += stl.amount
        elif stl.paid_by == user_b and stl.paid_to == user_a:
            net -= stl.amount

    return round(net, 2)


# ------------------------------------------------------------------------------------

@router.get("/balances/group/{group_name}/")
def get_group_balance(group_name: str, db: Session = Depends(get_session), username: str = Depends(verify_token)):

    group_record = db.execute(select(Group).where(Group.group_name == group_name)).scalars().first()
    if not group_record:
        raise HTTPException(status_code=404, detail=f"Group '{group_name}' does not exist.")

    if username not in group_record.groupmember:
        raise HTTPException(status_code=403, detail="You are not a member of this group.")

    balance = get_group_balances(db, group_name)

    return {"group_name": group_name, "balances": balance}


# ------------------------------------------------------------------------------------

@router.get("/settlements/group/{group_name}/")
def get_settlement_history(group_name: str, db: Session = Depends(get_session), username: str = Depends(verify_token)):

    group_record = db.execute(select(Group).where(Group.group_name == group_name)).scalars().first()
    if not group_record:
        raise HTTPException(status_code=404, detail=f"Group '{group_name}' does not exist.")

    if username not in group_record.groupmember:
        raise HTTPException(status_code=403, detail="You are not a member of this group.")

    settlement_records = db.execute(select(Settlement).where(Settlement.group_name == group_name)).scalars().all()

    result = []
    for stl in settlement_records:
        result.append({
            "paid_by": stl.paid_by,
            "paid_to": stl.paid_to,
            "amount": stl.amount,
            "date": stl.date
        })

    return {"group_name": group_name, "history": result}


# ------------------------------------------------------------------------------------

@router.get("/balances/friend/{friend_username}/")
def get_friend_balance(friend_username: str, db: Session = Depends(get_session), username: str = Depends(verify_token)):

    if friend_username == username:
        raise HTTPException(status_code=400, detail="Cannot check balance with yourself.")

    friend_record = db.execute(select(User).where(User.username == friend_username)).scalars().first()
    if not friend_record:
        raise HTTPException(status_code=404, detail=f"User '{friend_username}' does not exist.")

    net = get_pairwise_balance(db, username, friend_username)

    if net > 0:
        msg = f"'{friend_username}' owes you {net}"
    elif net < 0:
        msg = f"You owe '{friend_username}' {abs(net)}"
    else:
        msg = "All settled up"

    return {"friend": friend_username, "net_balance": net, "msg": msg}


# ------------------------------------------------------------------------------------

@router.get("/balances/overall/")
def get_overall_summary(db: Session = Depends(get_session), username: str = Depends(verify_token)):

    all_groups = db.execute(select(Group)).scalars().all()
    my_groups = [g for g in all_groups if username in g.groupmember]

    total_owed_to_me = 0.0
    total_i_owe = 0.0
    group_wise = {}

    for g in my_groups:
        bal = get_group_balances(db, g.group_name)
        my_bal = bal.get(username, 0.0)
        group_wise[g.group_name] = my_bal

        if my_bal > 0:
            total_owed_to_me += my_bal
        else:
            total_i_owe += abs(my_bal)

    return {
        "username": username,
        "total_owed_to_me": round(total_owed_to_me, 2),
        "total_i_owe": round(total_i_owe, 2),
        "net_balance": round(total_owed_to_me - total_i_owe, 2),
        "group_wise_balance": group_wise
    }