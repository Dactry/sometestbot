from domain.booking import Booking
from ports.bookings_port import BookingRepository


def create_booking(repo: BookingRepository, booking_data: Booking):
    if not any(repo.is_slot_free(booking_data.date, t) for t in booking_data.times):
        raise ValueError("Some times are already booked")
    repo.create_booking(booking_data)
