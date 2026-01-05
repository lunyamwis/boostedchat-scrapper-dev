from datetime import date
from decimal import Decimal
from api.bookings.models import RoomInventory

def calculate_yield_price(room, target_date):
    inventory = RoomInventory.objects.get(
        room=room,
        date=target_date
    )

    occupancy = Decimal(inventory.occupancy_rate)

    # Base multipliers
    occupancy_multiplier = Decimal("1.0")
    days_to_checkin = (target_date - date.today()).days

    # Occupancy logic
    if occupancy > Decimal("0.80"):
        occupancy_multiplier += Decimal("0.30")
    elif occupancy > Decimal("0.60"):
        occupancy_multiplier += Decimal("0.15")
    elif occupancy < Decimal("0.30"):
        occupancy_multiplier -= Decimal("0.20")

    # Urgency logic
    if days_to_checkin < 3:
        occupancy_multiplier += Decimal("0.20")
    elif days_to_checkin < 7:
        occupancy_multiplier += Decimal("0.10")

    price = room.base_price * occupancy_multiplier

    # Clamp price
    price = max(room.min_price, min(price, room.max_price))

    return round(price, 2)
