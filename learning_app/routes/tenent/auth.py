from fastapi import APIRouter, Depends
from core.security import get_current_org

router = APIRouter(tags=["Tenant Auth"])


@router.get("/me")

async def get_current_org(current_org=Depends(get_current_org)):
    return current_org
