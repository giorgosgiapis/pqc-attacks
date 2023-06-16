r"""
Utility quantum functions
"""
from math import ceil, log2
from qiskit import QuantumCircuit, QuantumRegister
from qiskit.circuit import Gate


def controlled_X(n: int) -> Gate:
    r"""
    Returns a controlled :math:`X^{\otimes n}` gate
    """
    circuit: QuantumCircuit = QuantumCircuit(n)
    circuit.x(range(n))
    return circuit.control(1).to_gate(label="c-X^(⊗n)")


def controlled_incr(num_qubits: int) -> Gate:
    r"""
    Returns a controlled increment gate.
    """
    incr_circuit: QuantumCircuit = QuantumCircuit(num_qubits)
    for i in range(num_qubits - 1, 0, -1):
        incr_circuit.mcx(list(range(i)), i)
    incr_circuit.x(0)

    return incr_circuit.control(1).to_gate(label="c-Incr")


def encode_signed_int(value: int, bits: int) -> Gate:
    r"""
    Returns a gate encoding a signed integer in a quantum register in sign-
    magnitude representation
    """
    magnitude_bits: int = bits - 1
    if abs(value) > 0 and ceil(log2(abs(value))) > magnitude_bits:
        raise ValueError(f"{bits} bits are not enough bits to encode {value}")

    circuit: QuantumCircuit = QuantumCircuit()
    value_reg: QuantumRegister = QuantumRegister(magnitude_bits, name="value")
    sign_reg: QuantumRegister = QuantumRegister(1, name="sgn")
    circuit.add_register(value_reg, sign_reg)

    if value < 0:
        circuit.x(sign_reg)

    value_bin: str = bin(value)[2:].zfill(magnitude_bits)[::-1]
    for i, bit in enumerate(value_bin):
        if bit == "1":
            circuit.x(value_reg[i])

    return circuit.to_gate(label="encode")
