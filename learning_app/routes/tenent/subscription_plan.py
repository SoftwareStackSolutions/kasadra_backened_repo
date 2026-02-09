from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database.db import get_session
from models.tenent.subscription_plan import SubscriptionPlan

router = APIRouter(
    prefix="/tenant/subscription-plans",
    tags=["Tenant Subscription"]
)

@router.get("/")
async def get_subscription_plans(
    db: AsyncSession = Depends(get_session)
):
    result = await db.execute(
        select(SubscriptionPlan).order_by(SubscriptionPlan.price_usd)
    )
    return result.scalars().all()
