# Flappy Dot

A tiny Flappy Bird-style clone written in PyGame with no external assets, designed to run both as a normal desktop app and through Pygbag/WebAssembly.

## Run Desktop

```bash
python3 -m pip install -r ../requirements.txt
python3 main.py
```

## Run In Browser

```bash
python3 -m pip install -r ../requirements.txt
python3 -m pygbag .
```

## Tweak It

Most of the important knobs live at the top of `main.py`, including:

- `SCROLL_SPEED`
- `BIRD_GRAVITY`
- `BIRD_FLAP_VELOCITY`
- `BIRD_SIZE`
- `PIPE_SPACING`
- `PIPE_COUNT`
- `PIPE_WIDTH`
- `PIPE_GAP`
- `GROUND_HEIGHT`
- `BACKGROUND_DOT_COUNT`

Controls:

- `Space`, `Up`, `W`, click, or tap to flap
- `R` to reset
- `Esc` to quit on desktop
