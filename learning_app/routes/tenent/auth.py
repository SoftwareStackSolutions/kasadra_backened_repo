from fastapi import APIRouter, Depends
from core.security import get_current_org

router = APIRouter(prefix="/tenant", tags=["Tenant Auth"])

@router.get("/me")
async def get_me(current_org: dict = Depends(get_current_org)):
    return {
        "org_id": current_org.get("org_id"),
        "email": current_org.get("email"),
        "domain": current_org.get("domain")
    }
