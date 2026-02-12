from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database.db import get_session
from models.tenent.subscription_plan import SubscriptionPlan
from fastapi import HTTPException
from schemas.tenent.organization import SubscriptionPlanUpdate


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


## update subscription api

@router.put("/{plan_id}")
async def update_subscription_plan(
    plan_id: int,
    payload: SubscriptionPlanUpdate,
    db: AsyncSession = Depends(get_session)
):
    result = await db.execute(
        select(SubscriptionPlan).where(SubscriptionPlan.id == plan_id)
    )
    plan = result.scalar_one_or_none()

    if not plan:
        raise HTTPException(status_code=404, detail="Subscription plan not found")

    update_data = payload.dict(exclude_unset=True)

    for key, value in update_data.items():
        setattr(plan, key, value)

    await db.commit()
    await db.refresh(plan)

    return {
        "message": "Subscription plan updated successfully",
        "data": plan
    }
