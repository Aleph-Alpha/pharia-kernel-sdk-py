#!/bin/bash

JFROG_USER=$1
JFROG_TOKEN=$2
AA_API_TOKEN=$3

podman login alephalpha.jfrog.io/pharia-kernel-images -u $JFROG_USER -p $JFROG_TOKEN
podman pull alephalpha.jfrog.io/pharia-kernel-images/pharia-kernel:latest
podman tag alephalpha.jfrog.io/pharia-kernel-images/pharia-kernel:latest pharia-kernel

mkdir -p skills

(podman run \
  -v ./skills:/app/skills \
  -e AA_API_TOKEN=$AA_API_TOKEN \
  -e NAMESPACE_UPDATE_INTERVAL=1s \
  -e LOG_LEVEL="pharia_kernel=debug" \
  -p 8081:8081\
  pharia-kernel | cat) &
