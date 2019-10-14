"""CPU functionality."""

import sys

class CPU:
    """Main CPU class."""

    def __init__(self):
        """Construct a new CPU."""
        self.ram = [0b00000000] * 256
        self.reg = [0b00000000] * 8
        self.pc = 0b00000000  # Program Counter
        self.ir = 0b00000000  # Instruction Register
        self.mar = 0b00000000  # Memory Address Register
        self.mdr = 0b00000000  # Memory Data Register
        self.flags = 0b00000000  # Flags (00000LGE) - example, if (00000100): A < B
        # TODO: set self.reg[5] to initial interrupt mask (IM)
        # TODO: set self.reg[6] to initial interrupt status (IS)
        # TODO: set self.reg[7] to initial stack pointer (SP)
        """
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

    def load(self):
        """Load a program into memory."""

        address = 0

        # For now, we've just hardcoded a program:

        program = [
            # From print8.ls8
            0b10000010, # LDI R0,8
            0b00000000,
            0b00001000,
            0b01000111, # PRN R0
            0b00000000,
            0b00000001, # HLT
        ]

        for instruction in program:
            self.ram[address] = instruction
            address += 1

    def alu(self, op, reg_a, reg_b):
        """ALU operations."""

        if op == "ADD":
            self.reg[reg_a] += self.reg[reg_b]
        #elif op == "SUB": etc
        else:
            raise Exception("Unsupported ALU operation")

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

    def run(self):
        """Run the CPU."""
        endProgram = False
        while not endProgram:
            self.ir = self.pc
            operator = self.ram_read(self.pc)
            operand_a = self.ram_read(self.pc + 1)
            operand_b = self.ram_read(self.pc + 2)

            codes = {
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

            if operator in codes:
                if operator < 0b01000000:
                    function = getattr(self, codes[operator])
                    ret = function()
                    if ret != "JMP":
                        self.pc += 0b00000001
                elif operator < 0b10000000:
                    function = getattr(self, codes[operator])
                    ret = function(operand_a)
                    if ret != "JMP":
                        self.pc += 0b00000010
                else:
                    function = getattr(self, codes[operator])
                    ret = function(operand_a, operand_b)
                    if ret != "JMP":
                        self.pc += 0b00000011
            else:
                print(f"ERROR: Unrecognized command {operator} at location {self.pc}.")
                endProgram = True

            if ret == "HLT":
                endProgram = True


    ##################
    # Function Logic #
    ##################

    def ADD(self, registerA, registerB):
        # Add the value in two registers and store the result in registerA.
        self.reg[registerA] = self.reg[registerA] + self.reg[registerB]

    def AND(self, registerA, registerB):
        # Bitwise-AND the values in registerA and registerB, then store the result in registerA.
        self.reg[registerA] = self.reg[registerA] & self.reg[registerB]

    def CALL(self, register): #TODO
        # Calls a subroutine (function) at the address stored in the register.
        # The address of the instruction directly after CALL is pushed onto the stack. This allows us to return to where we left off when the subroutine finishes executing.
        # The PC is set to the address stored in the given register. We jump to that location in RAM and execute the first instruction in the subroutine. The PC can move forward or backwards from its current location.
        pass

    def CMP(self, registerA, registerB):
        # Compare the values in two registers.
        if self.reg[registerA] < self.reg[registerB]:
            self.flags = 0b00000100
        elif self.reg[registerA] < self.reg[registerB]:
            self.flags = 0b00000010
        else:
            self.flags = 0b00000001

    def DEC(self, register):
        # Decrement (subtract 1 from) the value in the given register.
        self.reg[register] -= 0b00000001

    def DIV(self, registerA, registerB):
        # Divide the value in the first register by the value in the second, storing the result in registerA.
        # If the value in the second register is 0, the system should print an error message and halt.
        if self.reg[registerB] == 0b00000000:
            print("ERROR: DIVIDE BY ZERO")
            return "HLT"
        else:
            self.reg[registerA] = self.reg[registerA] / self.reg[registerB]

    def HLT(self):
        # Halt the CPU (and exit the emulator).
        return "HLT"

    def INC(self, register):
        # Increment (add 1 to) the value in the given register.
        self.reg[register] += 0b00000001

    def INT(self, register): #TODO
        # Issue the interrupt number stored in the given register.
        # This will set the _n_th bit in the IS register to the value in the given register.
        pass

    def IRET(self): #TODO
        # Return from an interrupt handler.
        # The following steps are executed:
            # Registers R6-R0 are popped off the stack in that order.
            # The FL register is popped off the stack.
            # The return address is popped off the stack and stored in PC.
            # Interrupts are re-enabled
        pass

    def JEQ(self, register):
        # If equal flag is set (true), jump to the address stored in the given register.
        if self.flags % 0b00000010:
            self.pc = register
            return "JMP"

    def JGE(self, register):
        # If greater-than flag or equal flag is set (true), jump to the address stored in the given register.
        if self.flags % 0b00000100 >= 0b00000010 or self.flags % 0b00000010:
            self.pc = register
            return "JMP"

    def JGT(self, register):
        # If greater-than flag is set (true), jump to the address stored in the given register.
        if self.flags % 0b00000100 >= 0b00000010:
            self.pc = register
            return "JMP"

    def JLE(self, register):
        # If less-than flag or equal flag is set (true), jump to the address stored in the given register.
        if self.flags % 0b00001000 >= 0b00000100 or self.flags % 0b00000010:
            self.pc = register
            return "JMP"

    def JLT(self, register):
        # If less-than flag is set (true), jump to the address stored in the given register.
        if self.flags % 0b00001000 >= 0b00000100:
            self.pc = register
            return "JMP"

    def JMP(self, register):
        # Jump to the address stored in the given register.
        # Set the PC to the address stored in the given register.
            self.pc = register
            return "JMP"

    def JNE(self, register):
        # If E flag is clear (false, 0), jump to the address stored in the given register.
        if not self.flags % 0b00000010:
            self.pc = register
            return "JMP"

    def LD(self, registerA, registerB):
        # Loads registerA with the value at the memory address stored in registerB.
        # This opcode reads from memory.
        self.reg[registerA] = self.ram_read(self.reg[registerB])

    def LDI(self, register, immediate):
        # Set the value of a register to an integer.
        self.reg[register] = immediate

    def MOD(self, registerA, registerB):
        # Divide the value in the first register by the value in the second, storing the remainder of the result in registerA.
        # If the value in the second register is 0, the system should print an error message and halt.
        if self.reg[registerB] == 0b00000000:
            print("ERROR: DIVIDE BY ZERO")
            return "HLT"
        else:
            self.reg[registerA] = self.reg[registerA] % self.reg[registerB]

    def MUL(self, registerA, registerB):
        # Multiply the values in two registers together and store the result in registerA.
        self.reg[registerA] = self.reg[registerA] * self.reg[registerB]

    def NOP(self):
        # No operation. Do nothing for this instruction.
        pass

    def NOT(self, register):
        # Perform a bitwise-NOT on the value in a register.
        self.reg[register] = ~ self.reg[register]

    def OR(self, registerA, registerB):
        # Perform a bitwise-OR between the values in registerA and registerB, storing the result in registerA.
        self.reg[registerA] = self.reg[registerA] | self.reg[registerB]

    def POP(self, register): #TODO
        # Pop the value at the top of the stack into the given register.
            # Copy the value from the address pointed to by SP to the given register.
            # Increment SP.
        pass

    def PRA(self, register):
        # Print alpha character value stored in the given register.
        # Print to the console the ASCII character corresponding to the value in the register.
        print(chr(self.reg[register]))

    def PRN(self, register):
        # Print numeric value stored in the given register.
        # Print to the console the decimal integer value that is stored in the given register.
        print(int(self.reg[register]))

    def PUSH(self, register): #TODO
        # Push the value in the given register on the stack.
        # Decrement the SP.
        # Copy the value in the given register to the address pointed to by SP.
        pass

    def RET(self): #TODO
        # Return from subroutine.
        # Pop the value from the top of the stack and store it in the PC.
        pass

    def SHL(self, registerA, registerB):
        # Shift the value in registerA left by the number of bits specified in registerB, filling the low bits with 0.
        self.reg[registerA] = self.reg[registerA] << self.reg[registerB]

    def SHR(self, registerA, registerB):
        # Shift the value in registerA right by the number of bits specified in registerB, filling the high bits with 0.
        self.reg[registerA] = self.reg[registerA] >> self.reg[registerB]

    def ST(self, registerA, registerB):
        # Store value in registerB in the address stored in registerA.
        # This opcode writes to memory.
        self.ram_write(self.reg[registerA], self.reg[registerB])

    def SUB(self, registerA, registerB):
        # Subtract the value in the second register from the first, storing the result in registerA.
        self.reg[registerA] = self.reg[registerA] - self.reg[registerB]

    def XOR(self, registerA, registerB):
        # Perform a bitwise-XOR between the values in registerA and registerB, storing the result in registerA.
        self.reg[registerA] = self.reg[registerA] ^ self.reg[registerB]