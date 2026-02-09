from sqlalchemy import select
from models.tenent.subscription_plan import SubscriptionPlan
from database.db import async_session

PLANS = [
    {
        "plan_name": "Free",
        "price_usd": 0,
        "max_users": 5,
        "max_projects": 10,
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
        for plan in PLANS:
            result = await session.execute(
                select(SubscriptionPlan)
                .where(SubscriptionPlan.plan_name == plan["plan_name"])
            )
            existing = result.scalar_one_or_none()

            if existing:
                # 🔁 UPDATE
                for key, value in plan.items():
                    setattr(existing, key, value)
            else:
                # ➕ INSERT
                session.add(SubscriptionPlan(**plan))

        await session.commit()
