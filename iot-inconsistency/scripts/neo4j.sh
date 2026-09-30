#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
NAME=iot-inconsistency-neo4j
IMAGE=neo4j@sha256:5eb12ad77fa46ab73e23df9ea1f43f5c0f2a79523435577648e046be042b9b93
case "${1:-start}" in
  start)
    mkdir -p runtime/neo4j/data runtime/neo4j/logs
    if docker container inspect "$NAME" >/dev/null 2>&1; then
      docker start "$NAME"
    else
      docker run -d --name "$NAME" --label research.project=iot-inconsistency --memory 2g --cpus 2 \
        -p 127.0.0.1:17474:7474 -p 127.0.0.1:17687:7687 \
        -e NEO4J_AUTH=none -e NEO4J_server_memory_heap_initial__size=256m \
        -e NEO4J_server_memory_heap_max__size=512m -e NEO4J_server_memory_pagecache_size=256m \
        -v "$PWD/runtime/neo4j/data:/data" -v "$PWD/runtime/neo4j/logs:/logs" "$IMAGE"
    fi
    ;;
  status) docker inspect --format '{{.State.Status}}' "$NAME";;
  stop) docker stop "$NAME";;
  query) shift; docker exec "$NAME" cypher-shell "$@";;
  *) echo 'Usage: bash scripts/neo4j.sh {start|status|stop|query CYPHER}' >&2;exit 2;;
esac
