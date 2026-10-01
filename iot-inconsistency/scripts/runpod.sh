#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
REMOTE_HOST=root@213.173.108.109
REMOTE_DIR=/workspace/iot-inconsistency
SSH_ARGS=(-p 18860 -o BatchMode=yes -o ConnectTimeout=20 -o UserKnownHostsFile=/tmp/dspaces2026-runpod-known-hosts)
case "${1:-status}" in
  sync)
    ssh "${SSH_ARGS[@]}" "$REMOTE_HOST" "mkdir -p $REMOTE_DIR"
    rsync -az --exclude=.git --exclude=.venv --exclude=runtime --exclude=results --exclude=__pycache__ --exclude=literature/upstream --exclude=literature/downloads -e "ssh ${SSH_ARGS[*]}" ./ "$REMOTE_HOST:$REMOTE_DIR/"
    ;;
  pull)
    rsync -az --exclude='*.pt' --exclude='*.tmp' -e "ssh ${SSH_ARGS[*]}" "$REMOTE_HOST:$REMOTE_DIR/results/" results/
    ;;
  pull-flow)
    mkdir -p results/graph_flow_v1
    rsync -az --exclude=models --exclude=raw --exclude=cache --exclude='*.tmp' -e "ssh ${SSH_ARGS[*]}" "$REMOTE_HOST:$REMOTE_DIR/results/graph_flow_v1/" results/graph_flow_v1/
    ;;
  push-flow-baselines)
    ssh "${SSH_ARGS[@]}" "$REMOTE_HOST" "mkdir -p $REMOTE_DIR/results/graph_flow_v1/models $REMOTE_DIR/results/graph_flow_v1/development"
    rsync -az --include='ppca_*.pkl' --include='ppca_*.json' --include='*_supervised.npz' --exclude='*' -e "ssh ${SSH_ARGS[*]}" results/graph_flow_v1/models/ "$REMOTE_HOST:$REMOTE_DIR/results/graph_flow_v1/models/"
    rsync -az --include='*_baselines.json' --exclude='*' -e "ssh ${SSH_ARGS[*]}" results/graph_flow_v1/development/ "$REMOTE_HOST:$REMOTE_DIR/results/graph_flow_v1/development/"
    ;;
  status)
    ssh "${SSH_ARGS[@]}" "$REMOTE_HOST" 'nvidia-smi; pgrep -af "iot-inconsistency|run_study" || true'
    ;;
  exec)
    shift
    printf -v COMMAND '%q ' "$@"
    ssh "${SSH_ARGS[@]}" "$REMOTE_HOST" "cd $REMOTE_DIR && $COMMAND"
    ;;
  *) echo 'Usage: bash scripts/runpod.sh {sync|pull|pull-flow|push-flow-baselines|status|exec COMMAND...}' >&2; exit 2;;
esac
