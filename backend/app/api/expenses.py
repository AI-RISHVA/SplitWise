from fastapi import APIRouter,Depends , HTTPException
from app.schemas.expenses import ExpenseCreate , SharedExpense
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.db.data import get_session

# table import
from app.models.expense import Expense  
from app.models.group import Group
from app.models.user import User

# security imports
from app.api.auth import verify_token


router = APIRouter()
# ##------------------------------------------------------------------------------------------
def calculate_split_details(expd: SharedExpense):

    if expd.split_method in ["unequally", "percentage"]:
        if not expd.split_details:
            raise HTTPException(status_code=400, detail="split_details is required for this split method")

        shared_set = set(expd.shared_by)
        details_set = set(expd.split_details.keys())

        if shared_set != details_set:
            extra_names = details_set - shared_set
            missing_names = shared_set - details_set
            error_details = "Names not match! "
            if extra_names:
                error_details += f"extra names in split_details : {list(extra_names)}. "
            if missing_names:
                error_details += f"names missing in split_details : {list(missing_names)}."
            raise HTTPException(status_code=400, detail=error_details)

    if expd.split_method == "equally":
        total_person = len(expd.shared_by)
        if total_person == 0:
            raise HTTPException(status_code=400, detail="shared_by list can't be empty")

        per_person_amount = expd.amount / total_person
        final_split_details = {i: per_person_amount for i in expd.shared_by}

        total_split = sum(final_split_details.values())
        if round(total_split, 2) != round(expd.amount, 2):
            raise HTTPException(status_code=400, detail=f"{total_split} is not equal match to {expd.amount}")

    elif expd.split_method == "unequally":
        total_split = sum(expd.split_details.values())
        if round(total_split, 2) != round(expd.amount, 2):
            raise HTTPException(status_code=400, detail=f"{total_split} is not equal match to {expd.amount}")

        final_split_details = expd.split_details

    elif expd.split_method == "percentage":
        total_split = sum(expd.split_details.values())
        if not (99.99 <= total_split <= 100.1):
            raise HTTPException(status_code=400, detail=f"{total_split}% is not equal match to 100%")

        final_split_details = {}
        for person, percentage in expd.split_details.items():
            final_split_details[person] = round((expd.amount * percentage) / 100, 2)

    else:
        raise HTTPException(status_code=400, detail="Invalid split_method. Use 'equally', 'unequally' or 'percentage'.")

    return final_split_details



@router.post("/add_expense/")
def add_expense(expd: SharedExpense, db: Session = Depends(get_session), username: str = Depends(verify_token)):
    # ---------- split calculation ----------
    final_split_details = calculate_split_details(expd)

    group_record = db.execute(select(Group).where(Group.group_name == expd.group_name)).scalars().first()
    user_record = db.execute(select(User).where(User.username == expd.paid_by)).scalars().first()

    if not group_record:
            raise HTTPException(status_code=404, detail=f"Group '{expd.group_name}' does not exist.")
       
    if not user_record:
        raise HTTPException(status_code=404, detail=f"User '{expd.paid_by}' does not exist.")

    group_members_set = set(group_record.groupmember) 
    wrong_member =[]
    for i in expd.shared_by:
        if i not in group_members_set:
            wrong_member.append(i)

    if wrong_member:
        raise HTTPException(status_code=400, detail=f"'{wrong_member}' is not member of '{expd.group_name}' group")

    if expd.paid_by not in group_members_set:
        raise HTTPException(status_code=400, detail=f"'{expd.paid_by}' is not a member of '{expd.group_name}' group")

    db_expense = Expense(
        group_id=group_record.id,
        group_name=expd.group_name,
        paid_by_id=user_record.id,
        amount=expd.amount,
        paid_by_name=expd.paid_by,
        split_method=expd.split_method,
        shared_by=expd.shared_by,
        split_details=final_split_details,
        description=expd.description,
        date=expd.date,
    )

    db.add(db_expense)
    db.commit()
    db.refresh(db_expense)

    return {
        'status': 'adding your data succesfully',
        'data': {
            'group_name': db_expense.group_name,
            'amount': db_expense.amount,
            'shared_by': db_expense.shared_by,
            'paid_by_name': db_expense.paid_by_name,
            'split_method': db_expense.split_method,
            'split_details': db_expense.split_details,
            'date': db_expense.date,
            'description': db_expense.description
        }
    }

# ------------------------------------------------------------------------------------------

@router.put("/update_expense/{expense_id}/")
def update_expense(expense_id: int, expd: SharedExpense, db: Session = Depends(get_session), username: str = Depends(verify_token)):

    db_expense = db.execute(select(Expense).where(Expense.id == expense_id, Expense.is_deleted == False)).scalars().first()
    if not db_expense:
        raise HTTPException(status_code=404, detail="Expense not found.")

    group_record = db.execute(select(Group).where(Group.group_name == db_expense.group_name)).scalars().first()
    is_admin = group_record and username in (group_record.admins or [])

    if db_expense.paid_by_name != username and not is_admin:
        raise HTTPException(status_code=403, detail="Only the person who paid, or a group admin, can edit this expense.")

    # naye group/user ka check (agar group_name badla ho)
    group_record = db.execute(select(Group).where(Group.group_name == expd.group_name)).scalars().first()
    user_record = db.execute(select(User).where(User.username == expd.paid_by)).scalars().first()

    if not group_record:
        raise HTTPException(status_code=404, detail=f"Group '{expd.group_name}' does not exist.")
    if not user_record:
        raise HTTPException(status_code=404, detail=f"User '{expd.paid_by}' does not exist.")

    group_members_set = set(group_record.groupmember)
    wrong_member = [i for i in expd.shared_by if i not in group_members_set]
    if wrong_member:
        raise HTTPException(status_code=400, detail=f"'{wrong_member}' is not member of '{expd.group_name}' group")
    if expd.paid_by not in group_members_set:
        raise HTTPException(status_code=400, detail=f"'{expd.paid_by}' is not a member of '{expd.group_name}' group")

    final_split_details = calculate_split_details(expd)

    db_expense.group_id = group_record.id
    db_expense.group_name = expd.group_name
    db_expense.paid_by_id = user_record.id
    db_expense.amount = expd.amount
    db_expense.paid_by_name = expd.paid_by
    db_expense.split_method = expd.split_method
    db_expense.shared_by = expd.shared_by
    db_expense.split_details = final_split_details
    db_expense.description = expd.description
    if expd.date:
        db_expense.date = expd.date

    db.add(db_expense)
    db.commit()
    db.refresh(db_expense)

    return {
        "status": "Success",
        "msg": "Expense updated successfully",
        "data": {
            "id": db_expense.id,
            "group_name": db_expense.group_name,
            "amount": db_expense.amount,
            "paid_by_name": db_expense.paid_by_name,
            "split_method": db_expense.split_method,
            "split_details": db_expense.split_details,
            "description": db_expense.description
        }
    }


# ------------------------------------------------------------------------------------------

@router.delete("/delete_expense/{expense_id}/")
def delete_expense(expense_id: int, db: Session = Depends(get_session), username: str = Depends(verify_token)):

    db_expense = db.execute(
        select(Expense).where(Expense.id == expense_id, Expense.is_deleted == False)
    ).scalars().first()
    if not db_expense:
        raise HTTPException(status_code=404, detail="Expense not found.")

    group_record = db.execute(select(Group).where(Group.group_name == db_expense.group_name)).scalars().first()
    is_admin = group_record and username in (group_record.admins or [])

    if db_expense.paid_by_name != username and not is_admin:
        raise HTTPException(status_code=403, detail="Only the person who paid, or a group admin, can delete this expense.")

    db_expense.is_deleted = True     # soft delete — data delete nahi hota, bas hide ho jata hai
    db.add(db_expense)
    db.commit()

    return {"status": "Success", "msg": "Expense deleted successfully."}
# ------------------------------------------------------------------------------------------------------------------------------------------
# 