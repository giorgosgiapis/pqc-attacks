from math import ceil, log2
from qiskit import QuantumCircuit, QuantumRegister
from qiskit.circuit.library import (
    CDKMRippleCarryAdder,
    HRSCumulativeMultiplier,
)


class Norm2(QuantumCircuit):
    r"""
    Returns a circuit to calculate the square of the norm of a given vector
    stored in a quantum register

    :param dimension: Dimension of the vector
    :param max_value: Upper bound for the maximum value of any vector element.
        :math:`\lceil\log_2(\text{max_value})\rceil` qubits are needed to store
        each vector entry

    TODO: add details about the circuit implementation, number qubits, ancillas,
    etc
    """

    def __init__(
        self, dimension: int, max_value: int, name: str = "NormCalc"
    ) -> None:
        r"""
        Creating a norm calcluating circuit
        """
        super().__init__(name=name)
        N = ceil(log2(max_value))  # no of qubits needed to represent elements
        values = [QuantumRegister(N, name=f"v_{i}") for i in range(dimension)]
        self.add_register(*values)
        copy = QuantumRegister(N, name="copy")
        self.add_register(copy)

        mult_gate = HRSCumulativeMultiplier(N).to_gate(label="SquareCalc")
        mult_outs = [
            QuantumRegister(2 * N + i, name=f"square_{i}")
            for i in range(dimension)
        ]
        mult_helper = QuantumRegister(1, name="multiplication helper")
        self.add_register(*mult_outs, mult_helper)

        add_helper = QuantumRegister(1, name="addition helper")
        couts = [
            QuantumRegister(1, name=f"cout_{i}") for i in range(dimension)
        ]
        self.add_register(*couts, add_helper)

        norm = QuantumRegister(2 * N + dimension, name="norm")
        self.add_register(norm)

        circuit = QuantumCircuit(*self.qregs)
        for i in range(dimension):
            circuit.cx(values[i], copy)
            circuit.append(
                mult_gate,
                [*values[i], *copy, *mult_outs[i][: 2 * N], mult_helper],
            )
            circuit.append(
                CDKMRippleCarryAdder(2 * N + i, kind="half").to_gate(),
                [*mult_outs[i], *norm[: 2 * N + i], couts[i], add_helper],
            )
            circuit.cx(couts[i], norm[[2 * N + i]])
            circuit.cx(values[i], copy)

        self.append(circuit.to_gate(label=name), self.qubits)
