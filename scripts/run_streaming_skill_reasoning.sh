#!/bin/bash
# Test any message stream skill that expects a single string input.

SKILL_NAME=$1
PHARIA_AI_TOKEN=$2
PHARIA_KERNEL_ADDRESS=${3-http://127.0.0.1:8081}

echo "Copying built Skill..."
mkdir -p skills
cp $SKILL_NAME.wasm skills/$SKILL_NAME.wasm

echo "Waiting for Skill to be available..."
sleep 1

echo "Executing Skill..."
RESPONSE_CODE=$(curl -w '%{http_code}' -s -o output.result \
                $PHARIA_KERNEL_ADDRESS/v1/skills/dev/$SKILL_NAME/message-stream \
                -H "Authorization: Bearer $PHARIA_AI_TOKEN" \
                -H 'Content-Type: application/json' \
                -d '"Kernel"' )

cat output.result

if [ "$RESPONSE_CODE" = "200" ]; then
    # assert that there is at least one "event: reasoning" in the output
    if [ $(grep -c "event: reasoning" output.result) -eq 0 ]; then
        echo "expected at least one event: reasoning"
        exit 1
    fi
    # assert that there is no error event
    if [ $(grep -c "event: error" output.result) -ne 0 ]; then
        echo "unexpected error event: $(grep -c "event: error" output.result)"
        exit 1
    fi
    exit 0
else
    echo "unexpected response code: RESPONSE_CODE='$RESPONSE_CODE'"
    exit 1
fi
