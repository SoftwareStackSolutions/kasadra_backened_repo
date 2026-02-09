from sqlalchemy import select
from database.db import async_session
from models.tenent.subscription_plan import SubscriptionPlan

PLANS = [
    {
        "plan_name": "Free",
        "price_usd": 0,
        "max_users": 3,
        "max_projects": 1,
        "reporting": "Basic",
        "support": "Community",
    },
    {
        "plan_name": "Team",
        "price_usd": 15,
        "max_users": 25,
        "max_projects": 10,
        "reporting": "Advanced",
        "support": "Email",
    },
]

async def seed_subscription_plans():
    async with async_session() as session:
        result = await session.execute(
            select(SubscriptionPlan.id).limit(1)
        )
        if result.first():
            return

        session.add_all(
            [SubscriptionPlan(**plan) for plan in PLANS]
        )
        await session.commit()
