#!/usr/bin/env bash
# ==============================================================================
# StreakNudge API Demo Script
# Course: BIS505 Cloud Computing Mini-Project
#
# Usage:
#   ./scripts/demo.sh [API_BASE_URL] [API_KEY]
#
# Example:
#   ./scripts/demo.sh https://abc123xyz.execute-api.ap-south-1.amazonaws.com/dev streaknudge-secret-key-12345
# ==============================================================================

set -euo pipefail

# Color formatting
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

API_URL="${1:-http://localhost:3000}"
API_KEY="${2:-streaknudge-secret-key-12345}"

echo -e "${BLUE}====================================================${NC}"
echo -e "${BLUE}        StreakNudge Cloud API Demonstration         ${NC}"
echo -e "${BLUE}====================================================${NC}"
echo -e "Target API URL: ${YELLOW}${API_URL}${NC}"
echo -e "Using API Key : ${YELLOW}${API_KEY}${NC}\n"

# Helper function to print test titles
test_case() {
    echo -e "\n${BLUE}▶ Test Case $1: $2${NC}"
}

# ------------------------------------------------------------------------------
# 1. Security Check: Missing API Key
# ------------------------------------------------------------------------------
test_case "1" "Reject request when 'x-api-key' header is missing (Expected: 401)"
curl -s -w "\nHTTP Status: %{http_code}\n" \
  -X POST "${API_URL}/solves" \
  -H "Content-Type: application/json" \
  -d '{"user": "demo_user", "problem": "Two Sum", "difficulty": "Easy"}' || true

# ------------------------------------------------------------------------------
# 2. Input Validation: Invalid Difficulty & Malformed Payload
# ------------------------------------------------------------------------------
test_case "2" "Reject invalid payload schema (Expected: 400)"
curl -s -w "\nHTTP Status: %{http_code}\n" \
  -X POST "${API_URL}/solves" \
  -H "Content-Type: application/json" \
  -H "x-api-key: ${API_KEY}" \
  -d '{"user": "demo_user", "problem": "Two Sum", "difficulty": "SuperHard"}' || true

# ------------------------------------------------------------------------------
# 3. Log First Solve (First-ever solve initializes streak to 1)
# ------------------------------------------------------------------------------
test_case "3" "Log first solve for 'student_demo' (Expected: 201, streak_count: 1)"
curl -s -w "\nHTTP Status: %{http_code}\n" \
  -X POST "${API_URL}/solves" \
  -H "Content-Type: application/json" \
  -H "x-api-key: ${API_KEY}" \
  -d '{
    "user": "student_demo",
    "problem": "Contains Duplicate",
    "difficulty": "Easy",
    "email": "student_demo@example.com"
  }' || true

# ------------------------------------------------------------------------------
# 4. Same-Day Re-log Idempotency Check
# ------------------------------------------------------------------------------
test_case "4" "Log another solve on the same day (Expected: 201, streak_count remains 1)"
curl -s -w "\nHTTP Status: %{http_code}\n" \
  -X POST "${API_URL}/solves" \
  -H "Content-Type: application/json" \
  -H "x-api-key: ${API_KEY}" \
  -d '{
    "user": "student_demo",
    "problem": "Valid Anagram",
    "difficulty": "Easy"
  }' || true

# ------------------------------------------------------------------------------
# 5. Retrieve Current Streak Status
# ------------------------------------------------------------------------------
test_case "5" "Get streak for 'student_demo' (Expected: 200, status: ACTIVE_TODAY)"
curl -s -w "\nHTTP Status: %{http_code}\n" \
  -X GET "${API_URL}/streak/student_demo" \
  -H "x-api-key: ${API_KEY}" || true

# ------------------------------------------------------------------------------
# 6. Retrieve Nonexistent User
# ------------------------------------------------------------------------------
test_case "6" "Get streak for unknown user 'unknown_user_999' (Expected: 404)"
curl -s -w "\nHTTP Status: %{http_code}\n" \
  -X GET "${API_URL}/streak/unknown_user_999" \
  -H "x-api-key: ${API_KEY}" || true

echo -e "\n${GREEN}====================================================${NC}"
echo -e "${GREEN}      API Demonstration Completed Successfully!     ${NC}"
echo -e "${GREEN}====================================================${NC}"
