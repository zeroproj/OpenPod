; map=xip bias=0x00C00000  off 0x12F540 -> addr 0x00D2F540
  00D2F540  2de9f041  push.w   {r4, r5, r6, r7, r8, lr}
  00D2F544  854d      ldr      r5, [pc, #0x214]  ; = 0x0081CE2C
  00D2F546  2b68      ldr      r3, [r5]
  00D2F548  d3f8b840  ldr.w    r4, [r3, #0xb8]
  00D2F54C  0646      mov      r6, r0
  00D2F54E  2cb9      cbnz     r4, #0xd2f55c
  00D2F550  8349      ldr      r1, [pc, #0x20c]  ; = 0x00CD44B3  "page_music_album_event_cb"
  00D2F552  8448      ldr      r0, [pc, #0x210]  ; = 0x00CD3265  "-%s page_p NULL 
"
  00D2F554  bde8f041  pop.w    {r4, r5, r6, r7, r8, lr}
  00D2F558  d0f6aa96  b.w      #0x2b0
  00D2F55C  17f06afd  bl       #0xd47034
  00D2F560  0d28      cmp      r0, #0xd
  00D2F562  40f08480  bne.w    #0xd2f66e
  00D2F566  3046      mov      r0, r6
  00D2F568  17f066fd  bl       #0xd47038
  00D2F56C  0278      ldrb     r2, [r0]
  00D2F56E  142a      cmp      r2, #0x14
  00D2F570  00f0b380  beq.w    #0xd2f6da
  00D2F574  3dd8      bhi      #0xd2f5f2
  00D2F576  0b2a      cmp      r2, #0xb
  00D2F578  7bd0      beq      #0xd2f672
  00D2F57A  09d8      bhi      #0xd2f590
  00D2F57C  092a      cmp      r2, #9
  00D2F57E  7fd0      beq      #0xd2f680
  00D2F580  0a2a      cmp      r2, #0xa
  00D2F582  57d0      beq      #0xd2f634
  00D2F584  7649      ldr      r1, [pc, #0x1d8]  ; = 0x00CD44B3  "page_music_album_event_cb"
  00D2F586  7848      ldr      r0, [pc, #0x1e0]  ; = 0x00C5D769  "-%s no c: %d 
"
  00D2F588  bde8f041  pop.w    {r4, r5, r6, r7, r8, lr}
  00D2F58C  d0f69096  b.w      #0x2b0
  00D2F590  112a      cmp      r2, #0x11
  00D2F592  00f0a280  beq.w    #0xd2f6da
  00D2F596  f5d3      blo      #0xd2f584
  00D2F598  744e      ldr      r6, [pc, #0x1d0]  ; = 0x00823EB0
  00D2F59A  3278      ldrb     r2, [r6]
  00D2F59C  032a      cmp      r2, #3
  00D2F59E  03d1      bne      #0xd2f5a8
  00D2F5A0  6f49      ldr      r1, [pc, #0x1bc]  ; = 0x00CD44B3  "page_music_album_event_cb"
  00D2F5A2  7348      ldr      r0, [pc, #0x1cc]  ; = 0x00C5D739  "-%s right 
"
  00D2F5A4  d0f684d6  bl       #0x2b0
  00D2F5A8  17f060ff  bl       #0xd4746c
  00D2F5AC  8046      mov      r8, r0
  00D2F5AE  18f04bf8  bl       #0xd47648
  00D2F5B2  2b68      ldr      r3, [r5]
  00D2F5B4  dd6b      ldr      r5, [r3, #0x3c]
  00D2F5B6  4545      cmp      r5, r8
  00D2F5B8  0746      mov      r7, r0
  00D2F5BA  58d1      bne      #0xd2f66e
  00D2F5BC  2846      mov      r0, r5
  00D2F5BE  18f0c1f8  bl       #0xd47744
  00D2F5C2  0028      cmp      r0, #0
  00D2F5C4  53d0      beq      #0xd2f66e
  00D2F5C6  54f82030  ldr.w    r3, [r4, r0, lsl #2]
  00D2F5CA  bb42      cmp      r3, r7
  00D2F5CC  5fd1      bne      #0xd2f68e
  00D2F5CE  3378      ldrb     r3, [r6]
  00D2F5D0  032b      cmp      r3, #3
  00D2F5D2  03d1      bne      #0xd2f5dc
  00D2F5D4  6249      ldr      r1, [pc, #0x188]  ; = 0x00CD44B3  "page_music_album_event_cb"
  00D2F5D6  6748      ldr      r0, [pc, #0x19c]  ; = 0x00CD3B39  "-%s PgDn 
"
  00D2F5D8  d0f66ad6  bl       #0x2b0
  00D2F5DC  0720      movs     r0, #7
  00D2F5DE  1623      movs     r3, #0x16
  00D2F5E0  0022      movs     r2, #0
  00D2F5E2  0621      movs     r1, #6
  00D2F5E4  f3f794ff  bl       #0xd23510
  00D2F5E8  6068      ldr      r0, [r4, #4]
  00D2F5EA  bde8f041  pop.w    {r4, r5, r6, r7, r8, lr}
  00D2F5EE  18f05fb8  b.w      #0xd476b0
  00D2F5F2  872a      cmp      r2, #0x87
  00D2F5F4  71d0      beq      #0xd2f6da
  00D2F5F6  16d8      bhi      #0xd2f626
  00D2F5F8  1b2a      cmp      r2, #0x1b
  00D2F5FA  00f0a780  beq.w    #0xd2f74c
  00D2F5FE  812a      cmp      r2, #0x81
  00D2F600  c0d1      bne      #0xd2f584
  00D2F602  5a4b      ldr      r3, [pc, #0x168]  ; = 0x00823EB0
  00D2F604  1b78      ldrb     r3, [r3]
  00D2F606  032b      cmp      r3, #3
  00D2F608  03d1      bne      #0xd2f612
  00D2F60A  5549      ldr      r1, [pc, #0x154]  ; = 0x00CD44B3  "page_music_album_event_cb"
  00D2F60C  5a48      ldr      r0, [pc, #0x168]  ; = 0x00C5D75D  "-%s back 
"
  00D2F60E  d0f64fd6  bl       #0x2b0
  00D2F612  2b68      ldr      r3, [r5]
  00D2F614  dc6b      ldr      r4, [r3, #0x3c]
  00D2F616  17f029ff  bl       #0xd4746c
  00D2F61A  8442      cmp      r4, r0
  00D2F61C  27d1      bne      #0xd2f66e
  00D2F61E  1423      movs     r3, #0x14
  00D2F620  0022      movs     r2, #0
  00D2F622  0121      movs     r1, #1
  00D2F624  1be0      b        #0xd2f65e
  00D2F626  982a      cmp      r2, #0x98
  00D2F628  57d0      beq      #0xd2f6da
  00D2F62A  9b2a      cmp      r2, #0x9b
  00D2F62C  b4d0      beq      #0xd2f598
  00D2F62E  8a2a      cmp      r2, #0x8a
  00D2F630  a8d1      bne      #0xd2f584
  00D2F632  b1e7      b        #0xd2f598
  00D2F634  4d4b      ldr      r3, [pc, #0x134]  ; = 0x00823EB0
  00D2F636  1b78      ldrb     r3, [r3]
  00D2F638  032b      cmp      r3, #3
  00D2F63A  03d1      bne      #0xd2f644
  00D2F63C  4849      ldr      r1, [pc, #0x120]  ; = 0x00CD44B3  "page_music_album_event_cb"
  00D2F63E  4f48      ldr      r0, [pc, #0x13c]  ; = 0x00C5D714  "-%s enter 
"
  00D2F640  d0f636d6  bl       #0x2b0
  00D2F644  17f012ff  bl       #0xd4746c
  00D2F648  17f0feff  bl       #0xd47648
  00D2F64C  0434      adds     r4, #4
  00D2F64E  0023      movs     r3, #0
  00D2F650  54f8041b  ldr      r1, [r4], #4
  00D2F654  8142      cmp      r1, r0
  00D2F656  dab2      uxtb     r2, r3
  00D2F658  06d1      bne      #0xd2f668
  00D2F65A  0423      movs     r3, #4
  00D2F65C  1946      mov      r1, r3
  00D2F65E  0720      movs     r0, #7
  00D2F660  bde8f041  pop.w    {r4, r5, r6, r7, r8, lr}
  00D2F664  f3f754bf  b.w      #0xd23510
  00D2F668  0133      adds     r3, #1
  00D2F66A  062b      cmp      r3, #6
  00D2F66C  f0d1      bne      #0xd2f650
  00D2F66E  bde8f081  pop.w    {r4, r5, r6, r7, r8, pc}
  00D2F672  3e4b      ldr      r3, [pc, #0xf8]  ; = 0x00823EB0
  00D2F674  1b78      ldrb     r3, [r3]
  00D2F676  032b      cmp      r3, #3
  00D2F678  f9d1      bne      #0xd2f66e
  00D2F67A  3949      ldr      r1, [pc, #0xe4]  ; = 0x00CD44B3  "page_music_album_event_cb"
  00D2F67C  4048      ldr      r0, [pc, #0x100]  ; = 0x00C5D721  "-%s prev 
"
  00D2F67E  69e7      b        #0xd2f554
  00D2F680  3a4b      ldr      r3, [pc, #0xe8]  ; = 0x00823EB0
  00D2F682  1b78      ldrb     r3, [r3]
  00D2F684  032b      cmp      r3, #3
  00D2F686  f2d1      bne      #0xd2f66e
  00D2F688  3549      ldr      r1, [pc, #0xd4]  ; = 0x00CD44B3  "page_music_album_event_cb"
  00D2F68A  3e48      ldr      r0, [pc, #0xf8]  ; = 0x00C5D72D  "-%s next 
"
  00D2F68C  62e7      b        #0xd2f554
  00D2F68E  94f85030  ldrb.w   r3, [r4, #0x50]
  00D2F692  04eb8303  add.w    r3, r4, r3, lsl #2
  00D2F696  0421      movs     r1, #4
  00D2F698  d869      ldr      r0, [r3, #0x1c]
  00D2F69A  2ff033fc  bl       #0xd5ef04
  00D2F69E  17f0e5fe  bl       #0xd4746c
  00D2F6A2  17f00fff  bl       #0xd474c4
  00D2F6A6  2846      mov      r0, r5
  00D2F6A8  17f0ceff  bl       #0xd47648
  00D2F6AC  0025      movs     r5, #0
  00D2F6AE  231d      adds     r3, r4, #4
  00D2F6B0  53f8042b  ldr      r2, [r3], #4
  00D2F6B4  8242      cmp      r2, r0
  00D2F6B6  eeb2      uxtb     r6, r5
  00D2F6B8  0bd1      bne      #0xd2f6d2
  00D2F6BA  04eb8505  add.w    r5, r4, r5, lsl #2
  00D2F6BE  3046      mov      r0, r6
  00D2F6C0  fff726ff  bl       #0xd2f510
  00D2F6C4  0321      movs     r1, #3
  00D2F6C6  e869      ldr      r0, [r5, #0x1c]
  00D2F6C8  2ff01cfc  bl       #0xd5ef04
  00D2F6CC  84f85060  strb.w   r6, [r4, #0x50]
  00D2F6D0  cde7      b        #0xd2f66e
  00D2F6D2  0135      adds     r5, #1
  00D2F6D4  062d      cmp      r5, #6
  00D2F6D6  ebd1      bne      #0xd2f6b0
  00D2F6D8  c9e7      b        #0xd2f66e
  00D2F6DA  244e      ldr      r6, [pc, #0x90]  ; = 0x00823EB0
  00D2F6DC  3278      ldrb     r2, [r6]
  00D2F6DE  032a      cmp      r2, #3
  00D2F6E0  03d1      bne      #0xd2f6ea
  00D2F6E2  1f49      ldr      r1, [pc, #0x7c]  ; = 0x00CD44B3  "page_music_album_event_cb"
  00D2F6E4  2848      ldr      r0, [pc, #0xa0]  ; = 0x00C5D746  "-%s left 
"
  00D2F6E6  d0f6e3d5  bl       #0x2b0
  00D2F6EA  17f0bffe  bl       #0xd4746c
  00D2F6EE  0746      mov      r7, r0
  00D2F6F0  17f0aaff  bl       #0xd47648
  00D2F6F4  2b68      ldr      r3, [r5]
  00D2F6F6  dd6b      ldr      r5, [r3, #0x3c]
  00D2F6F8  bd42      cmp      r5, r7
  00D2F6FA  b8d1      bne      #0xd2f66e
  00D2F6FC  6368      ldr      r3, [r4, #4]
  00D2F6FE  8342      cmp      r3, r0
  00D2F700  0ad1      bne      #0xd2f718
  00D2F702  3378      ldrb     r3, [r6]
  00D2F704  032b      cmp      r3, #3
  00D2F706  03d1      bne      #0xd2f710
  00D2F708  1549      ldr      r1, [pc, #0x54]  ; = 0x00CD44B3  "page_music_album_event_cb"
  00D2F70A  2048      ldr      r0, [pc, #0x80]  ; = 0x00CD3B54  "-%s PgUp 
"
  00D2F70C  d0f6d0d5  bl       #0x2b0
  00D2F710  1723      movs     r3, #0x17
  00D2F712  0022      movs     r2, #0
  00D2F714  0621      movs     r1, #6
  00D2F716  a2e7      b        #0xd2f65e
  00D2F718  94f85030  ldrb.w   r3, [r4, #0x50]
  00D2F71C  04eb8303  add.w    r3, r4, r3, lsl #2
  00D2F720  0421      movs     r1, #4
  00D2F722  d869      ldr      r0, [r3, #0x1c]
  00D2F724  2ff0eefb  bl       #0xd5ef04
  00D2F728  17f0a0fe  bl       #0xd4746c
  00D2F72C  17f0d6fe  bl       #0xd474dc
  00D2F730  2846      mov      r0, r5
  00D2F732  17f089ff  bl       #0xd47648
  00D2F736  0025      movs     r5, #0
  00D2F738  231d      adds     r3, r4, #4
  00D2F73A  53f8042b  ldr      r2, [r3], #4
  00D2F73E  8242      cmp      r2, r0
  00D2F740  eeb2      uxtb     r6, r5
  00D2F742  bad0      beq      #0xd2f6ba
  00D2F744  0135      adds     r5, #1
  00D2F746  062d      cmp      r5, #6
  00D2F748  f7d1      bne      #0xd2f73a
  00D2F74A  90e7      b        #0xd2f66e
  00D2F74C  074b      ldr      r3, [pc, #0x1c]  ; = 0x00823EB0
  00D2F74E  1b78      ldrb     r3, [r3]
  00D2F750  032b      cmp      r3, #3
  00D2F752  8cd1      bne      #0xd2f66e
  00D2F754  0249      ldr      r1, [pc, #8]  ; = 0x00CD44B3  "page_music_album_event_cb"
  00D2F756  0e48      ldr      r0, [pc, #0x38]  ; = 0x00C5D752  "-%s esc 
"
  00D2F758  fce6      b        #0xd2f554
  00D2F75A  00bf      nop      
  00D2F75C  2cce      ldm      r6!, {r2, r3, r5}
  00D2F75E  8100      lsls     r1, r0, #2
  00D2F760  b344      add      fp, r6
  00D2F762  cd00      lsls     r5, r1, #3
  00D2F764  6532      adds     r2, #0x65
  00D2F766  cd00      lsls     r5, r1, #3
  00D2F768  69d7      bvc      #0xd2f83e
  00D2F76A  c500      lsls     r5, r0, #3
  00D2F76C  b03e      subs     r6, #0xb0
  00D2F76E  8200      lsls     r2, r0, #2
  00D2F770  39d7      bvc      #0xd2f7e6
  00D2F772  c500      lsls     r5, r0, #3
  00D2F774  393b      subs     r3, #0x39
  00D2F776  cd00      lsls     r5, r1, #3
  00D2F778  5dd7      bvc      #0xd2f836
  00D2F77A  c500      lsls     r5, r0, #3
  00D2F77C  14d7      bvc      #0xd2f7a8
  00D2F77E  c500      lsls     r5, r0, #3
  00D2F780  21d7      bvc      #0xd2f7c6
  00D2F782  c500      lsls     r5, r0, #3
  00D2F784  2dd7      bvc      #0xd2f7e2
  00D2F786  c500      lsls     r5, r0, #3
  00D2F788  46d7      bvc      #0xd2f818
  00D2F78A  c500      lsls     r5, r0, #3
  00D2F78C  543b      subs     r3, #0x54
  00D2F78E  cd00      lsls     r5, r1, #3
  00D2F790  52d7      bvc      #0xd2f838
  00D2F792  c500      lsls     r5, r0, #3
  00D2F794  2de9f74f  push.w   {r0, r1, r2, r4, r5, r6, r7, r8, sb, sl, fp, lr}
  00D2F798  5420      movs     r0, #0x54
  00D2F79A  28f0f5fc  bl       #0xd58188
  00D2F79E  8146      mov      sb, r0
  00D2F7A0  40b9      cbnz     r0, #0xd2f7b4
  00D2F7A2  7049      ldr      r1, [pc, #0x1c0]  ; = 0x00CD44CD  "page_music_album_create"
  00D2F7A4  7048      ldr      r0, [pc, #0x1c0]  ; = 0x00CD3245  "-%s page_p malloc failed 
"
  00D2F7A6  d0f683d5  bl       #0x2b0
  00D2F7AA  4ff0ff30  mov.w    r0, #-1
  00D2F7AE  03b0      add      sp, #0xc
  00D2F7B0  bde8f08f  pop.w    {r4, r5, r6, r7, r8, sb, sl, fp, pc}
  00D2F7B4  5422      movs     r2, #0x54
  00D2F7B6  0021      movs     r1, #0
  00D2F7B8  e1f672f6  bl       #0x8114a0
  00D2F7BC  27f06cf8  bl       #0xd56898
  00D2F7C0  17f030fb  bl       #0xd46e24
  00D2F7C4  0646      mov      r6, r0
  00D2F7C6  f1f793ff  bl       #0xd216f0
  00D2F7CA  0446      mov      r4, r0
  00D2F7CC  27f064f8  bl       #0xd56898
  00D2F7D0  27f07cf8  bl       #0xd568cc
  00D2F7D4  0725      movs     r5, #7
  00D2F7D6  90fbf5f1  sdiv     r1, r0, r5
  00D2F7DA  2046      mov      r0, r4
  00D2F7DC  09b2      sxth     r1, r1
  00D2F7DE  1af004fd  bl       #0xd4a1ea
  00D2F7E2  0022      movs     r2, #0
  00D2F7E4  1146      mov      r1, r2
  00D2F7E6  2046      mov      r0, r4
  00D2F7E8  1df08afc  bl       #0xd4d100
  00D2F7EC  2046      mov      r0, r4
  00D2F7EE  2ef07bfd  bl       #0xd5e2e8
  00D2F7F2  5e49      ldr      r1, [pc, #0x178]  ; = 0x00C4F981
  00D2F7F4  0190      str      r0, [sp, #4]
  00D2F7F6  2ff0cdfa  bl       #0xd5ed94
  00D2F7FA  0023      movs     r3, #0
  00D2F7FC  1a46      mov      r2, r3
  00D2F7FE  0921      movs     r1, #9
  00D2F800  0198      ldr      r0, [sp, #4]
  00D2F802  1af0cefd  bl       #0xd4a3a2
  00D2F806  3046      mov      r0, r6
  00D2F808  f1f742ff  bl       #0xd21690
  00D2F80C  0446      mov      r4, r0
  00D2F80E  27f043f8  bl       #0xd56898
  00D2F812  27f05bf8  bl       #0xd568cc
  00D2F816  0646      mov      r6, r0
  00D2F818  27f03ef8  bl       #0xd56898
  00D2F81C  27f056f8  bl       #0xd568cc
  00D2F820  90fbf5f0  sdiv     r0, r0, r5
  00D2F824  301a      subs     r0, r6, r0
  00D2F826  01b2      sxth     r1, r0
  00D2F828  2046      mov      r0, r4
  00D2F82A  1af0defc  bl       #0xd4a1ea
  00D2F82E  0521      movs     r1, #5
