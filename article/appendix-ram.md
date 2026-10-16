# Appendix B — RAM variables

Named nibbles of page 0. *Readers/writers* are the number of distinct instructions measured reading or writing the address; *tasks* are the main-loop tasks or interrupts those writers belong to.

| Address | Name | Conf. | Readers | Writers | Writing tasks | Meaning |
|---|---|---|---:|---:|---|---|
| `000` | `tick_flags` | read | 15 | 7 | animation, input, life, screens, sound | set by the 2 Hz timer IRQ: bit0 every tick, bit3 half-second phase, bits1-2 once a second |
| `001` | `anim_counter` | read | 11 | 3 | animation, input, life, screens, sound |  |
| `002` | `key_event` | measured | 3 | 1 | input | debounced key bits (A=4, B=2, C=1) |
| `003` | `key_state` | read | 8 | 4 | input |  |
| `005` | `status_flags` | measured | 10 | 4 | animation, input, life, sound | bit0 injured, bit1 sick, bit2 ? |
| `006` | `ui_flags` | read | 16 | 10 | animation, input, life, sound |  |
| `009` | `mode` | measured | 23 | 14 | input, life, screens, sound | 0 idle/pet, 1 clock set, 2 menu, 5 battle, 9 evolving, B dying, C grave |
| `00A` | `submode` | measured | 59 | 35 | animation, input, life, screens, sound | per-mode step; battle uses 0-8 |
| `00B` | `species_slot` | measured | 26 | 6 | input, life, screens, sound, spine | growth-chart slot (0 egg, 1 baby I, 2 baby II, 3.. child..; F dead) |
| `00C` | `overlay_icon` | read | 33 | 24 | animation, input, life, screens, sound |  |
| `00D` | `sound_flags` | read | 10 | 7 | animation, input, life, link_battle, screens, spine |  |
| `010` | `link_tx_word` | measured | 5 | 1 | input | 4 nibbles: 16-bit word to send (low nibble first) + complement |
| `015` | `menu_index` | measured | 0 | 1 | input |  |
| `017` | `sound_seq_flags` | read | 14 | 6 | input, life, sound |  |
| `01A` | `clock_seconds` | read | 3 | 1 | life, sound | BCD seconds, 2 nibbles |
| `01C` | `clock_minutes` | read | 2 | 1 | life, sound | BCD minutes, 2 nibbles |
| `01E` | `clock_hour` | read | 4 | 1 | life | 1..12 |
| `01F` | `clock_pm` | read | 2 | 0 |  | bit0 = PM |
| `036` | `injury_minutes` | measured | 0 | 2 | input, life, screens | 2-digit BCD minutes since injury |
| `038` | `injury_hours` | measured | 1 | 2 | input, life, screens, sound | 6 -> death |
| `046` | `stage_seconds` | read | 1 | 2 | animation, input, life, screens, sound | BCD seconds in the current stage |
| `048` | `stage_minutes` | measured | 4 | 3 | animation, input, life, screens, sound, spine | BCD minutes in the current stage |
| `04A` | `stage_hours` | measured | 3 | 4 | animation, input, life, screens, spine | 8-bit hours in the current stage |
| `04C` | `next_evolution_at` | measured | 1 | 2 | life, spine | stage time (BCD minutes + hours) at which the next evolution fires |
| `054` | `schedule_flags` | read | 6 | 4 | animation, life | bit0/bit1 set by the hourly wake/sleep check |
| `066` | `bedtime_hour` | read | 1 | 4 | life | PM hour this species goes to sleep |
| `067` | `wake_hour` | read | 0 | 4 | life | AM hour this species wakes |
| `075` | `battles_since_injury` | read | 0 | 2 | input, life, screens |  |
| `076` | `life_flags` | read | 6 | 2 | input, life, screens | bit1 evolution pending, bit3 ? |
| `078` | `battle_state` | measured | 0 | 1 | input, screens |  |
| `079` | `battle_result` | measured | 0 | 1 | input, screens | 1 win, 2 lose (this device) |
| `07B` | `own_enhancement` | measured | 1 | 2 | input, screens | power bonus sent in packet 1 |
| `07E` | `opp_enhancement` | measured | 0 | 1 | input, screens | from the opponent's packet 1 |
| `07F` | `opp_slot` | measured | 0 | 1 | input, screens | from the opponent's packet 1 |
| `08C` | `energy` | measured | 4 | 2 | input, life, sound | battle energy (decrements per battle) |
| `0A0` | `rng` | measured | 2 | 1 | library | 4 nibbles; A1A0 BCD +73, A3A2 binary +0x73 per loop pass |
| `0A4` | `key_debounce` | read | 1 | 1 | input | A4 last sample, A5 stable-pass count, A6 change pending |
