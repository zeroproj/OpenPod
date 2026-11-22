/* Reload 3.5 SDK layout: the menu hook stays at 0xDAB000 and the player
 * hooks get fixed addresses so the 3.5 tool can patch the factory calls
 * without a symbol table.  The gaps are zero-filled inside .text; the rest
 * of the free area is filled with 0xFF by the 3.5 tool. */
MEMORY
{
	CODE (rx) : ORIGIN = 0x00DAB000, LENGTH = 0x51000
}

SECTIONS
{
	.text : {
		KEEP(*(.text.hook_home_menu_create))
		. = 0x00DAB200;
		KEEP(*(.text.hook_home_create))
		. = 0x00DAB600;
		KEEP(*(.text.fw_player_title_hook))
		. = 0x00DAB700;
		KEEP(*(.text.fw_player_title_hook_home_wrap))
		. = 0x00DAB800;
		KEEP(*(.text.fw_player_timer_cb))
		. = 0x00DAB900;
		*(.text .text.*)
		*(.rodata .rodata.*)
		. = ALIGN(4);
	} > CODE

	.data : { *(.data .data.*) } > CODE
	.bss : { *(.bss .bss.* COMMON) } > CODE

	/DISCARD/ : { *(.ARM.exidx* .ARM.extab* .comment .note*) }
}

ASSERT(SIZEOF(.data) == 0, "writable globals are not supported: .data must be empty")
ASSERT(SIZEOF(.bss) == 0, "writable globals are not supported: .bss must be empty")
ASSERT(SIZEOF(.text) <= 0x51000, "SDK does not fit the free flash area")
