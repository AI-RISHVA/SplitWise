from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse

async def exception_middleware(request:Request ,call_next):
    try:
        response = await call_next(request)
        return response
    except HTTPException:
        raise 

    except Exception as error:
    
        return JSONResponse(
            status_code=500,
            content={
                "status":False,
                "message":"something went wrong",
                "data":None
            }
        )