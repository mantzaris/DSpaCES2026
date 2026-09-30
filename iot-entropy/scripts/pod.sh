#!/usr/bin/env bash
set -euo pipefail
project_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
connection="ssh -o IdentitiesOnly=yes -o StrictHostKeyChecking=accept-new -o UserKnownHostsFile=${project_dir}/.local/ssh/known_hosts -i ${HOME}/.ssh/id_rsa -p 22071"
case "${1:-}" in
  upload)
    rsync -az --exclude=.local --exclude=.venv --exclude=__pycache__ \
      --exclude=.pytest_cache --exclude=data/raw --exclude=literature/raw \
      --exclude=experiments -e "${connection}" "${project_dir}/" \
      root@194.68.245.88:/workspace/iot-entropy/
    ;;
  download)
    for directory in experiments data/processed data/manifests environment; do
      mkdir -p -- "${project_dir}/${directory}"
      rsync -az -e "${connection}" \
        "root@194.68.245.88:/workspace/iot-entropy/${directory}/" \
        "${project_dir}/${directory}/"
    done
    ;;
  exec)
    shift
    exec "${project_dir}/scripts/ssh-gpu.sh" "$@"
    ;;
  *) printf 'Usage: %s {upload|download|exec COMMAND}\n' "$0" >&2; exit 2 ;;
esac
