r"""
Module containing circuits to perform arithmetic operations on vectors
"""
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
    :param bits: Number of qubits used to store each vector component in sign-
        magnitute format

    TODO: add details about the circuit implementation, number qubits, ancillas,
    etc
    """

    def __init__(
        self, dimension: int, bits: int, name: str = "NormCalc"
    ) -> None:
        r"""
        Creates a norm calcluating circuit
        """
        super().__init__(name=name)
        magnitude_bits = bits - 1
        signs = [QuantumRegister(1, name=f"sgn_{i}") for i in range(dimension)]
        values = [
            QuantumRegister(magnitude_bits, name=f"val_{i}")
            for i in range(dimension)
        ]
        for i in range(dimension):
            self.add_register(values[i], signs[i])

        copy = QuantumRegister(magnitude_bits, name="copy")
        self.add_register(copy)

        mult_gate = HRSCumulativeMultiplier(magnitude_bits).to_gate(
            label="SquareCalc"
        )
        mult_outs = [
            QuantumRegister(2 * magnitude_bits + i, name=f"square_{i}")
            for i in range(dimension)
        ]
        mult_helper = QuantumRegister(1, name="multiplication helper")
        self.add_register(*mult_outs, mult_helper)

        add_helper = QuantumRegister(1, name="addition helper")
        couts = [
            QuantumRegister(1, name=f"cout_{i}") for i in range(dimension)
        ]
        self.add_register(*couts, add_helper)

        norm = QuantumRegister(2 * magnitude_bits + dimension, name="norm")
        self.add_register(norm)

        circuit = QuantumCircuit(*self.qregs)
        for i in range(dimension):
            circuit.cx(values[i], copy)
            circuit.append(
                mult_gate,
                [
                    *values[i],
                    *copy,
                    *mult_outs[i][: 2 * magnitude_bits],
                    mult_helper,
                ],
            )
            circuit.append(
                CDKMRippleCarryAdder(
                    2 * magnitude_bits + i, kind="half"
                ).to_gate(),
                [
                    *mult_outs[i],
                    *norm[: 2 * magnitude_bits + i],
                    couts[i],
                    add_helper,
                ],
            )
            circuit.cx(couts[i], norm[2 * magnitude_bits + i])
            circuit.cx(values[i], copy)

        self.append(circuit.to_gate(label=name), self.qubits)
        self.num_result_qubits: int = len(norm)


if __name__ == "__main__":
    print(Norm2(3, 5).draw())
