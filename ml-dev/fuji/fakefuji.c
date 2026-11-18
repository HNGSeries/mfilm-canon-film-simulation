/* A Fujifilm camera on a PC, for make check: the firmware functions and
 * memory fujiport.c uses, played from a script, so the port runs whole
 * (keys in, RGBA screen out) without a camera.
 *
 *   ./out/fakefuji-xa2 script.txt outdir
 *
 * A script line is "<ms> <key>" (up down left right ok back play fn
 * dial+ dial- half), "<ms> shot <name>" (the screen's layer as
 * outdir/<name>.ppm, at the camera's own size) or "<ms> end"; "open home"
 * or "open shelf" picks the first screen. The card is a folder (FUJI_CARD,
 * else out/card). It answers only as FujiHack's notes say the camera does:
 * where the camera is unknown, so is this.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../filmos/fos.h"
#include "fuji.h"

volatile uint32_t fake_ms;
volatile struct fuji_input fake_input;
static uint32_t fake_layer[FUJI_LAYERS][SCREEN_WIDTH * SCREEN_HEIGHT];
volatile uintptr_t fake_layers[FUJI_LAYERS] = {
    (uintptr_t) fake_layer[0], (uintptr_t) fake_layer[1], (uintptr_t) fake_layer[2] };

int mfilm_main(int open);

/* ---- the script */

struct ev { int t; uint32_t code, status, x; char shot[32]; };
static struct ev evs[256];
static int nev, next_ev, end_t = 4000;
static const char *outdir;

static void shot(const char *name)
{
    char path[512];
    snprintf(path, sizeof(path), "%s/%s.ppm", outdir, name);
    FILE *f = fopen(path, "wb");
    if (!f) { perror(path); exit(1); }
    fprintf(f, "P6\n%d %d\n255\n", SCREEN_WIDTH, SCREEN_HEIGHT);
    for (int i = 0; i < SCREEN_WIDTH * SCREEN_HEIGHT; i++)
    {
        uint32_t p = fake_layer[0][i];
        /* alpha 0 is LiveView showing through: a dull green stands in, as in the simulator */
        uint8_t rgb[3] = { (uint8_t) (p >> 24), (uint8_t) (p >> 16), (uint8_t) (p >> 8) };
        if ((p & 0xff) == 0) { rgb[0] = 40; rgb[1] = 70; rgb[2] = 60; }
        fwrite(rgb, 1, 3, f);
    }
    fclose(f);
}

static void play()
{
    while (next_ev < nev && evs[next_ev].t <= (int) fake_ms)
    {
        struct ev *e = &evs[next_ev++];
        if (e->shot[0]) { shot(e->shot); continue; }
        fake_input.key_code = e->code;
        fake_input.key_status = e->status;
        fake_input.x = e->x;
    }
}

/* ---- the firmware */

int fuji_task_sleep(int ms)
{
    fake_ms += (uint32_t) ms + 16;          /* a frame's drawing, roughly */
    play();
    return 0;
}

static FILE *files[32];
static char card[256] = "out/card";

char fuji_drive() { return 'C'; }
void fuji_file_wait() { }
void fuji_file_reset() { }

int fuji_fopen(fuji_file_handler h, const char *path, int flag)
{
    char p[512];
    snprintf(p, sizeof(p), "%s/%s", card, path + 3);      /* past "C:\" */
    for (char *c = p; *c; c++) if (*c == '\\') *c = '/';
    int fp = 1;
    while (fp < 32 && files[fp]) fp++;
    FILE *f = fp < 32 ? fopen(p, flag == FUJI_WRITE ? "wb" : "rb") : 0;
    if (f) files[fp] = f;
    h(f ? FUJI_OK : 2, fp, 0, 0);
    return f ? fp : -1;
}
int fuji_fread(fuji_file_handler h, int fp, int n, void *data)
{
    size_t got = fread(data, 1, (size_t) n, files[fp]);
    h(got == (size_t) n ? FUJI_OK : FUJI_EOF, fp, (int) got, 0);
    return 0;
}
int fuji_fwrite(fuji_file_handler h, int fp, int n, const void *data)
{
    h(fwrite(data, 1, (size_t) n, files[fp]) == (size_t) n ? FUJI_OK : 2, fp, n, 0);
    return 0;
}
int fuji_fseek(fuji_file_handler h, int fp, int pos, int a, int whence)
{
    h(fseek(files[fp], pos, SEEK_SET) ? 2 : FUJI_OK, fp, 0, 0);
    return 0;
}
int fuji_fclose(fuji_file_handler h, int fp, int x, int y)
{
    if (files[fp]) fclose(files[fp]);
    files[fp] = 0;
    h(FUJI_OK, fp, 0, 0);
    return 0;
}
int fuji_fstats(int fp, struct fuji_stats *s, int fp2)
{
    long here = ftell(files[fp]);
    fseek(files[fp], 0, SEEK_END);
    s->size = (uint32_t) ftell(files[fp]);
    fseek(files[fp], here, SEEK_SET);
    return 0;
}

/* ---- the script's words */

static int key(const char *s, struct ev *e)
{
    static const struct { const char *n; uint32_t code, x; } names[] = {
        { "up", FUJI_KEY_UP, 0 }, { "down", FUJI_KEY_DOWN, 0 }, { "left", FUJI_KEY_LEFT, 0 }, { "right", FUJI_KEY_RIGHT, 0 },
        { "ok", FUJI_KEY_OK, 0 }, { "back", FUJI_KEY_DISPBACK, 0 }, { "play", FUJI_KEY_PLAY, 0 }, { "fn", FUJI_KEY_FN, 0 },
        { "dial+", FUJI_KEY_DIAL, 1 }, { "dial-", FUJI_KEY_DIAL, 0x80000000u }, { "half", FUJI_KEY_HALF, 0 },
    };
    for (unsigned i = 0; i < sizeof(names) / sizeof(names[0]); i++)
        if (!strcmp(s, names[i].n)) { e->code = names[i].code; e->x = names[i].x; return 1; }
    return 0;
}

int main(int argc, char **argv)
{
    if (argc < 3) { fprintf(stderr, "usage: fakefuji script outdir\n"); return 1; }
    outdir = argv[2];
    if (getenv("FUJI_CARD")) snprintf(card, sizeof(card), "%s", getenv("FUJI_CARD"));
    FILE *f = fopen(argv[1], "r");
    if (!f) { perror(argv[1]); return 1; }
    char line[256], a[64], b[64];
    int t, open = FOS_OPEN_HOME;
    while (fgets(line, sizeof(line), f))
    {
        if (line[0] == '#' || line[0] == '\n') continue;
        if (sscanf(line, "open %63s", a) == 1) { open = !strcmp(a, "shelf") ? FOS_OPEN_SHELF : FOS_OPEN_HOME; continue; }
        if (sscanf(line, "%d shot %31s", &t, a) == 2)
        {
            evs[nev].t = t; snprintf(evs[nev].shot, sizeof(evs[nev].shot), "%s", a); nev++;
            continue;
        }
        if (sscanf(line, "%d %63s", &t, b) != 2) continue;
        if (!strcmp(b, "end")) { end_t = t; continue; }
        struct ev e;
        memset(&e, 0, sizeof(e));
        e.t = t;
        if (!key(b, &e)) { fprintf(stderr, "unknown key %s\n", b); return 1; }
        evs[nev++] = e;
        e.t = t + 110; e.status = FUJI_KEY_RELEASED;            /* and let go */
        if (e.code != FUJI_KEY_HALF) evs[nev++] = e;
    }
    fclose(f);
    for (int i = 1; i < nev; i++)
        for (int j = i; j > 0 && evs[j].t < evs[j - 1].t; j--) { struct ev x = evs[j]; evs[j] = evs[j - 1]; evs[j - 1] = x; }
    /* the end is a half-press, as leaving is on the camera */
    evs[nev].t = end_t; key("half", &evs[nev]); nev++;
    mfilm_main(open);
    fprintf(stderr, "%s: left at %u ms\n", MODEL_NAME, (unsigned) fake_ms);
    return 0;
}
