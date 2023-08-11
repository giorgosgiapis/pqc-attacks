from qiskit import QuantumCircuit, execute
from qiskit_aer import AerSimulator
from attacks.utils.quantum import encode_vector
from attacks.grover.oracles import ReductionOracle


def test_ReductionOracle():
    first_oracle = ReductionOracle(2, 2, 4)._marking_oracle()
    second_oracle = ReductionOracle(2, 2, 4)._marking_oracle(first=False)

    simulator = AerSimulator(method="matrix_product_state")

    # (1, 2) and (3, 4) satisfy the conditions for the first oracle but
    # not for the second
    circuit = QuantumCircuit(*first_oracle.qregs)
    circuit.append(encode_vector([1, 2], 4), circuit.qubits[2:10])
    circuit.append(encode_vector([3, 4], 4), circuit.qubits[10:18])
    circuit.append(first_oracle, circuit.qubits)
    circuit.measure_all()

    result = execute(circuit, simulator, shots=1024).result().get_counts()

    assert result == {
        "10000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000010000110010000100": 1024
    }

    circuit = QuantumCircuit(*second_oracle.qregs)
    circuit.append(encode_vector([1, 2], 4), circuit.qubits[2:10])
    circuit.append(encode_vector([3, 4], 4), circuit.qubits[10:18])
    circuit.append(second_oracle, circuit.qubits)
    circuit.measure_all()

    result = execute(circuit, simulator, shots=1024).result().get_counts()

    assert result == {
        "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000010000110010000100": 1024
    }

    # The same holds for (1, 2) and (-1, 2)
    circuit = QuantumCircuit(*first_oracle.qregs)
    circuit.append(encode_vector([1, 2], 4), circuit.qubits[2:10])
    circuit.append(encode_vector([-1, 2], 4), circuit.qubits[10:18])
    circuit.append(first_oracle, circuit.qubits)
    circuit.measure_all()

    result = execute(circuit, simulator, shots=1024).result().get_counts()

    assert result == {
        "10000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001010010010000100": 1024
    }

    circuit = QuantumCircuit(*second_oracle.qregs)
    circuit.append(encode_vector([1, 2], 4), circuit.qubits[2:10])
    circuit.append(encode_vector([-1, 2], 4), circuit.qubits[10:18])
    circuit.append(second_oracle, circuit.qubits)
    circuit.measure_all()

    result = execute(circuit, simulator, shots=1024).result().get_counts()

    assert result == {
        "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001010010010000100": 1024
    }

    # (-1, 2) and (0, 2) satisfy the conditions for the second oracle but not
    # the first
    circuit = QuantumCircuit(*second_oracle.qregs)
    circuit.append(encode_vector([-1, 2], 4), circuit.qubits[2:10])
    circuit.append(encode_vector([0, 2], 4), circuit.qubits[10:18])
    circuit.append(second_oracle, circuit.qubits)
    circuit.measure_all()

    result = execute(circuit, simulator, shots=1024).result().get_counts()

    assert result == {
        "10000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001000000010100100": 1024
    }

    circuit = QuantumCircuit(*first_oracle.qregs)
    circuit.append(encode_vector([-1, 2], 4), circuit.qubits[2:10])
    circuit.append(encode_vector([0, 2], 4), circuit.qubits[10:18])
    circuit.append(first_oracle, circuit.qubits)
    circuit.measure_all()

    result = execute(circuit, simulator, shots=1024).result().get_counts()

    assert result == {
        "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001000000010100100": 1024
    }

    # (1, 3) and (-1, 1) satisfy the conditions for the second oracle but not
    # the first
    circuit = QuantumCircuit(*second_oracle.qregs)
    circuit.append(encode_vector([1, 3], 4), circuit.qubits[2:10])
    circuit.append(encode_vector([-1, 1], 4), circuit.qubits[10:18])
    circuit.append(second_oracle, circuit.qubits)
    circuit.measure_all()

    result = execute(circuit, simulator, shots=1024).result().get_counts()

    assert result == {
        "10000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000110010011000100": 1024
    }

    circuit = QuantumCircuit(*first_oracle.qregs)
    circuit.append(encode_vector([1, 3], 4), circuit.qubits[2:10])
    circuit.append(encode_vector([-1, 1], 4), circuit.qubits[10:18])
    circuit.append(first_oracle, circuit.qubits)
    circuit.measure_all()

    result = execute(circuit, simulator, shots=1024).result().get_counts()

    assert result == {
        "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000110010011000100": 1024
    }
