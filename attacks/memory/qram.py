from math import ceil, log2
from qiskit import QuantumCircuit, QuantumRegister
from ..utils.quantum import encode_signed_int


class qRAM(QuantumCircuit):
    r"""
    TODO: Documentation
    """

    def __init__(self, values: list[list[int]], bits: int, name: str = "qRAM"):
        super().__init__(name=name)
        if not values:
            raise IndexError("No values to store in qRAM")

        dimension = len(values[0])
        n_values = len(values)
        num_addr_qubits = 1 if n_values == 1 else ceil(log2(n_values))

        addr_reg = QuantumRegister(num_addr_qubits, name="addr")
        self.add_register(addr_reg)

        value_regs = [
            QuantumRegister(bits, name=f"v_{i}") for i in range(dimension)
        ]
        self.add_register(*value_regs)

        circuit = QuantumCircuit(*self.qregs)
        for i in range(n_values):
            x_gates = []
            for j, bit in enumerate(bin(i)[2:].zfill(num_addr_qubits)):
                if bit == "0":
                    x_gates.append(addr_reg[j])
            if x_gates:
                circuit.x(x_gates)

            for j, element in enumerate(values[i]):
                controlled_encode = encode_signed_int(element, bits).control(
                    num_addr_qubits
                )
                circuit.append(controlled_encode, [*addr_reg, *value_regs[j]])

            if x_gates:
                circuit.x(x_gates)

        self.append(circuit.to_gate(label=name), self.qubits)
        self.address_register = addr_reg
        self.memory_register = value_regs
