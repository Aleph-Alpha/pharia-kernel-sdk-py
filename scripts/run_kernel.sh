#!/bin/bash

GITHUB_USER=$1
GITHUB_TOKEN=$2
domain=${3-product.pharia.com}

podman login ghcr.io -u $GITHUB_USER -p $GITHUB_TOKEN
podman pull ghcr.io/aleph-alpha/pharia-kernel/pharia-kernel:latest
podman tag ghcr.io/aleph-alpha/pharia-kernel/pharia-kernel:latest pharia-kernel

mkdir -p skills

(podman run \
  -v ./skills:/app/skills \
  -e NAMESPACE_UPDATE_INTERVAL=300ms \
  -e INFERENCE_URL=https://inference-api.$domain \
  -e DOCUMENT_INDEX_URL=https://document-index.$domain \
  -e AUTHORIZATION_URL=https://pharia-iam.$domain \
  -e LOG_LEVEL="pharia_kernel=debug" \
  -e NAMESPACES__DEV__DIRECTORY="skills" \
  -p 8081:8081\
  pharia-kernel | cat) &
