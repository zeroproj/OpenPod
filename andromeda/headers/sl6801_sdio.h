/* sl6801_sdio.h — ANDROMEDA: offsets provisórios do host SDIO/SDMMC
 * do SL6801 observados no firmware GN-438 (yp3_2.0.43).
 *
 * Base addresses:
 *   SL6801_SDIO0_BASE = 0x40020000  (SD host 0 / DMA?)
 *   SL6801_SDIO1_BASE = 0x40030000  (SD host 1 / controller principal?)
 *   SL6801_SDIO_DMA_BASE = 0x40038000  (DMA / bounce buffer config?)
 *
 * Os nomes dos registradores são placeholders. O significado real de cada
 * offset ainda não foi determinado — o header serve para experimentação
 * e comparação com outros SoCs da família Smartlink/SL680x.
 */

#ifndef SL6801_SDIO_H
#define SL6801_SDIO_H

#include <stdint.h>

#define SL6801_SDIO0_BASE       0x40020000
#define SL6801_SDIO1_BASE       0x40030000
#define SL6801_SDIO_DMA_BASE    0x40038000

/* SDIO0 — offsets acessados pelo firmware */
#define SDIO0_CTRL              (SL6801_SDIO0_BASE + 0x000)
#define SDIO0_CMD_ARG           (SL6801_SDIO0_BASE + 0x00C)
#define SDIO0_CMD_CTRL          (SL6801_SDIO0_BASE + 0x010)
#define SDIO0_RESP0             (SL6801_SDIO0_BASE + 0x018)
#define SDIO0_RESP1             (SL6801_SDIO0_BASE + 0x01C)
#define SDIO0_RESP2             (SL6801_SDIO0_BASE + 0x020)
#define SDIO0_RESP3             (SL6801_SDIO0_BASE + 0x030)
#define SDIO0_DATA_CTRL         (SL6801_SDIO0_BASE + 0x040)
#define SDIO0_DATA_LEN          (SL6801_SDIO0_BASE + 0x044)
#define SDIO0_DATA_FIFO         (SL6801_SDIO0_BASE + 0x080)
#define SDIO0_STATUS            (SL6801_SDIO0_BASE + 0x0C0)
#define SDIO0_INT_MASK          (SL6801_SDIO0_BASE + 0x1B0)
#define SDIO0_INT_STATUS        (SL6801_SDIO0_BASE + 0x1E4)

/* SDIO1 — offsets acessados pelo firmware */
#define SDIO1_CTRL              (SL6801_SDIO1_BASE + 0x000)
#define SDIO1_CLK_DIV           (SL6801_SDIO1_BASE + 0x020)
#define SDIO1_DATA_CTRL         (SL6801_SDIO1_BASE + 0x2B0)
#define SDIO1_STATUS            (SL6801_SDIO1_BASE + 0x2FC)
#define SDIO1_INT_STATUS        (SL6801_SDIO1_BASE + 0x304)
#define SDIO1_FIFO              (SL6801_SDIO1_BASE + 0x534)
#define SDIO1_UNKNOWN_EB8       (SL6801_SDIO1_BASE + 0xEB8)

/* SDIO DMA — offsets acessados pelo firmware */
#define SDIO_DMA_CTRL           (SL6801_SDIO_DMA_BASE + 0x000)

/* Macros de acesso (32 bits, little-endian) */
#define SDIO_REG32(base, off)   (*(volatile uint32_t *)((base) + (off)))

#endif /* SL6801_SDIO_H */
