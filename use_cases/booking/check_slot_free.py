from ports.bookings_port import BookingRepository


def check_slot_free(repo: BookingRepository, date: str, time: str) -> bool:
    return repo.is_slot_free(date, time)
