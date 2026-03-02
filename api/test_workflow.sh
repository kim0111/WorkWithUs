#!/usr/bin/env bash
# =============================================================
#  WorkWithUs API — Manual E2E Testing Workflow
#  Prerequisite: docker compose up -d  (from project root)
#                uv run uvicorn src.main:app --reload
# =============================================================

set -e
BASE="http://localhost:8000/api/v1"

echo "========================================"
echo "  1. REGISTER COMPANY"
echo "========================================"
COMPANY=$(curl -s -X POST "$BASE/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email":"company@test.com","password":"pass1234","role":"company"}')
echo "$COMPANY" | python3 -m json.tool
COMPANY_TOKEN=$(echo "$COMPANY" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
echo "COMPANY_TOKEN=$COMPANY_TOKEN"
echo

echo "========================================"
echo "  2. REGISTER STUDENT"
echo "========================================"
STUDENT=$(curl -s -X POST "$BASE/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email":"student@test.com","password":"pass1234","role":"student"}')
echo "$STUDENT" | python3 -m json.tool
STUDENT_TOKEN=$(echo "$STUDENT" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
echo "STUDENT_TOKEN=$STUDENT_TOKEN"
echo

echo "========================================"
echo "  3. CREATE SKILL (need admin — skip or seed manually)"
echo "========================================"
echo "Skipping — seed skills via DB or create an admin user first."
echo

echo "========================================"
echo "  4. CREATE PROJECT (draft)"
echo "========================================"
PROJECT=$(curl -s -X POST "$BASE/projects" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $COMPANY_TOKEN" \
  -d '{
    "title": "Build a Landing Page",
    "description": "We need a modern landing page for our SaaS product.",
    "deadline": "2026-06-01T00:00:00",
    "required_skill_ids": []
  }')
echo "$PROJECT" | python3 -m json.tool
PROJECT_ID=$(echo "$PROJECT" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
echo "PROJECT_ID=$PROJECT_ID"
echo

echo "========================================"
echo "  5. UPLOAD FILE to project"
echo "========================================"
echo "Test file content for specification" > /tmp/spec.txt
FILE=$(curl -s -X POST "$BASE/projects/$PROJECT_ID/files" \
  -H "Authorization: Bearer $COMPANY_TOKEN" \
  -F "file=@/tmp/spec.txt")
echo "$FILE" | python3 -m json.tool
FILE_ID=$(echo "$FILE" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
echo "FILE_ID=$FILE_ID"
echo

echo "========================================"
echo "  6. LIST FILES"
echo "========================================"
curl -s "$BASE/projects/$PROJECT_ID/files" \
  -H "Authorization: Bearer $COMPANY_TOKEN" | python3 -m json.tool
echo

echo "========================================"
echo "  7. GET DOWNLOAD URL"
echo "========================================"
curl -s "$BASE/projects/$PROJECT_ID/files/$FILE_ID/download" \
  -H "Authorization: Bearer $COMPANY_TOKEN" | python3 -m json.tool
echo

echo "========================================"
echo "  8. PUBLISH PROJECT (status → published)"
echo "========================================"
curl -s -X PATCH "$BASE/projects/$PROJECT_ID" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $COMPANY_TOKEN" \
  -d '{"status": "published"}' | python3 -m json.tool
echo

echo "========================================"
echo "  9. LIST PUBLISHED PROJECTS (as student)"
echo "========================================"
curl -s "$BASE/projects" \
  -H "Authorization: Bearer $STUDENT_TOKEN" | python3 -m json.tool
echo

echo "========================================"
echo " 10. GET PROJECT DETAILS (as student)"
echo "========================================"
curl -s "$BASE/projects/$PROJECT_ID" \
  -H "Authorization: Bearer $STUDENT_TOKEN" | python3 -m json.tool
echo

echo "========================================"
echo " 11. STUDENT APPLIES to project"
echo "========================================"
APP=$(curl -s -X POST "$BASE/projects/$PROJECT_ID/applications" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $STUDENT_TOKEN" \
  -d '{"cover_letter": "I am very interested in this project. I have 2 years of frontend experience."}')
echo "$APP" | python3 -m json.tool
APP_ID=$(echo "$APP" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
echo "APP_ID=$APP_ID"
echo

echo "========================================"
echo " 12. STUDENT: my applications"
echo "========================================"
curl -s "$BASE/applications/my" \
  -H "Authorization: Bearer $STUDENT_TOKEN" | python3 -m json.tool
echo

echo "========================================"
echo " 13. COMPANY: list applications for project"
echo "========================================"
curl -s "$BASE/projects/$PROJECT_ID/applications" \
  -H "Authorization: Bearer $COMPANY_TOKEN" | python3 -m json.tool
echo

echo "========================================"
echo " 14. COMPANY: view application details"
echo "========================================"
curl -s "$BASE/applications/$APP_ID" \
  -H "Authorization: Bearer $COMPANY_TOKEN" | python3 -m json.tool
echo

echo "========================================"
echo " 15. STUDENT: add comment to application"
echo "========================================"
COMMENT=$(curl -s -X POST "$BASE/applications/$APP_ID/comments" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $STUDENT_TOKEN" \
  -d '{"body": "Hi! When can we schedule an interview?"}')
echo "$COMMENT" | python3 -m json.tool
COMMENT_ID=$(echo "$COMMENT" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
echo "COMMENT_ID=$COMMENT_ID"
echo

echo "========================================"
echo " 16. COMPANY: reply to comment (threaded)"
echo "========================================"
curl -s -X POST "$BASE/applications/$APP_ID/comments" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $COMPANY_TOKEN" \
  -d "{\"body\": \"Let's meet next Monday at 10 AM.\", \"parent_id\": \"$COMMENT_ID\"}" \
  | python3 -m json.tool
echo

echo "========================================"
echo " 17. LIST COMMENTS (tree)"
echo "========================================"
curl -s "$BASE/applications/$APP_ID/comments" \
  -H "Authorization: Bearer $COMPANY_TOKEN" | python3 -m json.tool
echo

echo "========================================"
echo " 18. COMPANY: accept application"
echo "========================================"
curl -s -X PATCH "$BASE/applications/$APP_ID/status" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $COMPANY_TOKEN" \
  -d '{"status": "accepted"}' | python3 -m json.tool
echo

echo "========================================"
echo " 19. COMPANY: my projects"
echo "========================================"
curl -s "$BASE/projects/my" \
  -H "Authorization: Bearer $COMPANY_TOKEN" | python3 -m json.tool
echo

echo "========================================"
echo " 20. CLEANUP: delete file"
echo "========================================"
curl -s -X DELETE "$BASE/projects/$PROJECT_ID/files/$FILE_ID" \
  -H "Authorization: Bearer $COMPANY_TOKEN" -w "HTTP %{http_code}\n"
echo

echo "========================================"
echo "  DONE — Full E2E flow completed!"
echo "========================================"
