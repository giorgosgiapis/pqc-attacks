r"""
Utility quantum functions
"""
from qiskit import QuantumCircuit
from qiskit.circuit import Gate
from qiskit.circuit.library import CDKMRippleCarryAdder


def controlled_X(n: int) -> Gate:
    r"""
    Returns a controlled :math:`X^\otimes n` gate
    """
    circuit = QuantumCircuit(n)
    circuit.x(range(n))
    return circuit.control(1).to_gate(label="c-X^(⊗n)")


def controlled_adder(num_qubits: int) -> Gate:
    r"""
    Returns a controlled CDKMRippleCarryAdder half-adder gate.
    """
    return (
        CDKMRippleCarryAdder(num_qubits, kind="half")
        .control(1)
        .to_gate(label="c-Add")
    )
