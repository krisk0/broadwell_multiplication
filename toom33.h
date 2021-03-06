#pragma once

#include "toom22_generic.h"

#if 0

                T                        T
(v2,v1,v-,v0,vi)  = mu * (r4,r3,r2,r1,r0)


     ( 16  8  4  2  1 )
     (  1  1  1  1  1 )
mu = (  1 -1  1 -1  1 )
     (  0  0  0  0  1 )
     (  1  0  0  0  0 )

                     T                   T
nu * (v2,v1,v-,v0,vi)  = (r4,r3,r2,r1,r0)

             (   0    0    0   0    1 )
       -1    (  1/6 -1/2 -1/6 1/2  -2 )
nu = mu   =  (   0   1/2  1/2  -1  -1 )
             ( -1/6   1  -1/3 -1/2  2 )
             (   0    0    0   1    0 )

t0 := (v2 - v-)/3           | put into v2   (5 3 1 1 0)
t1 := (v1 - v-)/2           | put into v-   (0 1 0 1 0)
t2 := v1 - v0               | put into v1   (1 1 1 1 0)
t3 := (t0 - t2)/2           | put into v2   (2 1 0 0 0)
t4 := t2 - t1               | put into v1   (1 0 1 0 0)
t5 := v0 + (t1 & (2**64k-1)) << 64k    | spoil v0
t6 := v1 + (t1 >> 64k)                 |  spoil v1
                                       | don't need t1 any more
t5 := t3 - 2*vi             | put into v2   (0 1 0 0 0)

                            vi              (1 0 0 0 0)
                            v0              (0 0 0 0 1)
                            t1              (0 1 0 1 0)
                            t5              (0 1 0 0 0)
                            t4              (1 0 1 0 0)

8 subtractions, one division by 3, two divisions by 2, one multiplication by 2

for n=24:
5*131 + 12*27 + 8*29 + 54 + 3*30 = 1355 > 844
for n=30:
5*242 + 12*11*1.6 + 9*21*1.6 + 2*1.6*21 = 1790 > 1248
                     /
                    /
            9 subtractions, no left shift

for n=72:
2*844 + 3*1000 + 12*25*1.6 + 8*49*1.6 + 54*3 + 3*30*3 = 6227.2 > 5947
for n=90:
2*1309 + 3*1221 + 12*31*1.6 + 9*61*1.6 + 200 + 3*84 = 8207 > 8147
                                         /
                                        /
                                  division by 3, 197 ticks for size=60

5*1200 + 12*31*1.6 + 9*61*1.6 + 200 + 3*84 = 7925 < 8147
 \
  \
  multiply 32*32 instead of 31*31 or 30*30

Multiplication by 2 should be replaced by subtraction?

32 + 31 + 31 = 94


k = ceil(n/3)
h = n - 2*k, h <= k

v0 at rp + 0                | 2*k
vi at rp + 4*k              | 2*h, except junior limb which is at scratch[4*k+2]
v1 at rp + 2*k              | 2*k + 1
v- at scratch               | 2*k + 1, can be negative
v2 at scratch + 2*k+1       | 2*k + 1
vi[0] at scratch + 4*k+2    | 1
v- sign at scratch + 4*k+3  | 1

scratch size 4*k+4 plus scratch for multiplication of size k+1 or k or h

#endif
