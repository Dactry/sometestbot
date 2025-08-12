import json
from pathlib import Path

from adapters.json.json_booking_repository import JsonBookingRepository
from domain.booking import Booking
from domain.user import User

# ---------- Helpers ----------


def make_repo(tmp_path: Path) -> JsonBookingRepository:
    # абсолютний шлях безпечний: Path(base) / absolute → absolute
    return JsonBookingRepository(str(tmp_path / "bookings.json"))


def seed_json(repo: JsonBookingRepository, data: dict) -> None:
    # напряму пишемо файл для підготовки сценаріїв
    repo._path.parent.mkdir(parents=True, exist_ok=True)
    repo._path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


# ---------- Tests ----------


def test_start_without_file_returns_empty_and_free_slot(tmp_path: Path):
    repo = make_repo(tmp_path)

    # немає файлу — репозиторій має поводитись коректно
    users = list(repo.list_all_users())
    assert users == []

    assert repo.is_slot_free("2025-08-12", "10:00") is True
    assert repo.list_bookings_for_date("2025-08-12") == []


def test_upsert_user_insert_and_update_no_duplicates(tmp_path: Path):
    repo = make_repo(tmp_path)

    # вставка
    u = User(id=1, first_name="Max", username="max")
    repo.upsert_user(u)
    users = list(repo.list_all_users())
    assert len(users) == 1
    assert (
        users[0].id == 1 and users[0].first_name == "Max" and users[0].username == "max"
    )

    # оновлення того ж id
    u2 = User(id=1, first_name="Maxim", username="max_d")
    repo.upsert_user(u2)
    users2 = list(repo.list_all_users())
    assert len(users2) == 1  # не з’явився дубль
    got = repo.get_user(1)
    assert got is not None
    assert got.first_name == "Maxim" and got.username == "max_d"


def test_is_slot_free_false_and_true(tmp_path: Path):
    repo = make_repo(tmp_path)

    seed_json(
        repo,
        {
            "users": [],
            "bookings": [
                {"user_id": 1, "date": "2025-08-12", "times": ["10:00", "11:00"]},
                {"user_id": 2, "date": "2025-08-12", "times": ["12:00"]},
            ],
        },
    )

    assert repo.is_slot_free("2025-08-12", "10:00") is False
    assert repo.is_slot_free("2025-08-12", "12:00") is False
    assert repo.is_slot_free("2025-08-12", "13:00") is True
    # інша дата — слот вільний, бо бронювань на цю дату нема
    assert repo.is_slot_free("2025-08-11", "10:00") is True


def test_list_bookings_for_date_aggregates_and_sorts_times(tmp_path: Path):
    repo = make_repo(tmp_path)

    # дані з твого прикладу (з перетинами та дублями для user_id=2)
    seed_json(
        repo,
        {
            "users": [
                {"id": 1, "first_name": "Max", "username": "max"},
                {"id": 2, "first_name": "John", "username": "jojo"},
            ],
            "bookings": [
                {"user_id": 1, "date": "2025-08-12", "times": ["09:00", "10:00"]},
                {"user_id": 2, "date": "2025-08-12", "times": ["11:30", "12:00"]},
                {"user_id": 2, "date": "2025-08-12", "times": ["11:30", "11:00"]},
                {"user_id": 1, "date": "2025-08-11", "times": ["11:00", "12:00"]},
                {
                    "user_id": 2,
                    "date": "2025-08-12",
                    "times": ["12:00", "13:00", "14:00"],
                },
            ],
        },
    )

    result = repo.list_bookings_for_date("2025-08-12")

    # корисно мати стабільний порядок — за user_id
    result = sorted(result, key=lambda x: x[0])
    assert len(result) == 2

    (uid1, b1), (uid2, b2) = result
    assert uid1 == 1 and isinstance(b1, Booking)
    assert b1.user_id == 1 and b1.date == "2025-08-12"
    assert b1.times == ["09:00", "10:00"]

    assert uid2 == 2 and isinstance(b2, Booking)
    assert b2.user_id == 2 and b2.date == "2025-08-12"
    assert b2.times == ["11:00", "11:30", "12:00", "13:00", "14:00"]


def test_list_bookings_for_date_other_date(tmp_path: Path):
    repo = make_repo(tmp_path)

    seed_json(
        repo,
        {
            "users": [{"id": 1, "first_name": "Max", "username": "max"}],
            "bookings": [
                {"user_id": 1, "date": "2025-08-11", "times": ["11:00", "12:00"]}
            ],
        },
    )

    result_12 = repo.list_bookings_for_date("2025-08-12")
    assert result_12 == []

    result_11 = repo.list_bookings_for_date("2025-08-11")
    assert len(result_11) == 1
    uid, b = result_11[0]
    assert uid == 1
    assert b == Booking(user_id=1, date="2025-08-11", times=["11:00", "12:00"])


def test_list_all_users_types_and_values(tmp_path: Path):
    repo = make_repo(tmp_path)

    seed_json(
        repo,
        {
            "users": [
                {"id": 1, "first_name": "Max", "username": "max"},
                {"id": 2, "first_name": "John", "username": "jojo"},
            ],
            "bookings": [],
        },
    )

    users = list(repo.list_all_users())
    assert len(users) == 2
    assert all(isinstance(u, User) for u in users)
    # перевірка конкретних значень
    users_by_id = {u.id: u for u in users}
    assert users_by_id[1].first_name == "Max" and users_by_id[1].username == "max"
    assert users_by_id[2].first_name == "John" and users_by_id[2].username == "jojo"
