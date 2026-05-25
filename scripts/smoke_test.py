#!/usr/bin/env python
import os
import sys
import time
import uuid
from datetime import datetime, timedelta, timezone, time as dtime
from zoneinfo import ZoneInfo

import httpx

# Must match MS-BookingManager domain (premium window 18-22 local club time).
CLUB_TZ = ZoneInfo("America/Bogota")


GREEN = "\033[0;32m"
RED = "\033[0;31m"
NC = "\033[0m"


def print_result(ok: bool, name: str):
    if ok:
        print(f"{GREEN}PASSED{NC} - {name}")
    else:
        print(f"{RED}FAILED{NC} - {name}")


GATEWAY_URL = os.environ.get("GATEWAY_URL", "http://localhost")
BOOKING_URL = os.environ.get("BOOKING_URL", GATEWAY_URL)
PENALTY_URL = os.environ.get("PENALTY_URL", f"{GATEWAY_URL}/penalty")
RABBITMQ_API_URL = os.environ.get("RABBITMQ_API_URL", "http://localhost:15672/api")
RABBITMQ_USER = os.environ.get("RABBITMQ_USER", os.environ.get("RABBITMQ_DEFAULT_USER", "matchpoint"))
RABBITMQ_PASS = os.environ.get("RABBITMQ_PASS", os.environ.get("RABBITMQ_DEFAULT_PASS", "matchpoint"))


def new_uuid():
    return str(uuid.uuid4())


def iso_tomorrow_at_club_hour(hour: int) -> str:
    """Return UTC ISO timestamp for tomorrow at `hour` in America/Bogota."""
    now_club = datetime.now(CLUB_TZ)
    tomorrow = (now_club + timedelta(days=1)).date()
    local_dt = datetime.combine(tomorrow, dtime(hour=hour, minute=0), tzinfo=CLUB_TZ)
    return local_dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def is_premium_club_hour(moment: datetime) -> bool:
    """True when the instant falls in 18:00-22:00 America/Bogota."""
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    local = moment.astimezone(CLUB_TZ)
    return 18 <= local.hour < 22


def iso_in_hours(hours: float):
    now = datetime.now(timezone.utc)
    dt = now + timedelta(hours=hours)
    return dt.isoformat().replace("+00:00", "Z")


def wait_for_gateway(timeout=60):
    url = f"{GATEWAY_URL}/health"
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            r = httpx.get(url, timeout=5.0)
            if r.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(2)
    return False


def rabbitmq_publish_count():
    url = f"{RABBITMQ_API_URL}/exchanges/%2F/matchpoint.events"
    try:
        r = httpx.get(url, auth=(RABBITMQ_USER, RABBITMQ_PASS), timeout=5.0)
        if r.status_code == 200:
            stats = r.json().get("message_stats") or {}
            for key in ("publish_in", "publish_out"):
                if key in stats:
                    return int(stats[key])
    except Exception:
        pass
    return 0


def wait_for_rabbitmq_increase(before: int, timeout: float = 10.0) -> bool:
    """Return True when exchange publish count increases within timeout."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        if rabbitmq_publish_count() > before:
            return True
        time.sleep(0.5)
    return False


def list_available_court_ids(client: httpx.Client) -> list[str]:
    """Return court ids with availability for tomorrow, best first."""
    try:
        response = client.get(
            f"{BOOKING_URL}/courts/availability",
            params={"date": iso_tomorrow_date()},
        )
        if response.status_code != 200:
            return []
        courts = response.json().get("courts") or []
        courts.sort(key=lambda court: court.get("available_slots", 0), reverse=True)
        return [court["id"] for court in courts]
    except Exception:
        return []


def create_imminent_booking(
    client: httpx.Client,
    court_ids: list[str],
    player_id: str,
) -> tuple[str, str] | None:
    """Create a booking within the next 2 hours; return (booking_id, court_id)."""
    hour_offsets = (1.0, 1.25, 1.5, 0.75, 1.75)
    for court_id in court_ids:
        for offset in hour_offsets:
            start = datetime.now(timezone.utc) + timedelta(hours=offset)
            if is_premium_club_hour(start):
                continue
            end = start + timedelta(hours=1)
            payload = {
                "court_id": court_id,
                "player_id": player_id,
                "guest_player_ids": [],
                "start_time": start.isoformat().replace("+00:00", "Z"),
                "end_time": end.isoformat().replace("+00:00", "Z"),
                "is_ranked": False,
            }
            try:
                response = client.post(f"{BOOKING_URL}/bookings", json=payload)
                if response.status_code == 201:
                    return response.json().get("id"), court_id
            except Exception:
                continue
    return None


def iso_tomorrow_date() -> str:
    """Return YYYY-MM-DD for tomorrow in America/Bogota."""
    tomorrow = (datetime.now(CLUB_TZ) + timedelta(days=1)).date()
    return tomorrow.isoformat()


def pick_seeded_court_id(client: httpx.Client) -> str | None:
    """Return the seeded court with the most free slots for tomorrow."""
    try:
        response = client.get(
            f"{BOOKING_URL}/courts/availability",
            params={"date": iso_tomorrow_date()},
        )
        if response.status_code != 200:
            return None
        courts = response.json().get("courts") or []
        if not courts:
            return None
        best = max(courts, key=lambda court: court.get("available_slots", 0))
        return best["id"]
    except Exception:
        return None


def pick_available_slot(
    client: httpx.Client,
    court_id: str,
    *,
    premium: bool | None = None,
) -> tuple[str, str] | None:
    """Return (start_time, end_time) ISO strings for the first matching free slot."""
    try:
        response = client.get(
            f"{BOOKING_URL}/courts/{court_id}/availability",
            params={"date": iso_tomorrow_date()},
        )
        if response.status_code != 200:
            return None
        for slot in response.json().get("slots") or []:
            start = datetime.fromisoformat(slot["start_time"].replace("Z", "+00:00"))
            slot_is_premium = is_premium_club_hour(start)
            if premium is None or slot_is_premium == premium:
                start_iso = start.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
                end = datetime.fromisoformat(slot["end_time"].replace("Z", "+00:00"))
                end_iso = end.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
                return start_iso, end_iso
    except Exception:
        pass
    return None


def main():
    fail_count = 0

    # Test 1: Gateway health
    ok = wait_for_gateway(timeout=60)
    print_result(ok, "Gateway health")
    if not ok:
        fail_count += 1

    client = httpx.Client(timeout=10.0)

    # Test 2: Courts availability for tomorrow
    try:
        r_courts = client.get(
            f"{BOOKING_URL}/courts/availability",
            params={"date": iso_tomorrow_date()},
        )
        courts = r_courts.json().get("courts") if r_courts.status_code == 200 else []
        if r_courts.status_code == 200 and len(courts) >= 3:
            print_result(True, "Courts availability")
        else:
            print_result(False, "Courts availability")
            fail_count += 1
    except Exception:
        print_result(False, "Courts availability")
        fail_count += 1

    COURT_ID = pick_seeded_court_id(client)
    if not COURT_ID:
        print_result(False, "Resolve seeded court id")
        fail_count += 1
        COURT_ID = new_uuid()
    PLAYER_ID = new_uuid()
    GUEST_ID = new_uuid()

    NON_PREMIUM_SLOT = pick_available_slot(client, COURT_ID, premium=False)
    PREMIUM_SLOT = pick_available_slot(client, COURT_ID, premium=True)
    if not NON_PREMIUM_SLOT:
        print_result(False, "Resolve non-premium slot")
        fail_count += 1
        NON_PREMIUM_START = iso_tomorrow_at_club_hour(10)
        NON_PREMIUM_END = iso_tomorrow_at_club_hour(11)
    else:
        NON_PREMIUM_START, NON_PREMIUM_END = NON_PREMIUM_SLOT
    if not PREMIUM_SLOT:
        PREMIUM_START = iso_tomorrow_at_club_hour(19)
        PREMIUM_END = iso_tomorrow_at_club_hour(20)
    else:
        PREMIUM_START, PREMIUM_END = PREMIUM_SLOT

    # Test 2: Non-premium booking
    payload = {
        "court_id": COURT_ID,
        "player_id": PLAYER_ID,
        "guest_player_ids": [GUEST_ID],
        "start_time": NON_PREMIUM_START,
        "end_time": NON_PREMIUM_END,
        "is_ranked": False,
    }
    try:
        r = client.post(f"{BOOKING_URL}/bookings", json=payload)
        if r.status_code == 201:
            print_result(True, "Create non-premium booking")
        else:
            print_result(False, "Create non-premium booking")
            fail_count += 1
    except Exception:
        print_result(False, "Create non-premium booking")
        fail_count += 1

    # Test 3: Premium booking without membership
    premium_payload = {
        "court_id": COURT_ID,
        "player_id": new_uuid(),
        "guest_player_ids": [],
        "start_time": PREMIUM_START,
        "end_time": PREMIUM_END,
        "is_ranked": False,
    }
    try:
        r2 = client.post(f"{BOOKING_URL}/bookings", json=premium_payload)
        if r2.status_code == 403:
            print_result(True, "Premium booking without membership")
        else:
            print_result(False, "Premium booking without membership")
            fail_count += 1
    except Exception:
        print_result(False, "Premium booking without membership")
        fail_count += 1

    # Test 4: Ranked booking with level diff > 2.0
    # This test requires pre-seeded player ranks. If RANK_HIGH_PLAYER_ID and
    # RANK_LOW_PLAYER_ID are not provided via env, skip the test.
    RANK_HIGH_PLAYER_ID = os.environ.get("RANK_HIGH_PLAYER_ID")
    RANK_LOW_PLAYER_ID = os.environ.get("RANK_LOW_PLAYER_ID")
    if not (RANK_HIGH_PLAYER_ID and RANK_LOW_PLAYER_ID):
        print("SKIPPED - Ranked booking with level diff > 2.0 (no pre-seeded ranks)")
    else:
        rank_slot = pick_available_slot(client, COURT_ID, premium=False)
        if not rank_slot:
            print("SKIPPED - Ranked booking with level diff > 2.0 (no free slot)")
        else:
            rank_start, rank_end = rank_slot
            rank_payload = {
                "court_id": COURT_ID,
                "player_id": RANK_HIGH_PLAYER_ID,
                "guest_player_ids": [RANK_LOW_PLAYER_ID],
                "start_time": rank_start,
                "end_time": rank_end,
                "is_ranked": True,
            }
            try:
                r3 = client.post(f"{BOOKING_URL}/bookings", json=rank_payload)
                if r3.status_code == 400:
                    print_result(True, "Ranked booking with level diff > 2.0")
                else:
                    print_result(False, "Ranked booking with level diff > 2.0")
                    fail_count += 1
            except Exception:
                print_result(False, "Ranked booking with level diff > 2.0")
                fail_count += 1

    # Test 5: Late cancellation publishes event
    court_ids = list_available_court_ids(client) or ([COURT_ID] if COURT_ID else [])
    late_player_id = new_uuid()
    imminent = create_imminent_booking(client, court_ids, late_player_id)
    if not imminent:
        print("SKIPPED - Late cancellation (no free slot in next 2 hours)")
    else:
        late_booking_id, _ = imminent
        try:
            before_count = rabbitmq_publish_count()
            r5 = client.delete(
                f"{BOOKING_URL}/bookings/{late_booking_id}",
                params={"player_id": late_player_id},
            )
            cancelled = r5.status_code == 200 and r5.json().get("status") == "CANCELLED_LATE"
            published = wait_for_rabbitmq_increase(before_count)
            if cancelled and published:
                print_result(True, "Late cancellation")
            else:
                print_result(False, "Late cancellation")
                fail_count += 1
        except Exception:
            print_result(False, "Late cancellation")
            fail_count += 1

    # Test 6: Public ranking
    try:
        r6 = client.get(f"{PENALTY_URL}/ranking")
        if r6.status_code == 200:
            print_result(True, "Public ranking")
        else:
            print_result(False, "Public ranking")
            fail_count += 1
    except Exception:
        print_result(False, "Public ranking")
        fail_count += 1

    if fail_count == 0:
        print(f"{GREEN}ALL TESTS PASSED{NC}")
        sys.exit(0)
    else:
        print(f"{RED}{fail_count} TEST(S) FAILED{NC}")
        sys.exit(1)


if __name__ == '__main__':
    main()