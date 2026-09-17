00d21110  30 b4                 push     {r4, r5}
00d21112  80 4d                 ldr      r5, [pc, #0x200]
00d21114  aa 78                 ldrb     r2, [r5, #2]
00d21116  01 2a                 cmp      r2, #1
00d21118  0b 46                 mov      r3, r1
00d2111a  56 d1                 bne      #0xd211ca
00d2111c  69 78                 ldrb     r1, [r5, #1]
00d2111e  28 78                 ldrb     r0, [r5]
00d21120  00 24                 movs     r4, #0
00d21122  40 ea 01 40           orr.w    r0, r0, r1, lsl #16
00d21126  ac 70                 strb     r4, [r5, #2]
00d21128  01 0c                 lsrs     r1, r0, #0x10
00d2112a  00 28                 cmp      r0, #0
00d2112c  4d d0                 beq      #0xd211ca
00d2112e  c0 b2                 uxtb     r0, r0
00d21130  25 28                 cmp      r0, #0x25
00d21132  00 f0 b7 80           beq.w    #0xd212a4
00d21136  17 d8                 bhi      #0xd21168
00d21138  21 28                 cmp      r0, #0x21
00d2113a  6c d0                 beq      #0xd21216
00d2113c  22 28                 cmp      r0, #0x22
00d2113e  00 f0 8d 80           beq.w    #0xd2125c
00d21142  20 28                 cmp      r0, #0x20
00d21144  16 d1                 bne      #0xd21174
00d21146  40 29                 cmp      r1, #0x40
00d21148  00 f0 a8 80           beq.w    #0xd2129c
00d2114c  00 f2 9f 80           bhi.w    #0xd2128e
00d21150  10 29                 cmp      r1, #0x10
00d21152  4f f0 12 02           mov.w    r2, #0x12
00d21156  53 d0                 beq      #0xd21200
00d21158  30 29                 cmp      r1, #0x30
00d2115a  55 d0                 beq      #0xd21208
00d2115c  12 22                 movs     r2, #0x12
00d2115e  5a 60                 str      r2, [r3, #4]
00d21160  00 22                 movs     r2, #0
00d21162  9a 73                 strb     r2, [r3, #0xe]
00d21164  6c 48                 ldr      r0, [pc, #0x1b0]
00d21166  24 e0                 b        #0xd211b2
00d21168  42 28                 cmp      r0, #0x42
00d2116a  18 d0                 beq      #0xd2119e
00d2116c  08 d8                 bhi      #0xd21180
00d2116e  34 28                 cmp      r0, #0x34
00d21170  00 f0 b6 80           beq.w    #0xd212e0
00d21174  0a 46                 mov      r2, r1
00d21176  30 bc                 pop      {r4, r5}
00d21178  01 46                 mov      r1, r0
00d2117a  68 48                 ldr      r0, [pc, #0x1a0]
00d2117c  df f6 98 90           b.w      #0x2b0
00d21180  43 28                 cmp      r0, #0x43
00d21182  2b d0                 beq      #0xd211dc
00d21184  45 28                 cmp      r0, #0x45
00d21186  f5 d1                 bne      #0xd21174
00d21188  40 29                 cmp      r1, #0x40
00d2118a  63 d0                 beq      #0xd21254
00d2118c  5c d8                 bhi      #0xd21248
00d2118e  10 29                 cmp      r1, #0x10
00d21190  4f f0 81 02           mov.w    r2, #0x81
00d21194  34 d0                 beq      #0xd21200
00d21196  30 29                 cmp      r1, #0x30
00d21198  36 d0                 beq      #0xd21208
00d2119a  81 22                 movs     r2, #0x81
00d2119c  45 e0                 b        #0xd2122a
00d2119e  40 29                 cmp      r1, #0x40
00d211a0  18 d0                 beq      #0xd211d4
00d211a2  09 d8                 bhi      #0xd211b8
00d211a4  10 29                 cmp      r1, #0x10
00d211a6  0d d0                 beq      #0xd211c4
00d211a8  30 29                 cmp      r1, #0x30
00d211aa  10 d0                 beq      #0xd211ce
00d211ac  00 22                 movs     r2, #0
00d211ae  5c 48                 ldr      r0, [pc, #0x170]
00d211b0  9a 73                 strb     r2, [r3, #0xe]
00d211b2  30 bc                 pop      {r4, r5}
00d211b4  df f6 7c 90           b.w      #0x2b0
00d211b8  50 29                 cmp      r1, #0x50
00d211ba  0d d0                 beq      #0xd211d8
00d211bc  60 29                 cmp      r1, #0x60
00d211be  f5 d1                 bne      #0xd211ac
00d211c0  87 21                 movs     r1, #0x87
00d211c2  05 e0                 b        #0xd211d0
00d211c4  14 22                 movs     r2, #0x14
00d211c6  5a 60                 str      r2, [r3, #4]
00d211c8  9c 73                 strb     r4, [r3, #0xe]
00d211ca  30 bc                 pop      {r4, r5}
00d211cc  70 47                 bx       lr
00d211ce  14 21                 movs     r1, #0x14
00d211d0  59 60                 str      r1, [r3, #4]
00d211d2  7f e0                 b        #0xd212d4
00d211d4  85 21                 movs     r1, #0x85
00d211d6  fb e7                 b        #0xd211d0
00d211d8  86 21                 movs     r1, #0x86
00d211da  f9 e7                 b        #0xd211d0
00d211dc  40 29                 cmp      r1, #0x40
00d211de  16 d0                 beq      #0xd2120e
00d211e0  07 d8                 bhi      #0xd211f2
00d211e2  10 29                 cmp      r1, #0x10
00d211e4  0b d0                 beq      #0xd211fe
00d211e6  30 29                 cmp      r1, #0x30
00d211e8  0d d0                 beq      #0xd21206
00d211ea  00 22                 movs     r2, #0
00d211ec  9a 73                 strb     r2, [r3, #0xe]
00d211ee  4d 48                 ldr      r0, [pc, #0x134]
00d211f0  df e7                 b        #0xd211b2
00d211f2  50 29                 cmp      r1, #0x50
00d211f4  0d d0                 beq      #0xd21212
00d211f6  60 29                 cmp      r1, #0x60
00d211f8  f7 d1                 bne      #0xd211ea
00d211fa  8a 22                 movs     r2, #0x8a
00d211fc  04 e0                 b        #0xd21208
00d211fe  13 22                 movs     r2, #0x13
00d21200  5a 60                 str      r2, [r3, #4]
00d21202  00 22                 movs     r2, #0
00d21204  66 e0                 b        #0xd212d4
00d21206  13 22                 movs     r2, #0x13
00d21208  5a 60                 str      r2, [r3, #4]
00d2120a  01 22                 movs     r2, #1
00d2120c  62 e0                 b        #0xd212d4
00d2120e  88 21                 movs     r1, #0x88
00d21210  de e7                 b        #0xd211d0
00d21212  89 22                 movs     r2, #0x89
00d21214  f8 e7                 b        #0xd21208
00d21216  40 29                 cmp      r1, #0x40
00d21218  12 d0                 beq      #0xd21240
00d2121a  0b d8                 bhi      #0xd21234
00d2121c  10 29                 cmp      r1, #0x10
00d2121e  4f f0 0a 00           mov.w    r0, #0xa
00d21222  54 d0                 beq      #0xd212ce
00d21224  30 29                 cmp      r1, #0x30
00d21226  54 d0                 beq      #0xd212d2
00d21228  0a 22                 movs     r2, #0xa
00d2122a  5a 60                 str      r2, [r3, #4]
00d2122c  00 22                 movs     r2, #0
00d2122e  9a 73                 strb     r2, [r3, #0xe]
00d21230  3d 48                 ldr      r0, [pc, #0xf4]
00d21232  be e7                 b        #0xd211b2
00d21234  50 29                 cmp      r1, #0x50
00d21236  05 d0                 beq      #0xd21244
00d21238  60 29                 cmp      r1, #0x60
00d2123a  f5 d1                 bne      #0xd21228
00d2123c  8d 21                 movs     r1, #0x8d
00d2123e  c7 e7                 b        #0xd211d0
00d21240  8b 21                 movs     r1, #0x8b
00d21242  c5 e7                 b        #0xd211d0
00d21244  8c 21                 movs     r1, #0x8c
00d21246  c3 e7                 b        #0xd211d0
00d21248  50 29                 cmp      r1, #0x50
00d2124a  05 d0                 beq      #0xd21258
00d2124c  60 29                 cmp      r1, #0x60
00d2124e  a4 d1                 bne      #0xd2119a
00d21250  84 22                 movs     r2, #0x84
00d21252  d9 e7                 b        #0xd21208
00d21254  82 21                 movs     r1, #0x82
00d21256  bb e7                 b        #0xd211d0
00d21258  83 22                 movs     r2, #0x83
00d2125a  d5 e7                 b        #0xd21208
00d2125c  40 29                 cmp      r1, #0x40
00d2125e  12 d0                 beq      #0xd21286
00d21260  0b d8                 bhi      #0xd2127a
00d21262  10 29                 cmp      r1, #0x10
00d21264  4f f0 11 02           mov.w    r2, #0x11
00d21268  ad d0                 beq      #0xd211c6
00d2126a  30 29                 cmp      r1, #0x30
00d2126c  cc d0                 beq      #0xd21208
00d2126e  11 22                 movs     r2, #0x11
00d21270  5a 60                 str      r2, [r3, #4]
00d21272  00 22                 movs     r2, #0
00d21274  9a 73                 strb     r2, [r3, #0xe]
00d21276  2d 48                 ldr      r0, [pc, #0xb4]
00d21278  9b e7                 b        #0xd211b2
00d2127a  50 29                 cmp      r1, #0x50
00d2127c  05 d0                 beq      #0xd2128a
00d2127e  60 29                 cmp      r1, #0x60
00d21280  f5 d1                 bne      #0xd2126e
00d21282  98 22                 movs     r2, #0x98
00d21284  c0 e7                 b        #0xd21208
00d21286  96 21                 movs     r1, #0x96
00d21288  a2 e7                 b        #0xd211d0
00d2128a  97 21                 movs     r1, #0x97
00d2128c  a0 e7                 b        #0xd211d0
00d2128e  50 29                 cmp      r1, #0x50
00d21290  06 d0                 beq      #0xd212a0
00d21292  60 29                 cmp      r1, #0x60
00d21294  7f f4 62 af           bne.w    #0xd2115c
00d21298  9b 22                 movs     r2, #0x9b
00d2129a  b5 e7                 b        #0xd21208
00d2129c  99 21                 movs     r1, #0x99
00d2129e  97 e7                 b        #0xd211d0
00d212a0  9a 22                 movs     r2, #0x9a
00d212a2  b1 e7                 b        #0xd21208
00d212a4  40 29                 cmp      r1, #0x40
00d212a6  17 d0                 beq      #0xd212d8
00d212a8  0b d8                 bhi      #0xd212c2
00d212aa  10 29                 cmp      r1, #0x10
00d212ac  4f f0 a0 00           mov.w    r0, #0xa0
00d212b0  0d d0                 beq      #0xd212ce
00d212b2  30 29                 cmp      r1, #0x30
00d212b4  0d d0                 beq      #0xd212d2
00d212b6  a0 22                 movs     r2, #0xa0
00d212b8  5a 60                 str      r2, [r3, #4]
00d212ba  00 22                 movs     r2, #0
00d212bc  9a 73                 strb     r2, [r3, #0xe]
00d212be  1c 48                 ldr      r0, [pc, #0x70]
00d212c0  77 e7                 b        #0xd211b2
00d212c2  50 29                 cmp      r1, #0x50
00d212c4  0a d0                 beq      #0xd212dc
00d212c6  60 29                 cmp      r1, #0x60
00d212c8  f5 d1                 bne      #0xd212b6
00d212ca  a3 21                 movs     r1, #0xa3
00d212cc  80 e7                 b        #0xd211d0
00d212ce  58 60                 str      r0, [r3, #4]
00d212d0  7a e7                 b        #0xd211c8
00d212d2  58 60                 str      r0, [r3, #4]
00d212d4  9a 73                 strb     r2, [r3, #0xe]
00d212d6  78 e7                 b        #0xd211ca
00d212d8  a1 21                 movs     r1, #0xa1
00d212da  79 e7                 b        #0xd211d0
00d212dc  a2 21                 movs     r1, #0xa2
00d212de  77 e7                 b        #0xd211d0
00d212e0  40 29                 cmp      r1, #0x40
00d212e2  12 d0                 beq      #0xd2130a
00d212e4  0b d8                 bhi      #0xd212fe
00d212e6  10 29                 cmp      r1, #0x10
00d212e8  4f f0 92 02           mov.w    r2, #0x92
00d212ec  88 d0                 beq      #0xd21200
00d212ee  30 29                 cmp      r1, #0x30
00d212f0  8a d0                 beq      #0xd21208
00d212f2  92 22                 movs     r2, #0x92
00d212f4  5a 60                 str      r2, [r3, #4]
00d212f6  00 22                 movs     r2, #0
00d212f8  9a 73                 strb     r2, [r3, #0xe]
00d212fa  0e 48                 ldr      r0, [pc, #0x38]
00d212fc  59 e7                 b        #0xd211b2
00d212fe  50 29                 cmp      r1, #0x50
00d21300  05 d0                 beq      #0xd2130e
00d21302  60 29                 cmp      r1, #0x60
00d21304  f5 d1                 bne      #0xd212f2
00d21306  95 22                 movs     r2, #0x95
00d21308  7e e7                 b        #0xd21208
00d2130a  93 21                 movs     r1, #0x93
00d2130c  60 e7                 b        #0xd211d0
00d2130e  94 22                 movs     r2, #0x94
00d21310  7a e7                 b        #0xd21208
00d21312  00 bf                 nop      
00d21314  7a 3d                 subs     r5, #0x7a
00d21316  82 00                 lsls     r2, r0, #2
00d21318  f0 d4                 bmi      #0xd212fc
00d2131a  c5 00                 lsls     r5, r0, #3
00d2131c  64 d5                 bpl      #0xd213e8
00d2131e  c5 00                 lsls     r5, r0, #3
00d21320  59 d4                 bmi      #0xd213d6
00d21322  c5 00                 lsls     r5, r0, #3
00d21324  7f d4                 bmi      #0xd21426
00d21326  c5 00                 lsls     r5, r0, #3
00d21328  a6 d4                 bmi      #0xd21278
00d2132a  c5 00                 lsls     r5, r0, #3
00d2132c  cc d4                 bmi      #0xd212c8
00d2132e  c5 00                 lsls     r5, r0, #3
00d21330  16 d5                 bpl      #0xd21360
00d21332  c5 00                 lsls     r5, r0, #3
00d21334  3c d5                 bpl      #0xd213b0
