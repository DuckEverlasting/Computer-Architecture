"""CPU functionality."""

import sys
import msvcrt
from datetime import datetime

disp_table = {
    0b10100000: "ADD", 0b10101000: "AND", 0b01010000: "CALL",
    0b10100111: "CMP", 0b01100110: "DEC", 0b10100011: "DIV",
    0b00000001: "HLT", 0b01100101: "INC", 0b01010010: "INT",
    0b00010011: "IRET", 0b01010101: "JEQ", 0b01011010: "JGE",
    0b01010111: "JGT", 0b01011001: "JLE", 0b01011000: "JLT",
    0b01010100: "JMP", 0b01010110: "JNE", 0b10000011: "LD",
    0b10000010: "LDI", 0b10100100: "MOD", 0b10100010: "MUL",
    0b00000000: "NOP", 0b01101001: "NOT", 0b10101010: "OR",
    0b01000110: "POP", 0b01001000: "PRA", 0b01000111: "PRN",
    0b01000101: "PUSH", 0b00010001: "RET", 0b10101100: "SHL",
    0b10101101: "SHR", 0b10000100: "ST", 0b10100001: "SUB",
    0b10101011: "XOR"
}

class CPU:
    """Main CPU class."""

    def __init__(self):
        """Construct a new CPU."""
        self.reg = [0b00000000] * 8
        self.ram = [0b00000000] * 256
        self.pc = 0b00000000  # Program Counter
        self.ir = 0b00000000  # Instruction Register
        self.mar = 0b00000000  # Memory Address Register
        self.mdr = 0b00000000  # Memory Data Register
        self.flags = 0b00000000  # Flags (H0000LGE) - h = "halt", l = "<", G = ">", E = "="
        self.reg[0b101] = 0b11111111  # Interrupt Mask
        self.reg[0b111] = 0b11110011  # Stack Pointer
        self.clock = [0b00000000] * 8 # System Clock (stores time data when clock method is called to approximate system clock)
        
        """
        Register map:
        +-----------------------+
        | 0                     |
        | 1                     |
        | 2                     |
        | 3                     |
        | 4                     |
        | 5 Interrupt Mask      |
        | 6 Interrupt Status    |
        | 7 Stack Pointer       |
        +-----------------------+

        Clock map:
        +-----------------------+
        | 0 Year (last 2 digits)|
        | 1 Month               |
        | 2 Day                 |
        | 3 Hour                |
        | 4 Minute              |
        | 5 Second              |
        | 6                     |
        | 7 Changed registers   | (012345--)
        +-----------------------+
        

        Memory map:

            top of RAM
        +-----------------------+
        | FF  I7 vector         |    Interrupt vector table
        | FE  I6 vector         |
        | FD  I5 vector         |
        | FC  I4 vector         |
        | FB  I3 vector         |
        | FA  I2 vector         |
        | F9  I1 vector         |
        | F8  I0 vector         |
        | F7  Reserved          |
        | F6  Reserved          |
        | F5  Reserved          |
        | F4  Key pressed       |    Holds the most recent key pressed on the keyboard
        | F3  Start of Stack    |
        | F2  [more stack]      |    Stack grows down
        | ...                   |
        | 01  [more program]    |
        | 00  Program entry     |    Program loaded upward in memory starting at 0
        +-----------------------+
            bottom of RAM
        """

    def ram_read(self, address):
        self.mar = address
        self.mdr = self.ram[self.mar]
        return self.mdr
    
    def ram_write(self, address, data):
        self.mar = address
        self.mdr = data
        self.ram[self.mar] = self.mdr

    def load(self, filename):
        """Load a program into memory."""
        try:
            address = 0

            with open(filename) as f:
                for line in f:
                    # Process comments:
                    # Ignore anything after a # symbol
                    comment_split = line.split("#")

                    # Convert any numbers from binary strings to integers
                    num = comment_split[0].strip()
                    try:
                        val = int(num, 2)
                    except ValueError:
                        continue

                    self.ram[address] = val
                    address += 1
                    # print(f"{val:08b}: {val:d}")

        except FileNotFoundError:
            print(f"{sys.argv[0]}: {sys.argv[1]} not found")
            sys.exit(2)

    def alu(self, op, reg_a, reg_b=None):
        """ALU operations."""

        if op == "ADD":
            """
            Add the value in two registers and store the result in registerA.
            """
            self.reg[reg_a] += self.reg[reg_b]
        elif op == "SUB":
            """
            Subtract the value in the second register from the first, storing the result in registerA.
            """
            self.reg[reg_a] -= self.reg[reg_b]
        elif op == "MUL":
            """
            Multiply the values in two registers together and store the result in registerA.
            """
            self.reg[reg_a] *= self.reg[reg_b]
        elif op == "DIV":
            """
            Divide the value in the first register by the value in the second, storing the result in registerA.
            """
            # If the value in the second register is 0, the system should print an error message and halt.
            if self.reg[reg_b] == 0b00000000:
                print("ERROR: DIVIDE BY ZERO")
                self.HLT()
            else:
                self.reg[reg_a] /= self.reg[reg_b]
        elif op == "MOD":
            """
            Divide the value in the first register by the value in the second, storing the remainder of the result in registerA.
            """
            # If the value in the second register is 0, the system should print an error message and halt.
            if self.reg[reg_b] == 0b00000000:
                print("ERROR: DIVIDE BY ZERO")
                self.HLT()
            else:
                self.reg[reg_a] %= self.reg[reg_b]
        elif op == "CMP":
            """Compare the values in two registers."""
            # If they are equal, set the Equal `E` flag to 1, otherwise set it to 0.
            # If registerA is less than registerB, set the Less-than `L` flag to 1, otherwise set it to 0.
            # If registerA is greater than registerB, set the Greater-than `G` flag to 1, otherwise set it to 0.
            if self.reg[reg_a] < self.reg[reg_b]:
                self.flags = self.flags | 0b00000100
            else:
                self.flags = self.flags & 0b11111011
            if self.reg[reg_a] > self.reg[reg_b]:
                self.flags = self.flags | 0b00000010
            else:
                self.flags = self.flags & 0b11111101
            if self.reg[reg_a] == self.reg[reg_b]:
                self.flags = self.flags | 0b00000001
            else:
                self.flags = self.flags & 0b11111110
        elif op == "INC":
            """
            Increment (add 1 to) the value in the given register.
            """
            self.reg[reg_a] += 0b00000001
        elif op == "DEC":
            """
            Decrement (subtract 1 from) the value in the given register.
            """
            self.reg[reg_a] -= 0b00000001
        elif op == "AND":
            """
            Bitwise-AND the values in registerA and registerB, then store the result in registerA.
            """
            self.reg[reg_a] &= self.reg[reg_b]
        elif op == "OR":
            """
            Perform a bitwise-OR between the values in registerA and registerB, storing the result in registerA.
            """
            self.reg[reg_a] |= self.reg[reg_b]
        elif op == "XOR":
            """
            Perform a bitwise-XOR between the values in registerA and registerB, storing the result in registerA.
            """
            self.reg[reg_a] ^= self.reg[reg_b]
        elif op == "NOT":
            """
            Perform a bitwise-NOT on the value in a register.
            """
            self.reg[reg_a] = ~self.reg[reg_a]
        elif op == "SHL":
            """
            Shift the value in registerA left by the number of bits specified in registerB, filling the low bits with 0.
            """
            self.reg[reg_a] <<= self.reg[reg_b]
        elif op == "SHR":
            """
            Shift the value in registerA right by the number of bits specified in registerB, filling the high bits with 0.
            """
            self.reg[reg_a] >>= self.reg[reg_b]
        else:
            raise Exception("Unsupported ALU operation")
        self.reg[reg_a] &= 0b11111111
    
    def time(self):
        """
        Sets the system clock to the current time. Notes which values have changed.
        """
        self.clock[0b111] = 0b00000000
        if self.clock[0b000] != datetime.now().second:
            self.clock[0b000] = datetime.now().second
            self.clock[0b111] |= 0b00000001
        if self.clock[0b001] != datetime.now().minute:
            self.clock[0b001] = datetime.now().minute
            self.clock[0b111] |= 0b00000010
        if self.clock[0b010] != datetime.now().hour:
            self.clock[0b010] = datetime.now().hour
            self.clock[0b111] |= 0b00000100
        if self.clock[0b011] != datetime.now().day:
            self.clock[0b011] = datetime.now().day
            self.clock[0b111] |= 0b00001000
        if self.clock[0b100] != datetime.now().month:
            self.clock[0b100] = datetime.now().month
            self.clock[0b111] |= 0b00010000
        if self.clock[0b101] != datetime.now().year % 100:
            self.clock[0b101] = datetime.now().year % 100
            self.clock[0b111] |= 0b00100000

    def trace(self):
        """
        Handy function to print out the CPU state. You might want to call this
        from run() if you need help debugging.
        """
        print(f"TRACE: %02X | %02X %02X %02X |" % (
            self.pc,
            #self.fl,
            #self.ie,
            self.ram_read(self.pc),
            self.ram_read(self.pc + 1),
            self.ram_read(self.pc + 2)
        ), end='')

        for i in range(8):
            print(" %02X" % self.reg[i], end='')

        print()

    def interrupt(self, i_num):
        self.reg[0b110] &= ~(0b00000001 << i_num)
        self.alu("DEC", (0b111))
        self.ram_write(self.reg[0b111], self.pc)
        self.alu("DEC", (0b111))
        self.ram_write(self.reg[0b111], self.flags)
        self.POP(0b000)
        self.POP(0b001)
        self.POP(0b010)
        self.POP(0b011)
        self.POP(0b100)
        self.POP(0b101)
        self.POP(0b110)
        self.pc = i_num | 0b11111000

    def run(self):
        """Run the CPU."""
        self.time()
        while not self.flags & 0b10000000:
            self.time()

            if self.clock[0b111] & 0b00000001:
                self.reg[0b110] |= 0b00000001
            
            if msvcrt.kbhit():
                self.reg[0b110] |= 0b00000010
                self.ram_write(0b11110100, ord(msvcrt.getwch()))

            for i_num in range(0b1000):
                if (self.reg[0b101] & (0b00000001 << i_num)) & (self.reg[0b110] & (0b00000001 << i_num)):
                    self.interrupt(i_num)
                    break

            self.ir = self.pc
            self.pc = self.ram_read(self.pc)

            if self.pc in disp_table:
                if self.pc >> 0b110 == 0b00:
                    method = getattr(self, disp_table[self.pc])
                    method()
                    if not self.pc & 0b00010000:
                        self.ir += 0b01
                    
                elif self.pc >> 0b110 == 0b01:
                    if self.pc & 0b00100000:
                        self.alu(disp_table[self.pc], self.ram_read(self.ir + 0b01))
                    else:
                        method = getattr(self, disp_table[self.pc])
                        method(self.ram_read(self.ir + 0b01))
                    if not self.pc & 0b00010000:
                        self.ir += 0b10
                else:
                    if self.pc & 0b00100000:
                        self.alu(disp_table[self.pc], self.ram_read(self.ir + 0b01), 
                                 self.ram_read(self.ir + 0b10))
                    else:
                        method = getattr(self, disp_table[self.pc])
                        method(self.ram_read(self.ir + 0b01),
                               self.ram_read(self.ir + 0b10))
                    if not self.pc & 0b00010000:
                        self.ir += 0b11
                self.pc = self.ir
            else:
                print(f"ERROR: Unrecognized command {self.pc} at location {self.pc}.")
                self.flags |= 0b10000000


    ##################
    # Function Logic #
    ##################

    def CALL(self, register):
        """Calls a subroutine (function) at the address stored in the register."""
        # The address of the instruction directly after CALL is pushed onto the stack.
        # This allows us to return to where we left off when the subroutine finishes executing.
        # The PC is set to the address stored in the given register. We jump to that location in
        # RAM and execute the first instruction in the subroutine. The PC can move forward or
        # backwards from its current location.
        self.alu("DEC", (0b111))
        self.ram_write(self.reg[0b111], self.ir + 0b10)
        self.JMP(register)

    def HLT(self):
        """Halt the CPU (and exit the emulator)."""
        self.flags |= 0b10000000

    def INT(self, register):
        """Issue the interrupt number stored in the given register."""
        # This will set the _n_th bit in the IS register to the value in the given register.
        self.reg[0b110] |= (0b00000001 << self.reg[register])

    def IRET(self):
        """Return from an interrupt handler."""
        # The following steps are executed:
            # Registers R6-R0 are popped off the stack in that order.
            # The FL register is popped off the stack.
            # The return address is popped off the stack and stored in PC.
            # Interrupts are re-enabled
        self.POP(0b110)
        self.POP(0b101)
        self.POP(0b100)
        self.POP(0b011)
        self.POP(0b010)
        self.POP(0b001)
        self.POP(0b000)
        self.flags = self.ram_read(self.reg[0b111])
        self.alu("INC", (0b111))
        self.ir = self.ram_read(self.reg[0b111])
        self.alu("INC", (0b111))        

    def JEQ(self, register):
        """If equal flag is set (true), jump to the address stored in the given register."""
        if self.flags & 0b00000001:
            self.ir = self.reg[register]
        else:
            self.ir += 0b10

    def JGE(self, register):
        """If greater-than flag or equal flag is set (true), jump to the address stored in the given register."""
        if self.flags & 0b00000101:
            self.ir = self.reg[register]
        else:
            self.ir += 0b10

    def JGT(self, register):
        """If greater-than flag is set (true), jump to the address stored in the given register."""
        if self.flags & 0b00000100:
            self.ir = self.reg[register]
        else:
            self.ir += 0b10

    def JLE(self, register):
        """If less-than flag or equal flag is set (true), jump to the address stored in the given register."""
        if self.flags & 0b00000011:
            self.ir = self.reg[register]
        else:
            self.ir += 0b10

    def JLT(self, register):
        """If less-than flag is set (true), jump to the address stored in the given register."""
        if self.flags & 0b00000010:
            self.ir = self.reg[register]
        else:
            self.ir += 0b10

    def JMP(self, register):
        """Jump to the address stored in the given register."""
        # Set the PC to the address stored in the given register.
        self.ir = self.reg[register]

    def JNE(self, register):
        """If E flag is clear (false, 0), jump to the address stored in the given register."""
        if not self.flags & 0b00000001:
            self.ir = self.reg[register]
        else:
            self.ir += 0b10

    def LD(self, registerA, registerB):
        """Loads registerA with the value at the memory address stored in registerB."""
        # This opcode reads from memory.
        self.reg[registerA] = self.ram_read(self.reg[registerB])

    def LDI(self, register, immediate):
        """Set the value of a register to an integer."""
        self.reg[register] = immediate

    def NOP(self):
        """No operation. Do nothing for this instruction."""
        pass

    def POP(self, register):
        """Pop the value at the top of the stack into the given register."""
        # Copy the value from the address pointed to by SP to the given register.
        # Increment SP.
        self.reg[register] = self.ram_read(self.reg[0b111])
        self.alu("INC", (0b111))

    def PRA(self, register):
        """Print alpha character value stored in the given register."""
        # Print to the console the ASCII character corresponding to the value in the register.
        print(chr(self.reg[register]))

    def PRN(self, register):
        """Print numeric value stored in the given register."""
        # Print to the console the decimal integer value that is stored in the given register.
        print(int(self.reg[register]))

    def PUSH(self, register):
        """Push the value in the given register on the stack."""
        # Decrement the SP.
        # Copy the value in the given register to the address pointed to by SP.
        self.alu("DEC", (0b111))
        self.ram_write(self.reg[0b111], self.reg[register])

    def RET(self):
        """Return from subroutine."""
        # Pop the value from the top of the stack and store it in the PC.
        self.ir = self.ram_read(self.reg[0b111])
        self.alu("INC", (0b111))

    def ST(self, registerA, registerB):
        """Store value in registerB in the address stored in registerA."""
        # This opcode writes to memory.
        self.ram_write(self.reg[registerA], self.reg[registerB])
