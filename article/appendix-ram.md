# Appendix B — RAM variables

Named nibbles of page 0. *Readers/writers* are the number of distinct instructions measured reading or writing the address; *tasks* are the main-loop tasks or interrupts those writers belong to.

| Address | Name | Conf. | Readers | Writers | Writing tasks | Meaning |
|---|---|---|---:|---:|---|---|
| `000` | `tick_flags` | read | 16 | 9 | animation, input, life, sound, spine | set by the 2 Hz timer IRQ: bit0 every tick, bit3 half-second phase, bits1-2 once a second |
| `001` | `anim_counter` | read | 13 | 5 | animation, input, life, link_battle, screens, sound, spine |  |
| `002` | `key_event` | measured | 6 | 2 | input, spine | debounced key bits (A=4, B=2, C=1) |
| `003` | `key_state` | read | 15 | 10 | input, spine |  |
| `005` | `status_flags` | measured | 11 | 6 | animation, input, life, sound, spine | bit0 injured, bit1 sick, bit2 ? |
| `006` | `ui_flags` | read | 17 | 12 | animation, input, life, sound, spine |  |
| `007` | `poop_count` | read | 5 | 4 | life, screens, spine | piles on screen; +1 per poop (08ED), cleared by FLUSH (04D7); the 8th calls set_injured |
| `009` | `mode` | measured | 27 | 21 | input, life, screens, sound, spine | 0 home, 1 clock, 2-8 menu icons, 9 evolving, A pooping, B dying, C grave |
| `00A` | `submode` | measured | 59 | 49 | animation, input, life, link_battle, screens, sound, spine | per-mode step; battle uses 0-8 |
| `00B` | `species_slot` | measured | 29 | 12 | input, life, screens, sound, spine | growth-chart slot (0 egg, 1 baby I, 2 baby II, 3.. child..; F dead) |
| `00C` | `overlay_icon` | read | 34 | 42 | animation, input, life, link_battle, screens, sound, spine |  |
| `00D` | `sound_flags` | read | 16 | 12 | animation, input, life, link_battle, screens, spine |  |
| `010` | `link_tx_word` | measured | 5 | 7 | input, link_battle, spine | 4 nibbles: 16-bit word to send (low nibble first) + complement |
| `015` | `menu_index` | measured | 1 | 2 | input, spine |  |
| `017` | `sound_seq_flags` | read | 15 | 8 | input, life, sound, spine |  |
| `01A` | `clock_seconds` | read | 3 | 4 | input, life, sound, spine | BCD seconds, 2 nibbles |
| `01C` | `clock_minutes` | read | 2 | 3 | input, life, sound, spine | BCD minutes, 2 nibbles |
| `01E` | `clock_hour` | read | 5 | 3 | input, life, spine | 1..12 |
| `01F` | `clock_pm` | read | 2 | 2 | spine | bit0 = PM |
| `036` | `injury_count` | read | 0 | 4 | input, life, screens, spine | 2-digit BCD count of injuries, +1 in set_injured; 20 -> death (0518) |
| `038` | `injury_minutes` | measured | 1 | 4 | input, life, screens, sound, spine | 2-digit BCD minutes since the injury |
| `03A` | `injury_hours` | measured | 2 | 4 | input, life, screens, spine | hours untreated; 6 -> death (08DA) |
| `046` | `stage_seconds` | read | 4 | 4 | animation, input, life, screens, sound, spine | BCD seconds in the current stage |
| `048` | `stage_minutes` | measured | 4 | 4 | animation, input, life, screens, sound, spine | BCD minutes in the current stage |
| `04A` | `stage_hours` | measured | 3 | 8 | animation, input, life, screens, spine | 8-bit hours in the current stage |
| `04C` | `next_evolution_at` | measured | 1 | 5 | life, spine | stage time (BCD minutes + hours) at which the next evolution fires |
| `054` | `schedule_flags` | read | 9 | 9 | animation, life, spine | bit0/bit1 set by the hourly wake/sleep check |
| `066` | `bedtime_hour` | read | 1 | 7 | life, spine | PM hour this species goes to sleep |
| `067` | `wake_hour` | read | 1 | 7 | life, spine | AM hour this species wakes |
| `075` | `battles_since_injury` | read | 0 | 4 | input, life, screens, spine |  |
| `076` | `life_flags` | read | 6 | 4 | input, life, screens, spine | bit1 evolution pending, bit3 ? |
| `078` | `battle_state` | measured | 0 | 5 | input, life, link_battle, screens, spine |  |
| `079` | `battle_result` | measured | 7 | 5 | input, life, link_battle, screens, spine | 1 win, 2 lose (this device) |
| `07B` | `own_enhancement` | measured | 3 | 4 | input, life, link_battle, screens, spine | power bonus sent in packet 1 |
| `07E` | `opp_enhancement` | measured | 1 | 4 | input, life, link_battle, screens, spine | from the opponent's packet 1 |
| `07F` | `opp_slot` | measured | 1 | 4 | input, life, link_battle, screens, spine | from the opponent's packet 1 |
| `080` | `poop_timer` | read | 2 | 4 | input, life, sound, spine | 80-81 BCD minutes, 82 hours; at 3 hours (08D6..0881) a poop is due |
| `08C` | `energy` | measured | 5 | 5 | animation, input, life, screens, sound, spine | battle energy (decrements per battle) |
| `0A0` | `rng` | measured | 3 | 2 | library, spine | 4 nibbles; A1A0 BCD +73, A3A2 binary +0x73 per loop pass |
| `0A4` | `key_debounce` | read | 1 | 2 | input, spine | A4 last sample, A5 stable-pass count, A6 change pending |
