#!/bin/bash

PHARIA_AI_TOKEN=$1
PHARIA_KERNEL_ADDRESS=${2-http://127.0.0.1:8081}

echo "Copy built Skill..."
mkdir -p skills
cp failing.wasm skills/failing.wasm

echo "Waiting for Skill to be available..."
sleep 2

echo "Executing Skill..."
RESPONSE_BODY=$(curl -s $PHARIA_KERNEL_ADDRESS/v1/skills/dev/failing/run \
                -H "Authorization: Bearer $PHARIA_AI_TOKEN" \
                -H 'Content-Type: application/json' \
                -d '"Homer"')

if echo "$RESPONSE_BODY" | grep -q "ValueError: I never expect to finish"; then
    exit 0
else
    echo "ValueError not found in Skill response"
    exit 1
fi
