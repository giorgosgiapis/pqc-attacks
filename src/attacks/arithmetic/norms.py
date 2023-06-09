from typing import Sequence
from qiskit import QuantumCircuit, ClassicalRegister, QuantumRegister
from qiskit.circuit.library import CDKMRippleCarryAdder, HRSCumulativeMultiplier
from math import ceil, log2


class Norm2(QuantumCircuit):
    r"""
    Returns a circuit to calculate the norm of a given vector stored in a quantum register
    TODO: add details about the number of qubits, ancillas, etc.
    """

    def __init__(self, dimension: int, max_value: int, name: str = "NormCalc") -> None:
        r"""
        Creating a norm calcluating circuit
        """
        super().__init__(name=name)
        N = ceil(log2(max_value))  # number of qubits needed to store each entry
        values = [QuantumRegister(N, name=f"v_{i}") for i in range(dimension)]
        self.add_register(*values)
        copy = QuantumRegister(N, name="copy")
        self.add_register(copy)

        mult_gate = HRSCumulativeMultiplier(N).to_gate(label="SquareCalc")
        mult_outs = [
            QuantumRegister(2 * N + i, name=f"square_{i}") for i in range(dimension)
        ]
        mult_helper = QuantumRegister(1, name=f"multiplication helper")
        self.add_register(*mult_outs, mult_helper)

        add_helper = QuantumRegister(1, name=f"addition helper")
        couts = [QuantumRegister(1, name=f"cout_{i}") for i in range(dimension)]
        self.add_register(*couts, add_helper)

        norm = QuantumRegister(2 * N + dimension, name="norm")
        self.add_register(norm)

        circuit = QuantumCircuit(*self.qregs)
        for i in range(dimension):
            circuit.cx(values[i], copy)
            circuit.append(
                mult_gate, [*values[i], *copy, *mult_outs[i][: 2 * N], mult_helper]
            )
            circuit.append(
                CDKMRippleCarryAdder(2 * N + i, kind="half").to_gate(),
                [*mult_outs[i], *norm[: 2 * N + i], couts[i], add_helper],
            )
            circuit.cx(couts[i], norm[[2 * N + i]])
            circuit.cx(values[i], copy)

        self.append(circuit.to_gate(label=name), self.qubits)
