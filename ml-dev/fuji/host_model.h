/* make check: a camera on a PC (fakefuji.c), in place of FujiHack's
 * model/<model>.h. HOST_XF1 gives the XF1's 640-wide screen, else the X-A2. */

#include <stdint.h>

#ifdef HOST_XF1
#define MODEL_NAME "Fujifilm XF1"
#define SCREEN_WIDTH 640
#else
#define MODEL_NAME "Fujifilm X-A2"
#define SCREEN_WIDTH 720
#endif
#define SCREEN_HEIGHT 480

extern volatile uint32_t fake_ms;
extern volatile struct fuji_input fake_input;
extern volatile uintptr_t fake_layers[];
#define MEM_MS_TIMER       ((uintptr_t) &fake_ms)
#define MEM_INPUT_MAP      ((uintptr_t) &fake_input)
#define MEM_OPENGL_BUFFERS ((uintptr_t) fake_layers)
