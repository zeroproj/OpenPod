/*
 * ANDROMEDA — Header provisório para LCDC do SL6801
 *
 * Bases detectadas: 0x400D0000
 *                   0x400D1000
 * Fonte: andromeda/PERIPHERAL_REGISTER_SCAN.md
 *
 * ATENÇÃO: offsets coletados por análise estática. Nomes são placeholders.
 */

#ifndef SL6801_LCDC_H
#define SL6801_LCDC_H

#include <stdint.h>

#define SL6801_LCDC0_BASE ((volatile uint32_t *)0x400D0000)
#define SL6801_LCDC1_BASE ((volatile uint32_t *)0x400D1000)

#define LCDC0_REG(offset) (*((volatile uint32_t *)(0x400D0000 + (offset))))
#define LCDC1_REG(offset) (*((volatile uint32_t *)(0x400D1000 + (offset))))

/* LCDC0 (0x400D0000) */
#define LCDC0_000         LCDC0_REG(0x000)
#define LCDC0_008         LCDC0_REG(0x008)
#define LCDC0_00C         LCDC0_REG(0x00C)
#define LCDC0_020         LCDC0_REG(0x020)
#define LCDC0_040         LCDC0_REG(0x040)
#define LCDC0_060         LCDC0_REG(0x060)

/* LCDC1 (0x400D1000) */
#define LCDC1_000         LCDC1_REG(0x000)
#define LCDC1_008         LCDC1_REG(0x008)
#define LCDC1_00C         LCDC1_REG(0x00C)
#define LCDC1_010         LCDC1_REG(0x010)
#define LCDC1_014         LCDC1_REG(0x014)
#define LCDC1_018         LCDC1_REG(0x018)
#define LCDC1_020         LCDC1_REG(0x020)
#define LCDC1_024         LCDC1_REG(0x024)
#define LCDC1_028         LCDC1_REG(0x028)
#define LCDC1_02C         LCDC1_REG(0x02C)
#define LCDC1_040         LCDC1_REG(0x040)
#define LCDC1_044         LCDC1_REG(0x044)
#define LCDC1_050         LCDC1_REG(0x050)
#define LCDC1_05C         LCDC1_REG(0x05C)

#endif /* SL6801_LCDC_H */
