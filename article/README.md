# Inside the 1997 Digimon V-Pet

### A literate disassembly of Bandai's *Digital Monster* Ver. 1 firmware

> In 1997 every playground had a rule: kill your Digimon, then press **A** two hundred
> times, **B** two hundred times and **C** twenty-five times, and a flaming Teddymon
> comes back. Nobody's ever did. Twenty-nine years later the mask ROMs have been dumped,
> the CPU has an emulator, and the question can be put to the program itself.

This is a long walk through that program: 8,192 twelve-bit instructions running on a
4-bit Epson microcontroller, with nibble-wide memory, a 32 × 16 dot LCD, three buttons,
a buzzer and one metal prong for fighting. It is written to be read in order, the way
Knuth meant literate programs to be read: the machine first, then the loop that drives
everything, then each subsystem as the loop reaches it. Short excerpts of the machine code
appear where they carry the argument; the ROM itself is not here (see
[Reproducing this](#reproducing-this)).

Every claim is tagged with how it is known:

- **measured** — observed by running the ROM: an emulated unit driven headless, two units
  linked through a model of the prong, memory and I/O traces with the program counter that
  made each access, or a mechanical check such as byte-identical reassembly;
- **read** — inferred from reading the code and not separately exercised;
- **documented** — taken from a named outside source (Epson's manuals, BrickEmuPy,
  DMComm, humulos/NHOKO).

---

## Contents

1. [The machine](#1-the-machine)
2. [How it was read](#2-how-it-was-read)
3. [An atlas of the ROM](#3-an-atlas-of-the-rom)
4. [Power on](#4-power-on)
5. [The loop that runs everything](#5-the-loop-that-runs-everything)
6. [Page zero: a library you can call in one word](#6-page-zero-a-library-you-can-call-in-one-word)
7. [Pixels](#7-pixels)
8. [Three buttons](#8-three-buttons)
9. [The mode machine](#9-the-mode-machine)
10. [Time, care and death](#10-time-care-and-death)
11. [The dice](#11-the-dice)
12. [One wire](#12-one-wire)
13. [Battles](#13-battles)
14. [The factory test](#14-the-factory-test)
15. [The playground rumours, settled](#15-the-playground-rumours-settled)
16. [Ver. 1 against Ver. 2](#16-ver-1-against-ver-2)
17. [Notes on the tools](#17-notes-on-the-tools)
18. [Reproducing this](#reproducing-this)
19. [Appendices](#appendices)

---

## 1. The machine

The V-Pet is built around a member of Epson's **E0C6200** family of 4-bit
microcontrollers, the same core that runs the first-generation Tamagotchi
(**documented**: Epson *E0C6200 Core CPU Manual*; BrickEmuPy runs the Digimon ROMs on its
`E0C6200` core at 1.06 MHz). Three facts about this core shape everything that follows.

**Program words are 12 bits wide; data is 4 bits wide.** The ROM holds 8,192 instruction
words. Data memory is addressed in *nibbles*: there is no byte anywhere in the data
path, so an 8-bit quantity is two adjacent nibbles and the code adds them with carry by
hand. The dumps store each 12-bit word in a 16-bit big-endian slot; the top nibble is zero
in every word of both dumps (**measured**).

**The program counter is split into bank, page and step.** An address is one bank bit,
four page bits and eight step bits: 2 banks × 16 pages × 256 words. Jumps and calls carry
only the 8-bit step, so on their own they stay inside the current page. To leave the page,
a `PSET p` instruction placed immediately in front of the jump names the destination bank
and page for that single jump. The firmware is therefore full of two-word pairs like
`pset 0x0B / call 0B06`. One exception matters a great deal: **`CALZ`** ("call zero")
always lands on page 0 of the current bank in a single word, and Bandai used it to build a
small shared library there (§6).

**Memory pointers are 12 bits, assembled from a page and an offset.** Registers X and Y
are each a 4-bit page (XP, YP) plus an 8-bit offset; `M(X)` is "the nibble X points at".
Before touching I/O the code points XP at page F, before touching game state it points
XP at page 0, and four tiny page-0 helpers exist to do exactly that.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="figures/address_spaces-dark.svg">
  <img src="figures/address_spaces-light.svg" alt="Address spaces: program ROM of 8192 12-bit words in 2 banks of 16 pages; data memory of nibbles: RAM 000-2FF, display RAM E00-E4F and E80-ECF, I/O F00-F7E.">
</picture>

Data memory as this firmware uses it (**measured** from access traces):

| Range | What lives there |
|---|---|
| `000–0FF` | game state: mode, species slot, clock, timers, link buffer, dice, stack |
| `100–1FF` | scratch and draw buffers |
| `200–2FF` | scratch, and from `280` up, the note list the sound interrupt plays |
| `E00–E4F`, `E80–ECF` | display RAM: the bottom and top halves of the dot matrix, plus 8 icons |
| `F00–F7E` | I/O: of the registers the core defines, the firmware touches 24 |

The traces reach address `2FF`, so this chip has 768 nibbles of RAM rather than the
Tamagotchi part's 640.

---

## 2. How it was read

Four instruments, each checking the others.

1. **An emulator, driven without a screen.** BrickEmuPy (azya52) already runs these ROMs.
   Its core was wrapped in a headless harness that presses buttons, holds them during
   reset, renders the LCD to text or PNG, and records every program counter executed and
   every memory access with the program counter that made it. A second harness wires two
   units together through BrickEmuPy's model of the prong so that battles happen between
   two emulated devices, with a hook to drop or alter packets in transit.
2. **Ghidra 12**, headless, with the community E0C6S46 processor module (Veryyes), whose
   instruction set matches this core.
3. **A purpose-built control-flow walker** that follows the paging rules exactly as the
   emulator's core executes them, resolves `JPBA` jump tables (including an idiom that
   doubles the index into a 32-entry table of two-word entries), and handles `RETS`, which
   returns past the instruction after the call.
4. **A reassembler** built by inverting the disassembler. If the annotated listing
   reassembles to the identical ROM, nothing was lost or misread in the text.

What each found, for Ver. 1:

| Measure | Result |
|---|---|
| Words decoded and reassembled byte-identically | **8,192 / 8,192** (Ver. 1 and Ver. 2) — measured |
| Words reached by the walker | **8,087 / 8,192**; 74 of the remainder are `nop7` filler — measured |
| Words actually executed across the scenarios | **7,043 / 8,192** — measured |
| Executed words Ghidra's auto-analysis left undefined | **362** — measured |
| Executed words the walker missed before being seeded with the trace | **75** — measured |
| Subroutines (`CALL`/`CALZ` targets plus interrupt vectors) | **281** — measured |

The scenarios: power-on and reset; hatching and a baby's first hour; menus, feeding,
training and the light; six hours of neglect; a night with the clock wound to bedtime; a
linked battle in each role and a broken link; death and the grave; the factory test,
including the link self-test between two units; every button held during reset; and every
species slot forced in turn and allowed to reach its next evolution.

The round trip paid for itself early. It caught three bugs in BrickEmuPy's
*disassembler* (not its emulation, which is correct): `CP YL,i` printed as `ADC YL,i`,
`DEC M(n)` printed as `INC M(n)`, and `RLC r`'s doubled register field. Ghidra's gaps came
from two places: it cannot follow `JPBA`, and the module treats a `PSET`-prefixed `CALL`
as staying in the current bank, which the emulator's core does not. Details in §17.

---

## 3. An atlas of the ROM

<!-- ATLAS -->

---

## 4. Power on

Execution starts at bank 0, page 1, step 0 (`0x0100`), which jumps over the interrupt
vectors to `0x010E`. What follows is the whole of initialisation (**read**, and every line
**measured** as executed on power-up):

```asm
010E  rst F, 0x0          ; clear flags
010F  ld A, 0x0
0110  ld SPL, A           ; stack pointer = 0x00; the first push lands at 0xFF
0111  ld SPH, A
0112  callz 0007          ; cpu_clock_slow
0113  ld A, 0x0 / ld B, 0x2 / callz 0022    ; zero 000-0DF; the stack at 0E0-0FF survives
0116  callz 0010          ; cpu_clock_fast
0117  ld A, 0x1 / ld B, 0x0 / callz 0022    ; zero all of page 1, then all of page 2
011D  ld A, 0xE / ld B, 0x2 / callz 0022    ; zero E00-EDF: the whole display
0120  callz 0087          ; XP = F (I/O)
0121  ld X, 0x10 / lbpx M(X), 0x04          ; EIT (F10) = 4: enable the 2 Hz timer interrupt
0123  ld X, 0x71 / lbpx M(X), 0x80          ; LCD control (F71) = 0, contrast (F72) = 8
0125  ld X, 0x40 / ld A, M(X)               ; read the buttons (K0)
0127  and A, 0x7
0128  cp A, 0x3           ; exactly A held (active low: 011)?
0129  jp z, 016E          ;   -> factory test
...
0130  callz 00ED
0131  ei
0132  ...                 ; the main loop
```

Two details are worth noticing. The stack pointer starts at `00` and the first push wraps
to `FF`, so the stack grows down from the top of page 0 — which is why the very first
clear stops at `0DF`: it is called from inside a subroutine whose return address is
already sitting at `0FD`–`0FF`. And the factory test is not a
hidden menu: it is the very first decision the program makes, on the very first read of
the buttons.

---

## 5. The loop that runs everything

There is no operating system and no scheduler. From `0x0132` the program calls the same
twelve routines in the same order, forever (**read**; **measured** as the hot path in
every scenario):

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="figures/super_loop-dark.svg">
  <img src="figures/super_loop-light.svg" alt="The main loop calls twelve routines in order, then halts until an interrupt.">
</picture>

```asm
0132  callz 0010          ; cpu_clock_fast
0133  call 01CA           ; task_mark_awake
0134  pset 0x09 / call 0900   ; task_timekeeping
0136  pset 0x07 / call 07BF   ; task_key_scan
0138  pset 0x02 / call 0200   ; task_key_dispatch
013A  pset 0x08 / call 0800   ; task_life_clock
013C  pset 0x0A / call 0A5D   ; task_animation
013E  pset 0x0B / call 0B06   ; task_link_rx
0140  pset 0x0B / call 0B5B   ; task_link_tx
0142  pset 0x04 / call 0410   ; task_mode_render
0144  pset 0x0A / call 0A00   ; task_sound
0146  pset 0x0E / call 0E7B   ; rng_step
0148  ...                 ; anything pending? -> jp 0132
015B  di
...   callz 0007          ; cpu_clock_slow
016B  ei
016C  halt
016D  jp 0132
```

After the twelfth call the loop checks whether anything is still in flight: a key not yet
consumed, a link transfer, a mode that animates continuously. If so it goes straight round
again. If not, it drops the CPU back to its slow oscillator, enables interrupts and
**halts**. The chip then sleeps until one of three interrupts wakes it
(**read**, each handler **measured** as executed):

| Vector | Handler | Job |
|---|---|---|
| `0102` | `17B9` | **Heartbeat.** Reads the timer's 2 Hz factor and turns it into flags in `M(00)`: bit 0 on every tick (the animation frame), bit 3 flipping each half-second, bits 1–2 set once a second. The clock and the animation count these flags. |
| `0106` | `1AC6` | **Key wake.** Acknowledges the button interrupt, disables it, and returns. It does no work; it exists only to end the `HALT` so the loop can scan the keys. |
| `010C` | `1BB3` | **Sound player.** Driven by the programmable timer: walks a note list in RAM from `280`, reloads the timer for each note, and switches the buzzer off at the end. |

The design is a classic low-power super-loop. The interesting consequence comes in §11:
the dice advance once per pass of this loop, so anything that makes the loop run more
passes — pressing a button, an animation — moves the dice.

---

## 6. Page zero: a library you can call in one word

Because `CALZ` reaches page 0 in a single instruction from anywhere in the bank, page 0 is
where the small, hot helpers live: 44 subroutines, 36 of them called from more than one
place (**measured** from the call graph). The busiest, `0089`, is called from 53 sites. The
ones that explain the rest of the code:

| Address | Name | What it does |
|---|---|---|
| `0007` / `0010` | `cpu_clock_slow` / `cpu_clock_fast` | switch the CPU between the 32 kHz and fast oscillators (`F70`) |
| `0022` | `clear_ram_blocks` | zero 16-nibble blocks from the start of page A until B wraps past F; B = 0 clears the whole page |
| `002A` / `0033` | `bcd_inc_mod60` / `bcd_dec_mod60` | two-digit decimal counters that wrap at 60: minutes |
| `0039` | `hour12_inc` | the hour counter, 1 to 12 |
| `007C` | `bcd_inc_sat99` | a decimal counter that sticks at 99 |
| `0087` `0089` `008D` `008F` | page setters | XP = F (I/O), XP = YP = 0, XP = 1, XP = 2 |
| `00A8` / `00C2` | `prog_timer_start` / `_stop` | start or stop the sound interrupt |
| `00E7` | `is_battle_ready_screen` | Z set when mode 5, step 2 |
| `00F8` | `dispatch_page_0F` | a jump table on page F indexed by `M(Y)` |

The decimal helpers tell you how the designers thought: clocks, timers and counters are
kept in binary-coded decimal so that drawing them on the screen needs no division, which a
4-bit CPU with no multiply would have to do by repeated subtraction.

---

## 7. Pixels

### From nibbles to dots

The LCD is a 32 × 16 dot matrix with eight icons around it. The mapping from display RAM
to dots is the single most useful thing to know when reading this firmware
(**documented** from the LCD face in BrickEmuPy, which its author built from the device):

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="figures/display_map-dark.svg">
  <img src="figures/display_map-light.svg" alt="Each LCD column is one byte split across two nibbles. The top half of the screen sits at E82-EC9, the bottom half at E02-E49; left-half columns ascend through memory, right-half columns descend.">
</picture>

Each column of eight dots is one byte, stored as two adjacent nibbles with the higher
nibble on top and bit 3 at the very top. The top half of the screen lives in the second
display window at exactly the same offsets as the bottom half, plus `0x80`. Within each
half the left sixteen columns *ascend* through memory and the right sixteen *descend*,
meeting in the middle — an artefact of how the LCD's segment lines are wired to the
controller. The eight icons occupy the gaps the column runs skip.

### Sprites are code

The E0C6200 has an instruction made for this layout: `LBPX M(X), byte` writes the low
nibble of an 8-bit immediate to `M(X)`, the high nibble to `M(X+1)`, and advances X by
two. One `LBPX` is one column. So the graphics are not stored as data that a blitter
reads; they are stored as *instructions that draw themselves*. Point X at a column of
display RAM, call the routine, and eight `LBPX` instructions paint an 8 × 8 tile
(**read**; the result **measured** on screen):

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="figures/sprite_columns-dark.svg">
  <img src="figures/sprite_columns-light.svg" alt="Eight LBPX instructions with operands 00 38 44 42 21 42 44 38 draw an outlined heart.">
</picture>

The same trick explains `RETD l`, an instruction that returns from a subroutine *and*
writes an 8-bit immediate to `M(X)` and `M(X+1)` on the way out. A routine can end on the
last column of its sprite for free. About a third of the ROM is shaped like this
(see the atlas in §3), most of it in bank 1.

### One handler per species

Bank 1 is organised around the species. At `0x1230` the code reads the growth-chart slot
`M(0B)`, doubles it, and jumps through a 32-word table at `0x1200` made of sixteen
two-word `pset`/`jp` pairs (**read**; the walker needed a dedicated rule for this idiom):

```asm
1230  ld A, M(0xB)        ; species slot 0..15
1231  ld B, 0x0
1232  rcf
1233  rlc A               ; A = slot * 2 (low nibble), carry -> B
1234  rlc B
1235  ld X, 0xD2
1236  jpba                ; jump to 0x1200 + B:A
...
1200  pset 0x1C / jp 1C94  ; slot 0 (egg)
1202  pset 0x12 / jp 12B8  ; slot 1
1204  pset 0x13 / jp 1310  ; slot 2
...
121E  pset 0x1E / jp 1E48  ; slot 15
```

Fifteen distinct pages serve the sixteen slots; only the egg (slot 0) and slot 13 share
one.

---

## 8. Three buttons

The buttons are bits 2, 1 and 0 of the input port `K0` at `F40`, active low (**documented**,
BrickEmuPy device configuration). They are never read in an interrupt. The key-wake
interrupt only ends the `HALT`; the reading happens in the main loop, in
`task_key_scan` at `0x07BF` (**read**; presses **measured** to register at hold times from 80 to 200 ms):

```asm
07C2  ld Y, 0x40          ; YP = F, so M(Y) = K0
07C3  ld A, M(Y)
07C4  xor A, 0xF          ; active low -> active high
07C5  and A, 0x7          ; A=4, B=2, C=1
07C6  ld X, 0xA4
07C7  cp M(X), A          ; same as the last sample?
07C8  jp z, 07CC
07C9  ldpx M(X), A        ; no: remember it (A4), reset the count (A5),
07CA  ldpx M(X), 0x0      ;     and mark a change pending (A6)
07CB  or M(X), 0x1
07CC  ld X, 0xA6
07CD  fan M(X), 0x1       ; change pending?
07CE  jp z, 07D6
07CF  ld X, 0xA5
07D0  add M(X), 0x1       ; count stable passes
07D1  cp M(X), 0x3
07D2  jp c, 07D6
07D3  ld X, 0xA6          ; three in a row: accept
07D4  and M(X), 0xE
07D5  ld M(0x2), A        ; key_event = A
07D6  ret
```

A new button state is accepted after it has been seen on three consecutive passes of the
main loop. The accepted state goes into `key_event` at `M(02)`, and every screen reads
keys only from there. Note where the debounce state lives: `A4`–`A6`, right next to the
dice at `A0`–`A3`.

`task_key_dispatch` at `0x0200` then routes the event by mode. Its very first decision
is the one that settles the playground rumour (§15):

```asm
0243  cp B, 0x9           ; B = mode
0244  jp nc, 0208         ; mode >= 9 (evolving, dying, dead): drop the key
```

---

## 9. The mode machine

<!-- MODES -->

---

## 10. Time, care and death

<!-- LIFE -->

---

## 11. The dice

Every random decision in the game draws on four nibbles at `A0`–`A3`, advanced by
`rng_step` at `0x0E7B`, the last call of every main-loop pass (**read**; the values
**measured** in traces):

```asm
0E7B  callz 0089
0E7C  ld X, 0xA0
0E7D  sdf                 ; decimal mode on
0E7E  adc M(X), 0x3       ; A1:A0 += 73, in BCD
0E7F  inc X
0E80  adc M(X), 0x7
0E81  rdf                 ; decimal mode off
0E82  ld X, 0xA2
0E83  adc M(X), 0x3       ; A3:A2 += 0x73, in binary
0E84  inc X
0E85  adc M(X), 0x7
0E86  ret
```

It is not a random number generator in any statistical sense. It is two counters, one
stepping by 73 in decimal and one by `0x73` in binary, read at whatever moment a decision
is needed. Its unpredictability comes entirely from the number of main-loop passes that
happen between decisions, which depends on button presses, animation and the link. That is
why a sweep of battle start times (§13) finds the outcome flipping with a few hundred
milliseconds' difference in when B is pressed, and why no fixed button sequence can steer
it.

---

## 12. One wire

Two V-Pets fight through a single metal prong: one open-drain line, pulled high when
idle, that either unit can pull low. The firmware drives and samples it through bit 0 of
port `P2` (`F62`), polled from the main loop by `task_link_rx` at `0x0B06` and
`task_link_tx` at `0x0B5B` (**measured**: the only code that touches `F62`).

A word is sixteen bits. Each bit is a high/low pair whose split carries the value
(timings **documented** from BrickEmuPy's `CON_DGM` peripheral model; bit order
**measured** against DMComm's notation):

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="figures/link_timing-dark.svg">
  <img src="figures/link_timing-light.svg" alt="Pulse-width encoding: a 64 ms start pulse, two sync periods, then 16 bits each a high/low pair, then an end period.">
</picture>

Every word is sent together with its complement: the transmit routine at `0x0B16`
inverts the queued nibbles before sending, so a receiver can reject a corrupted word.
The factory test uses the link layer bare: in its comm screen, pressing A sends `5AA5`
and expects `A55A` back (**measured** between two emulated units: both show "OK!").

---

## 13. Battles

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="figures/battle_sequence-dark.svg">
  <img src="figures/battle_sequence-light.svg" alt="Unit A sends packet 1, unit B replies, A decides the outcome alone and sends it in packet 2, B takes the complement.">
</picture>

A battle is four words (**measured** between two emulated units):

1. The **initiator** — the unit whose B press starts the exchange while the other waits in
   battle stance — sends packet 1: its slot and enhancement (with complements).
2. The responder answers with its own packet 1.
3. The initiator now has everything it needs. `battle_outcome_roll` at `0x0D7A` computes a
   **threshold** from the two slots and the difference in enhancement, compares one nibble
   of the dice against it, and sends packet 2 carrying the *outcome*: 1 for a win, 2 for a
   loss.
4. The responder does not compute anything. At `0x0EB0` it takes `3 − outcome` and sends
   its own packet 2.

Then both screens play twenty seconds of animation whose ending was fixed about 0.6 s
after the button press.

### The threshold

The comparison is `win ⇔ M(A3) ≥ threshold`, so the initiator's chance is
`(16 − threshold) / 16`. Rather than paraphrase the comparison tree at `0x0D7A`, the
routine was executed on the emulated CPU for every pairing of slots (**measured**;
identical in Ver. 2, where the routine sits four words later at `0x0D7E`):

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="figures/battle_odds-dark.svg">
  <img src="figures/battle_odds-light.svg" alt="Heatmap of the initiator's wins out of 16 for every pairing of the twelve Ver.1 Digimon.">
</picture>

Three things fall out of the table.

- **Stage dominates.** A child initiating against an adult wins 2 or 3 times in 16; an
  adult against a child 13 or 14. A Perfect against anything below it wins 11 to 15.
- **Enhancement is linear.** Each point of enhancement the opponent has over you adds one
  to the threshold, exactly one sixteenth of a win, clamped at both ends (**measured**:
  from −4 to +4 the threshold for an even child match runs 4, 5, 6 … 12).
- **The table is not symmetric, so it matters who initiates.** If the two rows agreed,
  "A initiates against B" and "B initiates against A" would give complementary odds. They
  often do not. Two adults: whoever initiates wins 9 in 16, either way round. Two Perfects:
  whoever initiates wins only 5 in 16, so the better move is to wait. Agumon against
  Numemon: if Agumon initiates it wins 2 in 16; if Numemon initiates, Agumon wins 7. This is
  the mechanism behind an old forum tip that "it might matter which device you press the
  button on".

### What tampering does (measured)

The responder trusts packet 2 without checking it against anything:

| Experiment | Initiator | Responder |
|---|---|---|
| Normal battle | loses | wins |
| Flip the initiator's packet 2 in transit | loses | **loses** |
| Cut the line after packet 1 | loses | no result |
| Cut the line before the first reply | no result | no result |
| Mash A/B during the first half second | 3 of 16 timings: both lose; 1: result flips; 2: one side gets none | |
| Mash after about one second | no effect | no effect |

---

## 14. The factory test

Holding A while resetting sends the program to `0x016E` before the main loop ever
starts (§4). It fills the whole of display RAM with ones, then hands over to the test at
`0x09F4` (**measured**):

| Screen | Next key | Purpose (read) |
|---|---|---|
| every dot and icon on | B | find dead segments |
| checkerboard, four of the icons | C | find shorts between neighbouring segments |
| inverse checkerboard, the other four icons | A | the same, inverted; **A also sends `5AA5` on the prong** |
| comm result | — | "OK!" once the partner's `A55A` comes back (**measured** between two units) |

No other button combination held during reset does anything except restart the egg
(**measured**: B, C, A+B, A+C, B+C, A+B+C).

---

## 15. The playground rumours, settled

The 2010 "Digimon Mythbusters" thread on With the Will collected the schoolyard cheats.
Each was tried on the emulated Ver. 1 (**measured**), and the code explains each result.

| Rumour | What happens | Why |
|---|---|---|
| **Flaming Teddymon**: on the grave, A ×200, B ×200, C ×25 | nothing; the screen never changes | the key gate at `0x0243` drops every key while the mode is 9 or above. Comparing the 640 nibbles of RAM below `280` (all game state) after 25, 24 and 26 C presses, after a different press speed and after no presses at all, the only differences were the last key, stack residue and the dice. Nothing counts presses. |
| **Choose your Digimon**: reset, then C ×400 | nothing | the same comparison after 399, 400 and 401 presses: no nibble tracks the count |
| **Sure win**: AAABBBCC in battle | no effect once the battle has started | the result is fixed about 0.6 s after the B press (§13); mashing during the handshake only corrupts it (both lose, no result, or a flip) |
| **Poison your opponent**: ABCAABC | no effect | as above |
| **Shadow battle**: pull the units apart at the last moment | real, and explained | if the line breaks after the initiator has computed the outcome, it keeps its result and the other unit gets none (§13) |
| **Glitch Digimon** from battery tricks | consistent with the code | forcing only the species slot `M(0B)` produces a body that will not battle: a mature sprite with a baby's empty energy, much like the "insta-Teddymon that refuses every command" stories. Real battery-contact glitches corrupt RAM in ways an emulator cannot reproduce faithfully, so this is consistency, not proof. |

And two real things the rumours missed:

- **A + C on the grave** starts a new egg without a reset. The handler at `0x0CEF` checks
  for exactly that pair while the mode is C (**measured**).
- **Holding A at power-on** runs the factory test (§14), the first decision the program
  makes.


---

## 16. Ver. 1 against Ver. 2

Ver. 2 swaps the roster (Punimon, Tsunomon, Gabumon, Elecmon and their lines, per humulos)
but not the machine. Aligning the two instruction streams, with jump targets reduced to
their 8-bit step so that shifted code still matches (**measured**):

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="figures/versions-dark.svg">
  <img src="figures/versions-light.svg" alt="Alignment of Ver.1 and Ver.2: bank 0 is 82% shared in long runs; bank 1 only 35% in short runs.">
</picture>

| | Ver. 1 words in identical aligned runs |
|---|---|
| bank 0 (logic) | 3,376 / 4,096 — **82%** |
| bank 1 (species graphics and animation) | 1,436 / 4,096 — **35%** |
| whole ROM | 4,812 / 8,192 — 59%, in 755 runs, the longest 246 words |

The battle outcome routine is the cleanest example: identical instruction for instruction,
four words later in Ver. 2 (`0x0D7E`), and executing it yields the same threshold table
(§13). The two ROMs are one program with two sets of monsters.


---

## 17. Notes on the tools

### Ghidra and the E0C6S46 module

The community module (Veryyes/E0C6S46-Ghidra-Processor) compiles cleanly with Ghidra 12's
SLEIGH compiler and decodes every instruction correctly. Auto-analysis of Ver. 1 found
303 functions but left 362 *executed* words undefined (**measured**). Two causes:

1. **`JPBA` is a computed jump** to `B:A` on the current or `PSET` page. Ghidra cannot know
   B and A, so the jump tables behind it — the per-species table at `0x1200`, the mode
   handlers, the battle state machine — stay dark. `ghidra/ApplyMap.java` adds the
   recovered targets as computed-jump references.
2. **A `PSET`-prefixed `CALL` keeps the current bank** in the module
   (`:CALL s (thisPcb) is ... pprev=1`). In the emulator's core, which demonstrably runs
   the game, the `PSET` supplies the bank too.

Of Ghidra's 303 functions, 127 are not call targets at all: they are cross-page `JP`
targets that Ghidra promotes to functions. That is a different definition of "function",
not a disagreement about code; this article counts subroutines as `CALL`/`CALZ` targets plus
interrupt vectors (281).

### BrickEmuPy's disassembler

The round trip through the reassembler found three display bugs, all in the
disassembler only; the emulation core executes every one of these correctly
(**measured**):

| Opcode | Shown as | Actually |
|---|---|---|
| `A70`–`A7F` | `adc YL, i` | `cp YL, i` (the core's handler is `_cp_yl_i`) |
| `F70`–`F7F` | `inc M(n)` | `dec M(n)` (unused by both ROMs) |
| `AFx` | `rlc r` from the low two bits | the register field is written twice; the ROM uses only the canonical form |

`tools/static/dasm_fixed.py` patches all three.

### The walker

`tools/static/walker.py` follows the emulator core's paging rules exactly: a `PSET`
affects only the next jump or call and supplies both bank and page; `CALZ` goes to page 0
of the current bank; `RET` restores page and step but never the bank; `RETS` returns one
instruction further, which the walker only follows for callees that can actually execute
`RETS`. `JPBA` targets come from the nearest preceding `ld B, i`, including the
`ld B,0 / rcf / rlc A / rlc B` idiom that builds a doubled, even index into a table of
two-word `pset`/`jp` entries. One table (`0x1E47`) indexes from RAM and is filled in from
the execution trace instead.


---

## Reproducing this

Nothing here contains Bandai's code beyond short excerpts. To rebuild every number and
figure you need your own dump of the Ver. 1 (and optionally Ver. 2) mask ROM; the SHA-256
of the images used is in `roms/SHA256SUMS`.

```sh
git clone https://github.com/azya52/BrickEmuPy
export BRICK=$PWD/BrickEmuPy ROM=roms/digimon_v1.bin

# static map and lossless round trip
PYTHONPATH=tools/static python3 tools/static/walker.py $ROM generated/v1 $BRICK
#   (writes generated/v1/static.json; listing and reassembly checks in tools/static)

# emulation scenarios: coverage, memory traces, task attribution, mode transitions
cd tools/emulation
PYTHONPATH=$BRICK python3 coverage.py evolve ../../generated/cov/evolve.json ../../$ROM

# figures
python3 tools/figures/figs_static.py article/figures
python3 tools/figures/figs_battle.py data/battle_threshold_v1.json article/figures
```

Ghidra: install the E0C6S46 module as a user extension, compile its `.slaspec` with
`support/sleigh`, import the ROM with `-processor E0C6S46:2:default -loader BinaryLoader`,
and run `ghidra/SeedAndExport.java`, then `ghidra/ApplyMap.java` with the map the walker
produces.


---

## Appendices

<!-- APPENDICES -->
