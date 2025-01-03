#!/bin/bash

JFROG_USER=$1
JFROG_TOKEN=$2

podman login alephalpha.jfrog.io/pharia-kernel-images -u $JFROG_USER -p $JFROG_TOKEN
podman pull alephalpha.jfrog.io/pharia-kernel-images/pharia-kernel:latest
podman tag alephalpha.jfrog.io/pharia-kernel-images/pharia-kernel:latest pharia-kernel

mkdir -p skills

(podman run \
  -v ./skills:/app/skills \
  -e NAMESPACE_UPDATE_INTERVAL=300ms \
  -e LOG_LEVEL="pharia_kernel=debug" \
  -e NAMESPACES__DEV__DIRECTORY="skills" \
  -p 8081:8081\
  pharia-kernel | cat) &
