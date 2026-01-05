from celery import shared_task
from datetime import date, timedelta
from api.bookings.services.sync_reservations import sync_reservations
from api.bookings.services.payout_service import process_payout
from api.bookings.services.yield_pricing_service import calculate_yield_price
from api.bookings.services.pricing_service import push_pricing
from api.bookings.models import SyncLog,Booking,RoomInventory, AirbnbListing, AirbnbReservation
from api.bookings.services.airbnb_api import AirbnbAPI

@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=60)
def sync_airbnb_reservations():
    api = AirbnbAPI()
    for listing in AirbnbListing.objects.all():
        reservations = api.get_reservations(listing.listing_id)
        for r in reservations:
            AirbnbReservation.objects.update_or_create(
                reservation_id=r["id"],
                defaults={
                    "listing": listing,
                    "guest_name": r["guest_name"],
                    "checkin": r["checkin"],
                    "checkout": r["checkout"],
                    "total_amount": r["total_amount"],
                    "status": r["status"]
                }
            )

@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=60)
def push_airbnb_availability_pricing():
    api = AirbnbAPI()
    today = date.today()
    for listing in AirbnbListing.objects.all():
        # Example: next 7 days
        for i in range(7):
            target_date = today + timedelta(days=i)
            # Set dynamic pricing (simple example)
            price = listing.base_price
            api.update_pricing(listing.listing_id, target_date, price)
            api.update_availability(listing.listing_id, target_date, available=True)


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=60, retry_kwargs={'max_retries': 5})
def sync_reservations_task(self):
    try:
        sync_reservations()
        SyncLog.objects.create(task="sync_reservations", status="SUCCESS")
    except Exception as e:
        SyncLog.objects.create(task="sync_reservations", status="FAILED", message=str(e))
        raise




@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=60)
def process_payout_task(self, booking_id):
    booking = Booking.objects.get(id=booking_id)
    if not booking.payout_processed:
        process_payout(booking)


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=60)
def yield_pricing_task(self):
    inventories = RoomInventory.objects.select_related("room", "room__hotel")

    for inv in inventories:
        price = calculate_yield_price(inv.room, inv.date)
        push_pricing(inv.room.hotel, inv.room, inv.date, price)
