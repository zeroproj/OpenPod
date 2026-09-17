; map=xip bias=0x00C00000  off 0xF8210 -> addr 0x00CF8210
  00CF8210  2de9f04f  push.w   {r4, r5, r6, r7, r8, sb, sl, fp, lr}
  00CF8214  0320      movs     r0, #3
  00CF8216  8fb0      sub      sp, #0x3c
  00CF8218  72f00efe  bl       #0xd6ae38
  00CF821C  0021      movs     r1, #0
  00CF821E  1422      movs     r2, #0x14
  00CF8220  0746      mov      r7, r0
  00CF8222  6846      mov      r0, sp
  00CF8224  08f7c1d4  bl       #0xbaa
  00CF8228  4b4b      ldr      r3, [pc, #0x12c]  ; = 0x0081BBD0
  00CF822A  4c4c      ldr      r4, [pc, #0x130]  ; = 0x0081BBC0
  00CF822C  0222      movs     r2, #2
  00CF822E  1a70      strb     r2, [r3]
  00CF8230  4b4a      ldr      r2, [pc, #0x12c]  ; = 0x0081E87A
  00CF8232  9a62      str      r2, [r3, #0x28]
  00CF8234  4b4a      ldr      r2, [pc, #0x12c]  ; = 0x0082107A
  00CF8236  da62      str      r2, [r3, #0x2c]
  00CF8238  4b4a      ldr      r2, [pc, #0x12c]  ; = 0x00A00080
  00CF823A  1a63      str      r2, [r3, #0x30]
  00CF823C  2822      movs     r2, #0x28
  00CF823E  9a86      strh     r2, [r3, #0x34]
  00CF8240  0120      movs     r0, #1
  00CF8242  50f097ff  bl       #0xd49174
  00CF8246  1420      movs     r0, #0x14
  00CF8248  5ff09eff  bl       #0xd58188
  00CF824C  0546      mov      r5, r0
  00CF824E  a060      str      r0, [r4, #8]
  00CF8250  58bb      cbnz     r0, #0xcf82aa
  00CF8252  4648      ldr      r0, [pc, #0x118]  ; = 0x00C4993E  "-malloc view ring error!
"
  00CF8254  08f72cd0  bl       #0x2b0
  00CF8258  3f48      ldr      r0, [pc, #0xfc]  ; = 0x0081BBD0
  00CF825A  dff81c91  ldr.w    sb, [pc, #0x11c]  ; = 0x00823EB0
  00CF825E  dff81c81  ldr.w    r8, [pc, #0x11c]  ; = 0x00C4989D  "watch_view_task"
  00CF8262  dff81ca1  ldr.w    sl, [pc, #0x11c]  ; = 0x00C49979  "-%s pagp->page: %d 
"
  00CF8266  6af02dfa  bl       #0xd626c4
  00CF826A  29f065f8  bl       #0xd21338
  00CF826E  48f065f9  bl       #0xd4053c
  00CF8272  0025      movs     r5, #0
  00CF8274  d7f808b0  ldr.w    fp, [r7, #8]
  00CF8278  5846      mov      r0, fp
  00CF827A  15f7d0f2  bl       #0x80d81e
  00CF827E  0646      mov      r6, r0
  00CF8280  18b1      cbz      r0, #0xcf828a
  00CF8282  05a9      add      r1, sp, #0x14
  00CF8284  5846      mov      r0, fp
  00CF8286  15f7bef3  bl       #0x80da06
  00CF828A  06f03dfa  bl       #0xcfe708
  00CF828E  18bb      cbnz     r0, #0xcf82d8
  00CF8290  0cf71af6  bl       #0x804ec8
  00CF8294  bff34f8f  dsb      sy
  00CF8298  30bf      wfi      
  00CF829A  bff36f8f  isb      sy
  00CF829E  0cf711f6  bl       #0x804ec4
  00CF82A2  3846      mov      r0, r7
  00CF82A4  4ef08afc  bl       #0xd46bbc
  00CF82A8  e4e7      b        #0xcf8274
  00CF82AA  1022      movs     r2, #0x10
  00CF82AC  0021      movs     r1, #0
  00CF82AE  0430      adds     r0, #4
  00CF82B0  08f77bd4  bl       #0xbaa
  00CF82B4  4ff47050  mov.w    r0, #0x3c00
  00CF82B8  2860      str      r0, [r5]
  00CF82BA  5ff065ff  bl       #0xd58188
  00CF82BE  0646      mov      r6, r0
  00CF82C0  e860      str      r0, [r5, #0xc]
  00CF82C2  30b9      cbnz     r0, #0xcf82d2
  00CF82C4  a068      ldr      r0, [r4, #8]
  00CF82C6  5ff029ff  bl       #0xd5811c
  00CF82CA  2948      ldr      r0, [pc, #0xa4]  ; = 0x00C49959  "-view ring malloc buff error!
"
  00CF82CC  a660      str      r6, [r4, #8]
  00CF82CE  07f7efd7  bl       #0x2b0
  00CF82D2  0023      movs     r3, #0
  00CF82D4  e360      str      r3, [r4, #0xc]
  00CF82D6  bfe7      b        #0xcf8258
  00CF82D8  2278      ldrb     r2, [r4]
  00CF82DA  012a      cmp      r2, #1
  00CF82DC  15d0      beq      #0xcf830a
  00CF82DE  06d3      blo      #0xcf82ee
  00CF82E0  022a      cmp      r2, #2
  00CF82E2  33d0      beq      #0xcf834c
  00CF82E4  4146      mov      r1, r8
  00CF82E6  2348      ldr      r0, [pc, #0x8c]  ; = 0x00C4998F  "-%s no viewp->status: %d 
"
  00CF82E8  07f7e2d7  bl       #0x2b0
  00CF82EC  0ae0      b        #0xcf8304
  00CF82EE  4db9      cbnz     r5, #0xcf8304
  00CF82F0  2cf088f8  bl       #0xd24404
  00CF82F4  2af0d4fa  bl       #0xd228a0
  00CF82F8  0546      mov      r5, r0
  00CF82FA  0020      movs     r0, #0
  00CF82FC  04f0bef9  bl       #0xcfc67c
  00CF8300  0123      movs     r3, #1
  00CF8302  2370      strb     r3, [r4]
  00CF8304  60f0d6fe  bl       #0xd590b4
  00CF8308  cbe7      b        #0xcf82a2
  00CF830A  002e      cmp      r6, #0
  00CF830C  fad0      beq      #0xcf8304
  00CF830E  99f80030  ldrb.w   r3, [sb]
  00CF8312  032b      cmp      r3, #3
  00CF8314  05d1      bne      #0xcf8322
  00CF8316  bdf81c20  ldrh.w   r2, [sp, #0x1c]
  00CF831A  4146      mov      r1, r8
  00CF831C  5046      mov      r0, sl
  00CF831E  07f7c7d7  bl       #0x2b0
  00CF8322  bdf81c30  ldrh.w   r3, [sp, #0x1c]
  00CF8326  013b      subs     r3, #1
  00CF8328  522b      cmp      r3, #0x52
  00CF832A  ebd8      bhi      #0xcf8304
  00CF832C  2846      mov      r0, r5
  00CF832E  55f00ff8  bl       #0xd4d350
  00CF8332  bdf81c00  ldrh.w   r0, [sp, #0x1c]
  00CF8336  2cf095f8  bl       #0xd24464
  00CF833A  adf80000  strh.w   r0, [sp]
  00CF833E  6846      mov      r0, sp
  00CF8340  2bf0b4f8  bl       #0xd234ac
  00CF8344  0223      movs     r3, #2
  00CF8346  2370      strb     r3, [r4]
  00CF8348  0025      movs     r5, #0
  00CF834A  dbe7      b        #0xcf8304
  00CF834C  002e      cmp      r6, #0
  00CF834E  d9d0      beq      #0xcf8304
  00CF8350  05a8      add      r0, sp, #0x14
  00CF8352  2bf0afff  bl       #0xd242b4
  00CF8356  d5e7      b        #0xcf8304
  00CF8358  d0bb      cbnz     r0, #0xcf83d0
  00CF835A  8100      lsls     r1, r0, #2
  00CF835C  c0bb      cbnz     r0, #0xcf83d0
  00CF835E  8100      lsls     r1, r0, #2
  00CF8360  7ae88100  ldrd     r0, r0, [sl], #-0x204
  00CF8364  7a10      asrs     r2, r7, #1
  00CF8366  8200      lsls     r2, r0, #2
  00CF8368  8000      lsls     r0, r0, #2
  00CF836A  a000      lsls     r0, r4, #2
  00CF836C  3e99      ldr      r1, [sp, #0xf8]
  00CF836E  c400      lsls     r4, r0, #3
  00CF8370  5999      ldr      r1, [sp, #0x164]
  00CF8372  c400      lsls     r4, r0, #3
  00CF8374  8f99      ldr      r1, [sp, #0x23c]
  00CF8376  c400      lsls     r4, r0, #3
  00CF8378  b03e      subs     r6, #0xb0
  00CF837A  8200      lsls     r2, r0, #2
  00CF837C  9d98      ldr      r0, [sp, #0x274]
  00CF837E  c400      lsls     r4, r0, #3
  00CF8380  7999      ldr      r1, [sp, #0x1e4]
  00CF8382  c400      lsls     r4, r0, #3
  00CF8384  10b5      push     {r4, lr}
  00CF8386  124b      ldr      r3, [pc, #0x48]  ; = 0x0081BBC0
  00CF8388  96b0      sub      sp, #0x58
  00CF838A  0021      movs     r1, #0
  00CF838C  5822      movs     r2, #0x58
  00CF838E  6846      mov      r0, sp
  00CF8390  1970      strb     r1, [r3]
  00CF8392  5960      str      r1, [r3, #4]
  00CF8394  08f709d4  bl       #0xbaa
  00CF8398  0e4b      ldr      r3, [pc, #0x38]  ; = 0x00CF8211
  00CF839A  0493      str      r3, [sp, #0x10]
  00CF839C  0e4b      ldr      r3, [pc, #0x38]  ; = 0x00C499AB  "ViewTask"
  00CF839E  0793      str      r3, [sp, #0x1c]
  00CF83A0  4ff48053  mov.w    r3, #0x1000
  00CF83A4  0124      movs     r4, #1
  00CF83A6  0993      str      r3, [sp, #0x24]
  00CF83A8  6846      mov      r0, sp
  00CF83AA  0323      movs     r3, #3
  00CF83AC  8df85430  strb.w   r3, [sp, #0x54]
  00CF83B0  8df80040  strb.w   r4, [sp]
  00CF83B4  8df81440  strb.w   r4, [sp, #0x14]
  00CF83B8  72f078fc  bl       #0xd6acac
  00CF83BC  0298      ldr      r0, [sp, #8]
  00CF83BE  47f05bff  bl       #0xd40278
  00CF83C2  2246      mov      r2, r4
  00CF83C4  0549      ldr      r1, [pc, #0x14]  ; = 0x00CF8209
  00CF83C6  0648      ldr      r0, [pc, #0x18]  ; = 0x00C499B4  "viewTimer"
  00CF83C8  4df076fc  bl       #0xd45cb8
  00CF83CC  16b0      add      sp, #0x58
  00CF83CE  10bd      pop      {r4, pc}
  00CF83D0  c0bb      cbnz     r0, #0xcf8444
  00CF83D2  8100      lsls     r1, r0, #2
  00CF83D4  1182      strh     r1, [r2, #0x10]
  00CF83D6  cf00      lsls     r7, r1, #3
  00CF83D8  ab99      ldr      r1, [sp, #0x2ac]
  00CF83DA  c400      lsls     r4, r0, #3
  00CF83DC  0982      strh     r1, [r1, #0x10]
  00CF83DE  cf00      lsls     r7, r1, #3
  00CF83E0  b499      ldr      r1, [sp, #0x2d0]
  00CF83E2  c400      lsls     r4, r0, #3
  00CF83E4  f7b5      push     {r0, r1, r2, r4, r5, r6, r7, lr}
  00CF83E6  154e      ldr      r6, [pc, #0x54]  ; = 0x0081BBC0
  00CF83E8  d6e90253  ldrd     r5, r3, [r6, #8]
  00CF83EC  0746      mov      r7, r0
  00CF83EE  0c46      mov      r4, r1
  00CF83F0  13b9      cbnz     r3, #0xcf83f8
  00CF83F2  fff700fb  bl       #0xcf79f6
  00CF83F6  f060      str      r0, [r6, #0xc]
  00CF83F8  1148      ldr      r0, [pc, #0x44]  ; = 0x0081BBCC
  00CF83FA  15f7a5f3  bl       #0x80db48
  00CF83FE  2846      mov      r0, r5
  00CF8400  72f0f3fa  bl       #0xd6a9ea
  00CF8404  231d      adds     r3, r4, #4
  00CF8406  9842      cmp      r0, r3
  00CF8408  16d3      blo      #0xcf8438
  00CF840A  0422      movs     r2, #4
