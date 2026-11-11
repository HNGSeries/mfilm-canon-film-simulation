# The 1300D runs on our pinned Magic Lantern, with its port commit carried as a patch

Magic Lantern's 1300D port (magiclantern_simplified 142472e, 2026-10-04) came 144 commits after the commit every M-Film camera builds on (ed3e7c0). 58 of those commits change code all cameras share, including the removal of four picture-style setters the film OS calls. Moving every camera to the new Magic Lantern would send all 14 cameras back to testers. So we apply the 1300D commit on top of ed3e7c0 instead. It applies cleanly: its changes to shared files sit inside `CONFIG_1300D` blocks.

We drop this patch when all cameras move to a newer Magic Lantern, which is its own piece of work.

## Considered Options

- **Move every camera to the newest Magic Lantern.** Rejected for now: too much risk to cameras that already work, for one new camera.
- **Pin a different Magic Lantern commit for each camera in CI.** Rejected: the CI matrix, `cameras.py` and the film OS sources would have to carry per-camera versions.

## Consequences

- The 1300D doesn't get later fixes to Magic Lantern's 1300D code until the patch is refreshed or the whole pin moves.
- Magic Lantern turns off camera setting changes on the 1300D (`CONFIG_PROP_REQUEST_CHANGE`), and we leave it off. Loading a roll there doesn't set ISO, white balance or picture style.
- The 1300D zip leaves out `mlv_lite.mo` and the other RAW video modules, because Magic Lantern has reports of them damaging 1300Ds.
