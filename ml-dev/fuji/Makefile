# M-Film on Fujifilm cameras, over FujiHack (README.md).
#
#   make check          the port and the whole film OS built for a PC, run on a fake X-A2 and XF1
#   make mockups        the preview pictures (preview/), from the fake cameras
#   make camera         the camera build: needs arm-none-eabi-gcc and FujiHack (make fujihack)
#   make fujihack       FujiHack at the commit this port is written against

FOS = ../filmos
FOS_SRC = $(addprefix $(FOS)/, fos_gfx.c fos_film.c fos_ui.c fos_shelf.c fos_pages.c fos_hud.c fos_print.c \
          fos_dark.c fos_dev.c fos_lab.c fos_looks.c fos_jpeg.c)
PORT = fujiport.c
VERSION := $(shell tr -d " \r\n" < ../../VERSION)
CFLAGS = -O2 -g -Wall -Wextra -Wno-unused-parameter -std=gnu99 -DFOS_KEYS_FUJI -DMFILM_VERSION='"$(VERSION)"'

# the camera and firmware: FujiHack's model/<MODEL>.h
MODEL ?= xa2_130
FUJIHACK_URL = https://github.com/fujihack/fujihack
FUJIHACK_COMMIT = 3f14615cf0c92e8a9d35aca00f67bb8f4733b2b3
FUJIHACK = out/fujihack
ARMCC ?= arm-none-eabi

.PHONY: check mockups camera fujihack clean

# ---- on a PC

out/fakefuji-xa2: $(PORT) fakefuji.c fuji.h host_model.h $(FOS_SRC) $(FOS)/*.h
	mkdir -p out
	$(CC) $(CFLAGS) -include host_model.h -o $@ $(PORT) fakefuji.c $(FOS_SRC) -lm

out/fakefuji-xf1: $(PORT) fakefuji.c fuji.h host_model.h $(FOS_SRC) $(FOS)/*.h
	mkdir -p out
	$(CC) $(CFLAGS) -DHOST_XF1 -include host_model.h -o $@ $(PORT) fakefuji.c $(FOS_SRC) -lm

# a card as the zip would make it: the fonts and films the simulator builds
out/card: ../filmos/sim/out/FOSFONT.BIN ../filmos/sim/out/FOSFILMS.BIN
	mkdir -p out/card/ML/DATA out/card/ML/SETTINGS
	cp ../filmos/sim/out/FOSFONT.BIN ../filmos/sim/out/FOSFILMS.BIN out/card/ML/DATA/
../filmos/sim/out/FOSFONT.BIN ../filmos/sim/out/FOSFILMS.BIN:
	$(MAKE) -C ../filmos/sim out/FOSFONT.BIN out/FOSFILMS.BIN

check: out/fakefuji-xa2 out/fakefuji-xf1 out/card
	rm -rf out/check && mkdir -p out/check/xa2 out/check/xf1
	rm -f out/card/ML/SETTINGS/MFILM.FUJ && ./out/fakefuji-xa2 scenes/check.txt out/check/xa2
	rm -f out/card/ML/SETTINGS/MFILM.FUJ && ./out/fakefuji-xf1 scenes/check.txt out/check/xf1
	test -s out/card/ML/SETTINGS/MFILM.FUJ    # the roll was kept on the card
	python3 checkshots.py out/check/xa2 out/check/xf1

mockups: out/fakefuji-xa2 out/fakefuji-xf1 out/card
	python3 mockup.py

# ---- on the camera

fujihack: $(FUJIHACK)/model/$(MODEL).h
$(FUJIHACK)/model/$(MODEL).h:
	rm -rf $(FUJIHACK)
	git clone -q $(FUJIHACK_URL) $(FUJIHACK)
	git -C $(FUJIHACK) checkout -q $(FUJIHACK_COMMIT)

# an ELF for FujiHack's app loader (ML/MFILM.ELF on the card). It links, but
# nothing has run on a camera yet: README.md, "Where it stands"
camera: fujihack
	@command -v $(ARMCC)-gcc >/dev/null || { echo "no $(ARMCC)-gcc: install an ARM bare-metal toolchain"; exit 1; }
	mkdir -p out/$(MODEL)
	$(ARMCC)-gcc -O2 -marm -mcpu=cortex-a5 -fpic -std=gnu99 -ffreestanding -DFOS_KEYS_FUJI -DMFILM_VERSION='"$(VERSION)"' \
		-include $(FUJIHACK)/model/$(MODEL).h -I$(FUJIHACK)/src -c $(PORT) $(FOS_SRC)
	mv *.o out/$(MODEL)/
	@echo "objects in out/$(MODEL)/: linking against FujiHack's stubs and loader is the next step (README.md)"

clean:
	rm -rf out
