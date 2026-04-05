# Wasm Lab

This is a collection of small projects that demonstrate a few uses of WebAssembly.

## Labs

### Lab 1: Benchmarks

### Lab 2: Particle Sim

```bash
python3 -m pip install -r requirements.txt
python3 -m pygbag particles
```

Works on desktop as well; see the README files in each project for more details.

### Lab 3: Flappy Bird Clone

```bash
python3 -m pip install -r requirements.txt
python3 -m pygbag flappy-dot
```

Works on desktop as well; see the README files in each project for more details.

### Lab 4: Compiled games

1. Make sure that you have the `Dev Containers` extension installed in VSCode, as well
as have either `Docker` or `Podman` with `Docker-Podman` as your shim.
2. Hit `f1` or `ctrl`-`shift`-`p` and search for "Build and Open in Container"
3. Wait for the files to show up. This may take a few minutes.
4. Hit `f1` or `ctrl`-`shift`-`p` and search "Run Task". Select any of the following
- `Serve jumpy`
- `Serve punchy`
- `CMake Compile` followed by `CMake Serve`