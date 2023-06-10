r"""
Contains methods to perform arithemtic operations on (signed) integers stored
on quantum registers
"""
from qiskit import QuantumCircuit, QuantumRegister
from qiskit.circuit.library import CDKMRippleCarryAdder
from ..utils.quantum import controlled_X, controlled_adder


class SignedAdder(QuantumCircuit):
    r"""
    Accepts two integers stored in two quantum registers in sign-magnitude
    representation and computes their (in-place) sum in sign-magnitude
    representation.
    TODO: write docs
    """

    def __init__(self, bits: int, name: str = "SignedAdder") -> None:
        r"""
        Creates a signed adder circuit
        """
        super().__init__(name=name)
        nums = [
            QuantumRegister(bits, name="num1"),
            QuantumRegister(bits, name="num2"),
        ]
        self.add_register(*nums)

        cout = QuantumRegister(1, name="cout")
        helper = QuantumRegister(1, name="helper")
        self.add_register(cout, helper)

        ccout = QuantumRegister(1, name="c_cout")
        self.add_register(ccout)

        one = QuantumRegister(bits, name="one")
        self.add_register(one)

        circuit = QuantumCircuit(*self.qregs)
        circuit.x(one[0])

        # convert to 1's complement format
        c_tensor_x = controlled_X(bits - 1)
        for i in range(2):
            circuit.append(c_tensor_x, [nums[i][-1], *nums[i][:-1]])

        # add the two registers
        circuit.append(
            CDKMRippleCarryAdder(bits, kind="half").to_gate(),
            [*nums[0], *nums[1], cout, helper],
        )
        # if the carry bit is 1 disregard it and add 1 to the result
        circuit.append(
            controlled_adder(bits), [cout, *one, *nums[1], ccout, helper]
        )
        # reset the ancillary qubit storing the value of 1
        circuit.x(one[0])

        # convert the two registers to sign-magnitude format
        # the second register stores the value of the sum
        for i in range(2):
            circuit.append(c_tensor_x, [nums[i][-1], *nums[i][:-1]])

        self.append(circuit.to_gate(label=name), self.qubits)
