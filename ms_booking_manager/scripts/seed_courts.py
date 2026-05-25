#!/usr/bin/env python
import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from infrastructure.persistence.database import AsyncSessionLocal, init_db
from infrastructure.persistence.seed_courts import DEFAULT_COURTS, seed_default_courts


async def main() -> None:
    await init_db()
    async with AsyncSessionLocal() as session:
        await seed_default_courts(session)

    print("Courts seeded:")
    for court_id, name, _description in DEFAULT_COURTS:
        print(f"  {name}: {court_id}")


if __name__ == "__main__":
    asyncio.run(main())
