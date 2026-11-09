/* fos_dark: the darkroom.
 *
 * Rolls that have been shot and rewound wait here to be developed. The
 * camera develops them itself (fos_dev.c), a slice at a time, in a darkroom
 * under the red safelight: the latent image comes up on the paper in the
 * tray, then the print, and the prints made line up below. How big they are
 * developed is asked before it starts. The prints are looked at here as
 * well, each on its own palette, and looked into (a print developed medium
 * or large has a file to zoom in); PLAY comes here too: nothing undeveloped
 * is ever shown.
 */

#include "fos_ui.h"
#include "fos_dev.h"
#include <string.h>

#define MAX_ROLLS 48

/* The darkroom's lists live in memory taken while the film OS is up, not
 * in autoexec.bin: on the EOS M every byte of that is taken from Canon's
 * own memory at boot. */
static struct dark_mem
{
    struct fos_lab_roll rolls[MAX_ROLLS];
    uint8_t marked[MAX_ROLLS];
    int queue[MAX_ROLLS];
    struct fos_lab_frame frames[FOS_MAX_FRAMES], meta[FOS_MAX_FRAMES];
    char paths[FOS_MAX_FRAMES][64];
    struct fos_print print;
} *dm;
#define rolls   (dm->rolls)
#define marked  (dm->marked)
#define queue   (dm->queue)
#define pv_meta (dm->meta)
#define pv_print (dm->print)

static int nrolls;

static int dark_mem()
{
    if (!dm && (dm = fos_port_alloc(sizeof(*dm)))) memset(dm, 0, sizeof(*dm));
    return dm != 0;
}

void dark_free()
{
    fos_port_free(dm);
    dm = 0;
}

static void rescan()
{
    nrolls = dm ? fos_lab_scan(rolls, MAX_ROLLS) : 0;
}

static int roll_index(int number)
{
    for (int i = 0; i < nrolls; i++)
        if (rolls[i].number == number) return i;
    return -1;
}

/* developed: every frame has its print and the contact sheet is there;
 * waiting: shot, out of the camera, and a print or the sheet missing
 * (developing again skips the prints already made) */
/* developed: every frame printed, and every print in DCIM as a JPEG */
static int is_developed(const struct fos_lab_roll *r) { return r->sheet && r->developed >= r->shot && r->jpegs >= r->developed; }
/* Basic mode: a finished roll still in the camera waits too; developing it finishes it (fos_port_action) */
static int finished_in_camera(const struct fos_lab_roll *r) { return r->in_camera && !ui_realistic() && r->shot >= r->exposures; }
static int is_waiting(const struct fos_lab_roll *r)
{
    return !is_developed(r) && (!r->in_camera || finished_in_camera(r)) && r->shot > 0;
}
static int has_prints(const struct fos_lab_roll *r) { return r->sheet || r->developed > 0; }

/* about how long a frame takes at each print size: a guess, until one has
 * been developed at that size. The bigger print is finished pixel by pixel,
 * as the small one is, and has many more of them: counted in ARM
 * instructions (sim/tools/armcount.py), a medium print is about 2.4 times
 * the work of a small one and a large one 3.6 times. */
static int ms_per_frame[FOS_SIZES] = { 15000, 36000, 54000 };

static int cur_size()
{
    return fos_clamp(fos_port_get(FS_SIZE), 0, FOS_SIZES - 1);
}

static void format_eta(char *buf, int size, int frames, int per_ms, int extra_ms)
{
    int s = (int) (((int64_t) frames * per_ms + extra_ms) / 1000);
    if (s < 60) snprintf(buf, size, "under a minute");
    else if (s < 90 * 60) snprintf(buf, size, "about %d min", (s + 30) / 60);
    else snprintf(buf, size, "about %d h %02d min", s / 3600, (s % 3600 + 30) / 60);
}

static const char *short_date(const char *when)
{
    /* "2026-10-22 17:45" -> "22 Oct 2026" */
    static const char *const mon[12] = { "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec" };
    static char b[16];
    int m = (when[5] - '0') * 10 + (when[6] - '0');
    if (strlen(when) < 10 || m < 1 || m > 12) return "";
    char year[5];
    snprintf(b, sizeof(b), "%c%c %s %s", when[8] == '0' ? ' ' : when[8], when[9], mon[m - 1], fos_copy(year, sizeof(year), when, 4));
    return b[0] == ' ' ? b + 1 : b;
}

/* ================================================================ the list */

static int dk_sel;
static struct spring dk_hl, dk_scroll;
static int dk_hints_for = -1;           /* the hints show what SET does on this row */

/* Delete roll (LEFT, a roll out of the camera): which part, then sure? The
 * files go once the sheet is down, under a toast saying so. */
enum { DEL_NONE, DEL_WHICH, DEL_PRINTS, DEL_WHOLE,
       ASK_DEVELOP };                   /* the same sheet asks before developing: SET goes, INFO changes the print size */
static int dk_ask, dk_said;             /* the sheet up; what it said, while it goes down */
static int dk_doing;                    /* DEL_PRINTS or DEL_WHOLE: confirmed */
static struct spring dk_sheet;
static int dk_sheet_drawn;
static int dark_bake_due;

#define DK_X    24
#define DK_W    672
#define DK_Y    124
#define DK_ROW  60
#define DK_ROWS 5

static int count_waiting(int *frames)
{
    int n = 0, f = 0;
    for (int i = 0; i < nrolls; i++)
        if (is_waiting(&rolls[i])) { n++; f += rolls[i].shot - (rolls[i].jpegs < rolls[i].developed ? rolls[i].jpegs : rolls[i].developed); }
    if (frames) *frames = f;
    return n;
}

static int count_marked()
{
    int n = 0;
    for (int i = 0; i < nrolls; i++) n += marked[i] && is_waiting(&rolls[i]);
    return n;
}

static void dark_bake()
{
    ui_bg_plain();
    ui_to_bg(1);
    ui_status_bar("DARKROOM");
    fos_text(cv, &fos_font_lg, DK_X, 82, "Darkroom", C_TEXT, OPAQUE, 0);
    char b[96], eta[32];
    int frames, waiting = count_waiting(&frames);
    if (!nrolls)
        snprintf(b, sizeof(b), ui_realistic() ? "No rolls yet " T_MDASH " finish one, rewind it, and it waits here."
                                              : "No rolls yet " T_MDASH " finish one, and it waits here.");
    else if (waiting)
    {
        format_eta(eta, sizeof(eta), frames, ms_per_frame[cur_size()], 0);
        snprintf(b, sizeof(b), "%d roll%s to develop " T_DOT " %d frames " T_DOT " %s", waiting, waiting > 1 ? "s" : "", frames, eta);
    }
    else
        snprintf(b, sizeof(b), "Everything is developed " T_DOT " %d roll%s of prints", nrolls, nrolls > 1 ? "s" : "");
    int w = fos_text(cv, &fos_font_sm, DK_X, 106, b, C_TEXT3, OPAQUE, 0);
    /* the camera takes its time; a computer doesn't */
    if (waiting && w + 260 < DK_W)
        fos_text_r(cv, &fos_font_sm, DK_X + DK_W, 106, "Faster: Darkrooms on a computer", C_ACCENT2, OPAQUE, 0);
    ui_to_bg(0);
}

static void dark_hints()
{
    const struct fos_lab_roll *r = nrolls ? &rolls[dk_sel] : 0;
    int nm = count_marked();
    char dev[32];
    if (nm) snprintf(dev, sizeof(dev), "Develop %d", nm);
    else snprintf(dev, sizeof(dev), "Develop all");
    struct hint h[5];
    int n = 0;
    if (r && is_waiting(r)) h[n++] = (struct hint) { "SET", marked[dk_sel] ? "Unmark" : "Mark" };
    else if (r && has_prints(r)) h[n++] = (struct hint) { "SET", "Prints" };
    if (count_waiting(0)) h[n++] = (struct hint) { "INFO", dev };
    if (r && !r->in_camera) h[n++] = (struct hint) { "<", "Delete" };
    h[n++] = (struct hint) { "PLAY", "Prints" };
    h[n++] = (struct hint) { "MENU", "Back" };
    ui_bg_restore(0, HINTS_Y, FOS_W, FOS_H - HINTS_Y);
    ui_hints(h, n);
    dk_hints_for = dk_sel * 2 + marked[dk_sel];
}

void dark_enter(int arg)
{
    fos_port_roll(&ui_roll);
    dark_mem();
    rescan();
    if (dm) memset(marked, 0, sizeof(marked));
    int i = arg ? roll_index(arg) : -1;
    if (i < 0)
    {
        /* the newest roll waiting, else the newest */
        i = 0;
        for (int k = 0; k < nrolls; k++)
            if (is_waiting(&rolls[k])) { i = k; break; }
    }
    dk_sel = i;
    dk_hl.x = (float) dk_sel; dk_hl.v = 0;
    dk_scroll.x = (float) fos_clamp(dk_sel - DK_ROWS / 2, 0, nrolls > DK_ROWS ? nrolls - DK_ROWS : 0);
    dk_scroll.v = 0;
    dk_hints_for = -1;
    dk_ask = dk_doing = 0;
    dk_sheet.x = dk_sheet.v = 0;
    dk_sheet_drawn = 0;
    dark_bake();
}

void dark_queue_clear();
void dark_queue_add(int roll);

static void dark_develop()
{
    /* the marked rolls, or every one waiting; oldest first */
    int nm = count_marked();
    dark_queue_clear();
    for (int i = nrolls - 1; i >= 0; i--)
        if (is_waiting(&rolls[i]) && (!nm || marked[i]))
        {
            if (finished_in_camera(&rolls[i])) fos_port_action(FA_REWIND, 0, 0);    /* out of the camera first */
            dark_queue_add(rolls[i].number);
        }
    ui_go(SCR_DEVELOP, 0, GO_FADE);
}

void dark_key(int k)
{
    if (!dm)
    {
        if (k == FK_MENU) ui_go(SCR_HOME, HOME_DARK, GO_POP);
        return;
    }
    const struct fos_lab_roll *r = nrolls ? &rolls[dk_sel] : 0;
    if (dk_doing) return;
    if (dk_ask == ASK_DEVELOP)
    {
        if (k == FK_SET) { dk_ask = DEL_NONE; dark_develop(); return; }
        if (k == FK_MENU) dk_ask = DEL_NONE;
        else if (k == FK_INFO || k == FK_RIGHT || k == FK_WHEEL_R) fos_port_set(FS_SIZE, (cur_size() + 1) % FOS_SIZES);
        else if (k == FK_LEFT || k == FK_WHEEL_L) fos_port_set(FS_SIZE, (cur_size() + FOS_SIZES - 1) % FOS_SIZES);
        ui_damage_all();
        return;
    }
    if (dk_ask)
    {
        /* Delete roll: SET prints only (or, asked to be sure, yes), INFO the whole roll */
        if (k == FK_MENU) dk_ask = DEL_NONE;
        else if (dk_ask == DEL_WHICH && (k == FK_SET || k == FK_INFO)) dk_ask = k == FK_SET ? DEL_PRINTS : DEL_WHOLE;
        else if (dk_ask != DEL_WHICH && k == FK_SET)
        {
            dk_doing = dk_ask;
            dk_ask = DEL_NONE;
            ui_toast("Deleting" T_ELLIPSIS);
        }
        ui_damage_all();
        return;
    }
    switch (k)
    {
        case FK_UP: case FK_WHEEL_L:
            if (dk_sel > 0) dk_sel--;
            break;
        case FK_DOWN: case FK_WHEEL_R:
            if (dk_sel < nrolls - 1) dk_sel++;
            break;
        case FK_SET: case FK_RIGHT: case FK_LEFT:
            if (!r) break;
            /* LEFT: Delete roll, never the one in the camera */
            if (r->in_camera && (k == FK_LEFT || !finished_in_camera(r)))
                ui_toast(ui_realistic() ? "Still in the camera " T_MDASH " rewind it first"
                                        : "Still in the camera " T_MDASH " finish it on the Roll page first");
            else if (k == FK_LEFT) dk_ask = has_prints(r) || r->jpegs ? DEL_WHICH : DEL_WHOLE;   /* no prints: no choice */
            else if (is_waiting(r) && k == FK_SET) marked[dk_sel] ^= 1;
            else if (has_prints(r)) ui_go(SCR_PRINTS, r->number, GO_FADE);
            break;
        case FK_INFO:
            if (count_waiting(0)) dk_ask = ASK_DEVELOP;
            else ui_toast(nrolls ? "Nothing to develop" : "No rolls yet");
            break;
        case FK_PLAY:
            ui_go(SCR_PRINTS, r && has_prints(r) ? r->number : 0, GO_FADE);
            break;
        case FK_MENU:
            ui_go(SCR_HOME, HOME_DARK, GO_POP);
            break;
        case FK_HOME:
            ui_leave();
            break;
    }
    ui_damage(DK_Y - 4, FOS_H);
}

/* the confirmed Delete roll, with the sheet down and the toast up */
static void dark_delete()
{
    int left = fos_lab_delete(rolls[dk_sel].number, dk_doing == DEL_WHOLE, dm->frames);
    dk_doing = DEL_NONE;
    ui_toast(left ? "Not all of it could be deleted" : "Deleted");
    rescan();
    memset(marked, 0, sizeof(marked));
    if (dk_sel >= nrolls) dk_sel = nrolls > 0 ? nrolls - 1 : 0;
    dark_bake();
    ui_clobbered = 1;
}

int dark_update(int dt)
{
    int moving = 0;
    float top = (float) fos_clamp(dk_sel - DK_ROWS / 2, 0, nrolls > DK_ROWS ? nrolls - DK_ROWS : 0);
    moving |= spring_step(&dk_hl, (float) dk_sel, dt, 3.4f, 0.82f);
    moving |= spring_step(&dk_scroll, top, dt, 2.6f, 0.9f);
    if (moving) ui_damage(DK_Y - 4, DK_Y + DK_ROWS * DK_ROW + 4);
    if (dm && spring_step(&dk_sheet, dk_ask ? 1 : 0, dt, 3.0f, 0.95f)) { moving = 1; ui_damage_all(); }
    if (dk_doing && dk_sheet.x <= 0.002f) dark_delete();
    if (dk_ask == ASK_DEVELOP) dark_bake_due = 1;       /* the time on top follows the size chosen */
    else if (dark_bake_due && dk_sheet.x <= 0.002f) { dark_bake_due = 0; dark_bake(); ui_clobbered = 1; ui_damage_all(); moving = 1; }
    return moving;
}

/* a round mark: empty, or filled with a tick */
static void mark_dot(int cx, int cy, int on)
{
    if (on)
    {
        fos_disc(cv, cx * 256, cy * 256, 10 * 256, C_ACCENT, OPAQUE);
        fos_line(cv, (cx - 5) * 256, cy * 256, (cx - 1) * 256, (cy + 4) * 256, 2 * 256, FC(RAMP_GRAY, 12), OPAQUE);
        fos_line(cv, (cx - 1) * 256, (cy + 4) * 256, (cx + 6) * 256, (cy - 4) * 256, 2 * 256, FC(RAMP_GRAY, 12), OPAQUE);
    }
    else fos_ring(cv, cx * 256, cy * 256, 10 * 256, 2 * 256, FC(RAMP_GRAY, 90), OPAQUE);
}

static void dark_row(int i, int y)
{
    const struct fos_lab_roll *r = &rolls[i];
    int sel = i == dk_sel;
    int x = DK_X + 20;
    if (is_waiting(r)) mark_dot(x + 12, y + DK_ROW / 2, marked[i]);
    else ui_icon(r->in_camera ? ICON_FILM : ICON_PRINTS, x + 12, y + DK_ROW / 2, sel ? C_TEXT2 : C_TEXT3, OPAQUE);
    char b[96];
    fos_text(cv, &fos_font_mdb, x + 42, y + 27, fos_films[r->film].name, sel ? C_TEXT : C_TEXT2, OPAQUE, 0);
    const char *when = r->last[0] ? r->last : r->loaded;
    snprintf(b, sizeof(b), "Roll %03d " T_DOT " %d frame%s " T_DOT " %s", r->number, r->shot, r->shot == 1 ? "" : "s", short_date(when));
    fos_text(cv, &fos_font_sm, x + 42, y + 48, b, C_TEXT3, OPAQUE, 0);
    fcol c;
    if (r->in_camera && !finished_in_camera(r)) { snprintf(b, sizeof(b), "IN CAMERA"); c = C_TEXT3; }
    else if (is_developed(r)) { snprintf(b, sizeof(b), "DEVELOPED"); c = C_TEXT3; }
    else if (r->developed) { snprintf(b, sizeof(b), "%d OF %d DEVELOPED", r->developed, r->shot); c = C_ACCENT; }
    else { snprintf(b, sizeof(b), "TO DEVELOP"); c = C_ACCENT; }
    fos_text_r(cv, &fos_font_xs, DK_X + DK_W - 24, y + 36, b, c, OPAQUE, 48);
}

/* the Delete roll sheet */
static void dark_sheet()
{
    if (dk_ask) dk_said = dk_ask;
    const struct fos_lab_roll *r = &rolls[dk_sel];
    char t[48], b[96];
    if (dk_said == ASK_DEVELOP)
    {
        /* what will be developed, how big, how long it should take */
        static const char *const names[FOS_SIZES] = { "Small", "Medium", "Large" };
        static const char *const what[FOS_SIZES] = { "the screen's 720 " T_TIMES " 480", "a third of the sensor each way, zoom",
                                                     "half the sensor each way, more zoom" };
        char eta[32], alt[24];
        int nm = count_marked(), frames = 0, n = 0, size = cur_size(), exact;
        for (int i = 0; i < nrolls; i++)
            if (is_waiting(&rolls[i]) && (!nm || marked[i]))
            {
                n++;
                frames += rolls[i].shot - (rolls[i].jpegs < rolls[i].developed ? rolls[i].jpegs : rolls[i].developed);
            }
        format_eta(eta, sizeof(eta), frames, ms_per_frame[size], 0);
        if (fos_port_battery(&exact) <= 10) snprintf(t, sizeof(t), "The battery is low. Develop?");
        else snprintf(t, sizeof(t), "Develop %d roll%s?", n, n == 1 ? "" : "s");
        snprintf(b, sizeof(b), "%d frame%s " T_DOT " %s: %s " T_DOT " %s", frames, frames == 1 ? "" : "s", names[size], what[size], eta);
        snprintf(alt, sizeof(alt), "Size: %s", names[size]);
        ui_sheet3(dk_sheet.x, t, b, "Develop", alt, "Cancel");
        return;
    }
    int which = dk_said == DEL_WHICH, prints = dk_said == DEL_PRINTS;
    snprintf(t, sizeof(t), which ? "Delete roll %03d?" : prints ? "Delete its prints?" : "Delete all of roll %03d?", r->number);
    snprintf(b, sizeof(b), "Its %d frame%s, prints and log. They can't come back.", r->shot, r->shot == 1 ? "" : "s");
    /* which part: SET, INFO; then sure? SET */
    ui_sheet3(dk_sheet.x, t, which ? "Prints only keeps the RAW files and the log." : prints ? "Its JPEGs in DCIM go too." : b,
              which ? "Prints only" : "Delete", which ? "Whole roll" : 0, which ? "Cancel" : "Keep");
}

void dark_draw()
{
    int sheet = dk_sheet.x > 0.002f;
    if (ui_clobbered || sheet || dk_sheet_drawn)
    {
        ui_clobbered = 0;
        ui_bg_restore(0, 0, FOS_W, FOS_H);
        ui_damage_all();
        dk_hints_for = -1;
    }
    dk_sheet_drawn = sheet;
    if (!dm)
    {
        fos_text_c(cv, &fos_font_md, 360, DK_Y + 120, "Not enough memory for the darkroom.", C_TEXT3, OPAQUE, 0);
        return;
    }
    if (dk_hints_for != dk_sel * 2 + marked[dk_sel]) dark_hints();

    int y0 = DK_Y - 4, y1 = DK_Y + DK_ROWS * DK_ROW + 4;
    struct fos_canvas save = *cv;
    ui_bg_restore(0, y0, FOS_W, y1 - y0);
    fos_clip(cv, 0, DK_Y, FOS_W, DK_Y + DK_ROWS * DK_ROW);
    if (!nrolls)
    {
        fos_text_c(cv, &fos_font_md, 360, DK_Y + 120, ui_realistic() ? "Shot rolls appear here once they are rewound." : "Shot rolls appear here once they are finished.", C_TEXT3, OPAQUE, 0);
        *cv = save;
        return;
    }
    float top = dk_scroll.x;
    int hy = DK_Y + (int) ((dk_hl.x - top) * DK_ROW + 0.5f);
    fos_rrect(cv, DK_X, hy, DK_W, DK_ROW, 12, FC(RAMP_GRAY, 27), OPAQUE);
    fos_rrect(cv, DK_X, hy + 10, 3, DK_ROW - 20, 1, C_ACCENT, OPAQUE);
    for (int i = (int) top; i < nrolls && i <= (int) top + DK_ROWS; i++)
        dark_row(i, DK_Y + (int) ((i - top) * DK_ROW + 0.5f));
    *cv = save;
    /* the list goes on: a hint at the edge */
    if (top > 0.05f) fos_tri(cv, DK_X + DK_W - 14, DK_Y - 8, 8, 3, C_TEXT3, OPAQUE);
    if (top < nrolls - DK_ROWS - 0.05f) fos_tri(cv, DK_X + DK_W - 14, DK_Y + DK_ROWS * DK_ROW + 6, 8, 1, C_TEXT3, OPAQUE);
    ui_damage(y0, y1 + 8);
    if (dk_sheet_drawn) dark_sheet();
}

/* ================================================================ developing */

/* The scene, under the safelight: the tray with the paper in it on the left,
 * the roll and how far along it is on the right, the prints made so far in
 * a row along the bottom. Nothing in it moves by itself: the paper shows the
 * latent image as the RAW is read, then the print, and the screen is drawn
 * again only when one of those changes. The camera has one processor, and
 * every frame of an animation here was time the developing didn't get. */
#define SL(level)       FC(RAMP_RED, level)
#define SL_TEXT         SL(222)
#define SL_TEXT2        SL(160)
#define SL_TEXT3        SL(104)
#define SL_ACCENT       FC(RAMP_ORANGE, 200)

/* the tray, the paper in it and the picture on the paper */
#define TRAY_X   24
#define TRAY_Y   60
#define TRAY_W   400
#define TRAY_H   284
#define BATH_X   (TRAY_X + 12)
#define BATH_Y   (TRAY_Y + 12)
#define BATH_W   (TRAY_W - 24)
#define BATH_H   (TRAY_H - 24)
#define PAPER_W  348
#define PAPER_H  240
#define PAPER_X  (TRAY_X + (TRAY_W - PAPER_W) / 2)
#define PAPER_Y  (TRAY_Y + (TRAY_H - PAPER_H) / 2)
#define IMG_W    324
#define IMG_H    216
#define IMG_X    (PAPER_X + (PAPER_W - IMG_W) / 2)
#define IMG_Y    (PAPER_Y + (PAPER_H - IMG_H) / 2)
#define GHOST_W  (IMG_W / 2)
#define GHOST_H  (IMG_H / 2)
#define PAPER_LV 124                    /* white paper under the safelight */
#define BLACK_LV 9

/* the prints made, newest on the left */
#define DRY_Y    368
#define DRY_W    60
#define DRY_H    40
#define DRY_STEP 68
#define DRY_X0   26
#define DRY_N    10

/* the panel */
#define PANEL_X  444
#define PANEL_W  252
#define PANEL_CX (PANEL_X + PANEL_W / 2)
#define BAR_Y    250

#define WORK_MS  300                    /* developing between two looks at the buttons */
#define GHOST_MS 2000                   /* the latent image is read again this often */
#define HOLD_MS  1500                   /* a finished print stays on the paper at least this long */

static int nqueue, qi;
static char dcim_dir[128];              /* the roll's JPEG folder, or "" */
static int nframes, fi, roll_ready;
static int cur_roll, cur_film, cur_frame;
static struct fos_dev *dev;
static int frame_t0;
static int total_frames, done_frames, failed_frames, rolls_done;
static int jpeg_frames;                 /* of the failed ones, shot as JPEG */
static int finished, asking_stop;
static struct spring stop_sheet;
static int dv_size;                     /* FOS_SIZE_* asked for */
static int dv_made, dv_w, dv_h;         /* what the frame in the tray comes to (-1: not known yet) */
static int dv_dimmed;                   /* the screen's backlight is down (INFO) */

/* what the paper shows: the latent image of the frame being read, or the
 * print just made */
static int tray_print, tray_t;
static uint8_t *ghost;                  /* GHOST_W x GHOST_H: the latent image */
static uint8_t *img;                    /* IMG_W x IMG_H: the finished print */
static int ghost_t;                     /* ms since the latent image was read */
static int ghost_final;                 /* read once more when the RAW is through */
static uint8_t *dry;                    /* DRY_N x DRY_W x DRY_H */
static int ndry;

/* what the next frame draws again */
enum { DV_TRAY = 1, DV_ROW = 2, DV_PANEL = 4, DV_BAR = 8, DV_HINTS = 16 };
static int dv_dirty;
static int bar_drawn, last_doing = -1, panel_t;
static char eta_drawn[64];
static char last_error[72];             /* why the last frame that failed did */

void dark_queue_clear() { nqueue = 0; }
void dark_queue_add(int roll) { if (dark_mem() && nqueue < MAX_ROLLS) queue[nqueue++] = roll; }

static int file_exists(const char *path)
{
    void *f = fos_port_open(path, 0);
    if (f) fos_port_close(f);
    return f != 0;
}

/* the print's picture, small and grey, for the tray */
static void load_tray_image(const char *path)
{
    struct fos_print p;
    memset(img, 255, IMG_W * IMG_H);
    if (!fos_print_load(path, &p)) return;
    uint8_t lum[FOS_PRINT_COLOURS + 1];
    lum[0] = 0;
    for (int i = 0; i < FOS_PRINT_COLOURS; i++)
        lum[i + 1] = (uint8_t) ((p.pal[i][0] * 77 + p.pal[i][1] * 150 + p.pal[i][2] * 29) >> 8);
    for (int y = 0; y < IMG_H; y++)
    {
        int sy = (2 * y + 1) * FOS_PRINT_H / (2 * IMG_H);
        for (int x = 0; x < IMG_W; x++)
        {
            int sx = (2 * x + 1) * FOS_PRINT_W / (2 * IMG_W);
            /* the borders of a portrait frame stay white paper */
            if (sx < p.x0 || sx >= p.x0 + p.w) continue;
            const uint8_t *s = p.px + sy * FOS_PRINT_W + sx;
            int k0 = s[0], k1 = s[1], k2 = s[FOS_PRINT_W], k3 = s[FOS_PRINT_W + 1];
            img[y * IMG_W + x] = (uint8_t) ((lum[k0 > 240 ? 0 : k0] + lum[k1 > 240 ? 0 : k1] + lum[k2 > 240 ? 0 : k2]
                                             + lum[k3 > 240 ? 0 : k3]) >> 2);
        }
    }
    fos_print_free(&p);
}

/* a finished frame's thumbnail to the front of the row; a portrait frame's
 * sides are white paper */
static void hang(const uint8_t *thumb, int x0, int w)
{
    if (!dry || !thumb) return;
    memmove(dry + DRY_W * DRY_H, dry, (DRY_N - 1) * DRY_W * DRY_H);
    for (int y = 0; y < DRY_H; y++)
        for (int x = 0; x < DRY_W; x++)
        {
            int px = (2 * x + 1) * FOS_PRINT_W / (2 * DRY_W);
            const uint8_t *s = thumb + 3 * ((y * FOS_THUMB_H / DRY_H) * FOS_THUMB_W + x * FOS_THUMB_W / DRY_W);
            dry[y * DRY_W + x] = px < x0 || px >= x0 + w ? 255 : (uint8_t) ((s[0] * 77 + s[1] * 150 + s[2] * 29) >> 8);
        }
    if (ndry < DRY_N) ndry++;
    dv_dirty |= DV_ROW;
}

/* the next frame to develop, or the next roll's; the contact sheet when a
 * roll is through */
static void next_job()
{
    char path[64];
    while (qi < nqueue)
    {
        if (!roll_ready)
        {
            cur_roll = queue[qi];
            int ri = roll_index(cur_roll);
            cur_film = ri >= 0 ? rolls[ri].film : 0;
            nframes = fos_lab_frames(cur_roll, dm->frames, FOS_MAX_FRAMES);
            {
                char msg[96];
                int raws = 0;
                for (int i = 0; i < nframes; i++) raws += !dm->frames[i].missing;
                snprintf(msg, sizeof(msg), "darkroom: roll %03d (%s): %d frames, %d RAW files", cur_roll,
                         fos_films[cur_film].key, nframes, raws);
                fos_port_log(msg);
            }
            fos_lab_prepare(cur_roll);
            /* the roll's JPEGs go in DCIM, in a folder named for the day
             * its first frame was shot and the film */
            const char *first = 0;
            for (int i = 0; i < nframes; i++)
                if (dm->frames[i].when[0] && (!first || strcmp(dm->frames[i].when, first) < 0)) first = dm->frames[i].when;
            if (fos_lab_dcim_dir(dcim_dir, sizeof(dcim_dir), cur_roll, cur_film, first) < 0)
            {
                dcim_dir[0] = 0;
                fos_port_log("darkroom: no folder for the JPEGs in DCIM");
            }
            else
            {
                char msg[160];
                snprintf(msg, sizeof(msg), "darkroom: JPEGs in %s", dcim_dir);
                fos_port_log(msg);
            }
            fi = 0;
            roll_ready = 1;
            dv_dirty |= DV_PANEL;
        }
        while (fi < nframes)
        {
            const struct fos_lab_frame *f = &dm->frames[fi++];
            fos_lab_print_path(path, sizeof(path), cur_roll, f->no);
            /* its JPEG in DCIM: IMG_0102.CR2 -> IMG_0102.JPG */
            char jpeg[160] = "";
            if (dcim_dir[0])
            {
                const char *base = strrchr(f->cr2, '/');
                char name[9];
                snprintf(jpeg, sizeof(jpeg), "%s/%s.JPG", dcim_dir, fos_copy(name, sizeof(name), base ? base + 1 : f->cr2, 8));
            }
            /* developed before (and, by this version, written to DCIM too) */
            if (file_exists(path) && (!jpeg[0] || f->missing || file_exists(jpeg))) continue;
            if (f->missing)
            {
                char msg[120];
                const char *base = strrchr(f->cr2, '/');
                base = base ? base + 1 : f->cr2;
                snprintf(msg, sizeof(msg), "darkroom: roll %03d frame %d: %s %s", cur_roll, f->no,
                         f->jpeg ? "shot as JPEG, no RAW:" : "no RAW file", f->cr2);
                fos_port_log(msg);
                /* the panel shows it on two lines, split at the dash */
                if (f->jpeg)
                {
                    jpeg_frames++;
                    if (jpeg_frames == 1)
                        snprintf(last_error, sizeof(last_error), "%.8s was shot as JPEG " T_MDASH " set Image quality to RAW", base);
                    else
                        snprintf(last_error, sizeof(last_error), "%d frames were shot as JPEG " T_MDASH " set Image quality to RAW",
                                 jpeg_frames);
                }
                else if (!jpeg_frames)
                {
                    if (f->cr2[0])
                        snprintf(last_error, sizeof(last_error), "%s isn't on the card " T_MDASH " was it deleted?", base);
                    else
                        snprintf(last_error, sizeof(last_error), "No RAW file " T_MDASH " shoot with Image quality RAW");
                }
                failed_frames++;
                done_frames++;
                continue;
            }
            cur_frame = f->no;
            dev = fos_dev_start(f->cr2, path, cur_film, f->no, f->when, f->fstop);
            if (dev && jpeg[0]) fos_dev_jpeg(dev, jpeg);
            if (dev && dv_size > FOS_SIZE_S)
            {
                /* the bigger print: the JPEG at that size, and a file to zoom into beside the print */
                char zoom[64];
                fos_lab_zoom_path(zoom, sizeof(zoom), cur_roll, f->no);
                fos_dev_big(dev, dv_size, zoom);
            }
            if (dev && fos_port_get(FS_STAMP)) fos_dev_stamp(dev, 1);
            frame_t0 = ui_now;
            ghost_t = 100000;
            ghost_final = 0;
            dv_made = -1;
            memset(ghost, 255, GHOST_W * GHOST_H);      /* fresh paper */
            dv_dirty |= DV_PANEL;
            if (dev) return;
            snprintf(last_error, sizeof(last_error), "Not enough memory");
            failed_frames++;
            done_frames++;
        }
        /* the roll is through: its contact sheet */
        const char *pp[FOS_MAX_FRAMES];
        for (int i = 0; i < nframes; i++)
        {
            fos_lab_print_path(dm->paths[i], sizeof(dm->paths[i]), cur_roll, i + 1);
            pp[i] = dm->paths[i];
        }
        fos_lab_print_path(path, sizeof(path), cur_roll, 0);
        if (!fos_dev_sheet(path, cur_film, pp, nframes)) fos_port_log("darkroom: can't write the contact sheet");
        rolls_done++;
        qi++;
        roll_ready = 0;
    }
    finished = 1;
    cur_frame = 0;
    dv_dirty |= DV_PANEL | DV_BAR | DV_HINTS | DV_TRAY;
    fos_dev_release();
    fos_port_action(FA_BUSY, 0, 0);
    if (dv_dimmed) { dv_dimmed = 0; fos_port_action(FA_DIM, 0, 0); }
}

static void frame_finished(int ok)
{
    char msg[160];
    int took = ui_now - frame_t0;
    if (ok)
    {
        /* a running mean for the size it was made at, the first frames counting fully */
        int size = fos_clamp(dv_made, 0, FOS_SIZES - 1);
        ms_per_frame[size] = done_frames - failed_frames < 3 ? took : (ms_per_frame[size] * 3 + took) / 4;
        snprintf(msg, sizeof(msg), "darkroom: roll %03d frame %d developed in %d ms, %d x %d", cur_roll, cur_frame, took, dv_w, dv_h);
        fos_port_log(msg);
        /* onto the paper, and into the row */
        char path[64];
        fos_lab_print_path(path, sizeof(path), cur_roll, cur_frame);
        load_tray_image(path);
        tray_print = 1;
        tray_t = 0;
        int x0, w;
        fos_dev_picture(dev, &x0, &w);
        hang(fos_dev_thumb(dev), x0, w);
        dv_dirty |= DV_TRAY;
    }
    else
    {
        const char *why = fos_dev_error(dev) && fos_dev_error(dev)[0] ? fos_dev_error(dev) : "stopped without a reason";
        snprintf(msg, sizeof(msg), "darkroom: roll %03d frame %d: %s", cur_roll, cur_frame, why);
        fos_port_log(msg);
        snprintf(last_error, sizeof(last_error), "Frame %d: %s", cur_frame, why);
        failed_frames++;
    }
    done_frames++;
    fos_dev_free(dev);
    dev = 0;
    dv_dirty |= DV_PANEL | DV_BAR;
}

/* the battery in the room's own light: the cell, and the percentage where
 * the camera knows it */
static void room_battery()
{
    int exact = 0, pct = fos_port_battery(&exact);
    if (pct < 0) return;
    int x = FOS_W - 24 - 25, y = 15;
    fcol c = pct <= 10 ? SL_ACCENT : SL(pct <= 30 ? 190 : 130);
    fos_rrect_line(cv, x, y, 22, 12, 3, 1, SL(96), OPAQUE);
    fos_fill(cv, x + 22, y + 4, 2, 4, SL(96));
    int w = pct <= 0 ? 0 : 2 + pct * 16 / 100;
    if (w) fos_rrect(cv, x + 2, y + 2, w, 8, 1, c, OPAQUE);
    if (exact)
    {
        char b[16];
        snprintf(b, sizeof(b), "%d%%", pct);
        fos_text_r(cv, &fos_font_xs, x - 6, y + 11, b, pct <= 30 ? c : SL_TEXT3, OPAQUE, 16);
    }
}

static void develop_bake()
{
    ui_to_bg(1);
    /* the room: dark, the safelight from above */
    fos_vgrad(cv, 0, 0, FOS_W, FOS_H, RAMP_RED, LV12(30), LV12(7));
    fos_text(cv, &fos_font_xs, 24, 26, "DARKROOM", SL_TEXT2, OPAQUE, 64);
    room_battery();
    /* the tray and the developer in it */
    fos_rrect(cv, TRAY_X, TRAY_Y, TRAY_W, TRAY_H, 16, SL(26), OPAQUE);
    fos_rrect_line(cv, TRAY_X, TRAY_Y, TRAY_W, TRAY_H, 16, 2, SL(48), OPAQUE);
    fos_rrect(cv, BATH_X, BATH_Y, BATH_W, BATH_H, 10, SL(15), OPAQUE);
    /* where the prints go */
    for (int i = 0; i < DRY_N; i++)
        fos_rrect_line(cv, DRY_X0 + i * DRY_STEP - 3, DRY_Y - 3, DRY_W + 6, DRY_H + 6, 2, 1, SL(30), OPAQUE);
    ui_to_bg(0);
}

void develop_enter(int arg)
{
    if (!dark_mem()) nqueue = 0;
    rescan();
    total_frames = done_frames = failed_frames = rolls_done = 0;
    jpeg_frames = 0;
    for (int i = 0; i < nqueue; i++)
    {
        int ri = roll_index(queue[i]);
        if (ri >= 0) total_frames += rolls[ri].shot - rolls[ri].developed;
    }
    qi = 0; roll_ready = 0; dev = 0;
    last_error[0] = 0;
    finished = nqueue == 0;
    asking_stop = 0;
    stop_sheet.x = stop_sheet.v = 0;
    cur_frame = 0;
    dv_size = fos_clamp(fos_port_get(FS_SIZE), 0, FOS_SIZES - 1);
    dv_made = -1;
    dv_dimmed = 0;
    tray_print = 0; tray_t = 0;
    ndry = 0;
    ghost = fos_port_alloc(GHOST_W * GHOST_H);
    img = fos_port_alloc(IMG_W * IMG_H);
    dry = fos_port_alloc(DRY_N * DRY_W * DRY_H);
    if (ghost) memset(ghost, 255, GHOST_W * GHOST_H);
    dv_dirty = ~0;
    bar_drawn = -1;
    last_doing = -1;
    panel_t = 0;
    eta_drawn[0] = 0;
    char dir[64];
    fos_lab_cache_dir(dir, sizeof(dir));
    fos_dev_cache(dir);
    if (!finished) fos_port_action(FA_BUSY, 1, 0);
    develop_bake();
}

void develop_leave()
{
    if (dev) { fos_dev_free(dev); dev = 0; }
    if (!finished) fos_port_action(FA_BUSY, 0, 0);
    if (dv_dimmed) { dv_dimmed = 0; fos_port_action(FA_DIM, 0, 0); }
    finished = 1;
    fos_dev_release();
    fos_port_free(ghost); ghost = 0;
    fos_port_free(img); img = 0;
    fos_port_free(dry); dry = 0;
}

void develop_key(int k)
{
    /* with the screen dimmed, the first button only brings it back */
    if (dv_dimmed)
    {
        dv_dimmed = 0;
        fos_port_action(FA_DIM, 0, 0);
        dv_dirty |= DV_HINTS;
        return;
    }
    if (asking_stop)
    {
        if (k == FK_SET) { asking_stop = 0; ui_go(SCR_DARK, cur_roll, GO_FADE); }
        else if (k == FK_MENU) asking_stop = 0;
        ui_clobbered = 1;
        return;
    }
    switch (k)
    {
        case FK_MENU:
            if (finished) ui_go(SCR_DARK, cur_roll, GO_FADE);
            else asking_stop = 1;
            ui_clobbered = 1;
            break;
        case FK_INFO:
            if (finished) break;
            dv_dimmed = 1;
            fos_port_action(FA_DIM, 1, 0);
            dv_dirty |= DV_HINTS;
            break;
        case FK_SET: case FK_PLAY:
            if (finished) ui_go(SCR_PRINTS, nqueue ? queue[0] : 0, GO_FADE);
            break;
        case FK_HOME:
            ui_leave();
            break;
    }
}

int develop_update(int dt)
{
    if (!ghost || !img || !dry || !dm)
    {
        /* no memory for the scene: say so and stop */
        if (!finished) { finished = 1; fos_port_action(FA_BUSY, 0, 0); ui_toast("Not enough memory to develop"); }
        return 0;
    }
    int moving = spring_step(&stop_sheet, asking_stop ? 1 : 0, dt, 3.0f, 0.95f);
    if (moving) ui_clobbered = 1;
    tray_t += dt;
    ghost_t += dt;
    panel_t += dt;
    /* the work: only once the screen has settled, and not while asking */
    if (!finished && !asking_stop && ui_settled() && stop_sheet.x < 0.002f)
    {
        if (!dev) next_job();
        if (dev)
        {
            int p = fos_dev_step(dev, WORK_MS);
            if (dv_made < 0 && p > 0)
            {
                /* the size it comes to: the one asked for, or what the camera had the memory for */
                dv_made = fos_dev_made(dev, &dv_w, &dv_h);
                if (dv_made < dv_size)
                {
                    char msg[64];
                    snprintf(msg, sizeof(msg), "Not enough memory for %s prints: %s", dv_size == FOS_SIZE_L ? "large" : "medium",
                             dv_made == FOS_SIZE_M ? "medium" : "small");
                    ui_toast(msg);
                    dv_size = dv_made;                  /* said once: the rest of the roll the same */
                }
                dv_dirty |= DV_PANEL;
            }
            /* the latent image on the paper, once the print before it has been seen */
            int show = !tray_print || tray_t > HOLD_MS;
            if (p >= 0 && p < 1000 && !ghost_final && fos_dev_doing(dev) == FOS_DEV_FIXING)
            {
                /* the whole of it, while it can still be read */
                ghost_final = 1;
                if (fos_dev_preview(dev, ghost, GHOST_W, GHOST_H) && show) { tray_print = 0; dv_dirty |= DV_TRAY; }
            }
            else if (p >= 0 && p < 1000 && show && ghost_t > GHOST_MS && fos_dev_preview(dev, ghost, GHOST_W, GHOST_H))
            {
                ghost_t = 0;
                tray_print = 0;
                dv_dirty |= DV_TRAY;
            }
            if (p >= 1000) frame_finished(1);
            else if (p < 0) frame_finished(0);
        }
        return 1;           /* straight back to the work */
    }
    return moving || dv_dirty;
}

/* grey levels (paper 255 .. black 0) at density k/256 of their own, as
 * dithered positions on the red ramp */
static void density_table(int16_t *pos, int k)
{
    for (int l = 0; l < 256; l++)
    {
        int d = (255 - l) * k >> 8;                     /* density 0..255 */
        int lv = LV12(PAPER_LV) - (LV12(PAPER_LV) - LV12(BLACK_LV)) * d / 255;
        pos[l] = (int16_t) fos_ramp_pos(RAMP_RED, lv);
    }
}

/* w x h grey pixels (every one twice each way if half) onto the canvas at x, y */
static void room_image(const uint8_t *src, int sw, int half, int x, int y, int w, int h, const int16_t *pos)
{
    const int base = fos_ramp_base[RAMP_RED], last = fos_ramp_last[RAMP_RED];
    for (int j = 0; j < h; j++)
    {
        const uint8_t *s = src + (half ? j >> 1 : j) * sw;
        uint8_t *o = &cv->px[(y + j) * cv->pitch + x];
        const uint8_t *bay = fos_bayer[(y + j) & 3];
        for (int i = 0; i < w; i++)
        {
            int p = (pos[s[half ? i >> 1 : i]] + bay[i & 3]) >> 4;
            o[i] = (uint8_t) (base + (p > last ? last : p));
        }
    }
}

/* the paper in the bath, and what is on it: the latent image, faint, or the print */
static void draw_tray()
{
    ui_bg_restore(BATH_X, BATH_Y, BATH_W, BATH_H);
    ui_damage(BATH_Y, BATH_Y + BATH_H);
    if (finished && !tray_print) return;        /* nothing left to develop: the bath alone */
    fos_rrect(cv, PAPER_X + 3, PAPER_Y + 4, PAPER_W, PAPER_H, 3, SL(10), 160);
    fos_fill(cv, PAPER_X, PAPER_Y, PAPER_W, PAPER_H, SL(PAPER_LV));
    int16_t pos[256];
    density_table(pos, tray_print ? 256 : 90);
    if (tray_print) room_image(img, IMG_W, 0, IMG_X, IMG_Y, IMG_W, IMG_H, pos);
    else room_image(ghost, GHOST_W, 1, IMG_X, IMG_Y, IMG_W, IMG_H, pos);
}

/* the prints made so far, newest on the left */
static void draw_row()
{
    int16_t pos[256];
    density_table(pos, 256);
    for (int i = 0; i < ndry; i++)
    {
        int x = DRY_X0 + i * DRY_STEP;
        fos_fill(cv, x - 3, DRY_Y - 3, DRY_W + 6, DRY_H + 6, SL(PAPER_LV));
        room_image(dry + i * DRY_W * DRY_H, DRY_W, 0, x, DRY_Y, DRY_W, DRY_H, pos);
    }
    ui_damage(DRY_Y - 4, DRY_Y + DRY_H + 4);
}

static const char *stage_name()
{
    switch (fos_dev_doing(dev))
    {
        case FOS_DEV_MIXING:     return "Mixing the chemistry";
        case FOS_DEV_DEVELOPING: return "Exposing the paper";
        case FOS_DEV_FIXING:     return "Developer";
        case FOS_DEV_DRYING:     return "Fixer " T_DOT " wash";
        case FOS_DEV_ENLARGING:  return "Enlarging";
    }
    return "";
}

/* s centred at cx, on two lines if it is wider than w: split at its dash
 * (" - "), or else at the last space that fits */
static void text_lines_c(const struct fos_font *f, int cx, int y, int dy, int w, const char *s, fcol c)
{
    if (fos_text_w(f, s, 0) <= w)
    {
        fos_text_c(cv, f, cx, y, s, c, OPAQUE, 0);
        return;
    }
    char a[96], b[96];
    const char *dash = strstr(s, " " T_MDASH " ");
    int cut = -1, next = -1;
    if (dash)
    {
        cut = (int) (dash - s);
        next = cut + (int) strlen(" " T_MDASH " ");
        snprintf(a, sizeof(a), "%.*s", cut, s);
        if (fos_text_w(f, a, 0) > w) cut = -1;
    }
    if (cut < 0)
        for (int i = (int) strlen(s) - 1; i > 0; i--)
        {
            if (s[i] != ' ') continue;
            snprintf(a, sizeof(a), "%.*s", i, s);
            if (fos_text_w(f, a, 0) <= w) { cut = i; next = i + 1; break; }
        }
    if (cut < 0)
    {
        fos_text_c(cv, f, cx, y, s, c, OPAQUE, 0);
        return;
    }
    snprintf(a, sizeof(a), "%.*s", cut, s);
    snprintf(b, sizeof(b), "%s", s + next);
    if (b[0] >= 'a' && b[0] <= 'z') b[0] += 'A' - 'a';      /* a sentence of its own */
    fos_text_c(cv, f, cx, y, a, c, OPAQUE, 0);
    fos_text_c(cv, f, cx, y + dy, b, c, OPAQUE, 0);
}

/* how long is left, as the panel says it */
static void develop_eta(char *buf, int size)
{
    int left = total_frames - done_frames;
    int per = ms_per_frame[fos_clamp(dv_made >= 0 ? dv_made : dv_size, 0, FOS_SIZES - 1)];
    int spent = dev ? ui_now - frame_t0 : 0;
    char eta[32];
    format_eta(eta, sizeof(eta), left, per, -(spent < per ? spent : per));
    snprintf(buf, size, "%d to go " T_DOT " %s", left, eta);
}

/* the job as a whole along the bar, in pixels of its width */
static int bar_now()
{
    const int w = PANEL_W - 24;
    if (finished) return w;
    int p = dev ? fos_dev_progress(dev) : 0;
    if (p < 0) p = 0;
    return total_frames > 0 ? (int) (((int64_t) done_frames * 1000 + p) * w / ((int64_t) total_frames * 1000)) : 0;
}

static void draw_bar()
{
    const int x = PANEL_X + 12, w = PANEL_W - 24;
    ui_bg_restore(x - 2, BAR_Y - 2, w + 4, 12);
    fos_rrect(cv, x, BAR_Y, w, 8, 4, SL(22), OPAQUE);
    bar_drawn = fos_clamp(bar_now(), 0, w);
    if (bar_drawn > 3) fos_rrect(cv, x, BAR_Y, bar_drawn, 8, 4, SL_ACCENT, OPAQUE);
    ui_damage(BAR_Y - 2, BAR_Y + 10);
}

static void draw_panel()
{
    char b[96];
    ui_bg_restore(PANEL_X, 64, PANEL_W, BAR_Y - 68);
    ui_bg_restore(PANEL_X, BAR_Y + 14, PANEL_W, DRY_Y - 8 - BAR_Y - 14);
    if (finished)
    {
        fos_text_c(cv, &fos_font_xs, PANEL_CX, 104, "DONE", SL_ACCENT, OPAQUE, 64);
        snprintf(b, sizeof(b), "%d roll%s", rolls_done, rolls_done == 1 ? "" : "s");
        fos_text_c(cv, &fos_font_lg, PANEL_CX, 140, b, SL_TEXT, OPAQUE, 0);
        snprintf(b, sizeof(b), "%d print%s", done_frames - failed_frames, done_frames - failed_frames == 1 ? "" : "s");
        fos_text_c(cv, &fos_font_sm, PANEL_CX, 166, b, SL_TEXT2, OPAQUE, 0);
        if (failed_frames)
        {
            snprintf(b, sizeof(b), "%d frame%s could not be developed", failed_frames, failed_frames == 1 ? "" : "s");
            fos_text_c(cv, &fos_font_sm, PANEL_CX, BAR_Y + 40, b, SL_TEXT2, OPAQUE, 0);
            text_lines_c(&fos_font_xs, PANEL_CX, BAR_Y + 62, 16, PANEL_W, last_error, SL_TEXT3);
        }
    }
    else
    {
        snprintf(b, sizeof(b), "ROLL %03d", cur_roll);
        fos_text_c(cv, &fos_font_xs, PANEL_CX, 104, b, SL_ACCENT, OPAQUE, 64);
        fos_text_c(cv, &fos_font_lg, PANEL_CX, 140, fos_films[cur_film].name, SL_TEXT, OPAQUE, 0);
        if (cur_frame) snprintf(b, sizeof(b), "Frame %d of %d", cur_frame, nframes);
        else b[0] = 0;
        fos_text_c(cv, &fos_font_md, PANEL_CX, 172, b, SL_TEXT2, OPAQUE, 0);
        /* the size of its print, once the camera has said what it can make */
        static const char *const names[FOS_SIZES] = { "SMALL", "MEDIUM", "LARGE" };
        if (dv_made >= 0) snprintf(b, sizeof(b), "%s " T_DOT " %d " T_TIMES " %d", names[fos_clamp(dv_made, 0, FOS_SIZES - 1)], dv_w, dv_h);
        else snprintf(b, sizeof(b), "%s", names[dv_size]);
        fos_text_c(cv, &fos_font_xs, PANEL_CX, 204, b, SL_TEXT3, OPAQUE, 40);
        fos_text_c(cv, &fos_font_md, PANEL_CX, BAR_Y + 44, dev ? stage_name() : "", SL_TEXT, OPAQUE, 0);
        develop_eta(eta_drawn, sizeof(eta_drawn));
        fos_text_c(cv, &fos_font_sm, PANEL_CX, BAR_Y + 68, eta_drawn, SL_TEXT3, OPAQUE, 0);
    }
    ui_damage(64, DRY_Y - 8);
}

static void develop_hints()
{
    ui_bg_restore(0, HINTS_Y - 8, FOS_W, FOS_H - HINTS_Y + 8);
    int base = HINTS_Y + 23, x = 24;
    if (finished)
    {
        x += ui_keycap(x, base, "SET") + 8;
        x += fos_text(cv, &fos_font_sm, x, base - 1, "See the prints", SL_TEXT2, OPAQUE, 0) + 22;
        x += ui_keycap(x, base, "MENU") + 8;
        fos_text(cv, &fos_font_sm, x, base - 1, "Darkroom", SL_TEXT2, OPAQUE, 0);
    }
    else
    {
        x += ui_keycap(x, base, "MENU") + 8;
        x += fos_text(cv, &fos_font_sm, x, base - 1, "Stop", SL_TEXT2, OPAQUE, 0) + 22;
        x += ui_keycap(x, base, "INFO") + 8;
        fos_text(cv, &fos_font_sm, x, base - 1, dv_dimmed ? "Any button: screen back" : "Dim the screen", SL_TEXT2, OPAQUE, 0);
        fos_text_r(cv, &fos_font_sm, FOS_W - 24, base - 1, "Keep the camera on", SL_TEXT3, OPAQUE, 0);
    }
    ui_damage(HINTS_Y - 8, FOS_H);
}

void develop_draw()
{
    if (ui_clobbered)
    {
        ui_clobbered = 0;
        ui_bg_restore(0, 0, FOS_W, FOS_H);
        ui_damage_all();
        dv_dirty = ~0;
    }
    /* the stage's name follows the work; the time left is looked at once a second */
    int doing = fos_dev_doing(dev);
    if (dev && doing != last_doing) { last_doing = doing; dv_dirty |= DV_PANEL; }
    if (!finished && panel_t > 1000)
    {
        char eta[64];
        panel_t = 0;
        develop_eta(eta, sizeof(eta));
        if (strcmp(eta, eta_drawn)) dv_dirty |= DV_PANEL;
    }
    if (bar_now() != bar_drawn) dv_dirty |= DV_BAR;
    int what = dv_dirty;
    dv_dirty = 0;
    if (what & DV_TRAY) draw_tray();
    if (what & DV_ROW) draw_row();
    if (what & DV_PANEL) draw_panel();
    if (what & DV_BAR) draw_bar();
    if (what & DV_HINTS) develop_hints();
    if (stop_sheet.x > 0.002f)
        ui_sheet(stop_sheet.x, "Stop developing?", "The prints made so far are kept; the rest wait in the darkroom.", "Stop", "Keep going");
}

/* ================================================================ the prints */

/* While a print is up the palette is the print's own: entries 1..240 its
 * colours, the overlay drawn with the fixed ones (PX_*). Changing what is
 * shown goes through black, so the screen never shows one picture in
 * another's colours. */

enum { PV_WAIT, PV_IN, PV_SHOW, PV_OUT, PV_NONE };
enum { NEXT_LOAD, NEXT_BACK };

static int pv_roll;                     /* index into rolls */
static int pv_alone;
static int pv_mode;                     /* 0 the contact sheet, 1 a frame */
static int pv_cur;                      /* the frame (1..), also the sheet's cursor */
static int pv_state, pv_t, pv_next;
static int pv_info, pv_info_t;
static int pv_frames;                   /* frames on the roll */
static int pv_have;                     /* pv_print holds a picture */
static int pv_dirty;                    /* the picture or the overlay changed */

#define FADE_MS 180
#define INFO_H  44

/* Looking into a print (a frame developed medium or large has a zoom file,
 * the picture at that size in the print's own palette): the wheel goes in
 * and out, the arrows move about. The part on the screen is read from the
 * card each time, so a print of any size takes no more memory than its
 * rows on show. */
static struct fos_zoom pv_zf;           /* the frame's zoom file, open while its print is up */
static int pv_zsteps[4], pv_znsteps;    /* the file's pixels to a screen pixel at each level in, widest first */
static int pv_zlevel;                   /* 0: the whole print; 1 .. pv_znsteps: into it */
static int pv_zx, pv_zy;                /* the middle of the view, in the file's pixels */
static uint8_t *pv_zrows;               /* the file's rows on show, as read */
static char pv_note[40];                /* said in the details bar, in place of the hints */

static void pv_zoom_close()
{
    fos_zoom_close(&pv_zf);
    fos_port_free(pv_zrows);
    pv_zrows = 0;
    pv_znsteps = pv_zlevel = 0;
}

/* the frame's zoom file, if it has one, and the levels it gives */
static void pv_zoom_open()
{
    char path[64];
    pv_zoom_close();
    if (!pv_mode || pv_roll < 0) return;
    fos_lab_zoom_path(path, sizeof(path), rolls[pv_roll].number, pv_cur);
    if (!fos_zoom_open(path, &pv_zf)) return;
    /* a level where the picture is at least half as big again as it was
     * on the level before, down to the file's own pixels */
    int most = 0;
    for (int step = 4; step >= 1; step--)
    {
        if (step > 1 && (pv_zf.h / step) * 2 < FOS_PRINT_H * 3) continue;
        if (pv_zf.h / step <= FOS_PRINT_H) continue;
        pv_zsteps[pv_znsteps++] = step;
        int vh = pv_zf.h / step < FOS_PRINT_H ? pv_zf.h / step : FOS_PRINT_H;
        if (vh * step * pv_zf.w > most) most = vh * step * pv_zf.w;
    }
    if (pv_znsteps) pv_zrows = fos_port_alloc(most);
    if (!pv_zrows)
    {
        if (pv_znsteps) fos_port_log("prints: no memory to zoom in");
        pv_zoom_close();
    }
}

/* the view at the level it is on: the part of the file (fx, fy, every
 * step-th pixel) and where it goes on the screen (vw x vh, centred) */
static void pv_zoom_view(int *fx, int *fy, int *step, int *vw, int *vh)
{
    int s = pv_zsteps[pv_zlevel - 1];
    int w = pv_zf.w / s < FOS_PRINT_W ? pv_zf.w / s : FOS_PRINT_W;
    int h = pv_zf.h / s < FOS_PRINT_H ? pv_zf.h / s : FOS_PRINT_H;
    *fx = fos_clamp(pv_zx - w * s / 2, 0, pv_zf.w - w * s);
    *fy = fos_clamp(pv_zy - h * s / 2, 0, pv_zf.h - h * s);
    pv_zx = *fx + w * s / 2;
    pv_zy = *fy + h * s / 2;
    *step = s; *vw = w; *vh = h;
}

static int prints_roll_at(int from, int dir)
{
    for (int i = from; i >= 0 && i < nrolls; i += dir)
        if (has_prints(&rolls[i])) return i;
    return -1;
}

static void pv_load()
{
    char path[64];
    if (pv_have) fos_print_free(&pv_print);
    pv_have = 0;
    if (pv_roll < 0) return;
    const struct fos_lab_roll *r = &rolls[pv_roll];
    fos_lab_print_path(path, sizeof(path), r->number, pv_mode ? pv_cur : 0);
    pv_have = fos_print_load(path, &pv_print);
    if (!pv_have)
    {
        char msg[96];
        snprintf(msg, sizeof(msg), "prints: can't load %s", path);
        fos_port_log(msg);
    }
    pv_note[0] = 0;
    if (pv_have) pv_zoom_open();
    else pv_zoom_close();
    pv_dirty = 1;
}

static void pv_palette(int k)
{
    static const uint8_t black[1][3] = { { 0, 0, 0 } };
    if (pv_have) fos_port_photo((const uint8_t (*)[3]) pv_print.pal, FOS_PRINT_COLOURS, k);
    else fos_port_photo(black, 1, k);
}

void prints_enter(int arg)
{
    pv_alone = (arg & PRINTS_ALONE) != 0;
    arg &= ~PRINTS_ALONE;
    pv_have = 0;
    dark_mem();
    rescan();
    int i = arg ? roll_index(arg) : -1;
    if (i < 0 || !has_prints(&rolls[i])) i = prints_roll_at(0, 1);
    pv_roll = i;
    pv_mode = 0;
    pv_cur = 1;
    pv_frames = i >= 0 ? rolls[i].shot : 0;
    if (i >= 0) fos_lab_frames(rolls[i].number, pv_meta, FOS_MAX_FRAMES);
    pv_have = 0;
    pv_state = i >= 0 ? PV_WAIT : PV_NONE;
    pv_t = 0;
    pv_info = 1;
    pv_info_t = 0;
    pv_dirty = 1;
    if (pv_state == PV_NONE)
    {
        ui_bg_plain();
        ui_to_bg(1);
        ui_status_bar("PRINTS");
        fos_text_c(cv, &fos_font_lg, 360, 220, "No prints yet", C_TEXT, OPAQUE, 0);
        fos_text_c(cv, &fos_font_sm, 360, 248, "Develop a roll in the darkroom and its prints show here.", C_TEXT3, OPAQUE, 0);
        struct hint h[] = { { "SET", "Darkroom" }, { "MENU", "Back" } };
        ui_hints(h, 2);
        ui_to_bg(0);
    }
    else memset(ui_bg, fos_ix(FC(RAMP_GRAY, 0)), FOS_W * FOS_H);
}

void prints_leave()
{
    pv_zoom_close();
    if (pv_have) fos_print_free(&pv_print);
    pv_have = 0;
    if (pv_state != PV_NONE) fos_port_palette();
}

static void pv_go(int next)
{
    if (pv_state == PV_OUT) return;
    pv_next = next;
    pv_state = PV_OUT;
    pv_t = 0;
}

static void pv_back()
{
    if (pv_alone) ui_leave();
    else if (ui_from() == SCR_DARK || ui_from() == SCR_DEVELOP)
        ui_go(SCR_DARK, pv_roll >= 0 ? rolls[pv_roll].number : 0, GO_FADE);
    else ui_go(SCR_HOME, HOME_DARK, GO_FADE);
}

void prints_key(int k)
{
    if (pv_state == PV_NONE)
    {
        if (k == FK_SET) ui_go(SCR_DARK, 0, GO_FADE);
        else if (k == FK_MENU || k == FK_PLAY) { if (pv_alone) ui_leave(); else ui_go(SCR_HOME, HOME_DARK, GO_FADE); }
        return;
    }
    if (pv_state != PV_SHOW) return;
    int n = pv_frames;
    if (pv_mode && pv_zlevel > 0)
    {
        /* into the print: the arrows move a quarter of the screen, the wheel goes in and out, the rest come back out */
        int s = pv_zsteps[pv_zlevel - 1];
        switch (k)
        {
            case FK_LEFT:    pv_zx -= FOS_PRINT_W * s / 4; break;
            case FK_RIGHT:   pv_zx += FOS_PRINT_W * s / 4; break;
            case FK_UP:      pv_zy -= FOS_PRINT_H * s / 4; break;
            case FK_DOWN:    pv_zy += FOS_PRINT_H * s / 4; break;
            case FK_WHEEL_R: if (pv_zlevel < pv_znsteps) pv_zlevel++; break;
            case FK_WHEEL_L: pv_zlevel--; break;
            case FK_INFO:    pv_info = !pv_info; pv_info_t = 0; break;
            case FK_SET: case FK_MENU: case FK_PLAY: case FK_HOME: pv_zlevel = 0; break;
            default: return;
        }
        pv_dirty = 1;
        ui_damage_all();
        return;
    }
    switch (k)
    {
        case FK_LEFT: case FK_RIGHT: case FK_UP: case FK_DOWN:
        {
            int d = k == FK_LEFT ? -1 : k == FK_RIGHT ? 1 : k == FK_UP ? -6 : 6;
            if (pv_mode && (k == FK_UP || k == FK_DOWN)) break;
            int to = pv_cur + d;
            if (to < 1 || to > n) break;
            pv_cur = to;
            if (pv_mode) pv_go(NEXT_LOAD);
            else pv_dirty = 1;
            break;
        }
        case FK_WHEEL_L: case FK_WHEEL_R:
            if (pv_mode)
            {
                /* into the print, from its middle; a print developed small has nothing more in it */
                if (k == FK_WHEEL_L || !pv_have) break;
                if (pv_znsteps)
                {
                    pv_zlevel = 1;
                    pv_zx = pv_zf.w / 2;
                    pv_zy = pv_zf.h / 2;
                }
                else
                {
                    snprintf(pv_note, sizeof(pv_note), "DEVELOPED SMALL: NO ZOOM");
                    pv_info = 1;
                    pv_info_t = 0;
                }
                pv_dirty = 1;
            }
            else
            {
                /* the other rolls: newer to the left */
                int to = prints_roll_at(pv_roll + (k == FK_WHEEL_L ? -1 : 1), k == FK_WHEEL_L ? -1 : 1);
                if (to >= 0)
                {
                    pv_roll = to;
                    pv_frames = rolls[to].shot;
                    pv_cur = 1;
                    fos_lab_frames(rolls[to].number, pv_meta, FOS_MAX_FRAMES);
                    pv_go(NEXT_LOAD);
                }
            }
            break;
        case FK_SET:
            pv_mode = !pv_mode;
            pv_go(NEXT_LOAD);
            break;
        case FK_INFO:
            pv_info = !pv_info;
            pv_info_t = 0;
            pv_dirty = 1;
            break;
        case FK_MENU:
            if (pv_mode) { pv_mode = 0; pv_go(NEXT_LOAD); }
            else pv_go(NEXT_BACK);
            break;
        case FK_PLAY:
            pv_go(NEXT_BACK);
            break;
        case FK_HOME:
            pv_go(NEXT_BACK);
            break;
    }
    if (pv_state == PV_SHOW && (k == FK_SET || k == FK_LEFT || k == FK_RIGHT)) pv_info_t = 0;
    if (pv_dirty) ui_damage_all();
}

int prints_update(int dt)
{
    if (pv_state == PV_NONE) return 0;
    pv_t += dt;
    switch (pv_state)
    {
        case PV_WAIT:
            if (!ui_settled()) return 1;
            pv_load();
            pv_palette(0);
            pv_state = PV_IN;
            pv_t = 0;
            pv_info_t = 0;
            return 1;
        case PV_IN:
            pv_palette(fos_clamp(pv_t * 256 / FADE_MS, 0, 256));
            if (pv_t >= FADE_MS) pv_state = PV_SHOW;
            return 1;
        case PV_OUT:
            pv_palette(fos_clamp(256 - pv_t * 256 / FADE_MS, 0, 256));
            if (pv_t < FADE_MS) return 1;
            if (pv_next == NEXT_LOAD)
            {
                pv_load();
                pv_state = PV_IN;
                pv_t = 0;
                return 1;
            }
            /* back to the film OS's colours, on black */
            pv_state = PV_NONE;
            pv_zoom_close();
            if (pv_have) fos_print_free(&pv_print);
            pv_have = 0;
            memset(cv->px, fos_ix(FC(RAMP_GRAY, 0)), FOS_W * FOS_H);
            fos_port_present(cv->px, FOS_W, 0, FOS_H);
            fos_port_palette();
            memset(ui_bg, fos_ix(FC(RAMP_GRAY, 0)), FOS_W * FOS_H);
            pv_back();
            return 1;
        case PV_SHOW:
            /* the details go after a while on their own */
            if (pv_info && pv_info_t < 3000)
            {
                pv_info_t += dt;
                if (pv_info_t >= 3000) { pv_info = 0; pv_note[0] = 0; pv_dirty = 1; ui_damage_all(); }
            }
            return 0;
    }
    return 0;
}

static void sheet_cell(int i, int *x, int *y)
{
    int rows = (pv_frames + 5) / 6;
    int y0 = (FOS_PRINT_H - rows * FOS_THUMB_H) / 2;
    *x = (i % 6) * FOS_THUMB_W + FOS_SHEET_FX;
    *y = y0 + (i / 6) * FOS_THUMB_H + FOS_SHEET_FY;
}

static void frame_rect(int x, int y, int w, int h, uint8_t ix)
{
    for (int k = 0; k < 2; k++)
    {
        memset(&cv->px[(y + k) * cv->pitch + x], ix, w);
        memset(&cv->px[(y + h - 1 - k) * cv->pitch + x], ix, w);
    }
    for (int j = y; j < y + h; j++)
    {
        cv->px[j * cv->pitch + x] = cv->px[j * cv->pitch + x + 1] = ix;
        cv->px[j * cv->pitch + x + w - 1] = cv->px[j * cv->pitch + x + w - 2] = ix;
    }
}

void prints_draw()
{
    if (pv_state == PV_NONE)
    {
        if (ui_clobbered) { ui_clobbered = 0; ui_bg_restore(0, 0, FOS_W, FOS_H); ui_damage_all(); }
        return;
    }
    if (pv_state == PV_WAIT)
    {
        /* black, in the film OS's colours, until the screen has settled */
        memset(cv->px, fos_ix(FC(RAMP_GRAY, 0)), FOS_W * FOS_H);
        ui_clobbered = 0;
        return;
    }
    if (pv_state == PV_OUT) return;        /* what is fading out stays as it was */
    if (!pv_dirty && !ui_clobbered) return;
    pv_dirty = 0;
    ui_clobbered = 0;
    /* the picture: the part of it the zoom is on, or all of it */
    int zoomed = 0;
    if (pv_have && pv_mode && pv_zlevel > 0)
    {
        int fx, fy, step, vw, vh;
        pv_zoom_view(&fx, &fy, &step, &vw, &vh);
        memset(cv->px, PX_BLACK, FOS_W * FOS_H);
        zoomed = fos_zoom_read(&pv_zf, fx, fy, step, cv->px + ((FOS_H - vh) / 2) * cv->pitch + (FOS_W - vw) / 2, cv->pitch, vw, vh, pv_zrows);
        if (zoomed)
        {
            /* where that is in the print: a little map of it, top right, and how far in */
            int mh = 44, mw = mh * pv_zf.w / pv_zf.h, mx = FOS_W - 16 - mw, my = 16;
            for (int y = my - 4; y < my + mh + 4; y++) memset(&cv->px[y * cv->pitch + mx - 4], PX_PANEL, mw + 8);
            frame_rect(mx - 1, my - 1, mw + 2, mh + 2, PX_G2);
            int rx = mx + fx * mw / pv_zf.w, ry = my + fy * mh / pv_zf.h;
            int rw = vw * step * mw / pv_zf.w, rh = vh * step * mh / pv_zf.h;
            frame_rect(rx, ry, rw < 5 ? 5 : rw, rh < 5 ? 5 : rh, PX_AMBER);
            char z[16];
            int f10 = pv_zf.h * 10 / (FOS_PRINT_H * step);
            snprintf(z, sizeof(z), T_TIMES "%d.%d", f10 / 10, f10 % 10);
            int tw = fos_text_w(&fos_font_xs, z, 0);
            for (int y = my + mh + 8; y < my + mh + 28; y++) memset(&cv->px[y * cv->pitch + FOS_W - 26 - tw], PX_PANEL, tw + 14);
            ui_photo_text(&fos_font_xs, FOS_W - 19, my + mh + 23, z, 0, 2);
        }
        else
        {
            fos_port_log("prints: the zoom file can't be read");
            pv_zlevel = 0;
        }
    }
    if (zoomed) {}
    else if (pv_have) memcpy(cv->px, pv_print.px, FOS_W * FOS_H);
    else
    {
        memset(cv->px, PX_BLACK, FOS_W * FOS_H);
        char b[64];
        snprintf(b, sizeof(b), pv_mode ? "Frame %d was not developed" : "No contact sheet", pv_cur);
        ui_photo_text(&fos_font_md, 360, 244, b, 0, 1);
        /* and why, when the darkroom couldn't */
        const struct fos_lab_frame *m = pv_mode && pv_cur >= 1 && pv_cur <= FOS_MAX_FRAMES ? &pv_meta[pv_cur - 1] : 0;
        if (m && m->missing)
        {
            const char *base = strrchr(m->cr2, '/');
            base = base ? base + 1 : m->cr2;
            if (m->jpeg) snprintf(b, sizeof(b), "%.8s was shot as JPEG: set Image quality to RAW", base);
            else if (m->cr2[0]) snprintf(b, sizeof(b), "%s isn't on the card", base);
            else snprintf(b, sizeof(b), "No RAW file was logged for it");
            ui_photo_text(&fos_font_sm, 360, 274, b, 0, 1);
        }
    }
    const struct fos_lab_roll *r = &rolls[pv_roll];
    if (!pv_mode)
    {
        int x, y;
        sheet_cell(pv_cur - 1, &x, &y);
        frame_rect(x - 4, y - 4, FOS_SHEET_FW + 8, FOS_SHEET_FH + 8, PX_AMBER);
    }
    if (pv_info)
    {
        char b[96], c[64];
        int y = FOS_H - INFO_H;
        memset(&cv->px[y * cv->pitch], PX_PANEL, FOS_W * INFO_H);
        memset(&cv->px[y * cv->pitch], PX_LINE, FOS_W);
        const struct fos_lab_frame *m = pv_cur >= 1 && pv_cur <= FOS_MAX_FRAMES ? &pv_meta[pv_cur - 1] : 0;
        snprintf(b, sizeof(b), "ROLL %03d", r->number);
        int x = 20 + ui_photo_text(&fos_font_xs, 20, y + 28, b, 1, 0);
        snprintf(b, sizeof(b), "%s " T_DOT " frame %d of %d", fos_films[r->film].name, pv_cur, pv_frames);
        x += 14 + ui_photo_text(&fos_font_sm, x + 14, y + 28, b, 0, 0);
        if (m && m->when[0])
        {
            snprintf(c, sizeof(c), "%s%s%s", m->when, m->fstop[0] ? "  f/" : "", m->fstop);
            ui_photo_text(&fos_font_sm, x + 14, y + 28, c, 0, 0);
        }
        ui_photo_text(&fos_font_xs, FOS_W - 20, y + 28,
                      pv_note[0] ? pv_note : zoomed ? "ARROWS MOVE   SET OUT" :
                      !pv_mode ? "SET OPEN   WHEEL ROLLS" : pv_znsteps ? "WHEEL ZOOM   SET SHEET" : "SET SHEET   INFO HIDE", pv_note[0] != 0, 2);
    }
    ui_damage_all();
}
