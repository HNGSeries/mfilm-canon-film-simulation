/* What the Fujifilm port calls in the camera's firmware.
 *
 * The addresses don't live here: they come from FujiHack's header for the
 * camera and firmware (model/<model>.h, given with -include by the
 * Makefile), which defines MODEL_NAME, SCREEN_WIDTH/HEIGHT and the MEM_*
 * places, and from its stubs, which give the fuji_* functions below their
 * addresses. These are only our own declarations of what we call, written
 * from FujiHack's notes; a "?" marks what nobody has confirmed on a camera.
 * On a PC (make check) fakefuji.c stands in for all of it.
 */

#ifndef _fuji_h_
#define _fuji_h_

#include <stdint.h>

/* ---- keys: FujiHack's input map at MEM_INPUT_MAP, polled */
struct fuji_input
{
    uint32_t key_code;          /* FUJI_KEY_*, the last key that changed */
    uint32_t x;
    uint32_t key_status;        /* FUJI_KEY_UP when released; ? the other values */
    int32_t gyro, accel;
    uint32_t a, b, c;
};
enum
{
    FUJI_KEY_OK = 0x01, FUJI_KEY_UP = 0x02, FUJI_KEY_DOWN = 0x03,
    FUJI_KEY_LEFT = 0x04, FUJI_KEY_RIGHT = 0x05, FUJI_KEY_POWER = 0x06,
    FUJI_KEY_HALF = 0x07,       /* the shutter, half-way (S1) */
    FUJI_KEY_FULL = 0x08,       /* and all the way (S2) */
    FUJI_KEY_DISPBACK = 0x09, FUJI_KEY_PLAY = 0x0b,
    /* "may differ across devices" (FujiHack) */
    FUJI_KEY_FN = 0x2f, FUJI_KEY_Q = 0x32, FUJI_KEY_REC = 0x34, FUJI_KEY_EFN = 0x36,
    FUJI_KEY_DIAL = 0x3a,       /* ? the command dial: one code, the direction in x or key_status */
};
#define FUJI_KEY_RELEASED 0x80  /* ? key_status of a key let go (FujiHack leaves on DISP/BACK's 0x80) */

/* ---- the screen: three 32-bit layers (RGBA, A in the low byte) at the
 * addresses in MEM_OPENGL_BUFFERS; FujiHack draws into all three, as which
 * one is on show isn't known yet */
#define FUJI_LAYERS 3

/* ---- time and tasks */
int  fuji_task_sleep(int ms);

/* ---- files: DOS paths ("C:\\DCIM\\..."); every call reports through the
 * handler, and fuji_file_wait / fuji_file_reset go round each one */
typedef void (*fuji_file_handler)(int error, int id, int a, int b);
#define FUJI_OK      0
#define FUJI_EOF     14
#define FUJI_READ    0
#define FUJI_WRITE   1
#define FUJI_SEEK_SET 0
struct fuji_stats
{
    char filename[0x30];
    uint32_t a, size, b;
    char created[0x48], modified[0x48];
};
int  fuji_fopen(fuji_file_handler h, const char *path, int flag);   /* a file id, counting up */
int  fuji_fread(fuji_file_handler h, int fp, int n, void *data);
int  fuji_fwrite(fuji_file_handler h, int fp, int n, const void *data);
int  fuji_fseek(fuji_file_handler h, int fp, int pos, int a, int whence);
int  fuji_fclose(fuji_file_handler h, int fp, int x, int y);
int  fuji_fstats(int fp, struct fuji_stats *s, int fp2);
void fuji_file_wait();
void fuji_file_reset();
char fuji_drive();              /* the card's letter */
/* ? one listing at a time, no handle: found by what refers to "*.*" */
int  fuji_dir_open(char *first, char *second, char *buffer);
int  fuji_dir_next(char *buffer);

/* ---- memory: malloc and free (stdlib.h) are FujiHack's, through SQLite's
 * allocator: about 2 MB in all, against the EOS M's tens of MB */

#endif
