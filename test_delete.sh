#!/bin/bash
echo "Testing DELETE request through Next.js middleware..."
TOKEN=$(curl -s http://localhost:3000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}' | jq -r '.access_token')

echo "Got token: ${TOKEN:0:20}..."

curl -X DELETE "http://localhost:3000/api/v1/places/my/dc0bc2f4-7556-4a51-9c9b-83a66d3ddceb" \
  -H "Authorization: Bearer $TOKEN" \
  -v 2>&1 | head -30
