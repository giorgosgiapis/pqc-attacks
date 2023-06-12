import pytest
from qiskit import QuantumCircuit, execute
from qiskit_aer import AerSimulator
from attacks.utils.quantum import encode_signed_int


def test_encode_signed_int():
    circuit = QuantumCircuit(5)
    circuit.append(encode_signed_int(7, 5), *circuit.qregs)
    circuit.measure_all()

    simulator = AerSimulator(method="matrix_product_state")
    result = execute(circuit, simulator, shots=1024).result().get_counts()

    assert result == {"00111": 1024}

    circuit = QuantumCircuit(5)
    circuit.append(encode_signed_int(-2, 5), *circuit.qregs)
    circuit.measure_all()

    result = execute(circuit, simulator, shots=1024).result().get_counts()

    assert result == {"10010": 1024}

    circuit = QuantumCircuit(5)
    with pytest.raises(ValueError):
        circuit.append(encode_signed_int(256, 5), *circuit.qregs)
