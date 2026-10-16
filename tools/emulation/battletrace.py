import os
import pickle,sys,harness as h, link as L, battle as BT
def setup(sa="st_v1_childA.pkl", sb="st_v1_childB.pkl", pre_wait=0.0):
    a=BT.load(sa,None); b=BT.load(sb,None); lk=L.Link(a,b)
    lk.run_seconds(pre_wait)
    import os
    if os.environ.get('ENH_B'): b.poke(0x7B,int(os.environ['ENH_B'],16))
    BT.goto_icon(lk,a,"BATTLE"); BT.goto_icon(lk,b,"BATTLE")
    lk.press(a,"B",hold_s=0.15,gap_s=0.3); lk.press(b,"B",hold_s=0.15,gap_s=0.3)
    return a,b,lk
def instrument(p,tag,events,watch_r=(0xA0,0xA1,0xA2,0xA3),watch_w=(0x10,0x11,0x19,0x9A,0x9B,0x0A)):
    cpu=p.cpu; og=cpu.get_mem; os_=cpu.set_mem
    def gm(a,_o=og):
        if a in watch_r: events.append((p.cycles/h.CLOCK,tag,"R",a,_o(a),cpu.pc()))
        return _o(a)
    def sm(a,v,_o=os_):
        if a in watch_w: events.append((p.cycles/h.CLOCK,tag,"W",a,v,cpu.pc()))
        return _o(a,v)
    cpu.get_mem=gm; cpu.set_mem=sm
if __name__=="__main__":
    a,b,lk=setup()
    ev=[]; instrument(a,"A",ev); instrument(b,"B",ev)
    t0=a.cycles/h.CLOCK
    print("before: A 9A=%X 9B=%X  B 9A=%X 9B=%X"%(a.cpu.get_mem(0x9A),a.cpu.get_mem(0x9B),b.cpu.get_mem(0x9A),b.cpu.get_mem(0x9B)))
    lk.press(a,"B",hold_s=0.15,gap_s=0.3)
    lk.run_seconds(25)
    pk=[(t,"PKT",d,BT.bits_rev(w)) for t,d,w in lk.log]
    allev=sorted([(e[0],)+e[1:] for e in ev]+pk, key=lambda x:x[0])
    for e in allev:
        if e[1]=="PKT": print("%8.3f  ===== packet %s %04X"%(e[0]-t0,e[2],e[3]))
        else: print("%8.3f  %s %s %03X=%X pc=%03X"%(e[0]-t0,e[1],e[2],e[3],e[4],e[5]))
    print("after: A 9A=%X 9B=%X  B 9A=%X 9B=%X"%(a.cpu.get_mem(0x9A),a.cpu.get_mem(0x9B),b.cpu.get_mem(0x9A),b.cpu.get_mem(0x9B)))
