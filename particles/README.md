# PyGame Web Lab

This is a simple project to demonstrate how WASM can be used to run desktop applications in the browser.

## Running The Desktop App

```bash
python3 -m pip install -r requirements.txt
python3 particles.py
```

## Running The Web Port

```bash
python3 -m pip install -r requirements.txt # if not done already
python3 -m pygbag .
```

Use CTRL+C (twice) to stop serving it.

You can (and should!) adjust the constants in the `particles.py` file to change the behavior of the application, e.g. increasing the framerate cap, native (before browser scaling) resolution, and/or (most importantly) the `PARTICLE_COUNT`.

## Performance Differences

In my experience (on an M4 Max), for 1280x720 at 120FPS cap w/ 10k particles, the desktop version ran at around 50 FPS, while the web version ran at a cinematic ~24 FPS.

Why the web version is so much slower:

- pygbag runs CPython compiled to WebAssembly which is then interpreted by the browser's C code, adding overhead
- there's no JIT optimization for Python in WASM (unlike JS)
- Lots of Python objects are created and destroyed on each frame, which is not ideal for performance, esp. in WASM

JS would almost definitely beat WASM in terms of FPS, but that would require maintaining a separate codebase. Which is relevant because...

## Implementation Differences

The PyGame app was not programmed identically to how you would normally write a PyGame app. Normally, pygame apps have a synchronous main loop, but PygBag requires the use of an **async** main loop. That's the primary difference between the two implementations though; most everything else is the same, including (critically) the actual logic for the particle system.

One other (very small) difference is that making pygbag work requires a wrapper (`main.py`) to get things going.

However, a more complex app might have more differences. For instance, there is no support for tkinkter, no OS file dialogs, and no blocking desktop APIs.

tl;dr: the rendering and physics portions (the hard part) are identical between the two implementations. it's mostly just pygame "glue" code that needs to be written differently! but it still works as a desktop app too, so there's still the "one codebase, many platforms" benefit!

## Takeaways

- porting an existing desktop app to the web is a great use case for WASM
- but performance will be worse than the desktop version, esp. if the app is CPU-bound
- don't use Python for CPU-bound tasks like this in the first place!
- if you want to make the fastest possible web app, the answer isn't always WASM (especially not with Python as the source language) - you may genuinely be better off with JS for some things! HOWEVER, as mentioned earlier, maintaining a separate codebase is a big cost! if you've got a decade-old codebase with tens or hundreds of thousands of lines of code, it's probably not worth it to rewrite it in JS!
