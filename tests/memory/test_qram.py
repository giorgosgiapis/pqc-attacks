from qiskit import QuantumCircuit, ClassicalRegister, execute
from qiskit_aer import AerSimulator
from attacks.memory.qram import qRAM


def test_qRAM():
    test_list = [[-1], [2], [3]]
    qram = qRAM(test_list, bits=5)

    assert len(qram.address_register) == 2

    simulator = AerSimulator(method="matrix_product_state")

    for i in range(2):
        circuit = QuantumCircuit(*qram.qregs)
        if i == 1:
            circuit.x(qram.address_register[0])
        elif i == 2:
            circuit.x(qram.address_register[1])

        circuit.append(qram, circuit.qubits)

        result_reg = ClassicalRegister(5)
        circuit.add_register(result_reg)

        circuit.measure(*qram.memory_register, result_reg)

        result = execute(circuit, simulator, shots=1024).result().get_counts()

        expected_res = bin(abs(test_list[i][0]))[2:].zfill(4)
        if test_list[i][0] < 0:
            expected_res = '1' + expected_res
        else:
            expected_res = '0' + expected_res

        assert result == {expected_res: 1024}
