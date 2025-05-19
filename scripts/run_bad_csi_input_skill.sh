#!/bin/bash

PHARIA_AI_TOKEN=$1
PHARIA_KERNEL_ADDRESS=${2-http://127.0.0.1:8081}

echo "Copy built Skill..."
mkdir -p skills
cp bad_csi_input.wasm skills/bad_csi_input.wasm

echo "Waiting for Skill to be available..."
sleep 2

echo "Executing Skill..."
RESPONSE_BODY=$(curl -s $PHARIA_KERNEL_ADDRESS/v1/skills/dev/bad_csi_input/run \
                -H "Authorization: Bearer $PHARIA_AI_TOKEN" \
                -H 'Content-Type: application/json' \
                -d '"Homer"')

if echo "$RESPONSE_BODY" | grep -q "1 validation error for CompletionRequest"; then
    exit 0
else
    echo "$RESPONSE_BODY"
    exit 1
fi
