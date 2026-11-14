/* scenedump: a CR2 as the darkroom has it before the film goes on, for the Colour Tuner.
 *
 *   scenedump in.CR2 small.u16 [big.u16 [1|2]]
 *
 * small.u16: the screen's print, 720 x 480, scene-linear sRGB (4096 = 1.0), three uint16 a pixel:
 *            what stage_key meters and what the halation is gathered from.
 * big.u16:   the bigger print (1 = Medium, the sensor three by three; 2 = Large, two by two), the same
 *            values from its own sums, as big_finish makes them. Its size is printed.
 *
 * It is fos_dev.c itself, stopped once the RAW is read (ST_KEY) and before the film's exposure is
 * chosen, so the numbers are the camera's: the same decoder, black level, balance and matrix.
 * Build it for the camera the CR2 came from (-DCONFIG_6D ...; none: the EOS M). */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include "fos_dev.c"

int fos_port_ms()
{
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC, &t);
    return (int) (t.tv_sec * 1000 + t.tv_nsec / 1000000);
}
void *fos_port_alloc(int size) { return malloc((size_t) size); }
void fos_port_free(void *p) { free(p); }
int fos_port_dev_cap() { return 0; }
void fos_port_log(const char *msg) { fprintf(stderr, "%s\n", msg); }
void sim_films();             /* films.c */

int main(int argc, char **argv)
{
    if (argc < 3) { fprintf(stderr, "usage: scenedump in.CR2 small.u16 [big.u16 [1|2]]\n"); return 2; }
    sim_films();
    struct fos_dev *d = fos_dev_start(argv[1], "/dev/null", 0, 1, "", "");
    if (argc > 3) fos_dev_big(d, argc > 4 ? atoi(argv[4]) : FOS_SIZE_M, 0);
    while (d->stage != ST_KEY)
    {
        int p = fos_dev_step(d, 1000);
        if (p < 0) { fprintf(stderr, "%s: %s\n", argv[1], fos_dev_error(d)); return 1; }
        if (d->stage > ST_KEY) { fprintf(stderr, "went past the RAW (stage %d)\n", d->stage); return 1; }
    }
    if (d->mul[0] != 4096 || d->mul[1] != 4096 || d->mul[2] != 4096) { fprintf(stderr, "exposure already set\n"); return 1; }

    const int W = FOS_PRINT_W, H = FOS_PRINT_H;
    FILE *f = fopen(argv[2], "wb");
    if (!f) { perror(argv[2]); return 1; }
    for (int y = 0; y < H; y++)
        for (int x = 0; x < W; x++)
        {
            int lin[3];
            pixel_linear(d, x, y, lin);
            uint16_t v[3] = { (uint16_t) lin[0], (uint16_t) lin[1], (uint16_t) lin[2] };
            fwrite(v, 2, 3, f);
        }
    fclose(f);
    printf("small %d %d portrait %d picture_x0 %d picture_w %d black16 %d pre %d %d %d\n", W, H, d->rows_axis_x,
           d->rows_axis_x ? d->ox0 : 0, d->rows_axis_x ? d->ow : W, d->black16, d->pre[0], d->pre[1], d->pre[2]);

    if (argc > 3)
    {
        if (!d->big) { fprintf(stderr, "no bigger print for this frame\n"); return 1; }
        const int bw = d->bw, bh = d->bh, sh = d->bshift;
        f = fopen(argv[3], "wb");
        if (!f) { perror(argv[3]); return 1; }
        for (int y = 0; y < bh; y++)
        {
            /* big_finish, as far as the linear light */
            const uint16_t *s = d->brow[y];
            for (int i = 0; i < 3 * bw; i++) d->b32[i] = (uint32_t) s[i] << sh;
            int a, b;
            const uint16_t *ra, *rb;
            if (d->rows_axis_x) { a = d->bne_c[y]; b = d->bno_c[y]; ra = d->bne_r; rb = d->bno_r; }
            else { a = d->bne_r[y]; b = d->bno_r[y]; ra = d->bne_c; rb = d->bno_c; }
            expose_cam(d, d->b32, d->bcam, bw, a, b, ra, rb);
            expose_lin(d, d->bcam, d->blin, bw, 0, 0);
            fwrite(d->blin, 2, (size_t) bw * 3, f);
        }
        fclose(f);
        printf("big %d %d sensor %d\n", bw, bh, d->big);
    }
    return 0;
}
