#!/usr/bin/env python
import argparse
import asyncio
import uuid
import sys
from uuid import UUID
from pathlib import Path

# Ensure project root (/app) is on sys.path so imports like
# `infrastructure.persistence` resolve when running this script directly.
# When executed inside the container or via `python scripts/seed_ranks.py`
# this ensures the package imports work without rebuilding images.
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Seed rank entries into ms_penalty_rank MongoDB")
    p.add_argument("--high-id", dest="high_id", help="High player UUID", default=str(uuid.uuid4()))
    p.add_argument("--high-level", dest="high_level", type=float, default=8.5)
    p.add_argument("--low-id", dest="low_id", help="Low player UUID", default=str(uuid.uuid4()))
    p.add_argument("--low-level", dest="low_level", type=float, default=4.0)
    return p.parse_args()


async def seed(high_id: str, high_level: float, low_id: str, low_level: float) -> None:
    from infrastructure.persistence.mongodb import get_database
    from infrastructure.persistence.mongo_rank_repository import MongoRankRepository

    db = get_database()
    repo = MongoRankRepository(db)

    try:
        print(f"Seeding high player {high_id} -> level={high_level}")
        await repo.update_level(UUID(high_id), float(high_level))
        print(f"Seeding low player {low_id} -> level={low_level}")
        await repo.update_level(UUID(low_id), float(low_level))
        print("Seeding complete.")
    except Exception as e:
        print("Seeding failed:", e)
        raise


def main():
    args = parse_args()
    asyncio.run(seed(args.high_id, args.high_level, args.low_id, args.low_level))


if __name__ == "__main__":
    main()
