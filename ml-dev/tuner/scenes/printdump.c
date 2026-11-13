/* printdump: the camera's prints of a CR2 before the grain, to check the Colour Tuner against.
 *
 *   printdump in.CR2 film 1|2 small.rgb big.rgb
 *
 * small.rgb: the screen's print (720 x 480 x 3 bytes) as stage_finish leaves it; big.rgb: the bigger
 * print's rows as big_finish makes them (its size is printed). The film's grain is set to nothing and
 * there is no date stamp: the Tuner shows neither. fos_dev.c itself, one slice of work at a time. */
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
int fos_port_dev_cap() { return 1; }            /* a slice a step, to stop between stages */
void fos_port_log(const char *msg) { fprintf(stderr, "%s\n", msg); }
void sim_films();             /* films.c */

int main(int argc, char **argv)
{
    if (argc < 6) { fprintf(stderr, "usage: printdump in.CR2 film 1|2 small.rgb big.rgb\n"); return 2; }
    sim_films();
    int film = -1;
    for (int i = 0; i < fos_nfilms; i++) if (!strcmp(fos_films[i].key, argv[2])) film = i;
    if (film < 0) { fprintf(stderr, "no film %s\n", argv[2]); return 2; }
    struct fos_dev *d = fos_dev_start(argv[1], "/dev/null", film, 1, "", "");
    static struct fos_look look;
    look = *d->look;
    look.grain = 0;
    d->look = &look;
    fos_dev_big(d, atoi(argv[3]), 0);
    const int W = FOS_PRINT_W, H = FOS_PRINT_H;
    int small_done = 0;
    for (;;)
    {
        int p = fos_dev_step(d, 1000);
        if (p < 0) { fprintf(stderr, "%s: %s\n", argv[1], fos_dev_error(d)); return 1; }
        if (!small_done && d->stage == ST_QUANT)
        {
            FILE *f = fopen(argv[4], "wb");
            fwrite(d->rgb, 3, (size_t) W * H, f);
            fclose(f);
            small_done = 1;
            printf("small %d %d mul %d %d %d halation %g thr %g\n", W, H, d->mul[0], d->mul[1], d->mul[2],
                   (double) look.halation, (double) look.hal_thr);
        }
        if (d->stage == ST_BIG && d->row < 0) break;
        if (d->stage >= ST_WRITE) { fprintf(stderr, "no bigger print was made\n"); return 1; }
    }
    big_begin(d);
    uint8_t *row = malloc((size_t) d->bw * 3);
    FILE *f = fopen(argv[5], "wb");
    for (int y = 0; y < d->bh; y++)
    {
        big_finish(d, y, row);
        fwrite(row, 3, (size_t) d->bw, f);
    }
    fclose(f);
    printf("big %d %d\n", d->bw, d->bh);
    return 0;
}
