import pytest
from qiskit import QuantumCircuit, ClassicalRegister, execute
from qiskit_aer import AerSimulator
from attacks.utils.quantum import encode_signed_int
from attacks.arithmetic.operations import SignedAdder, Compare


def test_SignedAdder():
    test_vals = [-5, -3, -2, 0, 1, 4]
    signed_adder = SignedAdder(5)
    simulator = AerSimulator(method="matrix_product_state")

    for num_1, num_2 in zip(test_vals, test_vals):
        circuit = QuantumCircuit(signed_adder.num_qubits)
        circuit.append(encode_signed_int(num_1, 5), circuit.qubits[0:5])
        circuit.append(encode_signed_int(num_2, 5), circuit.qubits[5:10])
        circuit.append(signed_adder, *circuit.qregs)

        result_reg = ClassicalRegister(5)
        circuit.add_register(result_reg)

        circuit.measure(circuit.qubits[5:10], result_reg)
        result = execute(circuit, simulator, shots=1024).result().get_counts()

        res_bitstring = list(result.keys())[0]
        value = int(res_bitstring[1:], 2)
        if res_bitstring[0] == "1":
            value *= -1

        assert len(result) == 1 and value == num_1 + num_2


def test_Compare():
    test_vals = [-5, -2, 0, 1, 4]
    simulator = AerSimulator(method="matrix_product_state")

    for num_1, num_2 in zip(test_vals, test_vals):
        for cmp in ["==", ">", "<", ">=", "<="]:
            comparator = Compare(5, cmp=cmp)
            circuit = QuantumCircuit(comparator.num_qubits)
            circuit.append(encode_signed_int(num_1, 5), circuit.qubits[0:5])
            circuit.append(encode_signed_int(num_2, 5), circuit.qubits[5:10])
            circuit.append(comparator, *circuit.qregs)

            result_reg = ClassicalRegister(1)
            circuit.add_register(result_reg)

            circuit.measure(circuit.qubits[-1], result_reg)
            result = (
                execute(circuit, simulator, shots=1024).result().get_counts()
            )
            expected = eval(f"{num_1}{cmp}{num_2}")
            assert result == {str(int(expected)): 1024}

    with pytest.raises(ValueError):
        comparator = Compare(5, cmp="!=")
