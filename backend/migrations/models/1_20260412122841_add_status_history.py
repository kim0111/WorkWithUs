from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "applications" ADD "status_history" JSONB NOT NULL DEFAULT '[]';"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "applications" DROP COLUMN "status_history";"""
