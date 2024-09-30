#!/bin/bash

AA_API_TOKEN=$1
PHARIA_KERNEL_ADDRESS=${2-http://127.0.0.1:8081}

if [ ! -d "wasi_deps" ]; then
  echo "Pulling Pydantic WASI..."
  mkdir -p wasi_deps
  cd wasi_deps
  curl -OL https://github.com/dicej/wasi-wheels/releases/download/latest/pydantic_core-wasi.tar.gz
  tar xf pydantic_core-wasi.tar.gz
  rm pydantic_core-wasi.tar.gz
  cd ..
fi

echo "Building skill..."
mkdir -p skills
componentize-py -w skill componentize examples.haiku -o skills/haiku.wasm -p . -p wasi_deps

echo "Waiting for skill to be available..."
sleep 2

echo "Executing skill..."
RESPONSE_CODE=$(curl -w '%{http_code}' -s -o /dev/null \
                $PHARIA_KERNEL_ADDRESS/execute_skill \
                -H "Authorization: Bearer $AA_API_TOKEN" \
                -H 'Content-Type: application/json' \
                -d '{ "skill" : "dev/haiku", "input" : { "topic" : "Homer" } }')

if [ "$RESPONSE_CODE" = "200" ]; then
    exit 0
else
    echo "unexpected response code: RESPONSE_CODE='$RESPONSE_CODE'"
    exit 1
fi
