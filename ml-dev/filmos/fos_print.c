/* fos_print: reading a print (the BMP the darkroom writes, fos_dev.c).
 *
 * Kept apart from the darkroom so every build can show prints: the shelf's
 * sample of each film is one, also in builds made --no-darkroom.
 */

#include "fos.h"
#include "fos_dev.h"
#include <string.h>

uint8_t fos_bmp_head[FOS_BMP_PIXELS];

static int u16le(const uint8_t *p) { return p[0] | p[1] << 8; }
static unsigned u32le(const uint8_t *p) { return p[0] | p[1] << 8 | p[2] << 16 | (unsigned) p[3] << 24; }

static int is_print(const uint8_t *h)
{
    return h[0] == 'B' && h[1] == 'M' && u32le(h + 10) == FOS_BMP_PIXELS && u32le(h + 18) == FOS_PRINT_W
        && !memcmp(h + FOS_BMP_META, "FOP2", 4);
}

int fos_print_thumb(const char *path, uint8_t *thumb)
{
    void *f = fos_port_open(path, 0);
    if (!f) return 0;
    uint8_t *h = fos_bmp_head;
    int ok = fos_port_read(f, h, FOS_BMP_PIXELS) == FOS_BMP_PIXELS && is_print(h)
          && fos_port_seek(f, FOS_BMP_THUMB) >= 0 && fos_port_read(f, thumb, FOS_THUMB_SIZE) == FOS_THUMB_SIZE;
    fos_port_close(f);
    return ok;
}

int fos_print_load(const char *path, struct fos_print *p)
{
    memset(p, 0, sizeof(*p));
    void *f = fos_port_open(path, 0);
    if (!f) return 0;
    uint8_t *h = fos_bmp_head;
    int ok = fos_port_read(f, h, FOS_BMP_PIXELS) == FOS_BMP_PIXELS && is_print(h);
    if (ok)
    {
        const uint8_t *m = h + FOS_BMP_META;
        p->film = m[4];
        p->frame = u16le(m + 6);
        memcpy(p->when, m + 8, 19);
        memcpy(p->fstop, m + 28, 7);
        p->x0 = u16le(m + 36);
        p->w = u16le(m + 38);
        if (!p->w || p->x0 + p->w > FOS_PRINT_W) p->x0 = 0, p->w = FOS_PRINT_W;
        for (int i = 0; i < FOS_PRINT_COLOURS; i++)
        {
            const uint8_t *q = h + FOS_BMP_PAL + 4 * (i + 1);
            p->pal[i][0] = q[2]; p->pal[i][1] = q[1]; p->pal[i][2] = q[0];
        }
        p->px = fos_port_alloc(FOS_PRINT_W * FOS_PRINT_H);
        ok = p->px && fos_port_read(f, p->px, FOS_PRINT_W * FOS_PRINT_H) == FOS_PRINT_W * FOS_PRINT_H;
    }
    fos_port_close(f);
    if (!ok) fos_print_free(p);
    return ok;
}

void fos_print_free(struct fos_print *p)
{
    fos_port_free(p->px);
    p->px = 0;
}

/* ---------------------------------------------------------------- zoom files */

int fos_zoom_open(const char *path, struct fos_zoom *z)
{
    uint8_t h[FOS_ZOOM_HEAD];
    memset(z, 0, sizeof(*z));
    z->f = fos_port_open(path, 0);
    if (!z->f) return 0;
    if (fos_port_read(z->f, h, FOS_ZOOM_HEAD) == FOS_ZOOM_HEAD && !memcmp(h, "FOZ1", 4))
    {
        z->w = u16le(h + 4);
        z->h = u16le(h + 6);
    }
    if (z->w < 16 || z->h < 16) fos_zoom_close(z);
    return z->f != 0;
}

int fos_zoom_read(struct fos_zoom *z, int x, int y, int step, uint8_t *out, int pitch, int ow, int oh, uint8_t *rows)
{
    if (!z->f || step < 1 || x < 0 || y < 0 || x + ow * step > z->w + step - 1 || y + oh * step > z->h + step - 1) return 0;
    int nrows = oh * step;
    if (y + nrows > z->h) nrows = z->h - y;
    if (fos_port_seek(z->f, FOS_ZOOM_HEAD + y * z->w) < 0) return 0;
    if (fos_port_read(z->f, rows, nrows * z->w) != nrows * z->w) return 0;
    for (int j = 0; j < oh; j++)
    {
        int ry = j * step;
        const uint8_t *s = rows + (ry < nrows ? ry : nrows - 1) * z->w + x;
        uint8_t *o = out + j * pitch;
        if (step == 1) memcpy(o, s, ow);
        else
            for (int i = 0; i < ow; i++)
            {
                int sx = i * step;
                o[i] = s[x + sx < z->w ? sx : z->w - 1 - x];
            }
    }
    return 1;
}

void fos_zoom_close(struct fos_zoom *z)
{
    if (z->f) fos_port_close(z->f);
    z->f = 0;
}
