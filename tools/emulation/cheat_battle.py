import harness as h, link as L, battle as BT, battletrace as T, battle_exp as E
import sys
def go(seq, delay):
    a,b,lk=T.setup()
    a.poke(0x79,0); b.poke(0x79,0)
    lk.press(a,"B",hold_s=0.15,gap_s=0.0)
    lk.run_seconds(delay)
    for ch in seq: lk.press(a,ch,hold_s=0.08,gap_s=0.07)
    lk.run_seconds(25)
    return E.outcome_of(a), E.outcome_of(b), " ".join("%s:%04X"%(d,E.rev(w)) for t,d,w in lk.log)
if __name__ == "__main__":
  for seq,delay in [("",0),("AAABBBCC",0.0),("AAABBBCC",2.0),("ABCAABC",2.0),("AAAAAAAAAAAAAAAAAAAA",1.0)]:
      print(repr(seq),"start+%.1fs"%delay, go(seq,delay))
