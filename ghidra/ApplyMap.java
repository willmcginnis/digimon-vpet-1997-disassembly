// Apply an externally recovered map to an E0C6S46-language program:
//   code  ADDR             -> disassemble here (walker-reached words Ghidra missed)
//   jpba  ADDR T1,T2,...   -> add COMPUTED_JUMP references for a JPBA table
//   func  ADDR NAME [CMT]  -> create/rename a function, plate comment
//   label ADDR NAME [CMT]  -> code label + pre comment
//   ram   ADDR NAME [CMT]  -> label in the ram space
// Input: tab-separated file passed as the first script argument.
//@category Digimon
import ghidra.app.script.GhidraScript;
import ghidra.app.cmd.disassemble.DisassembleCommand;
import ghidra.app.cmd.function.CreateFunctionCmd;
import ghidra.program.model.address.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.symbol.*;
import java.io.*;
import java.nio.file.*;
import java.util.*;

public class ApplyMap extends GhidraScript {
    private AddressSpace romSpace;
    /** ROM word number -> Address (getAddress takes a byte offset in this word-addressed space). */
    private Address W(long word) { return romSpace.getAddress(word * romSpace.getAddressableUnitSize()); }

    @Override
    public void run() throws Exception {
        List<String> lines = Files.readAllLines(Paths.get(getScriptArgs()[0]));
        AddressSpace rom = currentProgram.getAddressFactory().getAddressSpace("rom");
        romSpace = rom;
        AddressSpace ram = currentProgram.getAddressFactory().getAddressSpace("ram");
        Listing listing = currentProgram.getListing();
        FunctionManager fm = currentProgram.getFunctionManager();
        SymbolTable st = currentProgram.getSymbolTable();
        ReferenceManager rm = currentProgram.getReferenceManager();
        int code = 0, funcs = 0, labels = 0, rams = 0, jrefs = 0;
        // pass 1: code
        AddressSet toDis = new AddressSet();
        for (String l : lines) {
            String[] f = l.split("\t", -1);
            if (f[0].equals("code")) toDis.add(W(Long.parseLong(f[1], 16)));
        }
        for (AddressRange r : toDis) {
            if (listing.getInstructionAt(r.getMinAddress()) == null) {
                new DisassembleCommand(r.getMinAddress(), new AddressSet(r), false).applyTo(currentProgram, monitor);
            }
        }
        for (AddressRange r : toDis)
            for (Address a = r.getMinAddress(); a.compareTo(r.getMaxAddress()) <= 0; a = a.add(romSpace.getAddressableUnitSize()))
                if (listing.getInstructionAt(a) == null &&
                        new DisassembleCommand(a, new AddressSet(a), false).applyTo(currentProgram, monitor))
                    code++;
        // pass 2: jpba refs, functions, labels, ram
        for (String l : lines) {
            String[] f = l.split("\t", -1);
            if (f.length < 2) continue;
            String cmt = f.length > 3 ? f[3] : "";
            switch (f[0]) {
                case "jpba": {
                    Address src = W(Long.parseLong(f[1], 16));
                    for (String t : f[2].split(",")) {
                        if (t.isEmpty()) continue;
                        rm.addMemoryReference(src, W(Long.parseLong(t, 16)),
                                RefType.COMPUTED_JUMP, SourceType.USER_DEFINED, 0);
                        jrefs++;
                    }
                    break;
                }
                case "func": {
                    Address a = W(Long.parseLong(f[1], 16));
                    Function fn = fm.getFunctionAt(a);
                    if (fn == null) {
                        new CreateFunctionCmd(a).applyTo(currentProgram, monitor);
                        fn = fm.getFunctionAt(a);
                    }
                    if (fn != null) {
                        fn.setName(f[2], SourceType.USER_DEFINED);
                        if (!cmt.isEmpty()) setPlateComment(a, cmt);
                        funcs++;
                    }
                    break;
                }
                case "label": {
                    Address a = W(Long.parseLong(f[1], 16));
                    st.createLabel(a, f[2], SourceType.USER_DEFINED);
                    if (!cmt.isEmpty()) setPreComment(a, cmt);
                    labels++;
                    break;
                }
                case "ram": {
                    Address a = ram.getAddress(Long.parseLong(f[1], 16));
                    st.createLabel(a, f[2], SourceType.USER_DEFINED);
                    if (!cmt.isEmpty()) setEOLComment(a, cmt);
                    rams++;
                    break;
                }
            }
        }
        println(String.format("applied: code=%d jpba_refs=%d funcs=%d labels=%d ram=%d total_functions=%d",
                code, jrefs, funcs, labels, rams, fm.getFunctionCount()));
    }
}
