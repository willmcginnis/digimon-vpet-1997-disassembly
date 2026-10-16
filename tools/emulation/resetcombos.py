import pickle,sys,harness as h
rom=sys.argv[1]; state=sys.argv[2]
for combo in ["","A","B","C","AB","AC","BC","ABC"]:
    p=pickle.load(open(state,"rb"))
    p.hold(*combo); p.cpu.port_handler("RES",0,0); p.run_seconds(0.05); p.cpu.port_handler("RES",0,-1)
    frames=[]
    for i in range(30):          # keep buttons held 3s, sample every 0.1s
        p.run_seconds(0.1); frames.append(p.ascii())
    p.release(*combo)
    for i in range(20):
        p.run_seconds(0.25); frames.append(p.ascii())
    uniq=[]
    for f in frames:
        if f not in uniq: uniq.append(f)
    print("=== combo [%s]+Reset: %d distinct screens, M9=%X"%(combo,len(uniq),p.cpu.get_mem(9)))
    for f in uniq[:4]:
        print(f.replace(".", " ")); print("-")
