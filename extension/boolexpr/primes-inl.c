/*
** Filename: primes-inl.c
*/

static size_t _primes[] = {
    /* (2^0,  2^1)  */ 2,
    /* (2^1,  2^2)  */ 3,
    /* (2^2,  2^3)  */ 7,
    /* (2^3,  2^4)  */ 13,
    /* (2^4,  2^5)  */ 23,

    /* From: http://planetmath.org/goodhashtableprimes */

    /* (2^5,  2^6)  */ 53,
    /* (2^6,  2^7)  */ 97,
    /* (2^7,  2^8)  */ 193,
    /* (2^8,  2^9)  */ 389,
    /* (2^9,  2^10) */ 769,
    /* (2^10, 2^11) */ 1543,
    /* (2^11, 2^12) */ 3079,
    /* (2^12, 2^13) */ 6151,
    /* (2^13, 2^14) */ 12289,
    /* (2^14, 2^15) */ 24593,
    /* (2^15, 2^16) */ 49157,
    /* (2^16, 2^17) */ 98317,
    /* (2^17, 2^18) */ 196613,
    /* (2^18, 2^19) */ 393241,
    /* (2^19, 2^20) */ 786433,
    /* (2^20, 2^21) */ 1572869,
    /* (2^21, 2^22) */ 3145739,
    /* (2^22, 2^23) */ 6291469,
    /* (2^23, 2^24) */ 12582917,
    /* (2^24, 2^25) */ 25165843,
    /* (2^25, 2^26) */ 50331653,
    /* (2^26, 2^27) */ 100663319,
    /* (2^27, 2^28) */ 201326611,
    /* (2^28, 2^29) */ 402653189,
    /* (2^29, 2^30) */ 805306457,
    /* (2^30, 2^31) */ 1610612741,
};

