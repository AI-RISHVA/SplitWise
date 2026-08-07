from fastapi import APIRouter, Depends , HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.schemas.groups import GroupInfo , UpdateGroup
from app.db.data import get_session
from app.api.settlement import get_group_balances

# table import
from app.models.group import Group
from app.models.user import User
from app.models.expense import Expense

#security import
from app.api.auth import verify_token





router = APIRouter()
 ## app.inculde_router(user_routes) #a line main file ma lakhvi jethi a file na endpoints tya jova malse

# -----------------------------------------------------------

@router.post("/add_group/", status_code= 201)
def add_group(groupdata : GroupInfo , db: Session = Depends(get_session),username: str = Depends(verify_token)):  

    invalid_users = []
    for member_username in groupdata.groupmember:
        user_check = db.execute(select(User).where(User.username == member_username)).scalars().first()

        if not user_check:
            invalid_users.append(member_username)

    if invalid_users:
        raise HTTPException(
            status_code=400, 
            detail=f"{invalid_users} do not exist on this app. Register first."
        )

    unique_members = list(set(groupdata.groupmember))

    db_group = Group(
        group_name =groupdata.group_name,
        group_description=groupdata.group_description,
        groupmember = unique_members,
        admins = [username]

    )

    db.add(db_group) #db na session ma add kare
    
    db.commit() #db ma save kare
    
    db.refresh(db_group)  #data ne refresh kare jethi koi id bani hoy to db ma store thay
  
    return {'status':'adding your data succesfully', 'data' :groupdata,'created_by': username}


# ---------------------------------------------------------------------------



@router.put("/update_group/")
def update_group(
    groupdata: UpdateGroup,db: Session = Depends(get_session),username: str = Depends(verify_token)):

    statement = select(Group).where(Group.group_name == groupdata.group_name)
    db_group = db.execute(statement).scalars().first()

    if not db_group:
        return {'error': "not found the group name"}

    if username not in db_group.groupmember:
        raise HTTPException(
            status_code=403, 
            detail=f"Access Denied: You ('{username}') are not a member of this group, so you cannot edit it."
        )

    if groupdata.old_member and groupdata.new_member:
        if groupdata.old_member not in db_group.groupmember:
            return {'error': f"Member '{groupdata.old_member}' is not in this group."}

        user_check = db.execute(select(User).where(User.username == groupdata.new_member)).scalars().first()
        if not user_check:
            raise HTTPException(
                status_code=400, 
                detail=f"{groupdata.new_member} do not exist on this app. Register first."
            )

        updated_list = list(db_group.groupmember)
        index_to_replace = updated_list.index(groupdata.old_member)
        updated_list[index_to_replace] = groupdata.new_member
        db_group.groupmember = updated_list

    elif groupdata.groupmember:
        invalid_users = []
        for member_username in groupdata.groupmember:
            user_check = db.execute(select(User).where(User.username == member_username)).scalars().first()
            if not user_check:
                invalid_users.append(member_username)

        if invalid_users:
            raise HTTPException(
                status_code=400, 
                detail=f"{invalid_users} do not exist on this app. Register first."
            )
        db_group.groupmember = list(set(groupdata.groupmember))

    if groupdata.new_group_name:
        db_group.group_name = groupdata.new_group_name
        
    if groupdata.group_description:
        db_group.group_description = groupdata.group_description

    db.add(db_group)
    db.commit()
    db.refresh(db_group)
  
    return {'status': 'Updating your data successfully', 'current_group_data': db_group}


# ---------------------------------------------------------------------------

@router.post("/add_members/")
def Add(group_name: str, member: list[str] = [],db: Session = Depends(get_session),username: str = Depends(verify_token)):
    statement = select(Group).where(Group.group_name == group_name) #a ek quary che table ni field shosdhva mate ni
    group = db.execute(statement).scalars().first() #a line execute karse uper ni statement quary and .first no matlab k db ma j only pehlu resulf malse a apse
    if not group:
        return {'error':"not found the group name"}

    if username not in group.groupmember:          
        raise HTTPException(status_code=403, detail="You are not a member of this group.")

    updated_members = set(group.groupmember)
    
    for i in member:
        if i in group.groupmember:
            return{"msg": f" {i} is already in the group"}
        updated_members.add(i)

    group.groupmember = list(updated_members)

    db.add(group)
    db.commit()

    return {"msg":f"Successfully {member} added in {group_name} "}
 


# ---------------------------------------------------------------------------


@router.put("/remove_members/")
def Remove(group_name: str, member: list[str] = [] ,db: Session = Depends(get_session),username: str = Depends(verify_token)):
    statement = select(Group).where(Group.group_name == group_name)
    group = db.execute(statement).scalars().first()
    if not group:
            return {'error':"not found the group name"}
    
    if username not in group.groupmember:          
        raise HTTPException(status_code=403, detail=" You are not a member of this group.")

    current_members = set(group.groupmember)
    balances = get_group_balances(db, group_name)

    for j in member:
        if j not in current_members:
            return {"error": f"Member {j} is not in group."}
        if abs(balances.get(j, 0.0)) > 0.01:      
            raise HTTPException(
                status_code=400,
                detail=f"Cannot remove '{j}' — their balance is not settled (₹{balances.get(j)})."
            )

    group.groupmember = list(set(group.groupmember) - set(member))

    db.add(group)
    db.commit()
    db.refresh(group)
    return {"msg":f"{member} remove in {group_name} "}
   

# ----------------------------------------------------------------------



@router.get("/get_groups/")
def get_group(db: Session = Depends(get_session),username: str = Depends(verify_token)):
    all_groups = db.execute(select(Group)).scalars().all()
    result = {}
    for data in all_groups:
        if username not in data.groupmember: 
            continue

        balances = get_group_balances(db, data.group_name)   # 👈 NEW

        result[data.group_name] = {
            "group_name": data.group_name,
            "group_description": data.group_description,
            "groupmember":(list(data.groupmember)),
            "member": len(data.groupmember),
            "your_balance": balances.get(username, 0.0)      # 👈 NEW
        }
    return result

    
# ---------------------------------------------------------------


@router.delete("/delete_group/")
def group_del(group_name:str,db: Session = Depends(get_session),username: str = Depends(verify_token)):
    statement = select(Group).where(Group.group_name == group_name)
    group = db.execute(statement).scalars().first()
    if not group:
        return{'error':"group not exists"}
    if username not in (group.admins or []):
            raise HTTPException(status_code=403, detail=" Only group admins can delete this group.")

    balances = get_group_balances(db, group_name)
    unsettled = {m: b for m, b in balances.items() if abs(b) > 0.01}   # 👈 NEW
    if unsettled:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete group — balances are not settled: {unsettled}"
        )

    db.delete(group)
    db.commit()
    return{"msg":"succesfully delete the group"}


    
# ----------------------------------------------------------

@router.post("/leave_group/")
def leave_group(group_name: str, db: Session = Depends(get_session), username: str = Depends(verify_token)):
    statement = select(Group).where(Group.group_name == group_name)
    group = db.execute(statement).scalars().first()
    if not group:
        return {'error': "not found the group name"}

    if username not in group.groupmember:
        raise HTTPException(status_code=400, detail="You are not a member of this group.")

    balances = get_group_balances(db, group_name)
    if abs(balances.get(username, 0.0)) > 0.01:      # 👈 NEW
        raise HTTPException(
            status_code=400,
            detail=f"Cannot leave — your balance in this group is not settled (₹{balances.get(username)}). Settle up first."
        )
#   MEMBER LIST MATHI REMOVE
    if username in group.groupmember:
        group.groupmember.remove(username)

#   JO ADMIN HOY TO ADMIN LIST MATHI REMOVE THASE
    if group.admins and username in group.admins:
        group.admins.remove(username)

    db.add(group)
    db.commit()
    db.refresh(group)
    return {"msg": f"You have successfully left '{group_name}'"}

# ---------------------------------------------------------------

@router.get("/groups/{group_name}/details/")
def group_details(group_name: str, db: Session = Depends(get_session), username: str = Depends(verify_token)):
    statement = select(Group).where(Group.group_name == group_name)
    group = db.execute(statement).scalars().first()
    if not group:
        return {'error': "not found the group name"}

    if username not in group.groupmember:
        raise HTTPException(status_code=403, detail=" You are not a member of this group.")
    
    expense_records = db.execute(
        select(Expense).where(Expense.group_name == group_name, Expense.is_deleted == False)
    ).scalars().all()

    total_spend = 0.0
    for exp in expense_records:
        total_spend += exp.amount 

    expenses_list = [] 
    for exp in expense_records:
        exp_details = {
            "id": exp.id,
            "amount": exp.amount,
            "paid_by_name": exp.paid_by_name,
            "split_method": exp.split_method,
            "description": exp.description,
            "date": exp.date
        }
        expenses_list.append(exp_details) 
        

    return {
        "group_name": group.group_name,
        "group_description": group.group_description,
        "members": group.groupmember,
        "admins": group.admins,
        "total_members": len(group.groupmember),
        "total_spend": total_spend,
        "total_expenses": len(expenses_list),
        "expenses": expenses_list
    }
