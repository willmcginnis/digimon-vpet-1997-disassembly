import pickle,sys,io,harness as h
rom=sys.argv[1]
p=h.Pet(rom)
p.hold("A"); p.cpu.port_handler("RES",0,0); p.run_seconds(0.05); p.cpu.port_handler("RES",0,-1); p.run_seconds(1); p.release("A"); p.run_seconds(1)
def clone(x): return pickle.loads(pickle.dumps(x))
def sig(x): return x.ascii()
seen={sig(p):0}; screens=[sig(p)]; frontier=[(p,"A+Reset")]
edges=[]
while frontier and len(screens)<25:
    q,path=frontier.pop(0)
    for b in ["A","B","C"]:
        r=clone(q); r.press(b,hold_s=0.15,gap_s=0.8); r.run_seconds(1.5)
        s=sig(r)
        if s not in seen:
            seen[s]=len(screens); screens.append(s); frontier.append((r,path+" "+b))
            edges.append((path+" "+b, seen[s], r.host.tx.hex(), "M9=%X"%r.cpu.get_mem(9)))
for e in edges: print(e)
for i,s in enumerate(screens):
    print("--- screen",i); print(s.replace("."," "))
