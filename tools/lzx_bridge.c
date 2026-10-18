/* Copyright (c) 2026 jyh9521. MIT; see LICENSE and NOTICE.md.
 * Narrow migration from MagnaCarta2-Recompiled bc0d93ae886a9ebfd998b48b7ec30cf0f92e0c47.
 * Memory bridge compiled separately with LGPL-2.1 libmspack; see docs/LZX_RESEARCH.md. */
#include <stdlib.h>
#include <string.h>
#include <mspack.h>
#include <lzx.h>
struct memory_file { unsigned char *data; int size, pos; };
static int read_mem(struct mspack_file *f, void *out, int count) {
    struct memory_file *m=(struct memory_file *)f;
    if(count<0) return -1;
    if(count>m->size-m->pos) count=m->size-m->pos;
    memcpy(out,m->data+m->pos,count); m->pos+=count; return count;
}
static int write_mem(struct mspack_file *f, void *in, int count) {
    struct memory_file *m=(struct memory_file *)f;
    if(count<0 || count>m->size-m->pos) return -1;
    memcpy(m->data+m->pos,in,count); m->pos+=count; return count;
}
static void *alloc_mem(struct mspack_system *s,size_t n) { (void)s;return malloc(n); }
static void copy_mem(void *src,void *dst,size_t n) { memcpy(dst,src,n); }
static struct mspack_system sys={NULL,NULL,read_mem,write_mem,NULL,NULL,NULL,alloc_mem,free,copy_mem,NULL};
#ifdef _WIN32
#define API __declspec(dllexport)
#else
#define API __attribute__((visibility("default")))
#endif
API int ue3_lzx(const unsigned char *input,int input_size,unsigned char *output,int output_size) {
    struct memory_file src={(unsigned char *)input,input_size,0},dst={output,output_size,0};
    struct lzxd_stream *s; int result;
    if(!input || !output || input_size<=0 || output_size<=0 || output_size>134217728) return -1;
    s=lzxd_init(&sys,(struct mspack_file *)&src,(struct mspack_file *)&dst,17,0,262144,output_size,0);
    if(!s) return -2;
    result=lzxd_decompress(s,output_size); lzxd_free(s);
    return result ? result : (dst.pos==output_size ? 0 : -3);
}
