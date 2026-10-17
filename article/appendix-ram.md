# Appendix B — RAM variables

Named nibbles of page 0. *Readers/writers* are the number of distinct instructions measured reading or writing the address; *tasks* are the main-loop tasks or interrupts those writers belong to.

| Address | Name | Conf. | Readers | Writers | Writing tasks | Meaning |
|---|---|---|---:|---:|---|---|
| `000` | `tick_flags` | read | 16 | 9 | animation, input, life, sound, spine | set by the 2 Hz timer IRQ: bit0 every tick, bit3 half-second phase, bits1-2 once a second |
| `001` | `anim_counter` | read | 12 | 5 | animation, input, life, link_battle, screens, sound, spine |  |
| `002` | `key_event` | measured | 6 | 2 | input, spine | debounced key bits (A=4, B=2, C=1) |
| `003` | `key_state` | read | 15 | 10 | input, spine |  |
| `005` | `status_flags` | measured | 13 | 7 | animation, input, life, screens, sound, spine | bit0 injured, bit1 sick, bit2 ? |
| `006` | `ui_flags` | read | 17 | 12 | animation, input, life, sound, spine |  |
| `007` | `poop_count` | read | 5 | 4 | life, screens, spine | piles on screen; +1 per poop (08ED), cleared by FLUSH (04D7); the 8th calls set_injured |
| `009` | `mode` | measured | 27 | 21 | input, life, screens, sound, spine | 0 home, 1 clock, 2-8 menu icons, 9 evolving, A pooping, B dying, C grave |
| `00A` | `submode` | measured | 57 | 47 | animation, input, life, link_battle, screens, sound, spine | per-mode step; battle uses 0-8 |
| `00B` | `species_slot` | measured | 29 | 11 | input, life, screens, sound, spine | growth-chart slot (0 egg, 1 baby I, 2 baby II, 3.. child..; F dead) |
| `00C` | `overlay_icon` | read | 33 | 40 | animation, input, life, link_battle, screens, sound, spine |  |
| `00D` | `sound_flags` | read | 16 | 12 | animation, input, life, link_battle, screens, spine |  |
| `010` | `link_tx_word` | measured | 5 | 7 | input, link_battle, spine | 4 nibbles: 16-bit word to send (low nibble first) + complement |
| `015` | `menu_index` | measured | 1 | 2 | input, spine |  |
| `017` | `sound_seq_flags` | read | 15 | 8 | input, life, sound, spine |  |
| `01A` | `clock_seconds` | read | 3 | 3 | input, life, screens, sound, spine | BCD seconds, 2 nibbles |
| `01C` | `clock_minutes` | read | 2 | 2 | input, life, screens, sound, spine | BCD minutes, 2 nibbles |
| `01E` | `clock_hour` | read | 5 | 3 | input, life, spine | 1..12 |
| `01F` | `clock_pm` | read | 4 | 2 | life, spine | bit0 = PM |
| `031` | `care_mistakes` | measured | 3 | 5 | input, life, screens, spine | +1 per call unanswered for 20 min (08C8), saturates at 15; cleared at evolution |
| `032` | `overfeeds` | measured | 1 | 5 | input, life, screens, spine | evolution input (0D10); cleared at evolution |
| `033` | `sleep_disturbances` | measured | 1 | 5 | input, life, screens, spine | evolution input (0D10); cleared at evolution |
| `034` | `training_count` | measured | 1 | 5 | animation, input, life, screens, spine | 8-bit (34 low, 35 high); evolution input; cleared at evolution |
| `036` | `injury_count` | read | 1 | 5 | input, life, screens, sound, spine | 2-digit BCD count of injuries, +1 in set_injured; 20 -> death (0518) |
| `038` | `injury_minutes` | measured | 1 | 5 | input, life, screens, sound, spine | 2-digit BCD minutes since the injury |
| `03A` | `injury_hours` | measured | 2 | 5 | input, life, screens, spine | hours untreated; 6 -> death (08DA) |
| `03C` | `protein_counter` | read | 2 | 5 | input, life, screens, spine | every 4th protein: back to 0 and one more overdose in M(62) |
| `03D` | `strength_hearts` | read | 6 | 7 | animation, input, life, screens, spine | boost input (0FB9); 0 raises a call (08B3) |
| `03E` | `hunger_hearts` | read | 6 | 8 | input, life, screens, sound, spine | 0 raises a call (08A9) |
| `040` | `call_timer` | measured | 1 | 4 | animation, input, life, screens, sound, spine | 40-41 BCD minutes, 42 hours, 43 bit0 at 12 h; 20 min -> care mistake, 12 h -> death |
| `046` | `stage_seconds` | read | 4 | 4 | animation, input, life, screens, sound, spine | BCD seconds in the current stage |
| `048` | `stage_minutes` | measured | 3 | 4 | animation, input, life, screens, sound, spine | BCD minutes in the current stage |
| `04A` | `stage_hours` | measured | 2 | 8 | animation, input, life, screens, spine | 8-bit hours in the current stage |
| `04C` | `next_evolution_at` | measured | 1 | 4 | life, spine | stage time (BCD minutes + hours) at which the next evolution fires |
| `054` | `schedule_flags` | read | 9 | 9 | animation, life, spine | bit0/bit1 set by the hourly wake/sleep check |
| `062` | `protein_overdoses` | measured | 3 | 4 | input, life, screens, spine | saturates at 15; boost caps it at 4, the injury roll does not; cleared at evolution |
| `065` | `empty_heart_mask` | read | 7 | 7 | animation, input, life, spine | bit2 hunger, bit1 strength: which hearts raised the current call |
| `066` | `bedtime_hour` | read | 1 | 7 | life, spine | PM hour this species goes to sleep |
| `067` | `wake_hour` | read | 1 | 7 | life, spine | AM hour this species wakes |
| `068` | `base_weight` | measured | 2 | 7 | life, spine | BCD grams per species, set at evolution (0C17) |
| `06B` | `injury_base` | measured | 1 | 4 | life, screens, spine | per-species injury chance base for the post-battle roll (01EC); 6A gets the low nibble of the same table byte |
| `075` | `care_mistakes_after_lifespan` | measured | 0 | 4 | input, life, screens, spine | counted once M(76).1 is set; the 5th is fatal (08CD-08D2) |
| `076` | `life_flags` | measured | 6 | 4 | input, life, screens, spine | bit0 Perfect roll won (0D67), bit1 lifespan over (0D61), bit3 died of old age |
| `078` | `battle_state` | measured | 0 | 5 | input, life, link_battle, screens, spine |  |
| `079` | `battle_result` | measured | 7 | 5 | input, life, link_battle, screens, spine | 1 win, 2 lose (this device) |
| `07B` | `own_enhancement` | measured | 3 | 4 | input, life, link_battle, screens, spine | power bonus sent in packet 1 |
| `07E` | `opp_enhancement` | measured | 1 | 4 | input, life, link_battle, screens, spine | from the opponent's packet 1 |
| `07F` | `opp_slot` | measured | 1 | 4 | input, life, link_battle, screens, spine | from the opponent's packet 1 |
| `080` | `poop_timer` | read | 2 | 4 | input, life, screens, sound, spine | 80-81 BCD minutes, 82 hours; at 3 hours (08D6..0881) a poop is due |
| `08C` | `energy` | measured | 5 | 5 | animation, input, life, screens, sound, spine | battle energy (decrements per battle) |
| `098` | `win_score` | measured | 2 | 5 | input, life, screens, spine | +1 per win, -1 per loss, 0..15; picks the Perfect roll's odds |
| `099` | `battle_count` | measured | 2 | 3 | input, life, screens, spine | saturates at 15; the Perfect roll needs 15 |
| `0A0` | `rng` | measured | 3 | 2 | library, spine | 4 nibbles; A1A0 BCD +73+carry-in, A3A2 binary +0x73+decimal carry per loop pass |
| `0A4` | `key_debounce` | read | 1 | 2 | input, spine | A4 last sample, A5 stable-pass count, A6 change pending |
