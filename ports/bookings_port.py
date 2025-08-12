from typing import Iterable, Protocol

from domain.booking import Booking
from domain.user import User


class BookingRepository(Protocol):
    def get_user(self, incoming_user_id: int) -> User | None: ...

    def upsert_user(self, incoming_user: User) -> None: ...

    def list_all_users(self) -> Iterable[User]: ...

    def is_slot_free(self, incoming_date: str, incoming_time: str) -> bool: ...

    def create_booking(self, new_booking: Booking) -> None: ...

    def list_bookings_for_date(
        self, incoming_date: str
    ) -> list[tuple[int, Booking]]: ...
