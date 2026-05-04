#!/usr/bin/env bash
# cURL examples for the RK Gen AI Chatbot REST API.
# Requires: curl, jq (optional, for pretty output)
set -e

API="${API:-http://localhost:5000}"

echo "── Health ──"
curl -s "$API/api/health" | jq .

echo
echo "── Create session ──"
SID=$(curl -s "$API/api/session" | jq -r .session_id)
echo "session_id: $SID"

echo
echo "── Chat (sync) ──"
curl -s -X POST "$API/api/chat" \
  -H "Content-Type: application/json" \
  -d "{\"message\":\"Tell me about InternOps\",\"session_id\":\"$SID\"}" | jq .

echo
echo "── Chat (streaming, SSE) ──"
curl -N -s -X POST "$API/api/chat/stream" \
  -H "Content-Type: application/json" \
  -d "{\"message\":\"What are his certifications?\"}" \
  | head -20

echo
echo "── Integration endpoint (for SDKs / widgets) ──"
curl -s -X POST "$API/api/integrate/chat" \
  -H "Content-Type: application/json" \
  -d '{"message":"How can I contact Rajat?"}' | jq .

echo
echo "── AI bootstrap (frontend) ──"
curl -s "$API/api/ai/suggestions" | jq .data
