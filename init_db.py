import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from src.db.base import Base

async def init_db():
    engine = create_async_engine("sqlite+aiosqlite:///./treeservice.db")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()
    print("Database tables created!")

asyncio.run(init_db())
