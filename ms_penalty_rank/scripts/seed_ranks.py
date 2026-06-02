#!/usr/bin/env python
import argparse
import asyncio
import sys
from uuid import UUID
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from infrastructure.persistence.mongodb import get_database
from infrastructure.persistence.mongo_rank_repository import MongoRankRepository


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Seed rank entries into ms_penalty_rank MongoDB"
    )
    p.add_argument("--high-id", dest="high_id", help="High player UUID")
    p.add_argument("--high-level", dest="high_level", type=float, default=6.2)
    p.add_argument("--low-id", dest="low_id", help="Low player UUID")
    p.add_argument("--low-level", dest="low_level", type=float, default=3.0)
    p.add_argument(
        "--all",
        action="store_true",
        help="Seed all 6 default players (ignores --high-*/--low-*)",
    )
    return p.parse_args()


async def seed_all(repo: MongoRankRepository) -> None:
    from infrastructure.persistence.seed_ranks import DEFAULT_RANKS

    for player_id, level, username in DEFAULT_RANKS:
        await repo.update_level(UUID(player_id), level)
        print(f"  {username:<20} {player_id} -> level {level}")


async def seed_two(
    repo: MongoRankRepository,
    high_id: str,
    high_level: float,
    low_id: str,
    low_level: float,
) -> None:
    print(f"Seeding high player {high_id} -> level={high_level}")
    await repo.update_level(UUID(high_id), float(high_level))
    print(f"Seeding low player {low_id} -> level={low_level}")
    await repo.update_level(UUID(low_id), float(low_level))


def main() -> None:
    args = parse_args()
    db = get_database()
    repo = MongoRankRepository(db)

    if args.all:
        print("Seeding all 6 default ranks:")
        asyncio.run(seed_all(repo))
    elif args.high_id and args.low_id:
        asyncio.run(seed_two(repo, args.high_id, args.high_level, args.low_id, args.low_level))
    else:
        print("Running default seed (all 6 players)...")
        asyncio.run(seed_all(repo))

    print("Seeding complete.")


if __name__ == "__main__":
    main()
