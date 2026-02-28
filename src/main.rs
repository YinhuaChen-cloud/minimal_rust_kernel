#![no_std]
#![no_main]

use core::arch::global_asm;
use core::panic::PanicInfo;

global_asm!(include_str!("entry.S"));

const UART0_BASE: usize = 0x1000_0000;
const UART_THR: usize = 0;
const UART_LSR: usize = 5;
const UART_LSR_THRE: u8 = 1 << 5;

#[inline(always)]
fn uart_reg(offset: usize) -> *mut u8 {
    (UART0_BASE + offset) as *mut u8
}

fn uart_putc(byte: u8) {
    while unsafe { core::ptr::read_volatile(uart_reg(UART_LSR)) } & UART_LSR_THRE == 0 {}
    unsafe {
        core::ptr::write_volatile(uart_reg(UART_THR), byte);
    }
}

fn uart_puts(s: &str) {
    for b in s.bytes() {
        if b == b'\n' {
            uart_putc(b'\r');
        }
        uart_putc(b);
    }
}

#[no_mangle]
pub extern "C" fn rust_main() -> ! {
    uart_puts("hello world\n");

    loop {
        core::hint::spin_loop();
    }
}

#[panic_handler]
fn panic(_info: &PanicInfo) -> ! {
    uart_puts("panic\n");
    loop {
        core::hint::spin_loop();
    }
}
