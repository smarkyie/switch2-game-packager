/* SPDX-License-Identifier: MIT
 * Bounded, read-only probe for this packager's plaintext XCI/NSP images.
 * No imports, allocations, keys, writes, or persistent state. Called before
 * Eglantine's original IsSwitch2Program; false always falls back to that code.
 * VfsFile ABI is pinned to the executable hashes in emulator_profiles.py.
 */
typedef unsigned char u8;
typedef unsigned int u32;
typedef unsigned long long u64;
typedef u64 (*ReadFn)(void *, void *, u64, u64);
typedef u64 (*SizeFn)(void *);
#ifndef VFS_GNU
#define VFS_GNU 0
#endif
#ifndef VFS_SIZE_SLOT
#define VFS_SIZE_SLOT (3 + VFS_GNU)
#endif
#ifndef VFS_READ_SLOT
#define VFS_READ_SLOT (8 + VFS_GNU)
#endif
typedef struct { void *file; ReadFn read; u64 size, budget; u32 calls; } Reader;
typedef struct { u64 base, size; } Region;
int DllMain(void *module, u32 reason, void *reserved) { (void)module; (void)reason; (void)reserved; return 1; }
static u32 get32(const u8 *p) {
    return (u32)p[0] | (u32)p[1]<<8 | (u32)p[2]<<16 | (u32)p[3]<<24;
}
static u64 get64(const u8 *p) { return get32(p) | (u64)get32(p+4)<<32; }
static int read_at(Reader *r, Region v, u64 off, void *out, u64 n) {
    if (off>v.size || n>v.size-off || v.base>r->size ||
        v.size>r->size-v.base || n>r->budget || !r->calls) return 0;
    r->budget-=n; r->calls--;
    return r->read(r->file,out,n,v.base+off)==n;
}
static int subregion(Region v, u64 off, u64 n, Region *out) {
    if (off>v.size || n>v.size-off) return 0;
    out->base=v.base+off; out->size=n; return 1;
}
static int npdm_switch2(Reader *r, Region v) {
    u8 h[128], magic[4];
    if (!read_at(r,v,0,h,128) || get32(h)!=0x4154454d) return 0; /* META */
    u64 aci=get32(h+0x70), acisz=get32(h+0x74);
    u64 acid=get32(h+0x78), acidsz=get32(h+0x7c);
    Region a;
    if (aci<128 || acisz<0x40 || !subregion(v,aci,acisz,&a) ||
        !read_at(r,a,0,magic,4) || get32(magic)!=0x30494341) return 0; /* ACI0 */
    if (acid<128 || acidsz<0x340 || !subregion(v,acid,acidsz,&a)) return 0;
    if (!read_at(r,a,0x200,magic,4) || get32(magic)==0x44494341) return 0;
    return read_at(r,a,0x300,magic,4) && get32(magic)==0x44494341; /* ACID */
}
static int walk(Reader *, Region, u32);
static int partition(Reader *r, Region v, int hfs, u32 depth, int exefs) {
    u8 h[24], entry[24], name[10];
    if (!read_at(r,v,0,h,16) || get32(h)!=(hfs?0x30534648:0x30534650)) return 0;
    u64 count=get32(h+4), strings=get32(h+8), width=hfs?64:24;
    if (count>4096 || strings>1048576) return 0;
    u64 table=16+count*width, data=table+strings;
    if (data>v.size) return 0;
    for (u64 i=0;i<count;i++) {
        if (!read_at(r,v,16+i*width,entry,24)) return 0;
        u64 off=get64(entry), size=get64(entry+8), n=get32(entry+16);
        if (n>=strings || off>v.size-data || size>v.size-data-off) return 0;
        Region child;
        if (!subregion(v,data+off,size,&child)) return 0;
        if (exefs) {
            if (strings-n<10 || !read_at(r,v,table+n,name,10)) continue;
            if (get64(name)==0x64706e2e6e69616dULL && name[8]=='m' && !name[9])
                return npdm_switch2(r,child);
        } else if (walk(r,child,depth+1)) return 1;
        if (!r->calls || !r->budget) return 0;
    }
    return 0;
}
static int nca(Reader *r, Region v) {
    u8 head[128], section[16], fs[80];
    if (!read_at(r,v,0x200,head,128) || get32(head)!=0x3341434e || head[5]!=0) return 0;
    /* Only plaintext headers and plaintext hashed ExeFS sections are supported. */
    for (u32 i=0;i<4;i++) {
        if (!read_at(r,v,0x240+16*i,section,16) || !read_at(r,v,0x400+512*i,fs,80)) return 0;
        u64 start=(u64)get32(section)*512, end=(u64)get32(section+4)*512;
        if (end<=start || start<0xc00 || fs[2]!=1 || fs[3]!=2 || fs[4]!=1) continue;
        Region body, pfs;
        if (!subregion(v,start,end-start,&body) || !subregion(body,get64(fs+0x40),get64(fs+0x48),&pfs)) return 0;
        if (partition(r,pfs,0,0,1)) return 1;
    }
    return 0;
}
static int walk(Reader *r, Region v, u32 depth) {
    u8 h[4];
    if (depth>3 || !read_at(r,v,0,h,4)) return 0;
    u32 magic=get32(h);
    if (magic==0x30534648 || magic==0x30534650)
        return partition(r,v,magic==0x30534648,depth,0);
    return nca(r,v);
}
__declspec(dllexport) int container_probe(const void *shared_file) {
    if (!shared_file) return 0;
    void *file=*(void *const *)shared_file;
    if (!file) return 0;
    void **vt=*(void ***)file;
    Reader r={file,(ReadFn)vt[VFS_READ_SLOT],((SizeFn)vt[VFS_SIZE_SLOT])(file),1048576,8192};
    Region root={0,r.size}; u8 header[64];
    if (r.size<16 || r.size>0x10000000000ULL) return 0;
    if (read_at(&r,root,0x100,header,64) && get32(header)==0x44414548) {
        u64 off=get64(header+0x30);
        if (off<0x200 || off>=root.size || !subregion(root,off,root.size-off,&root)) return 0;
    }
    return walk(&r,root,0);
}
