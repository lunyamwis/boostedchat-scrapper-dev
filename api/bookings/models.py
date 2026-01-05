from django.db import models

# Create your models here.

class Room(models.Model):
    booking_room_id = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class Booking(models.Model):
    booking_id = models.CharField(max_length=100, unique=True)
    host_number = models.CharField(max_length=255, null=True,blank=True)
    guest_name = models.CharField(max_length=255)
    guest_email = models.EmailField(null=True, blank=True)
    guest_phone_number = models.CharField(max_length=255, null=True, blank=True)
    checkin = models.DateField()
    checkout = models.DateField()
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    status = models.CharField(max_length=50)
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    max_price = models.DecimalField(max_digits=10, decimal_places=2)
    min_price = models.DecimalField(max_digits=10, decimal_places=2)
    payment_requested = models.BooleanField(default=False)


    def __str__(self):
        return f"{self.room.name}"

    

class SyncLog(models.Model):
    task = models.CharField(max_length=100)
    status = models.CharField(max_length=50)
    message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class Payout(models.Model):
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    commission = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)



class RoomInventory(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    date = models.DateField()
    total_units = models.PositiveIntegerField()
    booked_units = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("room", "date")

    @property
    def occupancy_rate(self):
        return self.booked_units / self.total_units if self.total_units else 0




class AirbnbListing(models.Model):
    listing_id = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=255)
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    min_price = models.DecimalField(max_digits=10, decimal_places=2)
    max_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.name

class AirbnbReservation(models.Model):
    reservation_id = models.CharField(max_length=100, unique=True)
    listing = models.ForeignKey(AirbnbListing, on_delete=models.CASCADE)
    guest_name = models.CharField(max_length=255)
    host_number = models.CharField(max_length=255, null=True, blank=True)
    checkin = models.DateField()
    checkout = models.DateField()
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=50)
    payout_processed = models.BooleanField(default=False)

    def __str__(self):
        return self.reservation_id
