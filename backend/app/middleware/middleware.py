from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
import logging


logger = logging.getLogger("uvicorn.error")

async def exception_middleware(request:Request ,call_next):
    try:
        response = await call_next(request)
        return response
    
    except HTTPException as err:
        return JSONResponse(
            status_code=err.status_code, 
            content={
                "status": False,
                "message": err.detail,   
                "data": None
            }
        ) 

    except Exception as error:
        logger.error(f"Unhandled Server Crash: {str(error)}", exc_info=True)

        return JSONResponse(
            status_code=500,
            content={
                "status":False,
                "message":"something went wrong",
                "data":None
            }
        )