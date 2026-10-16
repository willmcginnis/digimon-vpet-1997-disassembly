# Digimon V-Pet (1997) — a literate disassembly

A prose walk through the firmware of Bandai's original *Digital Monster* virtual pet
(Ver. 1, with Ver. 2 compared alongside), written in the spirit of Knuth's literate
programming: the program explained in the order a reader wants to meet it, with short
excerpts of the machine code where they carry the argument.

The book lives in [`book/`](book/). Start with
[`book/00-the-machine.md`](book/00-the-machine.md).

## What is established, and how

Every claim in the book is labelled:

- **measured** — observed by running the ROM in an emulator (button presses, linked
  battles between two emulated units, memory and I/O traces), or checked mechanically
  (e.g. byte-identical reassembly);
- **read** — inferred from reading the code, not separately exercised.

Headline numbers for Ver. 1 (all measured):

| | |
|---|---|
| ROM size | 8,192 twelve-bit instruction words (2 banks × 16 pages × 256) |
| Decoded and reassembled byte-identically | 8,192 / 8,192 (Ver. 1 and Ver. 2) |
| Reached by static control-flow recovery | 8,087 / 8,192 (74 of the rest are `nop7` filler) |
| Executed across the emulation scenarios | 7,043 / 8,192 |
| Subroutines (`CALL`/`CALZ` targets + vectors) | 281 |

## No ROM here

Bandai's firmware is not distributed. Bring your own dump; `roms/SHA256SUMS` lists the
images this work was done against. Full machine listings reproduce the ROM byte for byte,
so they are generated locally into `generated/` and never committed.

## Tools

- `tools/static/walker.py` — control-flow recovery for the E0C6200 family (PSET paging,
  CALZ, `JPBA` jump tables including the doubled-index idiom, RETS skip-returns), seeded
  optionally with measured program counters.
- `tools/static/asm.py` — an assembler built by inverting the disassembler; used to prove
  the listing is lossless.
- `tools/static/dasm_fixed.py` — three corrections to BrickEmuPy's disassembler found by
  that round trip (see the errata appendix).
- `tools/emulation/` — a headless driver around [BrickEmuPy](https://github.com/azya52/BrickEmuPy)'s
  E0C6200 core, a two-unit link cable, coverage and memory tracing, and the experiments
  behind the battle and Easter-egg chapters.
- `ghidra/` — headless scripts for Ghidra 12 with the
  [E0C6S46 processor module](https://github.com/Veryyes/E0C6S46-Ghidra-Processor): seed the
  vectors and export, then apply the recovered map (computed-jump references, functions,
  names, RAM labels).

Point `BRICK` at a BrickEmuPy checkout and `ROM` at your dump.
