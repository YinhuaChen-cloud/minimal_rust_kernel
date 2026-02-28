# Minimal Rust Kernel (RISC-V64)

这个最小内核使用 `UART16550` MMIO（`0x1000_0000`）在 QEMU `virt` 机器上输出 `hello world`。

## 文件结构

- `src/entry.S`：启动入口，设置栈并跳转到 `rust_main`
- `src/main.rs`：`no_std` 内核主逻辑 + UART 输出
- `linker.ld`：链接地址和段布局（起始 `0x80200000`）
- `.cargo/config.toml`：默认目标和链接参数

## 标准 Rust 工具链（推荐）

1. 安装 target：

```bash
rustup target add riscv64gc-unknown-none-elf
```

2. 编译：

```bash
cargo build
```

3. 运行（QEMU 默认 OpenSBI）：

```bash
qemu-system-riscv64 -machine virt -nographic -kernel target/riscv64gc-unknown-none-elf/debug/minimal_rust_kernel
```

你会看到：

```text
hello world
```

## 当前环境（无 rustup，自定义工具链）

如果你的环境没有 `riscv64gc-unknown-none-elf` 标准库，可临时使用已安装目标构建：

```bash
CARGO_BUILD_TARGET=riscv64-vivo-blueos RUSTFLAGS='-C link-arg=-Tlinker.ld' cargo build
qemu-system-riscv64 -machine virt -nographic -kernel target/riscv64-vivo-blueos/debug/minimal_rust_kernel
```
