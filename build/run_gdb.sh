#!/usr/bin/env bash
set -euo pipefail

KERNEL_PATH="${1:-out/default/minimal_rust_kernel}"
GDB_PORT="${2:-1234}"

if [[ -n "${RISCV_GDB:-}" ]]; then
  GDB_BIN="${RISCV_GDB}"
elif command -v riscv64-unknown-elf-gdb >/dev/null 2>&1; then
  GDB_BIN="riscv64-unknown-elf-gdb"
elif command -v gdb-multiarch >/dev/null 2>&1; then
  GDB_BIN="gdb-multiarch"
else
  echo "No suitable GDB found. Please install riscv64-unknown-elf-gdb or gdb-multiarch." >&2
  exit 1
fi

exec "${GDB_BIN}" "${KERNEL_PATH}" \
  -ex "set confirm off" \
  -ex "target remote :${GDB_PORT}" \
  -ex "break rust_main"
