/* The film OS on a Fujifilm camera, over FujiHack: the fos_port_* functions
 * (fos.h) that filmroll.c gives it on a Canon.
 *
 * A scaffold: it builds and runs on a PC (make check, with fakefuji.c), and
 * it is written from FujiHack's notes, but it has never run on a camera.
 * Each "TODO(camera)" is something only a camera can answer; README.md lists
 * them in the order a port should go.
 *
 * The first camera is the X-A2 on firmware 1.30 (FujiHack's model/xa2_130.h):
 * its screen is 720 x 480, the film OS's own size. A 640-wide one (the XF1)
 * gets the canvas squeezed to fit (present below).
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../filmos/fos.h"
#include "../filmos/fos_dev.h"
#include "fuji.h"

#ifndef MFILM_VERSION
#define MFILM_VERSION "dev"
#endif

/* ---------------------------------------------------------------- state */

static int settings[FS_COUNT] = {
    [FS_HUD] = 1, [FS_LEDS] = 1, [FS_FOCUS] = 1, [FS_WIND] = 1,
    [FS_LENS_WIDE] = 6, [FS_FSTOP] = 10, [FS_STARTUP] = 2, [FS_PLAYLOCK] = 1,
    [FS_BOOTANIM] = 1, [FS_DEBUG] = 1, [FS_SIZE] = FOS_SIZE_S, [FS_FADE] = 1,
};
static struct fos_roll roll;
static int leave;               /* FA_CANON_MENU: back to Fujifilm's own screens */

#define STATE_FILE "ML/SETTINGS/MFILM.FUJ"
#define STATE_MAGIC 0x4d465531  /* "MFU1" */
static void state_save();

/* ---------------------------------------------------------------- time */

int fos_port_ms()
{
    /* the "timer" task's count of milliseconds */
    return (int) *(volatile uint32_t *) MEM_MS_TIMER;
}

static void poll_keys();

void fos_port_sleep(int ms)
{
    fuji_task_sleep(ms > 0 ? ms : 1);
    poll_keys();
}

/* ---------------------------------------------------------------- keys */

/* The X-A2's keys, as the film OS knows them (the EOS M's are in
 * fork/src/filmroll.c). MENU/OK is SET, DISP/BACK goes back, Fn is INFO,
 * the command dial is the wheel; half-press leaves, as on every camera. */
static const struct { uint32_t fuji; int fos; } keymap[] = {
    { FUJI_KEY_UP, FK_UP }, { FUJI_KEY_DOWN, FK_DOWN },
    { FUJI_KEY_LEFT, FK_LEFT }, { FUJI_KEY_RIGHT, FK_RIGHT },
    { FUJI_KEY_OK, FK_SET }, { FUJI_KEY_DISPBACK, FK_MENU },
    { FUJI_KEY_PLAY, FK_PLAY }, { FUJI_KEY_FN, FK_INFO },
};

#define KEYQ 16
static int keyq[KEYQ], keyq_in, keyq_out;
static int half_pressed;

static void key_push(int k)
{
    int next = (keyq_in + 1) % KEYQ;
    if (next == keyq_out) return;           /* full: the film OS is busy, drop it */
    keyq[keyq_in] = k;
    keyq_in = next;
}

/* FujiHack's input map holds the last key that changed and how: compare it
 * with what was there at the last look. TODO(camera): which key_status
 * values mean pressed, held and released (FujiHack only relies on 0x80 for
 * a released DISP/BACK), and how the command dial says which way it turned. */
static void poll_keys()
{
    static uint32_t last_code, last_status, last_x;
    volatile struct fuji_input *in = (volatile struct fuji_input *) MEM_INPUT_MAP;
    uint32_t code = in->key_code, status = in->key_status, x = in->x;
    if (code == last_code && status == last_status && x == last_x) return;
    last_code = code; last_status = status; last_x = x;

    int released = status == FUJI_KEY_RELEASED;
    if (code == FUJI_KEY_HALF) { half_pressed = !released; return; }
    if (code == FUJI_KEY_DIAL)
    {
        if (!released) key_push((int) x & 0x80000000 ? FK_WHEEL_L : FK_WHEEL_R);   /* ? */
        return;
    }
    for (unsigned i = 0; i < sizeof(keymap) / sizeof(keymap[0]); i++)
        if (keymap[i].fuji == code)
        {
            /* the film OS wants the four directions' releases too (fos.h) */
            int fos = keymap[i].fos;
            if (!released) key_push(fos);
            else if (fos >= FK_LEFT && fos <= FK_DOWN) key_push(fos | FK_RELEASE);
            return;
        }
}

int fos_port_key()
{
    if (keyq_out == keyq_in) return FK_NONE;
    int k = keyq[keyq_out];
    keyq_out = (keyq_out + 1) % KEYQ;
    return k;
}

int fos_port_abort()
{
    /* TODO(camera): a Fujifilm screen taking over (low battery, card door) */
    return leave || half_pressed;
}

/* ---------------------------------------------------------------- the screen */

/* the film OS's 256 colours as the screen's pixels: RGBA, A in the low byte */
static uint32_t lut[256];

static uint32_t rgba(uint32_t rgb) { return rgb << 8 | 0xff; }

void fos_port_palette()
{
    /* the screen takes RGB as it is: no Canon YUV to go through, so the
     * Screen colour settings aren't applied yet (TODO: through fos_screen_yuv_rgb) */
    for (int i = 0; i < 256; i++) lut[i] = rgba(fos_pal[i] & 0xffffff);
    lut[0] = 0;                 /* 0: clear, LiveView shows through. TODO(camera): does alpha 0 do it */
}

void fos_port_photo(const uint8_t (*pal)[3], int n, int k)
{
    for (int i = 1; i < 255; i++)
    {
        const uint8_t *c = i <= n ? pal[i - 1] : i >= FOS_FIXED_BASE && i < FOS_FIXED_BASE + FOS_FIXED_N ?
                           fos_fixed_rgb[i - FOS_FIXED_BASE] : (const uint8_t *) "\0\0\0";
        lut[i] = rgba((uint32_t) (c[0] * k >> 8) << 16 | (uint32_t) (c[1] * k >> 8) << 8 | (uint32_t) (c[2] * k >> 8));
    }
}

/* the canvas's column for each of the screen's: 1:1 at 720, squeezed at 640 */
static uint16_t colmap[SCREEN_WIDTH];

static void screen_init()
{
    for (int x = 0; x < SCREEN_WIDTH; x++) colmap[x] = (uint16_t) (x * FOS_W / SCREEN_WIDTH);
}

void fos_port_present(const uint8_t *rows, int pitch, int y0, int y1)
{
    if (y0 < 0) y0 = 0;
    if (y1 > FOS_H) y1 = FOS_H;
    /* FujiHack paints all three layers, as which one is on show isn't known.
     * TODO(camera): find the one in front and paint only that, or flip */
    volatile uintptr_t *layers = (volatile uintptr_t *) MEM_OPENGL_BUFFERS;
    for (int l = 0; l < FUJI_LAYERS; l++)
    {
        uint32_t *fb = (uint32_t *) layers[l];
        if (!fb) continue;
        for (int y = y0; y < y1 && y < SCREEN_HEIGHT; y++)
        {
            const uint8_t *src = rows + (y - y0) * pitch;
            uint32_t *dst = fb + y * SCREEN_WIDTH;
            for (int x = 0; x < SCREEN_WIDTH; x++) dst[x] = lut[src[colmap[x]]];
        }
    }
}

/* ---------------------------------------------------------------- memory */

void *fos_port_alloc(int size) { return malloc((size_t) size); }
void fos_port_free(void *p) { if (p) free(p); }

/* ---------------------------------------------------------------- the card */

/* Every call reports through a handler; wait before and after, as FujiHack's
 * own loader does. The size comes from the file's stats and the position is
 * kept here, so a read knows how much it got without the handler saying. */
static volatile int file_error;
static void file_done(int error, int id, int a, int b)
{
    fuji_file_reset();
    file_error = error;
}

struct fuji_file { int fp, pos, size, write; };

/* the film OS's "C:/ML/X" as the camera's "C:\ML\X" */
static void dos_path(char *dst, int size, const char *src)
{
    int i = 0;
    for (; src[i] && i < size - 1; i++) dst[i] = src[i] == '/' ? '\\' : src[i];
    dst[i] = 0;
}

const char *fos_port_card()
{
    static char root[4];
    root[0] = fuji_drive(); root[1] = ':'; root[2] = '/'; root[3] = 0;
    return root;
}

void *fos_port_open(const char *path, int write)
{
    char dos[128];
    if (!path || !*path) return 0;
    dos_path(dos, sizeof(dos), path);
    fuji_file_wait();
    file_error = FUJI_OK;
    int fp = fuji_fopen(file_done, dos, write ? FUJI_WRITE : FUJI_READ);
    fuji_file_wait();
    if (file_error != FUJI_OK || fp < 0) return 0;
    struct fuji_file *f = malloc(sizeof(*f));
    if (!f) { fuji_fclose(file_done, fp, 0, 0); fuji_file_wait(); return 0; }
    f->fp = fp; f->pos = 0; f->write = write; f->size = 0;
    if (!write)
    {
        struct fuji_stats st;
        fuji_fstats(fp, &st, fp);
        f->size = (int) st.size;
    }
    return f;
}

int fos_port_read(void *h, void *buf, int size)
{
    struct fuji_file *f = h;
    if (!f || f->write) return -1;
    if (size > f->size - f->pos) size = f->size - f->pos;
    if (size <= 0) return 0;
    file_error = FUJI_OK;
    fuji_fread(file_done, f->fp, size, buf);
    fuji_file_wait();
    if (file_error != FUJI_OK && file_error != FUJI_EOF) return -1;
    f->pos += size;
    return size;
}

int fos_port_write(void *h, const void *buf, int size)
{
    struct fuji_file *f = h;
    if (!f || !f->write) return -1;
    file_error = FUJI_OK;
    fuji_fwrite(file_done, f->fp, size, buf);
    fuji_file_wait();
    if (file_error != FUJI_OK) return -1;
    f->pos += size;
    return size;
}

int fos_port_seek(void *h, int offset)
{
    struct fuji_file *f = h;
    if (!f || offset < 0) return -1;
    file_error = FUJI_OK;
    fuji_fseek(file_done, f->fp, offset, 0, FUJI_SEEK_SET);
    fuji_file_wait();
    if (file_error != FUJI_OK) return -1;
    f->pos = offset;
    return 0;
}

void fos_port_close(void *h)
{
    struct fuji_file *f = h;
    if (!f) return;
    fuji_fclose(file_done, f->fp, 0, 0);
    fuji_file_wait();
    free(f);
}

/* TODO(camera): fuji_dir_open/next is one listing at a time, and what its
 * two names and the buffer hold isn't known. Until then nothing on the card
 * can be listed: the darkroom finds no rolls and the shelf no samples. */
int fos_port_list(const char *dir, int (*fn)(void *ctx, const char *name, int is_dir), void *ctx) { return -1; }
/* TODO(camera): no mkdir or remove found in the firmware yet; folders come in the zip */
int fos_port_mkdir(const char *path) { return -1; }
int fos_port_remove(const char *path) { return -1; }

/* ---------------------------------------------------------------- the camera */

void fos_port_roll(struct fos_roll *r) { *r = roll; }

int fos_port_get(int s)
{
    switch (s)
    {
        case FS_SCR_FLIP:       /* not a swivel screen */
        case FS_EXPSIM:         /* TODO(camera): Fujifilm's "preview exposure" setting */
        case FS_CANON_OFF:      /* no Canon graphics */
            return -1;
    }
    return s >= 0 && s < FS_COUNT ? settings[s] : 0;
}

void fos_port_set(int s, int v)
{
    if (s < 0 || s >= FS_COUNT) return;
    settings[s] = v;
    state_save();
}

void fos_port_action(int action, int a, int b)
{
    switch (action)
    {
        case FA_LOAD:
            /* TODO(camera): set the camera to the film: ISO (fos_films[a].iso),
             * white balance (kelvin, shifts) and a film simulation to look
             * through. None of Fujifilm's settings can be changed yet. */
            roll.loaded = 1; roll.number++; roll.film = a;
            roll.exposures = fos_exposure_choices[b];
            roll.shot = 0; roll.need_wind = 0; roll.nrecent = 0;
            fos_port_clock(roll.loaded_at, sizeof(roll.loaded_at));
            settings[FS_RECENT] = (settings[FS_RECENT] << 8 | (a + 1)) & 0xffffffff;
            state_save();
            break;
        case FA_REWIND:
            roll.loaded = 0;
            state_save();
            break;
        case FA_CANON_MENU:     /* "the camera's menu": Fujifilm's */
            leave = 1;
            break;
        case FA_REAPPLY: case FA_BUSY: case FA_DIM:
            /* TODO(camera): keep the camera awake while developing; dim the backlight */
            break;
    }
}

/* TODO(camera): counting frames. On a Canon a property says a picture was
 * taken; here the firmware's picture-taken code has to be found (FujiHack
 * has it on the X-T10 only, FIRM_TAKEPIC) and hooked to call this. */
void fuji_frame_taken()
{
    if (!roll.loaded || roll.shot >= roll.exposures) return;
    roll.shot++;
    state_save();
}

void fos_port_clock(char *buf, int size)
{
    /* TODO(camera): the camera's clock; the film OS shows "--:--" meanwhile */
    snprintf(buf, size, "--:--");
}

int fos_port_battery(int *exact) { if (exact) *exact = 0; return -1; }   /* TODO(camera) */
int fos_port_lens_manual() { return 0; }            /* TODO(camera): a lens with no contacts */
const char *fos_port_lens_name() { return "Fujinon"; }
const char *fos_port_version() { return MFILM_VERSION; }
const char *fos_port_model() { return MODEL_NAME; }
int fos_port_dev_cap() { return 0; }
void fos_port_stat(const struct fos_stat *s) { }

void fos_port_log(const char *msg)
{
    if (!settings[FS_DEBUG]) return;
    char path[32];
    snprintf(path, sizeof(path), "%sML/MFILM.LOG", fos_port_card());
    /* TODO: append; the firmware's open may only make new files */
    void *f = fos_port_open(path, 1);
    if (!f) return;
    fos_port_write(f, msg, (int) strlen(msg));
    fos_port_write(f, "\n", 1);
    fos_port_close(f);
}

/* ---------------------------------------------------------------- settings on the card */

struct saved { uint32_t magic; int settings[FS_COUNT]; struct fos_roll roll; };

static void state_save()
{
    char path[48];
    snprintf(path, sizeof(path), "%s" STATE_FILE, fos_port_card());
    struct saved s;
    memset(&s, 0, sizeof(s));
    s.magic = STATE_MAGIC;
    memcpy(s.settings, settings, sizeof(settings));
    s.roll = roll;
    void *f = fos_port_open(path, 1);
    if (!f) return;
    fos_port_write(f, &s, sizeof(s));
    fos_port_close(f);
}

static void state_load()
{
    char path[48];
    snprintf(path, sizeof(path), "%s" STATE_FILE, fos_port_card());
    struct saved s;
    void *f = fos_port_open(path, 0);
    if (!f) return;
    if (fos_port_read(f, &s, sizeof(s)) == (int) sizeof(s) && s.magic == STATE_MAGIC)
    {
        memcpy(settings, s.settings, sizeof(settings));
        roll = s.roll;
    }
    fos_port_close(f);
}

/* ---------------------------------------------------------------- start */

/* a file from the card into memory that stays (fonts and films point into it) */
static uint8_t *card_blob(const char *name, int *size)
{
    char path[64];
    snprintf(path, sizeof(path), "%sML/DATA/%s", fos_port_card(), name);
    struct fuji_file *f = fos_port_open(path, 0);
    if (!f) return 0;
    int want = f->size;
    uint8_t *blob = malloc((size_t) want);
    *size = blob ? fos_port_read(f, blob, want) : -1;
    fos_port_close(f);
    if (*size != want) { free(blob); return 0; }
    return blob;
}

/* What FujiHack's app loader runs (sys_load_app("C:\\ML\\MFILM.ELF")).
 * TODO(camera): how it is reached: FujiHack takes over a menu of the
 * firmware's (on the X-A2, Instax printing); M-Film wants a button, or
 * the start screen. */
int mfilm_main(int open)
{
    int size;
    leave = 0;
    screen_init();
    state_load();
    fos_ui_init();
    uint8_t *fonts = card_blob(FOS_FONT_FILE, &size);
    if (!fonts || !fos_fonts_load(fonts, size))
        fos_port_log("fonts: ML/DATA/" FOS_FONT_FILE " missing or not usable");
    uint8_t *films = card_blob(FOS_FILM_FILE, &size);
    if (films && !fos_films_load(films, size)) free(films);
    fos_port_palette();
    fos_ui_run(open);
    return 0;
}
