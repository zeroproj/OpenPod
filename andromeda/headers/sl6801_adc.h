/*
 * ANDROMEDA — Header provisório para ADC do SL6801
 *
 * Bases detectadas: 0x40095000 (ADC principal)
 *                   0x40096000 (ADC secundário)
 * Fonte: andromeda/PERIPHERAL_REGISTER_SCAN.md e andromeda/INPUT.md
 *
 * ATENÇÃO: a análise estática só confirmou que as bases são carregadas
 * (0x00D7C660 e 0x00D7C564). Os offsets internos ainda não foram
 * mapeados porque o firmware copia estruturas por loop/memcpy.
 */

#ifndef SL6801_ADC_H
#define SL6801_ADC_H

#include <stdint.h>

#define SL6801_ADC0_BASE  ((volatile uint32_t *)0x40095000)
#define SL6801_ADC1_BASE  ((volatile uint32_t *)0x40096000)

#define ADC0_REG(offset)  (*((volatile uint32_t *)(0x40095000 + (offset))))
#define ADC1_REG(offset)  (*((volatile uint32_t *)(0x40096000 + (offset))))

#endif /* SL6801_ADC_H */
