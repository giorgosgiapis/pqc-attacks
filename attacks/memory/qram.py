r"""
Implements methods needed for quantum memory
"""
from math import ceil, log2
from qiskit import QuantumCircuit, QuantumRegister
from qiskit.circuit import ControlledGate
from ..utils.quantum import encode_vector


class qRAM(QuantumCircuit):
    r"""
    Simple qRAM implementation. Given a list of intgers it builds a circuit
    containing an address and a memory register. Setting the address register
    to a value (in binary) between :code:`0` and :code:`len(L)-1` sets the
    address memory to the corresponding list element.

    :param values: list of integers
    :param bits: number of bits used to store each element in sign-magnitude
        format
    """

    def __init__(
        self, values: list[list[int]], bits: int, name: str = "qRAM"
    ) -> None:
        super().__init__(name=name)
        if not values:
            raise IndexError("No values to store in qRAM")

        dimension: int = len(values[0])
        n_values: int = len(values)
        num_addr_qubits: int = 1 if n_values == 1 else ceil(log2(n_values))

        addr_reg: QuantumRegister = QuantumRegister(
            num_addr_qubits, name="addr"
        )
        self.add_register(addr_reg)

        value_regs: list[QuantumRegister] = [
            QuantumRegister(bits, name=f"v_{i}") for i in range(dimension)
        ]
        self.add_register(*value_regs)

        circuit: QuantumCircuit = QuantumCircuit(*self.qregs)
        for i in range(n_values):
            x_gates: list[QuantumRegister] = []
            for j, bit in enumerate(bin(i)[2:].zfill(num_addr_qubits)[::-1]):
                if bit == "0":
                    x_gates.append(addr_reg[j])
            if x_gates:
                circuit.x(x_gates)

            controlled_encode: ControlledGate = encode_vector(
                values[i], bits
            ).control(num_addr_qubits)
            circuit.append(controlled_encode, circuit.qubits)

            if x_gates:
                circuit.x(x_gates)

        self.append(circuit.to_gate(label=name), self.qubits)
        self.address_register: QuantumRegister = addr_reg
        self.memory_register: QuantumRegister = value_regs
