# One Magic Lantern base for every camera, with camera patches where one camera needs more

Every camera builds on the same Magic Lantern commit, the base (`ed3e7c0`). When one camera needs a Magic Lantern change the base hasn't got, it becomes a camera patch in `ml-dev/fork/ml-patches/<camera>/`, applied only to that camera's build. We decided this when the 1300D came along: Magic Lantern's 1300D port (magiclantern_simplified 142472e, 2026-10-04) came 144 commits after the base, and 58 of those commits change code all cameras share, including the removal of four picture-style setters the film OS calls. Moving every camera to the new Magic Lantern would have sent all 14 cameras back to testers for one new camera. The 1300D's port commit applies cleanly to the base as a camera patch, because its changes to shared files sit inside `CONFIG_1300D` blocks.

The base itself moves as its own piece of work. While it moves, CI may build both bases at once, and each camera moves over once a tester has confirmed it on the new one. Once every camera has moved, the old base is dropped, along with any camera patch the new base already has.

M-Film keeps one version number for all cameras. How far each camera has got is its camera status, not its version.

## Considered Options

- **A Magic Lantern commit of its own for each camera, for good.** Rejected: the film OS is one set of sources and would have to build against many Magic Lanterns (`#ifdef`s per version), and every Magic Lantern fix would have to be brought to each camera separately.
- **Move every camera to the newest Magic Lantern whenever a new camera needs it.** Rejected: too much risk to cameras that already work.
- **An M-Film version number for each camera.** Rejected: the screens and features come from the same code on every camera, so different numbers would only confuse.

## Consequences

- A camera patch doesn't get Magic Lantern's later fixes to its own code until the patch is refreshed or the base moves.
- A camera's folder can also list Magic Lantern modules that must never be in its card files (`no-modules`). The 1300D lists `mlv_lite` and the other RAW video modules, because Magic Lantern has reports of them damaging 1300Ds.
- Magic Lantern turns off camera setting changes on the 1300D (`CONFIG_PROP_REQUEST_CHANGE`), and we leave it off. Loading a roll there doesn't set ISO, white balance or picture style.
