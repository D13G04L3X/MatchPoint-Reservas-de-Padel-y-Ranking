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
            data = r.json()
            return int(data.get("message_stats", {}).get("publish_in", 0))
    except Exception:
        pass
    return 0


def main():
    fail_count = 0

    # Test 1: Gateway health
    ok = wait_for_gateway(timeout=60)
    print_result(ok, "Gateway health")
    if not ok:
        fail_count += 1

    # Prepare IDs and times
    COURT_ID = new_uuid()
    PLAYER_ID = new_uuid()
    GUEST_ID = new_uuid()

    NON_PREMIUM_START = iso_tomorrow_at_club_hour(10)
    NON_PREMIUM_END = iso_tomorrow_at_club_hour(11)
    PREMIUM_START = iso_tomorrow_at_club_hour(19)
    PREMIUM_END = iso_tomorrow_at_club_hour(20)
    LATE_START = iso_in_hours(1)
    LATE_END = iso_in_hours(2)

    client = httpx.Client(timeout=10.0)

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

    booking_id = None
    try:
        booking_id = r.json().get("id")
    except Exception:
        booking_id = None

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
        rank_payload = {
            "court_id": COURT_ID,
            "player_id": RANK_HIGH_PLAYER_ID,
            "guest_player_ids": [RANK_LOW_PLAYER_ID],
            "start_time": NON_PREMIUM_START,
            "end_time": NON_PREMIUM_END,
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
    if not booking_id:
        print_result(False, "Late cancellation")
        fail_count += 1
    else:
        # Ensure we can create a slot within the next 2 hours outside premium hours.
        non_premium_offset = None
        for try_h in (1, 2):
            candidate = datetime.now(timezone.utc) + timedelta(hours=try_h)
            if not is_premium_club_hour(candidate):
                non_premium_offset = try_h
                break
        if non_premium_offset is None:
            print("SKIPPED - Late cancellation (no non-premium slot in next 2 hours)")
        else:
            try:
                late_payload = {
                    "court_id": COURT_ID,
                    "player_id": PLAYER_ID,
                    "guest_player_ids": [],
                    "start_time": LATE_START,
                    "end_time": LATE_END,
                    "is_ranked": False,
                }
                r4 = client.post(f"{BOOKING_URL}/bookings", json=late_payload)
                if r4.status_code != 201:
                    print_result(False, "Late cancellation")
                    fail_count += 1
                else:
                    late_booking_id = r4.json().get("id")
                    before_count = rabbitmq_publish_count()
                    cancel_payload = {"booking_id": late_booking_id, "player_id": PLAYER_ID}
                    r5 = client.delete(
                        f"{BOOKING_URL}/bookings/{late_booking_id}",
                        params={"player_id": PLAYER_ID}
)
                    time.sleep(2)
                    after_count = rabbitmq_publish_count()
                    if r5.status_code == 200 and after_count > before_count:
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