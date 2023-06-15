from qiskit import QuantumCircuit, ClassicalRegister, execute
from qiskit_aer import AerSimulator
from attacks.arithmetic.vectors import Norm2
from attacks.utils.quantum import encode_signed_int


def test_Norm2():
    vec = [1, -4, 6, -2]

    norm_calc = Norm2(len(vec), 5)
    circuit = QuantumCircuit(*norm_calc.qregs)

    ind = 0
    for element in vec:
        circuit.append(
            encode_signed_int(element, 5), circuit.qubits[ind : ind + 5]
        )
        ind += 5

    circuit.append(norm_calc, circuit.qubits)

    result_bits = len(norm_calc.result_register)
    result_reg = ClassicalRegister(result_bits)
    circuit.add_register(result_reg)

    circuit.measure(norm_calc.result_register, result_reg)

    simulator = AerSimulator(method="matrix_product_state")
    result = execute(circuit, simulator, shots=1024).result().get_counts()

    norm = sum([v**2 for v in vec])
    assert result == {bin(norm)[2::].zfill(result_bits): 1024}
