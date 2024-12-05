#!/bin/bash

JFROG_USER=$1
JFROG_TOKEN=$2
PHARIA_AI_TOKEN=$3

podman login alephalpha.jfrog.io/pharia-kernel-images -u $JFROG_USER -p $JFROG_TOKEN
podman pull alephalpha.jfrog.io/pharia-kernel-images/pharia-kernel:latest
podman tag alephalpha.jfrog.io/pharia-kernel-images/pharia-kernel:latest pharia-kernel

mkdir -p skills

(podman run \
  -v ./skills:/app/skills \
  -e PHARIA_AI_TOKEN=$PHARIA_AI_TOKEN \
  -e NAMESPACE_UPDATE_INTERVAL=300ms \
  -e LOG_LEVEL="pharia_kernel=debug" \
  -p 8081:8081\
  pharia-kernel | cat) &
