r"""
Implements oracles for Grover's algorithm
"""
from qiskit import QuantumRegister, QuantumCircuit
from ..arithmetic.vectors import Norm2
from ..arithmetic.operations import Compare, SignedAdder


class ReductionOracles:
    r"""
    Implements oracles for Grvoer's algorithm
    TODO: Write docs
    """

    def __init__(
        self, num_address_qubits: int, dimension: int, bits: int
    ) -> None:
        self.num_address_qubits = num_address_qubits
        self.dimension = dimension
        self.bits = bits

    def _first_marking_oracle(self) -> QuantumCircuit:
        r"""
        Marking oracle for the first part of GaussReduce algorithm. Marks all
        vectors :math:`v` in qRAM such that :math:`\|v\| \leq \|p\|` and
        :math:`\|p-v\| < \|p\|`
        """
        circuit: QuantumCircuit = QuantumCircuit()
        addr_reg: QuantumRegister = QuantumRegister(
            self.num_address_qubits, name="addr"
        )
        circuit.add_register(addr_reg)

        mem_regs: list[QuantumRegister] = [
            QuantumRegister(self.bits, name=f"v_{i}")
            for i in range(self.dimension)
        ]
        circuit.add_register(*mem_regs)


        p_value_regs: list[QuantumRegister] = [
            QuantumRegister(self.bits, name=f"p_{i}")
            for i in range(self.dimension)
        ]
        circuit.add_register(*p_value_regs)

        mem_regs_copy: list[QuantumRegister] = [
            QuantumRegister(self.bits, name=f"v_{i}_copy")
            for i in range(self.dimension)
        ]
        circuit.add_register(*mem_regs_copy)

        p_value_regs_copy: list[QuantumRegister] = [
            QuantumRegister(self.bits, name=f"p_{i}_copy")
            for i in range(self.dimension)
        ]
        circuit.add_register(*p_value_regs_copy)

        for i in range(self.dimension):
            circuit.cx(mem_regs[i], mem_regs_copy[i])
            circuit.cx(p_value_regs[i], p_value_regs_copy[i])

        norm_circ: QuantumCircuit = Norm2(self.dimension, self.bits)

        anc_norm_1: QuantumRegister = QuantumRegister(
            norm_circ.num_ancillas, name="anc1"
        )
        res_norm_1: QuantumRegister = QuantumRegister(
            len(norm_circ.result_register) + 1, name=r"\|v\|"
        )
        circuit.add_register(anc_norm_1, res_norm_1)

        anc_norm_2: QuantumRegister = QuantumRegister(
            norm_circ.num_ancillas, name="anc2"
        )
        res_norm_2: QuantumRegister = QuantumRegister(
            len(norm_circ.result_register) + 1, name=r"\|p\|"
        )
        circuit.add_register(anc_norm_2, res_norm_2)

        anc_norm_3: QuantumRegister = QuantumRegister(
            norm_circ.num_ancillas, name="anc3"
        )
        res_norm_3: QuantumRegister = QuantumRegister(
            len(norm_circ.result_register) + 1, name=r"\|p-v\|"
        )
        circuit.add_register(anc_norm_3, res_norm_3)

        anc_norm_4: QuantumRegister = QuantumRegister(
            norm_circ.num_ancillas, name="anc4"
        )
        res_norm_4: QuantumRegister = QuantumRegister(
            len(norm_circ.result_register) + 1, name=r"\|p\| (copy)"
        )
        circuit.add_register(anc_norm_4, res_norm_4)

        comp_leq_circ: QuantumCircuit = Compare(len(res_norm_1), cmp="<=")
        comp_le_circ: QuantumCircuit = Compare(len(res_norm_3), cmp="<")

        comp_leq_anc: QuantumRegister = QuantumRegister(
            comp_leq_circ.num_ancillas, name="leq_anc"
        )
        comp_res1: QuantumRegister = QuantumRegister(1, name=r"\|v\|\leq \|p\|")
        circuit.add_register(comp_leq_anc, comp_res1)

        comp_le_anc: QuantumRegister = QuantumRegister(
            comp_le_circ.num_ancillas, name="le_anc"
        )
        comp_res2: QuantumRegister = QuantumRegister(1, name=r"\|v-p\|<\|p\|")
        circuit.add_register(comp_le_anc, comp_res2)

        mem_qubits = []
        for reg in mem_regs:
            mem_qubits.extend([*reg])

        p_qubits = []
        for reg in p_value_regs:
            p_qubits.extend([*reg])

        mem_copy_qubits = []
        for reg in mem_regs_copy:
            mem_copy_qubits.extend([*reg])

        p_copy_qubits = []
        for reg in p_value_regs_copy:
            p_copy_qubits.extend([*reg])

        for reg in mem_regs_copy:
            circuit.x(reg[-1])

        adder: QuantumCircuit = SignedAdder(self.bits)
        couts = [
            QuantumRegister(1, name=f"cout_{i}") for i in range(self.dimension)
        ]
        add_helper = QuantumRegister(1, name="add_helper")
        circuit.add_register(*couts, add_helper)

        for i in range(self.dimension):
            circuit.append(
                adder,
                [
                    *p_value_regs_copy[i],
                    *mem_regs_copy[i],
                    couts[i],
                    add_helper,
                ],
            )

        circuit.append(norm_circ, [*mem_qubits, *anc_norm_1, *res_norm_1[:-1]])
        circuit.append(norm_circ, [*p_qubits, *anc_norm_2, *res_norm_2[:-1]])
        circuit.append(
            comp_leq_circ,
            [*res_norm_1, *res_norm_2, *comp_leq_anc, *comp_res1],
        )

        circuit.append(
            norm_circ, [*mem_copy_qubits, *anc_norm_3, *res_norm_3[:-1]]
        )
        circuit.append(
            norm_circ, [*p_copy_qubits, *anc_norm_4, *res_norm_4[:-1]]
        )
        circuit.append(
            comp_le_circ, [*res_norm_3, *res_norm_4, *comp_le_anc, *comp_res2]
        )

        final_res: QuantumRegister = QuantumRegister(
            1, name="final_result"
        )
        circuit.add_register(final_res)

        circuit.mcx([comp_res1, comp_res2], final_res)

        circuit.append(
            comp_le_circ.inverse(),
            [*res_norm_3, *res_norm_4, *comp_le_anc, *comp_res2],
        )
        circuit.append(
            norm_circ.inverse(),
            [*p_copy_qubits, *anc_norm_4, *res_norm_4[:-1]],
        )
        circuit.append(
            norm_circ.inverse(),
            [*mem_copy_qubits, *anc_norm_3, *res_norm_3[:-1]],
        )

        circuit.append(
            comp_leq_circ.inverse(),
            [*res_norm_1, *res_norm_2, *comp_leq_anc, *comp_res1],
        )
        circuit.append(
            norm_circ.inverse(), [*p_qubits, *anc_norm_2, *res_norm_2[:-1]]
        )
        circuit.append(
            norm_circ.inverse(), [*mem_qubits, *anc_norm_1, *res_norm_1[:-1]]
        )

        for i in range(self.dimension):
            circuit.append(
                adder.inverse(),
                [
                    *p_value_regs_copy[i],
                    *mem_regs_copy[i],
                    couts[i],
                    add_helper,
                ],
            )

        for reg in mem_regs_copy:
            circuit.x(reg[-1])

        for i in range(self.dimension):
            circuit.cx(mem_regs[i], mem_regs_copy[i])
            circuit.cx(p_value_regs[i], p_value_regs_copy[i])

        return circuit
