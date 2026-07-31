from fastapi import APIRouter,Depends , HTTPException
from app.schemas.expenses import ExpenseCreate , SharedExpense
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.db.data import get_session

# table import
from app.models.expense import Expense  
from app.models.group import Group
from app.models.user import User

router = APIRouter()

# ##------------------------------------------------------------------------------------------

@router.post("/add_expense/equal/")
def add_expense_equal(expd:ExpenseCreate ,db: Session = Depends(get_session)):

        if expd.split_method !="equally":
            raise HTTPException(status_code=400, detail="Invalid split method for this endpoint.")
        
        calculate_splite_detail={}
            
        total_person =len(expd.shared_by)
        
        if total_person == 0:
            raise HTTPException(status_code=400 , detail="shared_by list can't empty please enter the values")
        

        total_bill= expd.amount / total_person

        for i in expd.shared_by:
            calculate_splite_detail[i] = total_bill


        total_split=sum(calculate_splite_detail.values())

        if total_split != expd.amount:
            raise HTTPException(status_code=400, detail=f"{total_split}is not equal match to {expd.amount}")
    

    # -------------DATABASE

    
        group_record = db.execute(select(Group).where(Group.group_name == expd.group_name)).scalars().first()
        user_record = db.execute(select(User).where(User.username == expd.paid_by)).scalars().first()
            
        if not group_record:
            raise HTTPException(status_code=404, detail=f"Database Check Failed: Group '{expd.group_name}' does not exist.")
        if not user_record:
            raise HTTPException(status_code=404, detail=f"Database Check Failed: User '{expd.paid_by}' does not exist.")
        
        
        group_members_set = set(group_record.groupmember) 
    
    # Check karein ki kya shared_by ka koi banda group se bahar ka hai
        wrong_member =[]
        for i in expd.shared_by:
            if i not in group_members_set:
                wrong_member.append(i)
        if wrong_member:
            raise HTTPException(status_code=400, detail=f"Validation Error: ' {wrong_member}' is not member of '{expd.group_name}' group"
                )
        
        db_expense =Expense(
            group_id=group_record.id,
            group_name =expd.group_name, 
            paid_by_id=user_record.id,
            amount =expd.amount,
            paid_by_name=expd.paid_by,
            split_method=expd.split_method, 
            shared_by=expd.shared_by,
            split_details=calculate_splite_detail,
            description= expd.description,
            date=expd.date,
            
        )
        
        db.add(db_expense) #add in db session
        
        db.commit() #save in db
        
        db.refresh(db_expense)  #refresh the data to save any id is genrated
    
        return {'status':'adding your data succesfully',
                'message':f"{total_bill} pay to {expd.shared_by} ",
                'data': {
                'group_name': db_expense.group_name,
                'amount': db_expense.amount,
                'shared_by':db_expense.shared_by,
                'paid_by_name': db_expense.paid_by_name,
                'split_method': db_expense.split_method,
                'date': db_expense.date,
                'description': db_expense.description
                }
            }


# # ------------------------------------------------------------------------------------------

@router.post("/add_expense/unequal/")
def add_expense_unequal(expd:SharedExpense  ,db: Session = Depends(get_session)):
    if expd.split_method !="unequally":
        raise HTTPException(status_code=400, detail="Invalid split method for this endpoint.")
        
    
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
            

    if not expd.split_details: 
        raise HTTPException(status_code=400 , detail="unequally splite method need of split detail,enter the split detail")
            
    total_split=sum(expd.split_details.values())
            
    if total_split != expd.amount:
        raise HTTPException(status_code=400, detail=f"{total_split}is not equal match to {expd.amount}")


            # --------------------------DB SECTION------


    group_record = db.execute(select(Group).where(Group.group_name == expd.group_name)).scalars().first()
    
    user_record = db.execute(select(User).where(User.username == expd.paid_by)).scalars().first()
    
    if not group_record:
        raise HTTPException(status_code=404, detail=f"Database Check Failed: Group '{expd.group_name}' does not exist.")
    if not user_record:
        raise HTTPException(status_code=404, detail=f"Database Check Failed: User '{expd.paid_by}' does not exist.")
        
    db_expense =Expense(
    group_id=group_record.id,
    group_name =expd.group_name, 
    paid_by_id=user_record.id,
    amount =expd.amount,
    paid_by_name=expd.paid_by,
    split_method=expd.split_method, 
    shared_by=expd.shared_by,
    split_details=expd.split_details,
    description= expd.description,
    date=expd.date
    )
    
    db.add(db_expense) #db na session ma add kare
    
    db.commit() #db ma save kare
    
    db.refresh(db_expense)  #data ne refresh kare jethi koi id bani hoy to db ma store thay
  
    return {'status':'adding your data succesfully',
                'data': {
                'group_name': db_expense.group_name,
                'amount': db_expense.amount,
                'shared_by':db_expense.shared_by,
                'paid_by_name': db_expense.paid_by_name,
                'split_method': db_expense.split_method,
                'split_details':db_expense.split_details,
                'date': db_expense.date,
                'description': db_expense.description
                }}



# ------------------------------------------------------------------------------------
@router.post("/add_expense/percentage/")
def add_expense_percentage(expd:SharedExpense ,db: Session = Depends(get_session)):
    
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
    
    
    total_split = 0
    if expd.split_method !="percentage":
        raise HTTPException(status_code=400, detail="Invalid split method for this endpoint.")

    if not expd.split_details: 
        raise HTTPException(status_code=400 , detail="percentage splite method need of split detail,enter the split detail")
        
    total_split=sum(expd.split_details.values())
    
    
    if not (99.99 <= total_split <= 100.1):
        raise HTTPException(status_code=400, detail=f"{total_split}% is not equal match to 100%")
    rupees_split_details = {}
    for person, percentage in expd.split_details.items():
        rupees_split_details[person] = round((expd.amount * percentage) / 100, 2)
        
        
        
        # -------------------------DATABASE  QUART------------------------------------------------
        group_record = db.execute(select(Group).where(Group.group_name == expd.group_name)).scalars().first()

        user_record = db.execute(select(User).where(User.username == expd.paid_by)).scalars().first()

        if not group_record:
            raise HTTPException(status_code=404, detail=f"Database Check Failed: Group '{expd.group_name}' does not exist.")
        if not user_record:
            raise HTTPException(status_code=404, detail=f"Database Check Failed: User '{expd.paid_by}' does not exist.")
        
    db_expense =Expense(
        group_id=group_record.id,
        group_name =expd.group_name, 
        paid_by_id=user_record.id,
        amount =expd.amount,
        paid_by_name=expd.paid_by,
        split_method=expd.split_method, 
        shared_by=expd.shared_by,
        split_details=rupees_split_details,
        description= expd.description,
        date=expd.date,
        
    )
    
    db.add(db_expense) #db na session ma add kare
    
    db.commit() #db ma save kare
    
    db.refresh(db_expense)  #data ne refresh kare jethi koi id bani hoy to db ma store thay
  
    return {'status':'adding your data succesfully',
                'data': {
                'group_name': db_expense.group_name,
                'amount': db_expense.amount,
                'shared_by':db_expense.shared_by,
                'paid_by_name': db_expense.paid_by_name,
                'split_method': db_expense.split_method,
                'split_details':db_expense.split_details,
                'date': db_expense.date,
                'description': db_expense.description
                }}