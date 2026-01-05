from .booking_api import BookingAPI

def push_availability(hotel, room, date, available_units):
    api = BookingAPI()

    payload = {
        "room_id": room.booking_room_id,
        "date": str(date),
        "availability": available_units
    }

    api.update_availability(payload)
