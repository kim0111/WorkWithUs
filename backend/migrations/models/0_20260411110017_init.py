from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "users" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "email" VARCHAR(255) NOT NULL UNIQUE,
    "username" VARCHAR(100) NOT NULL UNIQUE,
    "hashed_password" VARCHAR(255) NOT NULL,
    "full_name" VARCHAR(255),
    "role" VARCHAR(9) NOT NULL DEFAULT 'student',
    "avatar_url" VARCHAR(500),
    "bio" TEXT,
    "is_active" BOOL NOT NULL DEFAULT True,
    "is_blocked" BOOL NOT NULL DEFAULT False,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "idx_users_email_133a6f" ON "users" ("email");
CREATE INDEX IF NOT EXISTS "idx_users_usernam_266d85" ON "users" ("username");
COMMENT ON COLUMN "users"."role" IS 'student: student\ncompany: company\ncommittee: committee\nadmin: admin';
CREATE TABLE IF NOT EXISTS "company_profiles" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "company_name" VARCHAR(255) NOT NULL,
    "industry" VARCHAR(255),
    "website" VARCHAR(500),
    "description" TEXT,
    "location" VARCHAR(255),
    "user_id" INT NOT NULL UNIQUE REFERENCES "users" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "student_profiles" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "university" VARCHAR(255),
    "major" VARCHAR(255),
    "graduation_year" INT,
    "gpa" DOUBLE PRECISION,
    "resume_url" VARCHAR(500),
    "rating" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "completed_projects_count" INT NOT NULL DEFAULT 0,
    "user_id" INT NOT NULL UNIQUE REFERENCES "users" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "skills" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "name" VARCHAR(100) NOT NULL UNIQUE,
    "category" VARCHAR(100)
);
CREATE TABLE IF NOT EXISTS "projects" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "title" VARCHAR(255) NOT NULL,
    "description" TEXT NOT NULL,
    "status" VARCHAR(11) NOT NULL DEFAULT 'open',
    "max_participants" INT NOT NULL DEFAULT 1,
    "deadline" TIMESTAMPTZ,
    "is_student_project" BOOL NOT NULL DEFAULT False,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "owner_id" INT NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE
);
COMMENT ON COLUMN "projects"."status" IS 'open: open\nin_progress: in_progress\nclosed: closed';
CREATE TABLE IF NOT EXISTS "project_files" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "filename" VARCHAR(500) NOT NULL,
    "object_name" VARCHAR(500) NOT NULL,
    "file_size" INT,
    "content_type" VARCHAR(255),
    "file_type" VARCHAR(50) NOT NULL DEFAULT 'attachment',
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "project_id" INT NOT NULL REFERENCES "projects" ("id") ON DELETE CASCADE,
    "uploader_id" INT NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "applications" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "cover_letter" TEXT,
    "status" VARCHAR(18) NOT NULL DEFAULT 'pending',
    "submission_note" TEXT,
    "revision_note" TEXT,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "applicant_id" INT NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE,
    "project_id" INT NOT NULL REFERENCES "projects" ("id") ON DELETE CASCADE,
    CONSTRAINT "uid_application_project_aee8fb" UNIQUE ("project_id", "applicant_id")
);
COMMENT ON COLUMN "applications"."status" IS 'pending: pending\naccepted: accepted\nrejected: rejected\nin_progress: in_progress\nsubmitted: submitted\nrevision_requested: revision_requested\napproved: approved\ncompleted: completed';
CREATE TABLE IF NOT EXISTS "reviews" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "rating" DOUBLE PRECISION NOT NULL,
    "comment" TEXT,
    "review_type" VARCHAR(50),
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "application_id" INT REFERENCES "applications" ("id") ON DELETE CASCADE,
    "project_id" INT NOT NULL REFERENCES "projects" ("id") ON DELETE CASCADE,
    "reviewee_id" INT NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE,
    "reviewer_id" INT NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "portfolio_items" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "title" VARCHAR(255) NOT NULL,
    "description" TEXT,
    "project_url" VARCHAR(500),
    "image_url" VARCHAR(500),
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "student_id" INT NOT NULL REFERENCES "student_profiles" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSONB NOT NULL
);
CREATE TABLE IF NOT EXISTS "user_skills" (
    "users_id" INT NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE,
    "skill_id" INT NOT NULL REFERENCES "skills" ("id") ON DELETE CASCADE
);
CREATE UNIQUE INDEX IF NOT EXISTS "uidx_user_skills_users_i_22746f" ON "user_skills" ("users_id", "skill_id");
CREATE TABLE IF NOT EXISTS "project_skills" (
    "projects_id" INT NOT NULL REFERENCES "projects" ("id") ON DELETE CASCADE,
    "skill_id" INT NOT NULL REFERENCES "skills" ("id") ON DELETE CASCADE
);
CREATE UNIQUE INDEX IF NOT EXISTS "uidx_project_ski_project_92ae3c" ON "project_skills" ("projects_id", "skill_id");"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """
