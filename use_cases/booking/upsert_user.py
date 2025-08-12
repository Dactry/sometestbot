from domain.user import User
from ports.bookings_port import BookingRepository


def upsert_user(repo: BookingRepository, incoming_user: User):
    return repo.upsert_user(incoming_user)
