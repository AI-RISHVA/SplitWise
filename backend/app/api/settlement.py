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
# paid_to - nene paisa apa

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



def get_group_balances(db: Session, group_name: str):
    # ++++++++++++++++++
    group_record = db.execute(select(Group).where(Group.group_name == group_name)).scalars().first()
    if not group_record:
        return {'msg':"group not exists"}

    balance = {}
    for member in group_record.groupmember:
        balance[member] = 0.0

    

    # ++++++++++++++++++++++++
    expense_records = db.execute(select(Expense).where(Expense.group_name == group_name, Expense.is_deleted == False)).scalars().all()


    # Jisne expense pay kiya, uska balance badh jata hai (poora amount add) — usko baaki logo se lena hai.
    for i in expense_records:
        if i.paid_by_name in balance:
            balance[i.paid_by_name] += i.amount

        # Jin-jin members ka us expense me share tha, unka balance utna kam ho jata hai — unhe apna hissa dena hai.
        for member, share in i.split_details.items():
            if member in balance:
                balance[member] -= share
    # ++++++++++++++++++++++++
    settlement_records = db.execute(select(Settlement).where(Settlement.group_name == group_name)).scalars().all()
    for stl in settlement_records:
        if stl.paid_by in balance:
            balance[stl.paid_by] += stl.amount
        if stl.paid_to in balance:
            balance[stl.paid_to] -= stl.amount

    result = {}
    for member, bal in balance.items():
        result[member] = round(bal, 2)
    return result

def get_pairwise_balance(db: Session, user_a: str, user_b: str):
    
    # agar positive ho gaya -> user_b, user_a ko paisa dega
    # agar negative ho gaya -> user_a, user_b ko paisa dega
    net = 0.0

    # Pehle pata karo dono users kis-kis group me SAATH members hain
    all_groups = db.execute(select(Group)).scalars().all()

    common_groups = []
    for group in all_groups:
        if user_a in group.groupmember and user_b in group.groupmember:
            common_groups.append(group.group_name)

    # Agar koi common group nahi mila -> matlab dono ka kabhi paisa share hi nahi hua
    if not common_groups:
        return 0.0

    #  Un common groups ke sare EXPENSES nikalo (jo delete nahi hue)
    expenses = db.execute(
        select(Expense).where(
            Expense.group_name.in_(common_groups),
            Expense.is_deleted == False
        )
    ).scalars().all()

    # Har expense check karo -> kisne paid kiya, kiska share tha
    for exp in expenses:

        #  user_a ne paisa pay kiya, aur user_b ka bhi share tha
        # -> matlab user_b, user_a ka denhaar bana -> net BADHAO
        if exp.paid_by_name == user_a and user_b in exp.split_details:
            net = net + exp.split_details[user_b]

        # : user_b ne paisa pay kiya, aur user_a ka share tha
        # -> matlab user_a, user_b ka denhaar bana -> net GHATAO
        elif exp.paid_by_name == user_b and user_a in exp.split_details:
            net = net - exp.split_details[user_a]

    # Ab check karo already kitna ACTUAL CASH settle ho chuka hai
    settlements = db.execute(
        select(Settlement).where(Settlement.group_name.in_(common_groups))
    ).scalars().all()

    for stl in settlements:

        #  user_a ne user_b ko cash diya -> uska udhaar kam hua -> net BADHAO
        if stl.paid_by == user_a and stl.paid_to == user_b:
            net = net + stl.amount

        # user_b ne user_a ko cash diya -> uska udhaar kam hua -> net GHATAO
        elif stl.paid_by == user_b and stl.paid_to == user_a:
            net = net - stl.amount

    # Final result, 2 decimal tak round
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
        raise HTTPException(status_code=403, detail="You are not  member of this group.")

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

# net > 0  -> friend tumhara denhaar hai (usne tumhe dena hai)
# net < 0  -> tum friend ke denhaar ho (tumne usko dena hai)
# net == 0 -> dono barabar, kuch bhi baaki nahi

    if net > 0:
    # friend tumhe paisa dega
        msg = f"'{friend_username}' owes you {net}"

    elif net < 0:
    # tumhe friend ko paisa dena hai
    # abs() lagaya kyuki negative number ("-100") dikhana ajeeb lagega,
    # "-100" ki jagah sirf "100" dikhana hai
        msg = f"You owe '{friend_username}' {abs(net)}"

    else:
        msg = "All settled up"

    return {"friend": friend_username, "net_balance": net, "msg": msg}


# ------------------------------------------------------------------------------------

@router.get("/balances/overall/")
def get_overall_summary(db: Session = Depends(get_session), username: str = Depends(verify_token)):

    all_groups = db.execute(select(Group)).scalars().all()
    my_groups = [g for g in all_groups if username in g.groupmember]

    total_owed_to_me = 0.   # sab groups milake mujhe kitna total milna hai
    total_i_owe = 0.0      # sab groups milake mujhe kitna total dena hai
    group_wise = {}

    for g in my_groups:
        bal = get_group_balances(db, g.group_name)
        my_bal = bal.get(username, 0.0)
        group_wise[g.group_name] = my_bal

        if my_bal > 0:
            # positive matlab mujhe MILNA hai 
            total_owed_to_me += my_bal
        else:
            # negative matlab mujhe dena hai 
            total_i_owe += abs(my_bal)

    return {
        "username": username,
        "total_owed_to_me": round(total_owed_to_me, 2),
        "total_i_owe": round(total_i_owe, 2),
        "net_balance": round(total_owed_to_me - total_i_owe, 2),
        "group_wise_balance": group_wise
    }