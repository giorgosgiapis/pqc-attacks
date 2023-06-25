r"""
Implements oracles for Grover's algorithm
"""
from qiskit import QuantumRegister, QuantumCircuit
from ..arithmetic.vectors import Norm2
from ..arithmetic.operations import Compare, SignedAdder


class ReductionOracle:
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
        circuit: QuantumCircuit = QuantumCircuit(
            name="|v| <= |p| & |p-v| < |p|"
        )
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

        for i in range(self.dimension):
            circuit.cx(mem_regs[i], mem_regs_copy[i])

        norm_circ: QuantumCircuit = Norm2(self.dimension, self.bits)

        v_norm_anc: QuantumRegister = QuantumRegister(
            norm_circ.num_ancillas, name="anc1"
        )
        v_norm: QuantumRegister = QuantumRegister(
            len(norm_circ.result_register) + 1, name=r"\|v\|"
        )
        circuit.add_register(v_norm_anc, v_norm)

        p_norm_anc: QuantumRegister = QuantumRegister(
            norm_circ.num_ancillas, name="anc2"
        )
        p_norm: QuantumRegister = QuantumRegister(
            len(norm_circ.result_register) + 1, name=r"\|p\|"
        )
        circuit.add_register(p_norm_anc, p_norm)

        diff_norm_anc: QuantumRegister = QuantumRegister(
            norm_circ.num_ancillas, name="anc3"
        )
        diff_norm: QuantumRegister = QuantumRegister(
            len(norm_circ.result_register) + 1, name=r"\|p-v\|"
        )
        circuit.add_register(diff_norm_anc, diff_norm)

        comp_geq_circ: QuantumCircuit = Compare(len(v_norm), cmp=">=")
        comp_le_circ: QuantumCircuit = Compare(len(diff_norm), cmp="<")

        comp_geq_anc: QuantumRegister = QuantumRegister(
            comp_geq_circ.num_ancillas, name="geq_anc"
        )
        v_leq_p: QuantumRegister = QuantumRegister(1, name=r"\|v\|\leq \|p\|")
        circuit.add_register(comp_geq_anc, v_leq_p)

        comp_le_anc: QuantumRegister = QuantumRegister(
            comp_le_circ.num_ancillas, name="le_anc"
        )
        diff_leq_p: QuantumRegister = QuantumRegister(1, name=r"\|p-v\|<\|p\|")
        circuit.add_register(comp_le_anc, diff_leq_p)

        mem_qubits = []
        for reg in mem_regs:
            mem_qubits.extend([*reg])

        p_qubits = []
        for reg in p_value_regs:
            p_qubits.extend([*reg])

        mem_copy_qubits = []
        for reg in mem_regs_copy:
            mem_copy_qubits.extend([*reg])

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
                    *p_value_regs[i],
                    *mem_regs_copy[i],
                    couts[i],
                    add_helper,
                ],
            )

        circuit.append(norm_circ, [*mem_qubits, *v_norm_anc, *v_norm[:-1]])
        circuit.append(norm_circ, [*p_qubits, *p_norm_anc, *p_norm[:-1]])
        circuit.append(
            comp_geq_circ,
            [*p_norm, *v_norm, *comp_geq_anc, *v_leq_p],
        )

        circuit.append(
            norm_circ, [*mem_copy_qubits, *diff_norm_anc, *diff_norm[:-1]]
        )
        circuit.append(
            comp_le_circ, [*diff_norm, *p_norm, *comp_le_anc, *diff_leq_p]
        )

        final_res: QuantumRegister = QuantumRegister(1, name="final_result")
        circuit.add_register(final_res)

        circuit.mcx([v_leq_p, diff_leq_p], final_res)

        circuit.append(
            comp_le_circ.inverse(),
            [*diff_norm, *p_norm, *comp_le_anc, *diff_leq_p],
        )
        circuit.append(
            norm_circ.inverse(),
            [*mem_copy_qubits, *diff_norm_anc, *diff_norm[:-1]],
        )

        circuit.append(
            comp_geq_circ.inverse(),
            [*p_norm, *v_norm, *comp_geq_anc, *v_leq_p],
        )
        circuit.append(
            norm_circ.inverse(), [*p_qubits, *p_norm_anc, *p_norm[:-1]]
        )
        circuit.append(
            norm_circ.inverse(), [*mem_qubits, *v_norm_anc, *v_norm[:-1]]
        )

        for i in range(self.dimension):
            circuit.append(
                adder.inverse(),
                [
                    *p_value_regs[i],
                    *mem_regs_copy[i],
                    couts[i],
                    add_helper,
                ],
            )

        for reg in mem_regs_copy:
            circuit.x(reg[-1])

        for i in range(self.dimension):
            circuit.cx(mem_regs[i], mem_regs_copy[i])

        return circuit

    def first_phase_oracle(self) -> QuantumCircuit:
        r"""
        Phase oracle corresponding to the marking oracle for the first part of
        GaussReduce algorithm. The marking oracle marks all vectors :math:`v`
        in qRAM such that :math:`\|v\| \leq \|p\|` and :math:`\|p-v\| < \|p\|`
        """
        marking_oracle: QuantumCircuit = self._first_marking_oracle()
        circuit: QuantumCircuit = QuantumCircuit(*marking_oracle.qregs)
        circuit.x(circuit.qubits[-1])
        circuit.h(circuit.qubits[-1])
        circuit.append(marking_oracle, circuit.qubits)
        circuit.h(circuit.qubits[-1])
        circuit.x(circuit.qubits[-1])

        return circuit
