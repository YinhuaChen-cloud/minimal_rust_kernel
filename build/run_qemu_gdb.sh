#!/usr/bin/env bash
set -euo pipefail

KERNEL_PATH="${1:-out/default/minimal_rust_kernel}"
GDB_PORT="${2:-1234}"

exec qemu-system-riscv64 \
  -machine virt \
  -nographic \
  -kernel "${KERNEL_PATH}" \
  -S \
  -gdb "tcp::${GDB_PORT}"
