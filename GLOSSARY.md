# M-Film

M-Film turns a Canon DSLR or EOS M running Magic Lantern into a film camera: you load a roll of a film stock and shoot it, then develop it in the camera or on a computer.

## Cameras

**Camera**:
One Canon model on one Canon firmware version, such as the 5D Mark III on 1.2.3. A model with two firmware versions counts as two cameras.
_Avoid_: platform, body (on the camera side), model (when the firmware matters)

**Port**:
The work that brings M-Film to a new camera. It is done when the camera has its own download and is listed with status Testing. It does not have to work yet.
_Avoid_: support (for a camera nobody has tried)

**Camera status**:
How far M-Film has got on a camera. The statuses are **Working** (tried, works), **Issues** (tried, with a known problem), **Testing** (has a download, nobody has tried it), **Planned** and **No** (Magic Lantern can't run there yet).
_Avoid_: supported, experimental

**Base**:
The one Magic Lantern version that every camera is built on.
_Avoid_: ML version, pin (on its own)

**Camera patch**:
A change to Magic Lantern that only one camera's build gets, because the base doesn't have it yet.
_Avoid_: fork patch, hotfix

**Tester**:
Someone who owns the camera, tries a build on it and reports in that camera's issue.

## Shooting

**Film stock**:
One of the films on the shelf, such as a colour negative or a black-and-white film, with its own look and ISO.
_Avoid_: film (on its own), preset, LUT

**Look**:
What a film stock does to a picture: its colour, tone, grain, halation and softness.
_Avoid_: style, filter, profile, colour (when you mean all five)

**Reference**:
The one paired shot that a film stock's look is measured against. A datasheet, a colour table or any other scan of the film is not a reference: a look can be built from the first two and compared by eye with the third, not measured against them.
_Avoid_: ground truth, sample (the samples on the shelf are M-Film's own prints)

**Paired shot**:
The same scene with a colour chart, shot on the real film and scanned by a lab, and shot on a Canon, with a record of how both were made. A film stock can have several; one of them is its reference.
_Avoid_: comparison shot, test shot

**Record**:
The written account of one paired shot: the film, both cameras, the light, the lab and its scanner, who shot it, and what each frame shows and is used for.
_Avoid_: metadata, log, sidecar

**Locked scan**:
A lab scan of a whole roll with the scanner's frame-by-frame corrections off and nothing corrected by hand, so every frame is treated alike. The reference is a locked scan. The lab's everyday scan of the same roll is the **automatic scan**, kept to compare.
_Avoid_: flat scan, raw scan, uncorrected scan

**Held-back frame**:
A frame of a paired shot that is kept out of building the look and used only to judge it.
_Avoid_: test frame, validation frame

**Pass mark**:
The largest distance from its reference at which a film stock still counts as measured. There is one for colour and one for tone.
_Avoid_: threshold, tolerance (that is what a camera is allowed to differ by)

**Measured**:
A film stock whose colour and tone are within the pass mark of its paired shot. For a black-and-white film stock, tone alone. Every other film stock is **not measured yet**, whether nobody has shot it or its look is still too far away.
_Avoid_: accurate, calibrated, verified, no reference yet

**Roll**:
A run of frames shot on one film stock, up to the roll's length.
_Avoid_: session, album

**Loading a roll**:
Choosing a film stock and starting a roll. Where the camera allows it, the camera takes on the film stock's ISO, white balance and picture style. Where it doesn't, the look comes only when the roll is developed, and each frame keeps the white balance the camera was on.
_Avoid_: applying a film, selecting a preset

## Website

**Body**:
The picture of a camera's back on the website, with buttons you can press.
_Avoid_: camera (on the website)

## Developing

**Darkroom**:
The developing that happens inside the camera.
_Avoid_: Darkrooms (that is the desktop program)

**Darkrooms**:
The desktop program that develops rolls on a computer.
