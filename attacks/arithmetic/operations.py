r"""
Contains methods to perform arithemtic operations on (signed) integers stored
on quantum registers
"""
from qiskit import QuantumCircuit, QuantumRegister, AncillaRegister
from qiskit.circuit.library import CDKMRippleCarryAdder
from ..utils.quantum import controlled_X, controlled_incr


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

        cout = AncillaRegister(1, name="cout")
        helper = AncillaRegister(1, name="helper")
        self.add_register(cout, helper)

        circuit = QuantumCircuit(*self.qregs)

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
        circuit.append(controlled_incr(bits), [cout, *nums[1]])

        # convert the two registers to sign-magnitude format
        # the second register stores the value of the sum
        for i in range(2):
            circuit.append(c_tensor_x, [nums[i][-1], *nums[i][:-1]])

        self.append(circuit.to_gate(label=name), self.qubits)


class Compare(QuantumCircuit):
    r"""
    Compares two signed integers stored in quantum registers:

    .. math::

        |a\rangle|b\rangle|0\rangle\mapsto |a\rangle|a-b\rangle|a\gtrless b\rangle

    TODO: add more
    """

    def __init__(self, bits: int, cmp: str = ">", name: str = "Compare"):
        r"""
        Creates a comparator circuit
        """
        super().__init__(name=name)
        magnitude_bits = bits - 1
        val_1 = QuantumRegister(magnitude_bits, name="val_1")
        sgn_1 = QuantumRegister(1, name="sgn1")
        val_2 = QuantumRegister(magnitude_bits, name="val_2")
        sgn_2 = QuantumRegister(1, name="sgn2")
        self.add_register(val_1, sgn_1, val_2, sgn_2)

        adder = SignedAdder(bits, name="Subtract")

        anc = AncillaRegister(adder.num_ancillas, name="ancillas")
        self.add_register(anc)

        is_zero = AncillaRegister(1, name="zero_flag")
        self.add_register(is_zero)

        result = QuantumRegister(1, name="result")
        self.add_register(result)

        circuit = QuantumCircuit(*self.qregs)
        circuit.x(sgn_2)
        circuit.append(adder.to_gate(), [*val_1, *sgn_1, *val_2, *sgn_2, *anc])

        circuit.x(val_2)
        circuit.mcx(val_2, is_zero)
        circuit.x(val_2)

        if cmp not in ("==", ">", "<", ">=", "<="):
            raise ValueError(
                "Parameter `cmp` should be one of '==', '>', '<', '>=', '<='"
            )

        if cmp == "==":
            circuit.cx(is_zero, result)
        elif cmp in (">", "<="):
            circuit.x(is_zero)
            circuit.x(sgn_2)
            circuit.mcx([*sgn_2, *is_zero], result)
            circuit.x(sgn_2)
        elif cmp in ("<", ">="):
            circuit.x(is_zero)
            circuit.mcx([*sgn_2, *is_zero], result)

        if cmp in (">=", "<="):
            circuit.x(result)

        self.append(circuit.to_gate(label=name), self.qubits)
