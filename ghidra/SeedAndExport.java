// Seed E0C6200-family entry points, re-run analysis, create functions at every
// CALL/CALZ target, then export functions, call graph, RAM xrefs and coverage.
//@category Digimon
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.symbol.*;
import ghidra.program.model.mem.*;
import ghidra.app.cmd.disassemble.DisassembleCommand;
import ghidra.app.cmd.function.CreateFunctionCmd;
import java.io.*;
import java.util.*;

public class SeedAndExport extends GhidraScript {
    @Override
    public void run() throws Exception {
        String outDir = getScriptArgs().length > 0 ? getScriptArgs()[0] : "/tmp";
        AddressSpace rom = currentProgram.getAddressFactory().getDefaultAddressSpace();
        Listing listing = currentProgram.getListing();
        FunctionManager fm = currentProgram.getFunctionManager();

        // Reset is bank 0 page 1 step 0; interrupt vectors are page 1 steps 2..0xC.
        long[] seeds = {0x100, 0x102, 0x104, 0x106, 0x108, 0x10A, 0x10C};
        String[] names = {"reset_vector", "int_vec_02", "int_vec_04", "int_vec_06", "int_vec_08", "int_vec_0A", "int_vec_0C"};
        for (int i = 0; i < seeds.length; i++) {
            Address a = rom.getAddress(seeds[i]);
            new DisassembleCommand(a, null, true).applyTo(currentProgram, monitor);
            currentProgram.getSymbolTable().createLabel(a, names[i], SourceType.USER_DEFINED);
            addEntryPoint(a);
        }
        analyzeAll(currentProgram);

        // Iterate to a fixed point: make a function at every call target.
        int round = 0, made;
        do {
            made = 0;
            for (Instruction ins : listing.getInstructions(true)) {
                if (!ins.getFlowType().isCall()) continue;
                for (Address t : ins.getFlows()) {
                    if (listing.getInstructionAt(t) == null)
                        new DisassembleCommand(t, null, true).applyTo(currentProgram, monitor);
                    if (fm.getFunctionAt(t) == null) {
                        if (new CreateFunctionCmd(t).applyTo(currentProgram, monitor)) made++;
                    }
                }
            }
            round++;
        } while (made > 0 && round < 20);

        // Exports
        try (PrintWriter fw = new PrintWriter(new FileWriter(outDir + "/functions.tsv"))) {
            fw.println("entry\tname\tbody_words\tinstructions\tcallers\tcallees");
            for (Function f : fm.getFunctions(true)) {
                int n = 0;
                for (Instruction ins : listing.getInstructions(f.getBody(), true)) n++;
                Set<Function> callers = f.getCallingFunctions(monitor);
                Set<Function> callees = f.getCalledFunctions(monitor);
                StringBuilder ce = new StringBuilder();
                for (Function c : callees) ce.append(c.getEntryPoint()).append(',');
                StringBuilder cr = new StringBuilder();
                for (Function c : callers) cr.append(c.getEntryPoint()).append(',');
                fw.printf("%s\t%s\t%d\t%d\t%s\t%s%n", f.getEntryPoint(), f.getName(),
                        f.getBody().getNumAddresses(), n, cr, ce);
            }
        }
        // Coverage: which ROM words are instructions vs undefined
        long code = 0, undef = 0;
        try (PrintWriter cw = new PrintWriter(new FileWriter(outDir + "/coverage.tsv"))) {
            Address start = rom.getAddress(0), end = rom.getAddress(0x1FFF);
            String state = null; Address runStart = start;
            for (Address a = start; a.compareTo(end) <= 0; a = a.next()) {
                String s = listing.getInstructionContaining(a) != null ? "code" : "undef";
                if (s.equals("code")) code++; else undef++;
                if (!s.equals(state)) {
                    if (state != null) cw.printf("%s\t%s\t%s%n", runStart, a.previous(), state);
                    state = s; runStart = a;
                }
                if (a.equals(end)) { cw.printf("%s\t%s\t%s%n", runStart, a, state); break; }
            }
        }
        // References into RAM/IO from instructions
        try (PrintWriter rw = new PrintWriter(new FileWriter(outDir + "/refs.tsv"))) {
            ReferenceManager rm = currentProgram.getReferenceManager();
            for (Instruction ins : listing.getInstructions(true)) {
                for (Reference r : ins.getReferencesFrom()) {
                    rw.printf("%s\t%s\t%s\t%s%n", ins.getAddress(), r.getToAddress(),
                            r.getReferenceType(), ins.toString());
                }
            }
        }
        // Full listing
        try (PrintWriter lw = new PrintWriter(new FileWriter(outDir + "/listing.txt"))) {
            for (Instruction ins : listing.getInstructions(true)) {
                Function f = fm.getFunctionContaining(ins.getAddress());
                Symbol s = currentProgram.getSymbolTable().getPrimarySymbol(ins.getAddress());
                if (s != null && f != null && f.getEntryPoint().equals(ins.getAddress()))
                    lw.printf("%n%s:%n", f.getName());
                else if (s != null) lw.printf("%s:%n", s.getName());
                lw.printf("  %s  %s%n", ins.getAddress(), ins);
            }
        }
        println(String.format("functions=%d code_words=%d undefined_words=%d rounds=%d",
                fm.getFunctionCount(), code, undef, round));
    }
}
