import json
import os
import tempfile
from collections.abc import Iterable
from pathlib import Path
from typing import TypedDict

from domain.booking import Booking
from domain.user import User
from ports.bookings_port import BookingRepository


class RawBooking(TypedDict):
    user_id: int
    date: str
    times: list[str]
    id: int


class RawUser(TypedDict):
    id: int
    first_name: str
    username: str


class RawData(TypedDict):
    users: list[RawUser]
    bookings: list[RawBooking]


class JsonBookingRepository(BookingRepository):

    def __init__(self, path: str):
        base = Path(__file__).resolve().parent
        self._path = (base / path).resolve()

    def __repr__(self) -> str:
        return f"Users: {[u for u in self._load()['users']]}\n\nBookings: {[d for d in self._load()['bookings']]}"

    def _make_default_dict(self) -> RawData:
        return {"users": [], "bookings": []}

    def _load(self) -> RawData:
        if not self._path.exists():
            return self._make_default_dict()
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
            users = data.get("users", [])
            bookings = data.get("bookings", [])
            if not isinstance(users, list) or not isinstance(bookings, list):
                return self._make_default_dict()
            return {"users": users, "bookings": bookings}
        except Exception:
            return self._make_default_dict()

    def _write(self, incoming_data: RawData) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        tmp_fd, tmp_path = tempfile.mkstemp(
            dir=str(self._path.parent), prefix=".tmp_", text=True
        )
        try:
            with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
                json.dump(incoming_data, f, ensure_ascii=False, indent=2)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_path, self._path)
        finally:
            try:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
            except OSError:
                pass

    def _normalize_times(self, times: list[str]):
        for time in times:
            if len(time.split(":")[0]) != 2 or len(time.split(":")[1]) != 2:
                times.remove(time)

        return sorted(
            set(times),
            key=lambda t: (int(t.split(":")[0]), int(t.split(":")[1])),
        )

    # User Methods
    def get_user(self, incoming_user_id: int) -> User | None:
        data = self._load()
        for user in data["users"]:
            if user["id"] == incoming_user_id:
                return User(user["id"], user["first_name"], user["username"])
        return None

    def upsert_user(self, incoming_user: User) -> None:
        json_data = self._load()

        # Create a dictionary representation of the incoming user
        incoming_user_obj: RawUser = {
            "id": incoming_user.id,
            "first_name": incoming_user.first_name,
            "username": incoming_user.username,
        }
        data_users = json_data["users"]

        for i, data_user in enumerate(data_users):
            # if user's id matches incoming user's id
            if data_user["id"] == incoming_user.id:
                # update existing user
                data_users[i] = incoming_user_obj
                break
        else:
            data_users.append(incoming_user_obj)

        self._write(json_data)

    def list_all_users(self) -> Iterable[User]:
        json_data = self._load()

        user_list: list[User] = []
        for user in json_data["users"]:
            new_user = User(user["id"], user["first_name"], user["username"])
            user_list.append(new_user)

        return user_list

    def is_slot_free(self, incoming_date: str, incoming_time: str) -> bool:
        data = self._load()

        for booking in data["bookings"]:
            if booking["date"] == incoming_date and incoming_time in booking["times"]:
                return False
        return True

    def list_bookings_for_date(self, incoming_date: str) -> list[tuple[int, Booking]]:
        json_data = self._load()
        sorted_list: list[RawBooking] = []

        for data_booking in json_data["bookings"]:
            if data_booking["date"] != incoming_date:
                continue

            for list_item in sorted_list:
                if list_item["user_id"] == data_booking["user_id"]:
                    list_item["times"].extend(data_booking["times"])
                    break
            else:
                sorted_list.append(
                    {
                        "id": data_booking["id"],
                        "user_id": data_booking["user_id"],
                        "date": data_booking["date"],
                        "times": list(data_booking["times"]),
                    }
                )

        booking_list: list[tuple[int, Booking]] = []

        for list_item in sorted_list:
            self._normalize_times(list_item["times"])

            booking_list.append(
                (
                    list_item["user_id"],
                    Booking(list_item["user_id"],list_item["date"],list_item["times"],list_item["id"])
                )
            )
        booking_list.sort(key=lambda x: x[0])
        return booking_list

    def create_booking(self, new_booking: Booking) -> Booking:
        json_data = self._load()
        json_bookings = json_data["bookings"]

        for json_booking in json_bookings:
            
            if (json_booking["date"] == new_booking.date and json_booking["user_id"] == new_booking.user_id):
                
                json_booking["times"].extend(new_booking.times)
                json_booking["times"] = self._normalize_times(json_booking["times"])
                self._write(json_data)

                return Booking(json_booking["user_id"], json_booking["date"], list(json_booking["times"]), json_booking["id"])

        next_id = max((b.get("id", 0) for b in json_bookings), default=0) + 1
        booking: RawBooking = {
            "id": next_id,
            "user_id": new_booking.user_id,
            "date": new_booking.date,
            "times": self._normalize_times(list(new_booking.times)),
        }
        
        json_bookings.append(booking)
        self._write(json_data)
        return Booking(booking["user_id"],booking["date"],list(booking["times"]),booking["id"])



