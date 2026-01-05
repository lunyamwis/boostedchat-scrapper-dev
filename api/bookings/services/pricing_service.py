from booking_api import BookingAPI

def push_pricing(room, date, price):
    api = BookingAPI()

    payload = {
        "room_id": room.booking_room_id,
        "date": str(date),
        "price": float(price)
    }

    api.update_pricing(payload)
