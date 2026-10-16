# Appendix C — I/O registers the firmware touches

Register names from BrickEmuPy's E0C6200 core (documented); usage measured.

| Address | Register | Read by | Written by | Tasks |
|---|---|---:|---:|---|
| `F00` | IT (timer int factors) | 1 | 0 | input, life, screens, sound |
| `F02` | IPT (prog-timer int) | 3 | 0 | animation, input, life, screens, sound |
| `F04` | IK0 (K0 int) | 2 | 0 | animation, input, life, screens, spine |
| `F12` | EIPT | 0 | 3 | animation, input, life, screens, sound |
| `F14` | EIK0 | 0 | 2 | animation, input, life, screens, spine |
| `F26` | RD3-0 | 0 | 1 | animation, input, life, screens, sound |
| `F27` | RD7-4 | 0 | 1 | animation, input, life, screens, sound |
| `F40` | K0 (buttons: A=4 B=2 C=1, active low) | 2 | 0 | input, spine |
| `F41` | DFK0 | 0 | 1 | spine |
| `F54` | R4 (buzzer) | 6 | 6 | input, life, screens, sound |
| `F62` | P2 (link prong, bit0) | 8 | 7 | link_battle |
| `F70` | CTRL_OSC | 3 | 6 | link_battle, spine |
| `F71` | CTRL_LCD | 2 | 2 | animation, input, life, screens, sound |
| `F74` | BZ1 | 0 | 3 | screens, sound |
| `F75` | BZ2 | 0 | 1 | sound |
| `F76` | TM reset | 0 | 1 | spine |
| `F78` | PT ctrl | 0 | 5 | animation, input, life, screens, sound |
| `F79` | PTC | 0 | 1 | animation, input, life, screens, sound |
| `F7D` | IOC | 2 | 2 | link_battle |
