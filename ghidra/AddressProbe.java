// Probe how the E0C6S46 module's word-addressed "rom" space maps numbers to addresses.
// Prints getAddress(n) for a few ROM word numbers n and what instruction sits there.
// Result on Ghidra 12.0.4 (measured): getAddress(0x100) is rom:0080, i.e. the argument is a
// byte offset and word w must be requested as getAddress(w * unitSize); see ApplyMap.W().
//@category Digimon
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.*;
import ghidra.program.model.listing.*;
public class AddressProbe extends GhidraScript {
  public void run() throws Exception {
    AddressSpace rom = currentProgram.getAddressFactory().getAddressSpace("rom");
    Listing l = currentProgram.getListing();
    println("rom unit size=" + rom.getAddressableUnitSize() + " min=" + rom.getMinAddress() + " max=" + rom.getMaxAddress());
    for (long w : new long[]{0x100, 0x132, 0x136, 0x137, 0x0D7A}) {
      Address a = rom.getAddress(w);
      Instruction i = l.getInstructionAt(a);
      Instruction c = l.getInstructionContaining(a);
      println(String.format("w=%04X addr=%s offset=%d at=%s containing=%s len=%s", w, a, a.getOffset(), i, c==null?null:c.getAddress()+" "+c, i==null?"-":""+i.getLength()));
    }
    Address a = rom.getAddress(0x132); println("next of 0132 = " + a.next() + "  add(1)=" + a.add(1) + " addWrap(2)=" + a.addWrap(2));
    long n=0; for (Instruction i : l.getInstructions(true)) n++; println("instructions=" + n);
  }
}
