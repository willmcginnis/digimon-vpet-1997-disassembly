# Ghidra

Headless Ghidra 12.0.4 scripts for the Digimon V-Pet ROMs, using the community
[E0C6S46 processor module](https://github.com/Veryyes/E0C6S46-Ghidra-Processor) (Veryyes;
the E0C6S46 has the same instruction set as the E0C6200 core in the V-Pet). No ROM and no
Ghidra project is in this repository. The project would contain the ROM bytes, so you build
it yourself from your own dump.

| File | What it does |
|---|---|
| `SeedAndExport.java` | Seeds the reset and interrupt vectors of both banks' tables, disassembles, creates functions (repeated until nothing new appears), and exports `functions.tsv`, `coverage.tsv`, `instr_starts.txt`, `refs.tsv` and `listing.txt` into the directory given as its argument |
| `ApplyMap.java` | Reads a map from `tools/static/export_ghidra_map.py`. It disassembles every word the walker reached, adds the resolved `JPBA` targets as computed-jump references, creates and names subroutines, labels named entry points, and names RAM and I/O |
| `AddressProbe.java` | Prints how numbers map to addresses in the module's word-addressed `rom` space (see the pitfall below) |

## Running it

1. Install the module as a user extension (`~/.config/ghidra/ghidra_12.0.4_PUBLIC/Extensions/E0C6S46`).
2. Compile its `.slaspec` with `support/sleigh`.
3. Run Ghidra twice, as below:

```sh
G=$PWD/generated ROM=$PWD/roms/digimon_v1.bin
H=~/ghidra_12.0.4_PUBLIC/support/analyzeHeadless
mkdir -p $G/ghidra/proj $G/ghidra/v1_alone $G/ghidra/v1_mapped
# 1. Ghidra on its own
$H $G/ghidra/proj digimon -import $ROM -overwrite -processor E0C6S46:2:default \
   -loader BinaryLoader -loader-baseAddr 0 -scriptPath ghidra \
   -postScript SeedAndExport.java $G/ghidra/v1_alone
# 2. the same program with the recovered map applied
$H $G/ghidra/proj digimon -process digimon_v1.bin -noanalysis -scriptPath ghidra \
   -postScript ApplyMap.java data/ghidra/ghidra_map_v1.tsv \
   -postScript SeedAndExport.java $G/ghidra/v1_mapped
```

Everything Ghidra writes goes under `generated/`, which git ignores. Keep it there. The
project holds the ROM, and the exported `listing.txt` and `refs.tsv` hold its
instructions; only the address, coverage and name exports in `data/ghidra/` are safe to
publish. The scripts expect their output directory to exist. Tested with Ghidra 12.0.4
and the module at revision `9382782`.

The maps for both versions are already in `data/ghidra/`. They hold addresses and names
only, so you can use them without running the walker. To regenerate them, see
[Reproducing this](../article/README.md#reproducing-this). The Ver. 2 names are carried
over from Ver. 1 by `tools/static/port_names.py` and are marked `ported`.

## What it measured

All figures below are **measured**. They come from `data/ghidra/summary.json` and the
exports next to it (`*_coverage.tsv` and `*_functions.tsv`, alone and mapped, for both
versions; `alone_bank0`, `alone_both` and `mapped` are the three runs).

| | Ver. 1 | Ver. 2 |
|---|---:|---:|
| Words Ghidra decodes on its own, both vector tables seeded | 4,799 (bank 0: 3,603, bank 1: 1,196) | 4,844 (bank 0: 3,597, bank 1: 1,247) |
| … with only the bank-0 table seeded | 4,788 | 4,833 |
| Words the walker reaches | 8,092 | 8,045 |
| Walker-reached words Ghidra alone leaves undefined | 3,293 | 3,201 |
| Executed words Ghidra alone leaves undefined | 2,612 of 7,080 | (no Ver. 2 traces) |
| Words decoded with the map applied | 8,098 | 8,045 |
| Walker-reached words still undefined with the map | 0 | 0 |
| Functions Ghidra finds on its own / matching walker subroutines | 320 / 193 | 334 / 197 |
| Walker subroutines / present as functions after the map | 288 / 288 | 267 / 267 |

Seeding the bank-1 vector table adds only 11 words in each version. The interrupt bodies
are already reachable through the bank-0 trampolines, and only the bank-1 table's own
`PSET`/`JP` pairs are new. `SeedAndExport.java` seeds both tables by default; pass
`bank0` as a second script argument to reproduce the bank-0-only row.

The gap is `JPBA`, a computed jump to `B:A`. Ghidra can't know the registers, so the
25 jump tables (the per-species table at `0x1200` among them) hide most of bank 1. Ghidra
also counts every `JP` target it promotes to a function, which is why its function counts
are higher than the subroutine counts after the map.

## Two things to know about the module

- **Word addressing.** `rom` is a word-addressed space, but `AddressSpace.getAddress(long)`
  takes a *byte* offset. `getAddress(0x100)` is `rom:0080`, as `AddressProbe.java` shows,
  so word `w` must be requested as `getAddress(w * getAddressableUnitSize())`. That is
  the `W()` helper in `ApplyMap.java`. Address *strings* are already in words: the
  module's `.pspec` `start` symbol, `rom:0x110`, lands on word `0x110`.
- **`CALL` after `PSET` keeps the bank.** That matches Epson's manual (`CALL` loads
  `PCP ← NPP`, with no bank transfer) and the hardware's `RET`, which can't return across
  banks. BrickEmuPy's core takes the bank from the `PSET` instead. Neither Digimon ROM
  ever makes a cross-bank call, so the two agree on these ROMs.
