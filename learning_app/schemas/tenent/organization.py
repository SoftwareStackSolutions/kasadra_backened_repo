from pydantic import BaseModel
from typing import Optional
from decimal import Decimal


class SubscriptionPlanUpdate(BaseModel):
    plan_name: Optional[str] = None
    price_usd: Optional[Decimal] = None
    max_users: Optional[int] = None
    max_projects: Optional[int] = None
    reporting: Optional[str] = None
    support: Optional[str] = None
