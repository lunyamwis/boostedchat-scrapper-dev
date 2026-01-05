from api.bookings.models import Booking, Room
from .booking_api import BookingAPI
from .payout_service import process_payout

def sync_reservations(payload):
    """
    Sync a single reservation from Booking.com webhook payload
    """
    r = payload  # webhook sends reservation object directly

    room, _ = Room.objects.get_or_create(
        booking_room_id=r["room_id"],
        defaults={"name": r.get("room_name", f"Room {r['room_id']}")}
    )

    booking,_ = Booking.objects.update_or_create(
        booking_id=r["id"],
        defaults={
            "guest_name": r.get("guest_name", "Guest"),
            "guest_email": r.get("guest_email"),  # store email here
            "guest_phone_number": r.get("guest_phone",""),
            "checkin": r["checkin"],
            "checkout": r["checkout"],
            "room": room,
            "status": r["status"]
        }
    )

    process_payout(booking)
