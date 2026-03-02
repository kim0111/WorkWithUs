from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "users" (
    "id" UUID NOT NULL PRIMARY KEY,
    "email" VARCHAR(255) NOT NULL UNIQUE,
    "hashed_password" VARCHAR(255) NOT NULL,
    "role" VARCHAR(7) NOT NULL,
    "is_active" BOOL NOT NULL DEFAULT True,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON COLUMN "users"."role" IS 'STUDENT: student\nCOMPANY: company\nADMIN: admin';
CREATE TABLE IF NOT EXISTS "company_profiles" (
    "id" UUID NOT NULL PRIMARY KEY,
    "company_name" VARCHAR(255) NOT NULL DEFAULT '',
    "description" TEXT NOT NULL,
    "website" VARCHAR(255) NOT NULL DEFAULT '',
    "contact_person" VARCHAR(255) NOT NULL DEFAULT '',
    "user_id" UUID NOT NULL UNIQUE REFERENCES "users" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "student_profiles" (
    "id" UUID NOT NULL PRIMARY KEY,
    "first_name" VARCHAR(100) NOT NULL DEFAULT '',
    "last_name" VARCHAR(100) NOT NULL DEFAULT '',
    "university" VARCHAR(255) NOT NULL DEFAULT '',
    "faculty" VARCHAR(255) NOT NULL DEFAULT '',
    "year_of_study" INT,
    "bio" TEXT NOT NULL,
    "user_id" UUID NOT NULL UNIQUE REFERENCES "users" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "skills" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "name" VARCHAR(100) NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSONB NOT NULL
);
CREATE TABLE IF NOT EXISTS "student_skills" (
    "student_profiles_id" UUID NOT NULL REFERENCES "student_profiles" ("id") ON DELETE CASCADE,
    "skill_id" INT NOT NULL REFERENCES "skills" ("id") ON DELETE CASCADE
);
CREATE UNIQUE INDEX IF NOT EXISTS "uidx_student_ski_student_9f96d4" ON "student_skills" ("student_profiles_id", "skill_id");"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """


MODELS_STATE = (
    "eJztmmtv2zYUhv+KoU8ZkAWNmyZFUAzwbauH2A5iuet6gUBLtE1EIlWJWmIE+e8jKepGXV"
    "bFl1iDvzjR4TkS+ZDi4UvqSXOIBW3/rEccF+D1rUcWyIbadetJw8Dh/5R4nLY04LpJOTdQ"
    "MBexmhn6Gm7oLArB3KceMCkrXwDbh8xkQd/0kEsRwcyKA9vmRmIyR4SXiSnA6EcADUqWkK"
    "6gxwq+fmdmhC34yG4uL917Y4GgbWUqjyz+bGE36NoVttls2P9dePLHzQ2T2IGDE293TVcE"
    "x+5BgKwzHsPLlhBDD1BopZrBaylbHpnCGjMD9QIYV9VKDBZcgMDmMLQPiwCbnEFLPIn/XP"
    "ym1cBjEszRIkw5i6fnsFVJm4VV44/qfezcnby9/EW0kvh06YlCQUR7FoGAgjBUcE1ARl0q"
    "rnNIeyvgFSNV4xS4rOIvwRoZEq7JmIrBbsBQc8CjYUO8pCt22X73rgLqp86d4Mq8BFjCRn"
    "n4GoxlUTss44AToOma5Xjq8JEW81TCmoGzgp4++KzzOzu+/8NOQzsZdT4Lns5altxMxn9E"
    "7inIvZtJV2H7AOc+orXGaSqkGUz3METZEymbsQ0Xen7RKK1669XII1QJNfChZ9RLS6mQ/e"
    "amiNu+ExFP54v7VB7ihjkw7x+AZxm5EtImhTmLc8tznmCoE/YjWA9ZjQE2i957ue6ZyZsc"
    "KN3EmjzCAw/xUig9eFjjWJMgDV/ezrTX6Q+05wzbLEpe5LQd1QIwWIom8ZrxekhUUxpYEN"
    "OKRaTiUbmI9EPf4yLy/7OIXCDPp7WXkNmoJiaS8zdvfiKRMK/SRCLKsonEBi9gmQk6oowS"
    "BUb/sJUKous6LLNRTYS5kwXOApisnrVIpkKOGCXGNQSeQRYGT4MFMIe4RCDm4hSifKXw30"
    "RlhqkFdLP1DKsR+/Nr+/zi6uL928uL98xFVCW2XFVAHo51hd8ckTq6Wro3Y/jtW08fNctR"
    "szRXsyRw/Xtkhyoji3cE8Fon/PcnAU/5jRpGWFTdUAVZ1BAP2rwZcblUXyEs4gnQ93AdU5"
    "TdE3dCVKaINulGVx4Jlqu0R9IXhV3M7EYO7nOl/BSjvkB0Rm9DudTk4+2oL5uvL6EDkF1n"
    "4RkHbCfv7/rt3sOycwX8FZsGXOD7D8QrGJjlMAtC97ecOniwHrFLlPoAB04u72TIRrGvjF"
    "Ob6rP+YKxft+Qk/g33JqPbzvjv65Y85/uGO/3RcHzdApaDxMZ/XfhVq/wI/VUp+CsVO/IN"
    "Np8zoZ5n3yUMK8Als2w6TuE+Z4G7Ah/PGNueVruTyU1GGHSH6sp/NuoO7k7OBVzmhMKMnJ"
    "dWpgfFWgHQPNQ+K6HIgSXnQplIBaslQ8+ifw50rmBtsCbYXsveqhJjw9FgqndGtxnw/Y4+"
    "4CXtjBqLrCeXyuCOb9L6a6h/bPHL1pfJeKDmx9hP/6LxOoGAEgOTBwNYqVQUWeMlVUbnud"
    "YLOzYbeezYV+1YUfmN9GiFvsp/EuImpznKBCvvEKnXO64xij9cKP3I6OD2qcoUVuZFUmTQ"
    "NtDkj86ag6buOaIQpUXHh5FarTg1jGXl4Wi50r3aQilXsEEru/JVpcdWtmfLpVvdg6ztnm"
    "HtV7ht7QxrV3N85R5aemNow120ulPa4W+n5VqU21dLtiCVXbXinbPcBltq823zXbVkdi6b"
    "izvQQ+aqaDKWJZWzMUh8jrNxg2Zjca5d75O/VMhx1ycGyV+NGhClezMB7uTTDP4lKcQFev"
    "TP6WRc/vGpDFFAzjBr4FcLmfS0ZSOffj9MrBUUeaurj3fVk9zTrJjkN+judelQkF6e/wVc"
    "a0mZ"
)
