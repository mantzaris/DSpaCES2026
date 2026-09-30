#!/usr/bin/env bash
set -euo pipefail

project_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
identity_file="${HOME}/.ssh/id_rsa"
ssh_state_dir="${project_dir}/.local/ssh"

if [[ ! -r "${identity_file}" ]]; then
    printf 'Cannot read the approved SSH key: %s\n' "${identity_file}" >&2
    exit 1
fi

mkdir -p -- "${ssh_state_dir}"
chmod 700 -- "${ssh_state_dir}"

exec ssh \
    -o IdentitiesOnly=yes \
    -o ConnectTimeout=15 \
    -o ServerAliveInterval=30 \
    -o ServerAliveCountMax=3 \
    -o StrictHostKeyChecking=accept-new \
    -o "UserKnownHostsFile=${ssh_state_dir}/known_hosts" \
    -i "${identity_file}" \
    -p 22071 \
    root@194.68.245.88 "$@"
