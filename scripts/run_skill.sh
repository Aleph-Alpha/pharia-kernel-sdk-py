#!/bin/bash

SKILL_NAME=$1
PHARIA_AI_TOKEN=$2
PHARIA_KERNEL_ADDRESS=${3-http://127.0.0.1:8081}

echo "Copying built skill..."
mkdir -p skills
cp $SKILL_NAME.wasm skills/$SKILL_NAME.wasm

echo "Waiting for skill to be available..."
sleep 1

echo "Executing skill..."
RESPONSE_CODE=$(curl -w '%{http_code}' -s -o output.result \
                $PHARIA_KERNEL_ADDRESS/execute_skill \
                -H "Authorization: Bearer $PHARIA_AI_TOKEN" \
                -H 'Content-Type: application/json' \
                -d "{ \"skill\" : \"dev/$SKILL_NAME\", \"input\" : \"Kernel\" }")

cat output.result

if [ "$RESPONSE_CODE" = "200" ]; then
    exit 0
else
    echo "unexpected response code: RESPONSE_CODE='$RESPONSE_CODE'"
    exit 1
fi
