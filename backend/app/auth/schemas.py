from pydantic import BaseModel, Field

class TOTPLoginRequest(BaseModel):
    totp: str = Field(description="6-digit TOTP from authenticator app", example="123456")
    
    class Config:
        json_schema_extra = {
            "example": {
                "totp": "123456"
            }
        }

class ValidateMPINRequest(BaseModel):
    mpin: str = Field(description="6-digit MPIN", example="123456")
    
    class Config:
        json_schema_extra = {
            "example": {
                "mpin": "123456"
            }
        }

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_token: str | None = None
    sid: str | None = None
