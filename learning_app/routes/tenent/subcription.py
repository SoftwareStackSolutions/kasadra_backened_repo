from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from database.db import get_session
from models.tenent.onboarding import OnboardingSession
from models.tenent.subcription_plan import SubscriptionPlan
from datetime import datetime

router = APIRouter(prefix="/subscriptions", tags=["Subscription"])

@router.get("/")
async def get_subscription_plans(
    db: AsyncSession = Depends(get_session)
):
    result = await db.execute(
        select(SubscriptionPlan)
        .where(SubscriptionPlan.is_active == True)
    )
    plans = result.scalars().all()

    return {
        "plans": plans
    }

@router.post("/select")
async def select_subscription_plan(
    onboarding_id: int,
    subscription_plan_id: int,
    db: AsyncSession = Depends(get_session)
):
    # 1️⃣ Validate onboarding session
    result = await db.execute(
        select(OnboardingSession)
        .where(OnboardingSession.id == onboarding_id)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Invalid onboarding session",
                "error_code": "INVALID_SESSION"
            }
        )

    if session.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Session expired",
                "error_code": "SESSION_EXPIRED"
            }
        )

    # 2️⃣ Validate subscription plan
    plan_result = await db.execute(
        select(SubscriptionPlan)
        .where(
            SubscriptionPlan.id == subscription_plan_id,
            SubscriptionPlan.is_active == True
        )
    )
    plan = plan_result.scalar_one_or_none()

    if not plan:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Invalid subscription plan",
                "error_code": "INVALID_PLAN"
            }
        )

    # 3️⃣ Store selection
    session.subscription_plan_id = subscription_plan_id
    await db.commit()

    return {
        "message": "Subscription plan selected successfully",
        "subscription_plan_id": subscription_plan_id
    }

@router.get("/selected/{onboarding_id}")
async def get_selected_plan(
    onboarding_id: int,
    db: AsyncSession = Depends(get_session)
):
    result = await db.execute(
        select(OnboardingSession)
        .where(OnboardingSession.id == onboarding_id)
    )
    session = result.scalar_one_or_none()

    if not session or not session.subscription_plan_id:
        return {"selected_plan": None}

    return {
        "selected_plan_id": session.subscription_plan_id
    }
