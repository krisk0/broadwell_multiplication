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
3*131 + 12*27 + 8*29 + 54 + 3*30 = 1093 > 844
for n=72:
3*844 + 12*24*1.6 + 8*49*1.6 + 54*3 + 3*30*3 = 4052 < 5947

Multiplication by 2 should be replaced by subtraction? 

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
