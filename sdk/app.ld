/* Injected code lives in the free flash area 0x1AB000..0x1FC000 and runs
 * in place at 0xC00000 + offset.  The first symbol is the menu hook; the
 * build tool patches the factory call at 0xD23CF8 to it. */
MEMORY
{
	CODE (rx) : ORIGIN = 0x00DAB000, LENGTH = 0x51000
}

SECTIONS
{
	.text : {
		KEEP(*(.text.entry*))
		*(.text .text.*)
		*(.rodata .rodata.*)
		. = ALIGN(4);
		KEEP(*(.fw_menu))
	} > CODE

	.data : { *(.data .data.*) } > CODE
	.bss : { *(.bss .bss.* COMMON) } > CODE

	/DISCARD/ : { *(.ARM.exidx* .ARM.extab* .comment .note*) }
}

ASSERT(SIZEOF(.data) == 0, "writable globals are not supported: .data must be empty")
ASSERT(SIZEOF(.bss) == 0, "writable globals are not supported: .bss must be empty")
ASSERT(SIZEOF(.text) <= 0x51000, "SDK does not fit the free flash area")
