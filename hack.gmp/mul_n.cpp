/* mpn_mul_n -- multiply natural numbers.

Copyright 1991, 1993, 1994, 1996-2003, 2005, 2008, 2009 Free Software
Foundation, Inc.
Copyright 2021 Крыськов Денис.

This file is part of the GNU MP Library.

The GNU MP Library is free software; you can redistribute it and/or modify
it under the terms of either:

  * the GNU Lesser General Public License as published by the Free
    Software Foundation; either version 3 of the License, or (at your
    option) any later version.

or

  * the GNU General Public License as published by the Free Software
    Foundation; either version 2 of the License, or (at your option) any
    later version.

or both in parallel, as here.

The GNU MP Library is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
for more details.

You should have received copies of the GNU General Public License and the
GNU Lesser General Public License along with the GNU MP Library.  If not,
see https://www.gnu.org/licenses/.  */

#include "gmp-impl.h"
#include "longlong.h"

#define AMD_ZEN 0

namespace {
#include "automagic/toom22.h"
}

extern "C" {
void mpn_mul_n(mp_ptr, mp_srcptr, mp_srcptr, mp_size_t);
}

void
mpn_mul_n (mp_ptr p, mp_srcptr a, mp_srcptr b, mp_size_t n)
{
  ASSERT (n >= 1);
  ASSERT (! MPN_OVERLAP_P (p, 2 * n, a, n));
  ASSERT (! MPN_OVERLAP_P (p, 2 * n, b, n));

  #include "automagic/mpn_mul_n_switch.h"
  
  if (BELOW_THRESHOLD (n, MUL_TOOM44_THRESHOLD))
    {
      mp_ptr ws;
      TMP_SDECL;
      TMP_SMARK;
      ws = TMP_SALLOC_LIMBS (mpn_toom33_mul_itch (n, n));
      mpn_toom33_mul (p, a, n, b, n, ws);
      TMP_SFREE;
    }
  else if (BELOW_THRESHOLD (n, MUL_TOOM6H_THRESHOLD))
    {
      mp_ptr ws;
      TMP_SDECL;
      TMP_SMARK;
      ws = TMP_SALLOC_LIMBS (mpn_toom44_mul_itch (n, n));
      mpn_toom44_mul (p, a, n, b, n, ws);
      TMP_SFREE;
    }
  else if (BELOW_THRESHOLD (n, MUL_TOOM8H_THRESHOLD))
    {
      mp_ptr ws;
      TMP_SDECL;
      TMP_SMARK;
      ws = TMP_SALLOC_LIMBS (mpn_toom6_mul_n_itch (n));
      mpn_toom6h_mul (p, a, n, b, n, ws);
      TMP_SFREE;
    }
  else if (BELOW_THRESHOLD (n, MUL_FFT_THRESHOLD))
    {
      mp_ptr ws;
      TMP_DECL;
      TMP_MARK;
      ws = TMP_ALLOC_LIMBS (mpn_toom8_mul_n_itch (n));
      mpn_toom8h_mul (p, a, n, b, n, ws);
      TMP_FREE;
    }
  else
    {
      /* The current FFT code allocates its own space.  That should probably
	 change.  */
      mpn_fft_mul (p, a, n, b, n);
    }
}
