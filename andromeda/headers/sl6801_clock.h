/*
 * ANDROMEDA — Header provisório para clock/reset do SL6801
 *
 * Bases detectadas: 0x40080000 (clock/reset principal)
 *                   0x40081000 (clock/reset secundário)
 * Fonte: andromeda/PERIPHERAL_REGISTER_SCAN.md
 *
 * ATENÇÃO: os offsets abaixo foram coletados por análise estática. Os
 * nomes são placeholders. O significado real de cada registrador ainda
 * não foi confirmado.
 */

#ifndef SL6801_CLOCK_H
#define SL6801_CLOCK_H

#include <stdint.h>

#define SL6801_CLK0_BASE  ((volatile uint32_t *)0x40080000)
#define SL6801_CLK1_BASE  ((volatile uint32_t *)0x40081000)

#define CLK0_REG(offset)  (*((volatile uint32_t *)(0x40080000 + (offset))))
#define CLK1_REG(offset)  (*((volatile uint32_t *)(0x40081000 + (offset))))

/* Clock/reset principal (0x40080000) */
#define CLK0_000          CLK0_REG(0x000)
#define CLK0_010          CLK0_REG(0x010)
#define CLK0_014          CLK0_REG(0x014)
#define CLK0_030          CLK0_REG(0x030)
#define CLK0_040          CLK0_REG(0x040)
#define CLK0_048          CLK0_REG(0x048)
#define CLK0_064          CLK0_REG(0x064)
#define CLK0_074          CLK0_REG(0x074)
#define CLK0_0E8          CLK0_REG(0x0E8)

/* Clock/reset secundário (0x40081000) */
#define CLK1_000          CLK1_REG(0x000)
#define CLK1_024          CLK1_REG(0x024)
#define CLK1_02C          CLK1_REG(0x02C)
/* 0x40081404 aparece como literal isolado; pode ser typo ou outro bloco */
#define CLK1_404          CLK1_REG(0x404)

#endif /* SL6801_CLOCK_H */
