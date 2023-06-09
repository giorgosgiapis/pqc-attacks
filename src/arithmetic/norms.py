from typing import Sequence
from qiskit import QuantumCircuit, ClassicalRegister, QuantumRegister
from qiskit.circuit.library import CDKMRippleCarryAdder, HRSCumulativeMultiplier
from math import ceil, log2


class Norm2(QuantumCircuit):
    def __init__(self, dimension: int, max_value: int, name: str = "NormCalc") -> None:
        r"""
        TODO: Add documentation
        """
        super().__init__(name=name)
        N = ceil(log2(max_value))
        values = [QuantumRegister(N, name=f"v_{i}") for i in range(dimension)]
        self.add_register(*values)
        copy = QuantumRegister(N, name="copy")
        self.add_register(copy)

        mult_gate = HRSCumulativeMultiplier(3).to_gate(label="SquareCalc")
        mult_outs = [
            QuantumRegister(2 * N + i, name=f"square_{i}") for i in range(dimension)
        ]
        mult_helpers = [
            QuantumRegister(1, name=f"multiplication helper_{i}")
            for i in range(dimension)
        ]
        self.add_register(*mult_outs, *mult_helpers)

        add_helpers = [
            QuantumRegister(1, name=f"addition helper_{i}") for i in range(dimension)
        ]
        couts = [QuantumRegister(1, name=f"cout_{i}") for i in range(dimension)]
        self.add_register(*couts, *add_helpers)

        norm = QuantumRegister(2 * N + dimension, name="norm")
        self.add_register(norm)

        circuit = QuantumCircuit(*self.qregs)
        for i in range(dimension):
            circuit.cx(values[i], copy)
            circuit.append(
                mult_gate, [*values[i], *copy, *mult_outs[i][: 2 * N], *mult_helpers[i]]
            )
            circuit.append(
                CDKMRippleCarryAdder(2 * N + i, kind="half").to_gate(),
                [*mult_outs[i], *norm[: 2 * N + i], *couts[i], *add_helpers[i]],
            )
            circuit.cx(couts[i], norm[[2 * N + i]])
            circuit.cx(values[i], copy)

        self.append(circuit.to_gate(label=name), self.qubits)
