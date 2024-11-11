#!/bin/bash

AA_API_TOKEN=$1
PHARIA_KERNEL_ADDRESS=${2-http://127.0.0.1:8081}

echo "Building skill..."
mkdir -p skills
pharia-skill build examples.failing
mv failing.wasm skills/failing.wasm

echo "Waiting for skill to be available..."
sleep 2

echo "Executing skill..."
RESPONSE_BODY=$(curl -s $PHARIA_KERNEL_ADDRESS/execute_skill \
                -H "Authorization: Bearer $AA_API_TOKEN" \
                -H 'Content-Type: application/json' \
                -d '{ "skill" : "dev/failing", "input" : "Homer" }')

if echo "$RESPONSE_BODY" | grep -q "ValueError: I never expect to finish"; then
    exit 0
else
    echo "ValueError not found in skill response"
    exit 1
fi
