#!/usr/bin/env python3
import argparse
import os
import subprocess
import sys


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rustc", required=True)
    parser.add_argument("--target", required=True)
    parser.add_argument("--crate-name", required=True)
    parser.add_argument("--src", required=True)
    parser.add_argument("--linker-script", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    src = os.path.abspath(args.src)
    linker_script = os.path.abspath(args.linker_script)
    out = os.path.abspath(args.out)
    out_dir = os.path.dirname(out)
    os.makedirs(out_dir, exist_ok=True)

    cmd = [
        args.rustc,
        "--edition=2021",
        "--crate-name",
        args.crate_name,
        "--crate-type",
        "bin",
        "--target",
        args.target,
        src,
        "-C",
        "panic=abort",
        "-C",
        "linker=rust-lld",
        "-C",
        f"link-arg=-T{linker_script}",
        "-C",
        "debuginfo=2",
        "-o",
        out,
    ]

    print("[GN kernel]", " ".join(cmd))
    result = subprocess.run(cmd, check=False)
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
