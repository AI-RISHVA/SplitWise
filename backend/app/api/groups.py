from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.schemas.groups import GroupCreat
from app.db.data import get_session
# table import
from app.models.group import Group

router = APIRouter()
 ### app.inculde_router(user_routes) #a line main file ma lakhvi jethi a file na endpoints tya jova malse



@router.post("/add_group/")
def add_group(groupdata : GroupCreat , db: Session = Depends(get_session)):  
    db_group = Group(
        group_name =groupdata.group_name,
        group_description=groupdata.group_description,
        groupmember = groupdata.groupmember
    )
    db.add(db_group) #db na session ma add kare
    
    db.commit() #db ma save kare
    
    db.refresh(db_group)  #data ne refresh kare jethi koi id bani hoy to db ma store thay
  
    return {'status':'adding your data succesfully', 'data' :groupdata}


@router.post("/add_members/")
def Add(group_name: str, member: list[str] = [],db: Session = Depends(get_session)):
    statement = select(Group).where(Group.group_name == group_name) #a ek quary che table ni field shosdhva mate ni
    group = db.execute(statement).scalars().first() #a line execute karse uper ni statement quary and .first no matlab k db ma j only pehlu resulf malse a apse
    if not group:
        return {'error':"not found the group name"}
    updated_members = set(group.groupmember)
    
    for i in member:
        if i in group.groupmember:
            return{"msg": f" {i} is already in the group"}
        updated_members.add(i)

    group.groupmember = list(updated_members)

    db.add(group)
    db.commit()

    return {"msg":f"Successfully {member} added in {group_name} "}
    

@router.put("/remove_members/")
def Remove(group_name: str, member: list[str] = [] ,db: Session = Depends(get_session)):
    statement = select(Group).where(Group.group_name == group_name)
    group = db.execute(statement).scalars().first()
    if not group:
            return {'error':"not found the group name"}
    current_members = set(group.groupmember)
    for j in member:
        if j not in current_members:
            return {"error": f"Member {j} is not in group."}
    group.groupmember = list(set(group.groupmember) - set(member))

    db.add(group)
    db.commit()
    db.refresh(group)
    return {"msg":f"{member} remove in {group_name} "}
   

@router.get("/get_groups/")
def get_group(db: Session = Depends(get_session)):
    all_groups = db.execute(select(Group)).scalars().all()
    result = {}
    for data in all_groups:
        result[data.group_name] = {
            "group_name": data.group_name,
            "group_description": data.group_description,
            "groupmember":(list(data.groupmember)),
            "member": len(data.groupmember)  
        }
    return result

    


@router.delete("/delete_group/")
def group_del(group_name:str,db: Session = Depends(get_session)):
    statement = select(Group).where(Group.group_name == group_name)
    group = db.execute(statement).scalars().first()
    if not group:
        return{'error':"group not exists"}
    db.delete(group)
    db.commit()
    return{"msg":"succesfully delete the group"}
    


