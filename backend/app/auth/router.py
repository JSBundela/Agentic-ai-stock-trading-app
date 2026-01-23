from fastapi import APIRouter, HTTPException, Depends
from app.auth.service import AuthService, auth_service
from app.auth.schemas import ValidateMPINRequest, TokenResponse, TOTPLoginRequest

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/totp-login")
async def totp_login(data: TOTPLoginRequest):
    try:
        result = await auth_service.login_step_1(data.totp)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/validate-mpin")
async def validate_mpin(data: ValidateMPINRequest):
    try:
        result = await auth_service.validate_mpin(data.mpin)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/reload-scrip-master")
async def reload_scrip_master():
    """Manually reload scrip master from Kotak API."""
    try:
        from app.scripmaster.service import scrip_master
        await scrip_master.load_scrip_master()
        count = len(scrip_master.scrip_data) if scrip_master.scrip_data is not None else 0
        return {"message": f"Scrip master reloaded successfully", "records": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
