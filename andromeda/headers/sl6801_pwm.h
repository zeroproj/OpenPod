/* sl6801_pwm.h — ANDROMEDA: offsets provisórios do timer/PWM
 * do SL6801 observados no firmware GN-438 (yp3_2.0.43).
 *
 * Base addresses:
 *   SL6801_TIMER0_BASE = 0x40010000
 *   SL6801_TIMER1_BASE = 0x40010100
 *   SL6801_TIMER2_BASE = 0x40010200
 *   SL6801_TIMER3_BASE = 0x40011000  (provavelmente PWM ou timer avançado)
 *
 * Os firmwares YP3 abrem dispositivos `/dev/pwm_ch0`..`/dev/pwm_ch5`. Os
 * quatro blocos acima podem corresponder a 6 canais mapeados em dois
 * controladores. Os nomes são placeholders.
 */

#ifndef SL6801_PWM_H
#define SL6801_PWM_H

#include <stdint.h>

#define SL6801_TIMER0_BASE      0x40010000
#define SL6801_TIMER1_BASE      0x40010100
#define SL6801_TIMER2_BASE      0x40010200
#define SL6801_TIMER3_BASE      0x40011000

/* Offsets comuns observados em todos os blocos de timer */
#define TIMER_CTRL              0x000
#define TIMER_CMP               0x100
#define TIMER_CNT               0x108
#define TIMER_PERIOD            0x120
#define TIMER_INT_CTRL          0x200
#define TIMER_INT_STATUS        0x21C
#define TIMER_DEAD_TIME         0x228
#define TIMER_CHANNEL_SEL       0x290
#define TIMER_DUTY              0x298
#define TIMER_PWM_CTRL          0x2C8
#define TIMER_PWM_STATUS        0x2F0
#define TIMER_DMA_CTRL          0x30C

/* Bloco 3 (0x40011000) — offsets próprios */
#define T3_CTRL                 (SL6801_TIMER3_BASE + 0x000)
#define T3_CMP                  (SL6801_TIMER3_BASE + 0x004)
#define T3_CNT                  (SL6801_TIMER3_BASE + 0x008)
#define T3_PERIOD               (SL6801_TIMER3_BASE + 0x00C)
#define T3_INT_CTRL             (SL6801_TIMER3_BASE + 0x010)
#define T3_DEAD_TIME            (SL6801_TIMER3_BASE + 0x020)
#define T3_CHANNEL_SEL          (SL6801_TIMER3_BASE + 0x024)
#define T3_PWM_CTRL0            (SL6801_TIMER3_BASE + 0x02C)
#define T3_PWM_CTRL1            (SL6801_TIMER3_BASE + 0x040)
#define T3_PWM_CTRL2            (SL6801_TIMER3_BASE + 0x044)
#define T3_PWM_CTRL3            (SL6801_TIMER3_BASE + 0x060)
#define T3_PWM_CTRL4            (SL6801_TIMER3_BASE + 0x064)
#define T3_PWM_CTRL5            (SL6801_TIMER3_BASE + 0x080)
#define T3_PWM_CTRL6            (SL6801_TIMER3_BASE + 0x084)
#define T3_PWM_CTRL7            (SL6801_TIMER3_BASE + 0x088)
#define T3_PWM_CTRL8            (SL6801_TIMER3_BASE + 0x0A0)
#define T3_PWM_CTRL9            (SL6801_TIMER3_BASE + 0x0A4)
#define T3_PWM_CTRL10           (SL6801_TIMER3_BASE + 0x0AC)
#define T3_PWM_CTRL11           (SL6801_TIMER3_BASE + 0x0B0)
#define T3_PWM_CTRL12           (SL6801_TIMER3_BASE + 0x0B4)
#define T3_PWM_CTRL13           (SL6801_TIMER3_BASE + 0x0B8)
#define T3_PWM_CTRL14           (SL6801_TIMER3_BASE + 0x0BC)
#define T3_PWM_CTRL15           (SL6801_TIMER3_BASE + 0x0C0)
#define T3_PWM_CTRL16           (SL6801_TIMER3_BASE + 0x0C4)
#define T3_PWM_CTRL17           (SL6801_TIMER3_BASE + 0x0CC)
#define T3_PWM_CTRL18           (SL6801_TIMER3_BASE + 0x0D0)
#define T3_PWM_CTRL19           (SL6801_TIMER3_BASE + 0x0E4)

#define PWM_REG32(base, off)    (*(volatile uint32_t *)((base) + (off)))

#endif /* SL6801_PWM_H */
