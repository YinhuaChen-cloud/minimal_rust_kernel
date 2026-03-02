# Minimal Rust Kernel (RISC-V64)

这个最小内核使用 `UART16550` MMIO（`0x1000_0000`）在 QEMU `virt` 机器上输出 `hello world`。

## 文件结构

- `src/entry.S`：启动入口，设置栈并跳转到 `rust_main`
- `src/main.rs`：`no_std` 内核主逻辑 + UART 输出
- `linker.ld`：链接地址和段布局（起始 `0x80200000`）
- `BUILD.gn`：GN 构建入口（`kernel` 目标）
- `build/build_kernel.py`：实际调用 `rustc` 生成内核 ELF

## GN + Ninja（当前推荐）

1. 安装依赖工具：

```bash
sudo apt-get install -y gn ninja-build
```

2. 生成构建目录（默认 target 为 `riscv64-vivo-blueos`）：

```bash
gn gen out/default
```

3. 编译内核：

```bash
ninja -C out/default kernel
```

4. 运行（QEMU 默认 OpenSBI）：

```bash
qemu-system-riscv64 -machine virt -nographic -kernel out/default/minimal_rust_kernel
```

你会看到：

```text
hello world
```

## QEMU + GDB 单步调试（GN 构建）

1. 准备工具（至少要有一个 GDB）：

```bash
sudo apt-get install -y qemu-system-misc gdb-multiarch
```

2. 构建带调试信息的内核（默认已开启 `-C debuginfo=2`）：

```bash
gn gen out/default
ninja -C out/default kernel
```

3. 终端 A：启动 QEMU 并等待 GDB 连接（CPU 暂停在入口）：

```bash
./build/run_qemu_gdb.sh out/default/minimal_rust_kernel 1234
```

4. 终端 B：连接 GDB：

```bash
./build/run_gdb.sh out/default/minimal_rust_kernel 1234
```

5. 在 GDB 中单步（源码或地址映射二选一，这里给源码流）：

```gdb
continue
list
stepi
x/i $pc
info line *$pc
```

说明：

- `break rust_main` 已在 `run_gdb.sh` 里自动设置。
- `list` 可查看当前 Rust 源码位置。
- `info line *$pc` 可查看当前地址到源码行的映射。

## Cargo（兼容保留）

如果你仍希望使用 Cargo，可继续使用原命令：

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

---

## 与 C 内核不同点

我询问：

从 `CARGO_BUILD_TARGET=riscv64-vivo-blueos RUSTFLAGS='-C link-arg=-Tlinker.ld' cargo build -v` 打印出的 rustc 命令来看，里面只出现了 main.rs 没有出现 entry.S。

或许这就是 C 语言 和 RUST 语言一个主要的区别？C 语言编译中要对每一个文件单独编译，再最后链接，因此可以打印 make 的全过程知道哪些文件参与了编译。

而 RUST 从 rustc 来看只会出现一个文件 main.rs，rust编译器会自己根据 main.rs 查找相关的文件，因此编译命令只有一个，编译命令也只会出现一个文件？

AI回答：

你理解得很接近了，结论是：Rust 以“crate”为编译单元，不是以“每个源文件”为编译单元。

cargo build -v 里看到的 rustc ... main.rs，表示这个 crate 的入口文件是 main.rs，但 crate 内其它模块文件也会被同一次 rustc 编译一起处理。

你这个项目里的 entry.S 不是作为“独立输入文件”传给 rustc，而是通过 main.rs 的 global_asm!(include_str!("entry.S")) 以内联汇编文本方式并入编译流程，所以命令行里不会单独列出它。

C/Make 常见流程是“每个 .c/.S 先产出 .o，最后链接”；Rust 常见流程是“每个 crate 一次 rustc（内部再做模块解析、代码生成、链接）”。

所以不是“Rust 只编译一个文件”，而是“Rust 把一个 crate 当作整体编译”，main.rs 只是入口。
如果你想看到更接近 C 的“单独编译汇编文件”效果，可以改成 build.rs + cc 去编译 .S，那日志里就会出现单独的汇编编译命令。

我询问：

我理解 C内核 编译流程的方法通常是，找到可以编译整个内核镜像的目标，然后 make -n 目标直接找到所有命令，就知道涉及的文件有哪些。

现在看起来RUST不能这么做，有没有方法达到类似的效果，让它列出所有会被编译器内核镜像的文件名？

AI回答：

Rust 里最接近 make -n 的办法是看 rustc 产物里的 dep-info（.d 文件），它会列出该 crate 的所有输入源文件。

你这个工程已经验证过，.d 里明确有 main.rs 和 entry.S，说明汇编文件确实参与了构建。

关键文件示例：/target/riscv64-vivo-blueos/debug/deps/minimal_rust_kernel-e2ee4cb559e2c371.d

---

# 逐步拆解 “QEMU + GDB 单步调试（GN 构建）” 过程

```bash
gn gen out/default
```

1.GN 从当前目录向上找工程根，并读取 .gn。

2.从 .gn 里拿到 buildconfig = "//build/BUILDCONFIG.gn"

3.在 BUILDCONFIG.gn 执行 set_default_toolchain("//build/toolchain:host")，确定默认工具链标签。

4.进入根 BUILD.gn，执行 declare_args()，得到默认参数：kernel_name/minimal_rust_kernel、kernel_target/riscv64-vivo-blueos、kernel_rustc/rustc（可被 args.gn 或 --args 覆盖）。

5.解析 action("kernel")：记录 script、inputs、outputs、args，把 rebase_path(...) 展开成相对 out/default 的路径。

6.因为默认工具链是 //build/toolchain:host，GN 加载 BUILD.gn，读取 toolchain("host") 里的 stamp/copy/action 工具定义。

7.GN 构建完整 target graph（你这里主要就是 //:kernel 这个 action target, 位于根目录 BUILD.gn），并做合法性检查（label、路径、输出格式等）。

8.GN 把图写成 Ninja：顶层规则写到 build.ninja，工具链具体规则写到 toolchain.ninja。

9.同时写再生成依赖 build.ninja.d（你这里记录了 .gn、BUILD.gn、BUILDCONFIG.gn、toolchain BUILD、args.gn），以及 build.ninja.stamp。

10.gn gen 结束；真正执行 python build/build_kernel.py / rustc 要等你跑 ninja -C out/default kernel 才会发生。

---



