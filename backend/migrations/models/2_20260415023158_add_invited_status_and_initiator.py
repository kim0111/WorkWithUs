from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "applications" ADD "initiator" VARCHAR(7) NOT NULL DEFAULT 'student';
        COMMENT ON COLUMN "applications"."status" IS 'invited: invited
pending: pending
accepted: accepted
rejected: rejected
in_progress: in_progress
submitted: submitted
revision_requested: revision_requested
approved: approved
completed: completed';
        COMMENT ON COLUMN "applications"."initiator" IS 'student: student
company: company';"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "applications" DROP COLUMN "initiator";
        COMMENT ON COLUMN "applications"."status" IS 'pending: pending
accepted: accepted
rejected: rejected
in_progress: in_progress
submitted: submitted
revision_requested: revision_requested
approved: approved
completed: completed';"""
