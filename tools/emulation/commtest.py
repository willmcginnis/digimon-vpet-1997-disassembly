import sys,harness as h, link as L
def to_screen3(p):
    p.hold("A"); p.cpu.port_handler("RES",0,0); p.run_seconds(0.05); p.cpu.port_handler("RES",0,-1); p.run_seconds(1); p.release("A"); p.run_seconds(1)
    for b in "BC": p.press(b,hold_s=0.15,gap_s=0.8); p.run_seconds(1.5)
a=h.Pet(sys.argv[1]); b=h.Pet(sys.argv[2]); to_screen3(a); to_screen3(b)
a.host.tx.clear(); b.host.tx.clear()
lk=L.Link(a,b)
lk.press(a,"A",hold_s=0.15,gap_s=0.5); lk.run_seconds(2)
for t,d,w in lk.log: print("%.3fs %s wire=%04X dmcomm=%04X"%(t,d,w,int('{:016b}'.format(w)[::-1],2)))
print("A:"); print(a.ascii().replace("."," ")); print("B:"); print(b.ascii().replace("."," "))
a.png("commtest_A.png"); 
