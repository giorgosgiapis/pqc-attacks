r"""
Module containing circuits to perform arithmetic operations on vectors
"""
from qiskit import QuantumCircuit, QuantumRegister, AncillaRegister
from qiskit.circuit import Gate
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
        magnitude_bits: int = bits - 1
        signs: list[QuantumRegister] = [
            QuantumRegister(1, name=f"sgn_{i}") for i in range(dimension)
        ]
        values: list[QuantumRegister] = [
            QuantumRegister(magnitude_bits, name=f"val_{i}")
            for i in range(dimension)
        ]
        for i in range(dimension):
            self.add_register(values[i], signs[i])

        copy: AncillaRegister = AncillaRegister(magnitude_bits, name="copy")
        self.add_register(copy)

        mult_gate: Gate = HRSCumulativeMultiplier(magnitude_bits).to_gate(
            label="SquareCalc"
        )
        mult_outs: list[AncillaRegister] = [
            AncillaRegister(2 * magnitude_bits + i, name=f"square_{i}")
            for i in range(dimension)
        ]
        mult_helper: AncillaRegister = AncillaRegister(
            1, name="multiplication helper"
        )
        self.add_register(*mult_outs, mult_helper)

        add_helper: AncillaRegister = AncillaRegister(
            1, name="addition helper"
        )
        couts: list[AncillaRegister] = [
            AncillaRegister(1, name=f"cout_{i}") for i in range(dimension)
        ]
        self.add_register(*couts, add_helper)

        norm: QuantumRegister = QuantumRegister(
            2 * magnitude_bits + dimension, name="norm"
        )
        self.add_register(norm)

        circuit: QuantumCircuit = QuantumCircuit(*self.qregs)
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
        self.result_register: QuantumRegister = norm
