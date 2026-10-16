# Appendix C — I/O registers the firmware touches

Register names from BrickEmuPy's E0C6200 core (documented); usage measured.

| Address | Register | Read by | Written by | Tasks |
|---|---|---:|---:|---|
| `F00` | IT (timer int factors) | 2 | 0 | input, life |
| `F01` | ISW (stopwatch int) | 2 | 0 | input |
| `F02` | IPT (prog-timer int) | 3 | 0 | animation, input, life, link_battle, screens, sound |
| `F04` | IK0 (K0 int) | 2 | 0 | input, spine |
| `F10` | EIT | 0 | 1 | spine |
| `F11` | EISW | 0 | 1 | spine |
| `F12` | EIPT | 0 | 3 | animation, input, life, link_battle, screens, sound |
| `F14` | EIK0 | 0 | 2 | input, spine |
| `F26` | RD3-0 | 0 | 1 | animation, input, life, link_battle, screens, sound |
| `F27` | RD7-4 | 0 | 1 | animation, input, life, link_battle, screens, sound |
| `F40` | K0 (buttons: A=4 B=2 C=1, active low) | 3 | 0 | input, spine |
| `F41` | DFK0 | 0 | 1 | spine |
| `F54` | R4 (buzzer) | 6 | 6 | input, life, screens, sound, spine |
| `F62` | P2 (link prong, bit0) | 32 | 7 | input, link_battle, spine |
| `F70` | CTRL_OSC | 3 | 6 | input, link_battle, spine |
| `F71` | CTRL_LCD | 2 | 3 | animation, input, life, link_battle, screens, sound, spine |
| `F72` | LC (contrast) | 0 | 1 | spine |
| `F74` | BZ1 | 0 | 3 | input, sound, spine |
| `F75` | BZ2 | 0 | 1 | input, sound, spine |
| `F76` | TM reset | 1 | 2 | input, spine |
| `F77` | SW ctrl | 0 | 3 | input |
| `F78` | PT ctrl | 0 | 5 | animation, input, life, link_battle, screens, sound |
| `F79` | PTC | 0 | 1 | animation, input, life, link_battle, screens, sound |
| `F7D` | IOC | 2 | 2 | input, link_battle, spine |
