import json
from pathlib import Path

from app.schemas.tool_outputs import CustomerProfile

CUSTOMER_DATA_PATH = Path("data/mock_customers.json")


def get_customer_profile(customer_id: str) -> CustomerProfile:
    customers = json.loads(CUSTOMER_DATA_PATH.read_text(encoding="utf-8"))

    for customer in customers:
        if customer["customer_id"] == customer_id:
            return CustomerProfile(**customer)

    return CustomerProfile(
        customer_id=customer_id,
        name="Unknown Customer",
        tier="unknown",
        region="unknown",
        account_status="unknown",
    )
