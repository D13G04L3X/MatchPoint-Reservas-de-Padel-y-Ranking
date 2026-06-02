#!/usr/bin/env python
import asyncio

from infrastructure.persistence.database import AsyncSessionLocal, init_db
from infrastructure.persistence.seed_players import DEFAULT_PLAYERS, seed_default_players


async def main() -> None:
    await init_db()
    async with AsyncSessionLocal() as session:
        await seed_default_players(session)

    print("\nJugadores insertados:\n")
    for p in DEFAULT_PLAYERS:
        print(f"  {p['username']:<20} id: {p['id']}")
    print("\nCopia estos UUIDs para usar en X-User-Id header en Postman.\n")


if __name__ == "__main__":
    asyncio.run(main())
