import json
from pathlib import Path

import pytest

from adapters.json.json_booking_repository import JsonBookingRepository
from domain.booking import Booking
from domain.user import User

# -----------------------
# Helpers
# -----------------------

def read_raw_json(path: Path) -> dict:
    if not path.exists():
        return {"users": [], "bookings": []}
    return json.loads(path.read_text(encoding="utf-8"))


# -----------------------
# Tests: users
# -----------------------

def test_upsert_user_insert_and_update_no_duplicates(tmp_path: Path):
    db_path = tmp_path / "db.json"
    repo = JsonBookingRepository(str(db_path))

    # insert new
    repo.upsert_user(User(1, "Max", "max_d"))
    users = list(repo.list_all_users())
    assert len(users) == 1
    assert users[0].id == 1
    assert users[0].first_name == "Max"
    assert users[0].username == "max_d"

    # update same id
    repo.upsert_user(User(1, "Maksym", "max_d2"))
    users = list(repo.list_all_users())
    assert len(users) == 1
    assert users[0].id == 1
    assert users[0].first_name == "Maksym"
    assert users[0].username == "max_d2"

    # get_user
    u = repo.get_user(1)
    assert isinstance(u, User)
    assert u and u.first_name == "Maksym"


# -----------------------
# Tests: bookings - create, ids, merge
# -----------------------

def test_create_booking_assigns_incremental_id_and_persists(tmp_path: Path):
    db_path = tmp_path / "db.json"
    repo = JsonBookingRepository(str(db_path))

    # first booking -> id=1
    b1_in = Booking(1, "2025-08-12", ["10:00"])
    b1_out = repo.create_booking(b1_in)
    assert isinstance(b1_out, Booking)
    assert b1_out.id == 1
    assert b1_out.times == ["10:00"]

    # second booking (different user/date) -> id=2
    b2_out = repo.create_booking(Booking(2, "2025-08-12", ["11:00", "12:00"]))
    assert b2_out.id == 2
    assert b2_out.times == ["11:00", "12:00"]

    # check raw json persisted with ids
    raw = read_raw_json(db_path)
    assert "bookings" in raw
    assert {b["id"] for b in raw["bookings"]} == {1, 2}


def test_create_booking_merge_same_user_and_date_preserves_id(tmp_path: Path):
    db_path = tmp_path / "db.json"
    repo = JsonBookingRepository(str(db_path))

    # create base record
    out1 = repo.create_booking(Booking(1, "2025-08-12", ["09:00", "10:00"]))
    assert out1.id == 1
    assert out1.times == ["09:00", "10:00"]

    # merge into the same (user_id, date) - id must stay the same
    out2 = repo.create_booking(Booking(1, "2025-08-12", ["10:00", "11:00", "08:10"]))
    assert out2.id == out1.id == 1
    # times normalized (unique + sorted)
    assert out2.times == ["08:10", "09:00", "10:00", "11:00"]

    # raw json contains only ONE booking for that user/date
    raw = read_raw_json(db_path)
    same_user_date = [b for b in raw["bookings"] if b["user_id"] == 1 and b["date"] == "2025-08-12"]
    assert len(same_user_date) == 1
    assert same_user_date[0]["id"] == 1
    assert same_user_date[0]["times"] == ["08:10", "09:00", "10:00", "11:00"]


# -----------------------
# Tests: is_slot_free
# -----------------------

def test_is_slot_free_basic(tmp_path: Path):
    db_path = tmp_path / "db.json"
    repo = JsonBookingRepository(str(db_path))

    repo.create_booking(Booking(1, "2025-08-12", ["10:00"]))
    repo.create_booking(Booking(2, "2025-08-12", ["12:00"]))

    assert repo.is_slot_free("2025-08-12", "10:00") is False
    assert repo.is_slot_free("2025-08-12", "12:00") is False
    assert repo.is_slot_free("2025-08-12", "13:00") is True
    assert repo.is_slot_free("2025-08-13", "10:00") is True


# -----------------------
# Tests: list_bookings_for_date (aggregation & sorting)
# -----------------------

def test_list_bookings_for_date_aggregates_and_sorts(tmp_path: Path):
    db_path = tmp_path / "db.json"
    repo = JsonBookingRepository(str(db_path))

    # user 1, same date -> will merge to one record
    repo.create_booking(Booking(1, "2025-08-12", ["10:00"]))
    repo.create_booking(Booking(1, "2025-08-12", ["09:00", "10:00"]))
    # user 2, same date -> multiple then merge
    repo.create_booking(Booking(2, "2025-08-12", ["12:00", "11:30"]))
    repo.create_booking(Booking(2, "2025-08-12", ["11:00", "11:30"]))

    result = repo.list_bookings_for_date("2025-08-12")
    # result: list[tuple[user_id, Booking]], sorted by user_id in repo
    assert isinstance(result, list)
    assert [uid for uid, _ in result] == [1, 2]

    uid1, booking1 = result[0]
    uid2, booking2 = result[1]

    assert uid1 == 1
    assert booking1.user_id == 1
    assert booking1.date == "2025-08-12"
    assert booking1.times == ["09:00", "10:00"]
    assert isinstance(booking1.id, int)

    assert uid2 == 2
    assert booking2.user_id == 2
    assert booking2.date == "2025-08-12"
    assert booking2.times == ["11:00", "11:30", "12:00"]
    assert isinstance(booking2.id, int)


# -----------------------
# Tests: time normalization
# -----------------------

@pytest.mark.parametrize(
    "input_times, expected",
    [
        (["09:00", "09:00", "10:00"], ["09:00", "10:00"]),
        (["9:0", "09:00", "10:00"], ["09:00", "10:00"]),          # invalid "9:0" removed
        (["12:30", "08:10", "08:05"], ["08:05", "08:10", "12:30"]),  # sorted
    ],
)
def test_create_booking_normalizes_times_on_create(tmp_path: Path, input_times, expected):
    db_path = tmp_path / "db.json"
    repo = JsonBookingRepository(str(db_path))

    out = repo.create_booking(Booking(1, "2025-08-12", input_times))
    assert out.times == expected

    raw = read_raw_json(db_path)
    assert raw["bookings"][0]["times"] == expected
