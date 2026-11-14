/* fos_lab: the rolls on the card and their prints, for the darkroom.
 *
 * A roll is what its logs say: DCIM/xxxCANON/ROLL_nnn.TXT, written by the
 * camera frame by frame (a roll that ran into a new DCIM folder has a log
 * in each). Its prints are kept in ML/DARKROOM/Rnnn/, Fnn.BMP for frame nn
 * and SHEET.BMP for the contact sheet; a roll is developed when they are
 * all there. A roll out of the camera can be deleted here too: its prints,
 * or with them the frames its logs list and the logs.
 */

#include "fos.h"
#include "fos_dev.h"
#include <string.h>
#include <stdlib.h>

#define LOG_MAX (16 * 1024)
#define MAX_ROLL_TRACK 64

/* which card each roll is on: fos_port_card() or the literal other_card()
 * gives, so a pointer is kept, never a copy (the PC's card is a long path) */
static const char *roll_cards[MAX_ROLL_TRACK];
static int roll_card_numbers[MAX_ROLL_TRACK];
static int nroll_cards = 0;

static const char *roll_card(int roll)
{
    for (int i = 0; i < nroll_cards; i++)
        if (roll_card_numbers[i] == roll && roll_cards[i])
            return roll_cards[i];
    return fos_port_card();
}

/* the camera's other card slot (CF A:/ <-> SD B:/), 0 on one-slot cameras */
static const char *other_card(const char *card)
{
    return card[0] == 'A' ? "B:/" : card[0] == 'B' ? "A:/" : 0;
}

/* the card a path is on, 0 if neither */
static const char *card_of(const char *path)
{
    const char *cards[2] = { fos_port_card(), other_card(fos_port_card()) };
    for (int c = 0; c < 2 && cards[c]; c++)
        if (!strncmp(path, cards[c], strlen(cards[c]))) return cards[c];
    return 0;
}

static void set_roll_card(int roll, const char *card)
{
    if (!card || !*card) return;
    for (int i = 0; i < nroll_cards; i++)
    {
        if (roll_card_numbers[i] == roll)
        {
            roll_cards[i] = card;
            return;
        }
    }
    if (nroll_cards < MAX_ROLL_TRACK)
    {
        roll_card_numbers[nroll_cards] = roll;
        roll_cards[nroll_cards] = card;
        nroll_cards++;
    }
}

void fos_lab_print_path(char *buf, int size, int roll, int frame)
{
    const char *card = roll_card(roll);
    if (frame) snprintf(buf, size, "%sML/DARKROOM/R%03d/F%02d.BMP", card, roll, frame);
    else snprintf(buf, size, "%sML/DARKROOM/R%03d/SHEET.BMP", card, roll);
}

void fos_lab_zoom_path(char *buf, int size, int roll, int frame)
{
    snprintf(buf, size, "%sML/DARKROOM/R%03d/F%02d.ZOM", roll_card(roll), roll, frame);
}

void fos_lab_cache_dir(char *buf, int size)
{
    snprintf(buf, size, "%sML/DARKROOM", fos_port_card());
}

static int first_only(void *ctx, const char *name, int is_dir) { return 0; }

static int dir_exists(const char *path)
{
    return fos_port_list(path, first_only, 0) >= 0;
}

/* a folder of ours: it holds the roll's tag file */
static int tagged(const char *dir, int roll)
{
    char path[128];
    snprintf(path, sizeof(path), "%s/ROLL%03d.TXT", dir, roll);
    void *f = fos_port_open(path, 0);
    if (f) fos_port_close(f);
    return f != 0;
}

/* a file, or an empty folder; 1 if it's still there */
static int remove_logged(const char *path)
{
    if (!fos_port_remove(path)) return 0;
    char msg[200];
    snprintf(msg, sizeof(msg), "lab: can't remove %s", path);
    fos_port_log(msg);
    return 1;
}

static int make_tagged(const char *dir, int roll, int film)
{
    if (fos_port_mkdir(dir) < 0) return 0;
    char path[128], text[96];
    snprintf(path, sizeof(path), "%s/ROLL%03d.TXT", dir, roll);
    void *f = fos_port_open(path, 1);
    if (!f)
    {
        /* the folder was made, but nothing can be written into it (a long
         * name on a 550D's exFAT card, #65): it goes again, still empty */
        remove_logged(dir);
        return 0;
    }
    int n = snprintf(text, sizeof(text), "roll = %03d\nfilm = %s\n", roll, fos_films[film].key);
    fos_port_write(f, text, n);
    fos_port_close(f);
    return 1;
}

/* The day's names for the folder, in the order they are tried: k 0..8 are
 * "Sep0906 Portra400", "Sep0906 Portra400 2" .. " 9" (another roll that
 * day), k 9.. are SEP0906, SEP0906B .. SEP0906Z where the card takes no
 * long names */
#define DAY_LONG 9
#define DAY_NAMES (DAY_LONG + 26)
static void day_dir(char *buf, int size, const char *card, int k, int m, int d, const char *film_name)
{
    static const char months[12][4] = { "Jan", "Feb", "Mar", "Apr", "May", "Jun",
                                        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec" };
    int short_name = k >= DAY_LONG;
    char mon[4], suffix[3] = { 0, 0, 0 };
    memcpy(mon, months[m - 1], 4);
    if (short_name)
    {
        mon[1] -= 32;
        mon[2] -= 32;
        if (k > DAY_LONG) suffix[0] = (char) ('A' + k - DAY_LONG);
    }
    else if (k)
    {
        suffix[0] = ' ';
        suffix[1] = (char) ('1' + k);
    }
    snprintf(buf, size, "%sDCIM/%s%02d%02d%s%s%s", card, mon, m, d, short_name ? "" : " ",
             short_name ? "" : film_name, suffix);
}

int fos_lab_dcim_dir(char *buf, int size, int roll, int film, const char *when)
{
    const char *card = roll_card(roll);
    int m = when && strlen(when) >= 10 ? atoi(when + 5) : 0, d = m ? atoi(when + 8) : 0;
    if (m < 1 || m > 12 || d < 1 || d > 31) return -1;
    film = fos_clamp(film, 0, fos_nfilms - 1);
    const char *film_name = fos_films[film].shortname ? fos_films[film].shortname : fos_films[film].key;
    /* developed before: its folder, long or short (so a card without long
     * names doesn't get the long one tried again each time), whichever of
     * the day's names it has: another roll deleted since leaves a gap */
    for (int k = 0; k < DAY_NAMES; k++)
    {
        day_dir(buf, size, card, k, m, d, film_name);
        if (dir_exists(buf) && tagged(buf, roll)) return 0;
    }
    /* else the first free name */
    for (int k = 0; k < DAY_NAMES; k++)
    {
        day_dir(buf, size, card, k, m, d, film_name);
        if (dir_exists(buf)) continue;
        if (k >= DAY_LONG) return make_tagged(buf, roll, film) ? 0 : -1;
        if (make_tagged(buf, roll, film) && dir_exists(buf)) return 0;
        k = DAY_LONG - 1;               /* no long names on this card */
    }
    return -1;
}

int fos_lab_prepare(int roll)
{
    const char *card = roll_card(roll);
    char path[64];
    snprintf(path, sizeof(path), "%sML/DARKROOM", card);
    if (fos_port_mkdir(path))
    {
        /* Try alternate card */
        const char *alt = other_card(card);
        if (alt)
        {
            snprintf(path, sizeof(path), "%sML/DARKROOM", alt);
            if (fos_port_mkdir(path)) return -1;
            set_roll_card(roll, alt);
            card = alt;
        }
        else return -1;
    }
    snprintf(path, sizeof(path), "%sML/DARKROOM/R%03d", card, roll);
    return fos_port_mkdir(path);
}

/* the film's place on the shelf; -1 if it isn't on it (a film that has left
 * the shelf since the roll was shot) */
static int film_index(const char *key)
{
    for (int i = 0; i < fos_nfilms; i++)
        if (!strcmp(fos_films[i].key, key)) return i;
    return -1;
}

/* ---------------------------------------------------------------- reading logs */

/* one log, a line at a time: header lines ("film = portra400") and
 * frames ("12  IMG_0012.CR2  2026-08-08 09:15:15  f/2.8") */
struct log_reader
{
    void (*header)(void *ctx, const char *key, const char *value);
    void (*frame)(void *ctx, int no, const char *file, const char *when, const char *fstop);
    void *ctx;
};

static void read_log(const char *path, const struct log_reader *r)
{
    char *buf = fos_port_alloc(LOG_MAX + 1);
    if (!buf) return;
    void *f = fos_port_open(path, 0);
    int n = f ? fos_port_read(f, buf, LOG_MAX) : 0;
    if (f) fos_port_close(f);
    if (n <= 0)
    {
        char msg[96];
        snprintf(msg, sizeof(msg), "lab: can't read %s (%s)", path, f ? "read failed" : "can't open");
        fos_port_log(msg);
    }
    buf[n > 0 ? n : 0] = 0;
    for (char *line = buf; *line; )
    {
        char *next = strchr(line, '\n');
        if (next) *next++ = 0;
        else next = line + strlen(line);
        char *cr = strchr(line, '\r');
        if (cr) *cr = 0;
        while (*line == ' ') line++;
        char *eq = strchr(line, '=');
        if (*line == '#' || !*line) { line = next; continue; }
        if (eq && !(line[0] >= '0' && line[0] <= '9'))
        {
            char *k = line, *v = eq + 1, *e = eq;
            while (e > k && e[-1] == ' ') e--;
            *e = 0;
            while (*v == ' ') v++;
            if (r->header) r->header(r->ctx, k, v);
        }
        else if (line[0] >= '0' && line[0] <= '9')
        {
            char *tok[5];
            int nt = 0;
            for (char *p = line; *p && nt < 5; )
            {
                while (*p == ' ' || *p == '\t') p++;
                if (!*p) break;
                tok[nt++] = p;
                while (*p && *p != ' ' && *p != '\t') p++;
                if (*p) *p++ = 0;
            }
            if (nt >= 2 && r->frame)
            {
                char when[20] = "";
                char hm[6];
                if (nt >= 4) snprintf(when, sizeof(when), "%s %s", tok[2], fos_copy(hm, sizeof(hm), tok[3], 5));
                r->frame(r->ctx, atoi(tok[0]), tok[1], when, nt >= 5 && !strncmp(tok[4], "f/", 2) ? tok[4] + 2 : "");
            }
        }
        line = next;
    }
    fos_port_free(buf);
}

/* every ROLL_nnn.TXT on the card: fn(ctx, card, folder, file name, roll number) */
struct each_log { void (*fn)(void *ctx, const char *card, const char *folder, const char *name, int number); void *ctx; const char *card; const char *folder; };

static int log_entry(void *ctx, const char *name, int is_dir)
{
    struct each_log *e = ctx;
    if (!is_dir && !strncmp(name, "ROLL_", 5) && strlen(name) == 12
        && (!strcmp(name + 8, ".TXT") || !strcmp(name + 8, ".txt")))
        e->fn(e->ctx, e->card, e->folder, name, atoi(name + 5));
    return 1;
}

static int folder_entry(void *ctx, const char *name, int is_dir)
{
    struct each_log *e = ctx;
    /* DCIM folders: three digits and five characters, "100CANON" */
    if (!is_dir || strlen(name) != 8 || name[0] < '1' || name[0] > '9') return 1;
    char dir[64];
    snprintf(dir, sizeof(dir), "%sDCIM/%s", e->card, name);
    struct each_log sub = *e;
    sub.folder = name;
    fos_port_list(dir, log_entry, &sub);
    return 1;
}

static void each_log(void (*fn)(void *, const char *, const char *, const char *, int), void *ctx)
{
    const char *primary = fos_port_card();
    char dir[64];
    snprintf(dir, sizeof(dir), "%sDCIM", primary);
    struct each_log e = { fn, ctx, primary, 0 };
    fos_port_list(dir, folder_entry, &e);

    /* On dual-card cameras, scan the alternate card's DCIM as well */
    const char *alt = other_card(primary);
    if (alt)
    {
        snprintf(dir, sizeof(dir), "%sDCIM", alt);
        struct each_log e_alt = { fn, ctx, alt, 0 };
        fos_port_list(dir, folder_entry, &e_alt);
    }
}

/* ---------------------------------------------------------------- the catalogue */

struct scan { struct fos_lab_roll *rolls; int n, max; struct fos_lab_roll *cur; };

static void scan_header(void *ctx, const char *k, const char *v)
{
    struct fos_lab_roll *r = ((struct scan *) ctx)->cur;
    if (!strcmp(k, "film"))
    {
        int i = film_index(v);
        r->film = i < 0 ? 0 : i;
        if (i < 0) fos_copy(r->gone, sizeof(r->gone), v, (int) sizeof(r->gone) - 1);
        else r->gone[0] = 0;
    }
    else if (!strcmp(k, "exposures")) r->exposures = atoi(v);
    else if (!strcmp(k, "loaded") && (!r->loaded[0] || strncmp(v, r->loaded, 16) < 0))
        fos_copy(r->loaded, sizeof(r->loaded), v, 16);
}

static void scan_frame(void *ctx, int no, const char *file, const char *when, const char *fstop)
{
    struct fos_lab_roll *r = ((struct scan *) ctx)->cur;
    if (no > r->shot) r->shot = no;
    if (strcmp(when, r->last) > 0) snprintf(r->last, sizeof(r->last), "%s", when);
}

static void scan_log(void *ctx, const char *card, const char *folder, const char *name, int number)
{
    set_roll_card(number, card);
    struct scan *s = ctx;
    struct fos_lab_roll *r = 0;
    for (int i = 0; i < s->n; i++)
        if (s->rolls[i].number == number) r = &s->rolls[i];
    if (!r)
    {
        if (s->n >= s->max) return;
        r = &s->rolls[s->n++];
        memset(r, 0, sizeof(*r));
        r->number = number;
        r->exposures = 36;
    }
    char path[64];
    snprintf(path, sizeof(path), "%sDCIM/%s/%s", card, folder, name);
    s->cur = r;
    struct log_reader rd = { scan_header, scan_frame, s };
    read_log(path, &rd);
}

static int print_entry(void *ctx, const char *name, int is_dir)
{
    struct fos_lab_roll *r = ctx;
    if (is_dir) return 1;
    if (!strcmp(name, "SHEET.BMP")) r->sheet = 1;
    else if (name[0] == 'F' && strlen(name) == 7 && !strcmp(name + 3, ".BMP"))
    {
        int no = atoi(name + 1);
        if (no >= 1 && no <= r->shot) r->developed++;
    }
    return 1;
}

/* paths found for a roll, to act on once their folders have been read */
struct found { int roll, n; char paths[8][64]; };

/* our folders in DCIM (not Canon's "100CANON"): which roll each holds, by
 * its tag file, and how many JPEGs; with found, the paths of those that
 * hold its roll */
struct jpeg_scan { struct fos_lab_roll *rolls; int n; int roll, count; struct found *found; const char *card; };

static int jpeg_file(void *ctx, const char *name, int is_dir)
{
    struct jpeg_scan *s = ctx;
    int len = (int) strlen(name);
    if (is_dir) return 1;
    if (len == 11 && !strncmp(name, "ROLL", 4) && !strcmp(name + 7, ".TXT")) s->roll = atoi(name + 4);
    else if (len > 4 && !strcmp(name + len - 4, ".JPG")) s->count++;
    return 1;
}

static int jpeg_folder(void *ctx, const char *name, int is_dir)
{
    struct jpeg_scan *s = ctx;
    if (!is_dir || (strlen(name) == 8 && name[0] >= '1' && name[0] <= '9')) return 1;
    char dir[128];
    snprintf(dir, sizeof(dir), "%sDCIM/%s", s->card, name);
    s->roll = -1;
    s->count = 0;
    fos_port_list(dir, jpeg_file, s);
    for (int i = 0; i < s->n; i++)
        if (s->rolls[i].number == s->roll) s->rolls[i].jpegs += s->count;
    struct found *f = s->found;
    if (f && s->roll == f->roll && f->n < 8 && strlen(dir) < sizeof(f->paths[0])) strcpy(f->paths[f->n++], dir);
    return 1;
}

int fos_lab_scan(struct fos_lab_roll *rolls, int max)
{
    struct scan s = { rolls, 0, max, 0 };
    each_log(scan_log, &s);
    struct fos_roll cam;
    fos_port_roll(&cam);
    for (int i = 0; i < s.n; i++)
    {
        struct fos_lab_roll *r = &rolls[i];
        const char *card = roll_card(r->number);
        char dir[64];
        snprintf(dir, sizeof(dir), "%sML/DARKROOM/R%03d", card, r->number);
        fos_port_list(dir, print_entry, r);

        /* Check alternate card if no prints were found on roll_card */
        if (!r->developed && !r->sheet)
        {
            const char *alt = other_card(card);
            if (alt)
            {
                snprintf(dir, sizeof(dir), "%sML/DARKROOM/R%03d", alt, r->number);
                fos_port_list(dir, print_entry, r);
            }
        }
        r->in_camera = cam.loaded && cam.number == r->number;
    }
    const char *primary = fos_port_card();
    char dcim[64];
    snprintf(dcim, sizeof(dcim), "%sDCIM", primary);
    struct jpeg_scan js = { rolls, s.n, -1, 0, 0, primary };
    fos_port_list(dcim, jpeg_folder, &js);

    /* Also scan DCIM JPEGs on alternate card */
    js.card = other_card(primary);
    if (js.card)
    {
        snprintf(dcim, sizeof(dcim), "%sDCIM", js.card);
        fos_port_list(dcim, jpeg_folder, &js);
    }

    /* newest first */
    for (int i = 1; i < s.n; i++)
        for (int j = i; j > 0; j--)
        {
            struct fos_lab_roll *a = &rolls[j - 1], *b = &rolls[j];
            int c = strcmp(a->loaded, b->loaded);
            if (c > 0 || (c == 0 && a->number > b->number)) break;
            struct fos_lab_roll t = *a; *a = *b; *b = t;
        }
    return s.n;
}

/* ---------------------------------------------------------------- one roll's frames */

struct frames { struct fos_lab_frame *frames; int max, roll; const char *card; const char *folder; };

static void frames_frame(void *ctx, int no, const char *file, const char *when, const char *fstop)
{
    struct frames *s = ctx;
    if (no < 1 || no > s->max) return;
    struct fos_lab_frame *f = &s->frames[no - 1];
    f->no = no;
    snprintf(f->cr2, sizeof(f->cr2), "%sDCIM/%s/%s", s->card, s->folder, file);
    snprintf(f->when, sizeof(f->when), "%s", when);
    snprintf(f->fstop, sizeof(f->fstop), "%s", fstop);
}

static void frames_log(void *ctx, const char *card, const char *folder, const char *name, int number)
{
    struct frames *s = ctx;
    if (number != s->roll) return;
    set_roll_card(number, card);
    char path[64];
    snprintf(path, sizeof(path), "%sDCIM/%s/%s", card, folder, name);
    s->card = card;
    s->folder = folder;
    struct log_reader rd = { 0, frames_frame, s };
    read_log(path, &rd);
}

/* open a frame's file (path: ...DCIM/100CANON/IMG_0012.CR2), by Canon's
 * name for it if that isn't the log's. The log's name is Magic Lantern's file
 * prefix and the file number, and Canon's name can differ:
 *  - in Adobe RGB the prefix's first letter is '_' (IMG_0012 -> _MG_0012,
 *    and a user prefix ABCD0012 -> _BCD0012);
 *  - on the 5D Mark III the prefix is the user one (C59A) even while the
 *    camera names its files IMG_ or _MG_ (#31).
 * So, keeping the number: the first letter '_', then Canon's own two. The
 * name that opens stays in path; when none does, path is as it was. */
static void *try_frame_prefixes(char *path)
{
    void *f = fos_port_open(path, 0);
    if (f) return f;
    char *base = strrchr(path, '/');
    base = base ? base + 1 : path;
    if (strlen(base) != 12 || base[8] != '.') return 0;    /* PPPPnnnn.CR2 */
    char was[4];
    memcpy(was, base, 4);
    const char *try[3] = { was, "IMG_", "_MG_" };
    for (int k = 0; k < 3 && !f; k++)
    {
        memcpy(base, try[k], 4);
        if (!k) base[0] = '_';
        if (k && !memcmp(base, was, 4)) continue;       /* tried already */
        f = fos_port_open(path, 0);
    }
    if (!f) memcpy(base, was, 4);
    return f;
}

static void *open_frame_file(char *path)
{
    void *f = try_frame_prefixes(path);
    if (f) return f;

    /* If not found on original card, check alternate card ('A' <-> 'B') */
    if (path && (path[0] == 'A' || path[0] == 'B' || path[0] == 'a' || path[0] == 'b') && path[1] == ':')
    {
        char orig_drive = path[0];
        if (orig_drive == 'A') path[0] = 'B';
        else if (orig_drive == 'B') path[0] = 'A';
        else if (orig_drive == 'a') path[0] = 'b';
        else if (orig_drive == 'b') path[0] = 'a';

        f = try_frame_prefixes(path);
        if (f)
        {
            /* Found on alternate card! Keep path[0] updated to the working card */
            return f;
        }
        /* Restore original drive if not found on either */
        path[0] = orig_drive;
    }
    return 0;
}

int fos_lab_frames(int roll, struct fos_lab_frame *frames, int max)
{
    memset(frames, 0, sizeof(*frames) * max);
    struct frames s = { frames, max, roll, 0, 0 };
    each_log(frames_log, &s);
    int n = 0;
    for (int i = 0; i < max; i++)
    {
        if (frames[i].no) n = i + 1;
        else frames[i].no = i + 1;
    }
    /* a frame whose file has gone (deleted on the camera, or never a RAW)
     * can't be developed */
    char seen[4] = "";                  /* the prefix of Canon's names on this roll */
    for (int i = 0; i < n; i++)
    {
        if (!frames[i].cr2[0]) { frames[i].missing = 1; continue; }
        void *f = open_frame_file(frames[i].cr2);
        if (f)
        {
            fos_port_close(f);
            const char *base = strrchr(frames[i].cr2, '/');
            base = base ? base + 1 : frames[i].cr2;
            if (!seen[0] && strlen(base) == 12) memcpy(seen, base, 4);
            continue;
        }
        frames[i].missing = 1;
        /* shot with Image quality set to a JPEG one: Canon's .JPG of the
         * same name is there instead, and the darkroom can say so */
        char *ext = strrchr(frames[i].cr2, '.');
        if (!ext || strcmp(ext, ".CR2")) continue;
        memcpy(ext, ".JPG", 4);
        f = open_frame_file(frames[i].cr2);
        if (f)
        {
            fos_port_close(f);
            frames[i].jpeg = 1;         /* cr2 names the JPEG now */
        }
        else memcpy(ext, ".CR2", 4);
    }
    /* a file that isn't there by any name is called by the roll's other
     * names, as the camera would have named it: _MG_0012.CR2 in Adobe RGB,
     * not the log's IMG_0012.CR2 (#17) */
    for (int i = 0; i < n && seen[0]; i++)
    {
        if (!frames[i].missing || frames[i].jpeg || !frames[i].cr2[0]) continue;
        char *base = strrchr(frames[i].cr2, '/');
        base = base ? base + 1 : frames[i].cr2;
        if (strlen(base) == 12 && base[8] == '.') memcpy(base, seen, 4);
    }
    /* Record the card where the frames actually reside */
    for (int i = 0; i < n; i++)
    {
        const char *card = frames[i].missing ? 0 : card_of(frames[i].cr2);
        if (card)
        {
            set_roll_card(roll, card);
            break;
        }
    }
    return n;
}

/* ---------------------------------------------------------------- deleting a roll */

/* A folder of ours: the roll's prints (ML/DARKROOM/Rnnn: Fnn.BMP, Fnn.ZOM, SHEET.BMP),
 * or its folder in DCIM (IMG_0102.JPG and the roll's tag, ROLL012.TXT).
 * Those files go, the tag last and only once the rest has (a folder that
 * couldn't all go is still the roll's, to delete again), then the folder
 * once nothing else is in it: one with anything left is never removed. The
 * names are taken first and removed after, not while the folder is read.
 * How many files couldn't be removed; a folder that stays adds to *dirs. */
#define SWEEP_MAX (2 * FOS_MAX_FRAMES + 2)       /* each frame's print and its zoom file, the sheet */
struct sweep { int n; char names[SWEEP_MAX][13]; };

static int sweep_entry(void *ctx, const char *name, int is_dir)
{
    struct sweep *s = ctx;
    int len = (int) strlen(name);
    if (!is_dir && len >= 5 && len <= 12 && s->n < SWEEP_MAX
        && (!strcmp(name + len - 4, ".BMP") || !strcmp(name + len - 4, ".JPG") || !strcmp(name + len - 4, ".ZOM")))
        memcpy(s->names[s->n++], name, len + 1);
    return 1;
}

static int sweep(const char *dir, int roll, int *dirs)
{
    struct sweep s;
    s.n = 0;
    fos_port_list(dir, sweep_entry, &s);
    char path[160];
    int failed = 0;
    for (int i = 0; i <= s.n; i++)
    {
        if (i < s.n) snprintf(path, sizeof(path), "%s/%s", dir, s.names[i]);
        else if (failed) break;
        else snprintf(path, sizeof(path), "%s/ROLL%03d.TXT", dir, roll);      /* none in Rnnn: nothing to do */
        failed += remove_logged(path);
    }
    int left = fos_port_list(dir, first_only, 0);       /* < 0: there was none */
    *dirs += left ? left > 0 : remove_logged(dir);
    return failed;
}

/* the roll's logs, one in each DCIM folder it ran into */
static void logs_log(void *ctx, const char *card, const char *folder, const char *name, int number)
{
    struct found *f = ctx;
    if (number == f->roll && f->n < 8) snprintf(f->paths[f->n++], sizeof(f->paths[0]), "%sDCIM/%s/%s", card, folder, name);
}

int fos_lab_delete(int roll, int whole, struct fos_lab_frame *frames)
{
    struct fos_roll cam;
    fos_port_roll(&cam);
    if (cam.loaded && cam.number == roll) return -1;           /* never the one in the camera */
    /* its prints: the darkroom's, and its folder in DCIM, on either card */
    const char *cards[2] = { fos_port_card(), other_card(fos_port_card()) };
    struct found f;
    f.roll = roll;
    f.n = 0;
    for (int c = 0; c < 2 && cards[c]; c++)
        snprintf(f.paths[f.n++], sizeof(f.paths[0]), "%sML/DARKROOM/R%03d", cards[c], roll);
    struct jpeg_scan js = { 0, 0, -1, 0, &f, 0 };
    char dcim[64];
    for (int c = 0; c < 2 && cards[c]; c++)
    {
        js.card = cards[c];
        snprintf(dcim, sizeof(dcim), "%sDCIM", cards[c]);
        fos_port_list(dcim, jpeg_folder, &js);
    }
    int failed = 0, dirs = 0;
    for (int i = 0; i < f.n; i++) failed += sweep(f.paths[i], roll, &dirs);
    if (whole)
    {
        /* its frames, only those its logs list, by the names the darkroom
         * finds them by (Canon's _MG_ in Adobe RGB, a JPEG where it was
         * shot as one, each in its folder across IMG_9999); then the logs,
         * last and only once every file has gone (an empty folder that
         * stays doesn't count), so a roll that couldn't all go is still
         * there to delete again */
        int n = fos_lab_frames(roll, frames, FOS_MAX_FRAMES);
        for (int i = 0; i < n; i++)
            if (!frames[i].missing || frames[i].jpeg) failed += remove_logged(frames[i].cr2);
        f.n = 0;
        if (!failed) each_log(logs_log, &f);
        for (int i = 0; i < f.n; i++) failed += remove_logged(f.paths[i]);
    }
    failed += dirs;
    char msg[64];
    snprintf(msg, sizeof(msg), "lab: roll %03d: deleted %s, %d left", roll, whole ? "all" : "prints", failed);
    fos_port_log(msg);
    return failed;
}
