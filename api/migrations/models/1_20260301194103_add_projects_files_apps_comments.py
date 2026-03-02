from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "projects" (
    "id" UUID NOT NULL PRIMARY KEY,
    "title" VARCHAR(255) NOT NULL,
    "description" TEXT NOT NULL,
    "status" VARCHAR(9) NOT NULL DEFAULT 'draft',
    "deadline" TIMESTAMPTZ,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "company_id" UUID NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE
);
COMMENT ON COLUMN "projects"."status" IS 'DRAFT: draft\nPUBLISHED: published\nCLOSED: closed';
        CREATE TABLE IF NOT EXISTS "file_attachments" (
    "id" UUID NOT NULL PRIMARY KEY,
    "original_filename" VARCHAR(512) NOT NULL,
    "storage_key" VARCHAR(1024) NOT NULL UNIQUE,
    "content_type" VARCHAR(255) NOT NULL,
    "size_bytes" BIGINT NOT NULL,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "project_id" UUID NOT NULL REFERENCES "projects" ("id") ON DELETE CASCADE,
    "uploaded_by_id" UUID NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE
);
        CREATE TABLE IF NOT EXISTS "applications" (
    "id" UUID NOT NULL PRIMARY KEY,
    "cover_letter" TEXT NOT NULL,
    "status" VARCHAR(8) NOT NULL DEFAULT 'pending',
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "project_id" UUID NOT NULL REFERENCES "projects" ("id") ON DELETE CASCADE,
    "student_id" UUID NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE,
    CONSTRAINT "uid_application_project_fcdde3" UNIQUE ("project_id", "student_id")
);
COMMENT ON COLUMN "applications"."status" IS 'PENDING: pending\nACCEPTED: accepted\nREJECTED: rejected';
        CREATE TABLE IF NOT EXISTS "comments" (
    "id" UUID NOT NULL PRIMARY KEY,
    "body" TEXT NOT NULL,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "application_id" UUID NOT NULL REFERENCES "applications" ("id") ON DELETE CASCADE,
    "author_id" UUID NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE,
    "parent_id" UUID REFERENCES "comments" ("id") ON DELETE CASCADE
);
        CREATE TABLE "project_required_skills" (
    "projects_id" UUID NOT NULL REFERENCES "projects" ("id") ON DELETE CASCADE,
    "skill_id" INT NOT NULL REFERENCES "skills" ("id") ON DELETE CASCADE
);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "project_required_skills";
        DROP TABLE IF EXISTS "project_required_skills";
        DROP TABLE IF EXISTS "projects";
        DROP TABLE IF EXISTS "file_attachments";
        DROP TABLE IF EXISTS "applications";
        DROP TABLE IF EXISTS "comments";"""


MODELS_STATE = (
    "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"
    "pbfWOR5Hp5+B8eK7Jd"
)
