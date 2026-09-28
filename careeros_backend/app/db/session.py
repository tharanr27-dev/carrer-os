from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import settings

connect_args = {}
if "sqlite" in settings.sqlalchemy_database_uri:
    connect_args["check_same_thread"] = False

engine = create_async_engine(settings.sqlalchemy_database_uri, echo=False, connect_args=connect_args)
AsyncSessionLocal = async_sessionmaker(
    autocommit=False, autoflush=False, bind=engine, expire_on_commit=False
)


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
