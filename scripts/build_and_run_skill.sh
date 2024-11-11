#!/bin/bash

AA_API_TOKEN=$1
PHARIA_KERNEL_ADDRESS=${2-http://127.0.0.1:8081}

echo "Building skill..."
mkdir -p skills
pharia-skill build examples.haiku
mv haiku.wasm skills/haiku.wasm

echo "Waiting for skill to be available..."
sleep 2

echo "Executing skill..."
RESPONSE_CODE=$(curl -w '%{http_code}' -s -o /dev/null \
                $PHARIA_KERNEL_ADDRESS/execute_skill \
                -H "Authorization: Bearer $AA_API_TOKEN" \
                -H 'Content-Type: application/json' \
                -d '{ "skill" : "dev/haiku", "input" : "Homer" }')

if [ "$RESPONSE_CODE" = "200" ]; then
    exit 0
else
    echo "unexpected response code: RESPONSE_CODE='$RESPONSE_CODE'"
    exit 1
fi
