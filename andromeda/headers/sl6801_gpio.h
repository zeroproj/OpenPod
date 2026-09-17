/*
 * ANDROMEDA — Header provisório para GPIO/pinmux do SL6801
 *
 * Base detectada: 0x40085000
 * Fonte: andromeda/PERIPHERAL_REGISTER_SCAN.md
 *
 * ATENÇÃO: os offsets abaixo foram coletados por análise estática do
 * firmware GN438_original.bin. Os nomes são placeholders. O significado
 * real de cada registrador ainda não foi confirmado.
 */

#ifndef SL6801_GPIO_H
#define SL6801_GPIO_H

#include <stdint.h>

#define SL6801_GPIO_BASE  ((volatile uint32_t *)0x40085000)

/*
 * Offsets acessados pelo firmware (conservativo):
 *
 * +0x000  base carregada 33x em 22 funções
 * +0x060  escrita
 * +0x070  leitura
 * +0x074  leitura/escrita
 * +0x078  leitura/escrita
 * +0x080  leitura/escrita
 * +0x084  leitura intensa
 * +0x088  leitura
 * +0x098  leitura/escrita intensa
 * +0x0A0  leitura/escrita
 * +0x0A4  leitura/escrita
 * +0x0AC..+0x0C0  escrita
 * +0x0D0..+0x0EC  leitura/escrita
 * +0x100..+0x110  leitura/escrita
 */

#define GPIO_REG(offset)  (*((volatile uint32_t *)(0x40085000 + (offset))))

#define GPIO_000          GPIO_REG(0x000)
#define GPIO_060          GPIO_REG(0x060)
#define GPIO_070          GPIO_REG(0x070)
#define GPIO_074          GPIO_REG(0x074)
#define GPIO_078          GPIO_REG(0x078)
#define GPIO_080          GPIO_REG(0x080)
#define GPIO_084          GPIO_REG(0x084)
#define GPIO_088          GPIO_REG(0x088)
#define GPIO_098          GPIO_REG(0x098)
#define GPIO_0A0          GPIO_REG(0x0A0)
#define GPIO_0A4          GPIO_REG(0x0A4)
#define GPIO_0AC          GPIO_REG(0x0AC)
#define GPIO_0B0          GPIO_REG(0x0B0)
#define GPIO_0B4          GPIO_REG(0x0B4)
#define GPIO_0B8          GPIO_REG(0x0B8)
#define GPIO_0BC          GPIO_REG(0x0BC)
#define GPIO_0C0          GPIO_REG(0x0C0)
#define GPIO_0D0          GPIO_REG(0x0D0)
#define GPIO_0D4          GPIO_REG(0x0D4)
#define GPIO_0D8          GPIO_REG(0x0D8)
#define GPIO_0DC          GPIO_REG(0x0DC)
#define GPIO_0E0          GPIO_REG(0x0E0)
#define GPIO_0E4          GPIO_REG(0x0E4)
#define GPIO_0E8          GPIO_REG(0x0E8)
#define GPIO_0EC          GPIO_REG(0x0EC)
#define GPIO_100          GPIO_REG(0x100)
#define GPIO_104          GPIO_REG(0x104)
#define GPIO_108          GPIO_REG(0x108)
#define GPIO_10C          GPIO_REG(0x10C)
#define GPIO_110          GPIO_REG(0x110)

#endif /* SL6801_GPIO_H */
