from fastapi import APIRouter, HTTPException
from app.portfolio.service import portfolio_service
from app.scripmaster.service import scrip_master
from app.core.exceptions import KotakAPIError
from typing import List, Dict

router = APIRouter(prefix="/portfolio", tags=["Portfolio"])

@router.get("/positions")
async def get_positions():
    try:
        data = await portfolio_service.get_positions()
        return data
    except KotakAPIError as e:
        if any(kw in str(e).lower() for kw in ["authenticated", "login", "session"]):
            raise HTTPException(status_code=401, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/holdings")
async def get_holdings():
    try:
        data = await portfolio_service.get_holdings()
        return data
    except KotakAPIError as e:
        if any(kw in str(e).lower() for kw in ["authenticated", "login", "session"]):
            raise HTTPException(status_code=401, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/limits")
async def get_limits():
    try:
        data = await portfolio_service.get_limits()
        return data
    except KotakAPIError as e:
        if any(kw in str(e).lower() for kw in ["authenticated", "login", "session"]):
            raise HTTPException(status_code=401, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
