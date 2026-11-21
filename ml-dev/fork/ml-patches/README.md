# Camera patches

Every camera builds on the same Magic Lantern commit, the **base** (`ed3e7c0`, pinned in
`.github/workflows/camera.yml`, `setup_wsl.sh` and `build_fork.sh`). When one camera needs
Magic Lantern changed in a way the base doesn't have, the change goes here, in that camera's
folder, and only that camera's build applies it. See `docs/adr/0001-one-magic-lantern-base-with-camera-patches.md`.

```
ml-patches/<platform>/*.patch     applied in name order to the Magic Lantern checkout, before apply_fork.py
ml-patches/<platform>/no-modules  Magic Lantern modules that must not be in this camera's card files,
                                  one name a line (# comments): build_fork.sh fails if one is
```

- A patch is applied with `git apply`. If the checkout already has it (an earlier build of the same
  camera), it is left alone. Patches keep their changes to shared files inside `CONFIG_<camera>`
  blocks, so the other cameras build the same with or without them.
- Make a patch from a Magic Lantern commit: cherry-pick it onto the base, then
  `git format-patch -1 HEAD --stdout > ml-patches/<platform>/0001-what-it-does.patch`.
- When the base moves to a Magic Lantern that already has the change, delete the patch.

| Camera | Patch | Why |
|---|---|---|
| 1300D.110 | `0001-1300D-initial-support.patch` | Magic Lantern's port (142472e, 2026-10-04), which came after the base |
| 1300D.110 | `0002-1300D-audio-gain-sem-placeholder-crash.patch` | The port froze a tester's 1300D at power on: `PROP_MVR_REC_START` gives the audio gain semaphore before `my_sounddev_task` has made it, and Canon asserts in PropMgr (#85). Found and fixed by the tester; not in Magic Lantern yet |
| 1300D.110 | `no-modules` | Magic Lantern has reports of `mlv_lite` damaging 1300Ds (magiclantern_simplified PR #199) |
| EOSM2.103 | `0001-EOSM2-initial-support.patch` | EOS M2 (1.0.3) port and 8.3 `EOSM2103.SYM` filename fix, rebased onto the base (not in Magic Lantern yet) |
