# Implements the oracles needed for the Gauss Reduce algorithm. The two required
# oracles are as follows:
#  1. Mark vectors v in L such that the norm of v is less than or equal to the
#     norm of p and the norm of p-v is strictly less than the norm of p
#  2. Mark vector v in L such that the norm of v is strictly greater than the
#     norm of p and the norm of p-v is less than or equal to the norm of p
#
# A reference classical implementation of GaussReduce can be found in the
# original paper by Daniele Micciancio and Panagiotis Voulgaris [1] where they
# introduce Gauss Siveve
# The oracle assumes that the list L is stored in a qRAM while the fixed vector
# p is stored in a separate register. It first copies the qRAM memory register
# to a separate register, negates it and adds p so it holds p-v. It then
# computes the norms of p, v and p-v and depending on whether the first or the
# seond oracle is computed performs the appropriate comparisons. Finally, it
# uncomputes everything
#
# [1] https://epubs.siam.org/doi/pdf/10.1137/1.9781611973075.119
r"""
Implements oracles for Grover's algorithm
"""
from qiskit import QuantumRegister, AncillaRegister, QuantumCircuit
from ..arithmetic.vectors import Norm2
from ..arithmetic.operations import Compare, SignedAdder


class ReductionOracle:
    r"""
    Class implementing quantum oracles for the GaussReduce algorithm. The 
    classical GaussReduce procedure can be decomposed in to a series of two 
    searching problems. The first search repeatedly searches for an element 
    :math:`v_i` in the list :math:`L` such that :math:`\|v_i\| \leq \|p\|` and 
    :math:`\|p-v_i\| < \|p\|` while the second one searches for elements 
    :math:`v_i` in :math:`L` such that :math:`\|v_i\| > \|p\|` and 
    :math:`\|p-v_i\| \leq \|p\|`. 
    
    This class implements both the oracles corresponding to the above search 
    problems. Pseudocode for a reference classical implementation of the 
    GaussReduce procedure as well as the whole Gauss Sieve algorithm can be 
    found in [1]

    :param num_address_qubits: number of address qubits in qRAM
    :param dimension: dimension of lattice
    :param bits: number of bits used to store each vector element in 
        sign-magnitude format
    
    References:
    ===========

    `[1]`_ Daniele Micciancio and Panagiotis Voulgaris. **Faster exponential 
    time algorithms for the shortest vector problem**. In Proceedings of the 
    twenty-first annual ACM-SIAM symposium on Discrete Algorithms, pages 
    1468–1480. SIAM, 2010

    .. _[1]: https://epubs.siam.org/doi/pdf/10.1137/1.9781611973075.119
    """

    def __init__(
        self, num_address_qubits: int, dimension: int, bits: int
    ) -> None:
        self.num_address_qubits = num_address_qubits
        self.dimension = dimension
        self.bits = bits

    def _marking_oracle(self, first: bool = True) -> QuantumCircuit:
        r"""
        Marking oracle for GaussReduce algorithm. If :code:`first` is set to
        :code:`True` it marks all vectors :math:`v` in qRAM such that
        :math:`\|v\| \leq \|p\|` and :math:`\|p-v\| < \|p\|`. Otherwise, it
        marks all vectors :math:`v` in qRAM such that :math:`\|v\| > \|p\|`
        and :math:`\|p-v\| \leq \|p\|`.
        """
        circuit: QuantumCircuit = QuantumCircuit(name="GaussReduce")
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

        mem_regs_copy: list[AncillaRegister] = [
            AncillaRegister(self.bits, name=f"v_{i}_copy")
            for i in range(self.dimension)
        ]
        circuit.add_register(*mem_regs_copy)

        for i in range(self.dimension):
            circuit.cx(mem_regs[i], mem_regs_copy[i])

        norm_circ: QuantumCircuit = Norm2(self.dimension, self.bits)

        v_norm_anc: AncillaRegister = AncillaRegister(
            norm_circ.num_ancillas, name="anc1"
        )
        v_norm: AncillaRegister = AncillaRegister(
            len(norm_circ.result_register) + 1, name=r"\|v\|"
        )
        circuit.add_register(v_norm_anc, v_norm)

        p_norm_anc: AncillaRegister = AncillaRegister(
            norm_circ.num_ancillas, name="anc2"
        )
        p_norm: AncillaRegister = AncillaRegister(
            len(norm_circ.result_register) + 1, name=r"\|p\|"
        )
        circuit.add_register(p_norm_anc, p_norm)

        diff_norm_anc: AncillaRegister = AncillaRegister(
            norm_circ.num_ancillas, name="anc3"
        )
        diff_norm: AncillaRegister = AncillaRegister(
            len(norm_circ.result_register) + 1, name=r"\|p-v\|"
        )
        circuit.add_register(diff_norm_anc, diff_norm)

        comp_p_v: QuantumCircuit = Compare(
            len(v_norm), cmp=">=" if first else "<"
        )
        comp_p_v_anc: AncillaRegister = AncillaRegister(
            comp_p_v.num_ancillas, name="cmp(p,v)_anc"
        )
        comp_p_v_res: AncillaRegister = AncillaRegister(
            1, name=r"cmp(\|v\|, \|p\|)"
        )
        circuit.add_register(comp_p_v_anc, comp_p_v_res)

        comp_diff_p: QuantumCircuit = Compare(
            len(diff_norm), cmp="<" if first else "<="
        )
        comp_diff_p_anc: AncillaRegister = AncillaRegister(
            comp_diff_p.num_ancillas, name="cmp(p-v, p)_anc"
        )
        comp_diff_p_res: AncillaRegister = AncillaRegister(
            1, name=r"cmp(\|p-v\|,\|p\|)"
        )
        circuit.add_register(comp_diff_p_anc, comp_diff_p_res)

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
            AncillaRegister(1, name=f"cout_{i}") for i in range(self.dimension)
        ]
        add_helper = AncillaRegister(1, name="add_helper")
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
            comp_p_v,
            [*p_norm, *v_norm, *comp_p_v_anc, *comp_p_v_res],
        )

        circuit.append(
            norm_circ, [*mem_copy_qubits, *diff_norm_anc, *diff_norm[:-1]]
        )
        circuit.append(
            comp_diff_p,
            [*diff_norm, *p_norm, *comp_diff_p_anc, *comp_diff_p_res],
        )

        final_res: AncillaRegister = AncillaRegister(1, name="final_result")
        circuit.add_register(final_res)

        circuit.mcx([comp_p_v_res, comp_diff_p_res], final_res)

        circuit.append(
            comp_diff_p.inverse(),
            [*diff_norm, *p_norm, *comp_diff_p_anc, *comp_diff_p_res],
        )
        circuit.append(
            norm_circ.inverse(),
            [*mem_copy_qubits, *diff_norm_anc, *diff_norm[:-1]],
        )

        circuit.append(
            comp_p_v.inverse(),
            [*p_norm, *v_norm, *comp_p_v_anc, *comp_p_v_res],
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

    def phase_oracle(self, first: bool = True) -> QuantumCircuit:
        r"""
        Phase oracle corresponding to the marking oracle for GaussReduce
        algorithm. If :code:`first` is set to :code:`True` the marking orcale
        marks all vectors :math:`v` in qRAM such that  :math:`\|v\| \leq \|p\|`
        and :math:`\|p-v\| < \|p\|`. Otherwise, it marks all vectors :math:`v`
        in qRAM such that :math:`\|v\| > \|p\|` and :math:`\|p-v\| \leq \|p\|`.
        """
        marking_oracle: QuantumCircuit = self._marking_oracle(first=first)
        circuit: QuantumCircuit = QuantumCircuit(*marking_oracle.qregs)
        circuit.x(circuit.qubits[-1])
        circuit.h(circuit.qubits[-1])
        circuit.append(marking_oracle, circuit.qubits)
        circuit.h(circuit.qubits[-1])
        circuit.x(circuit.qubits[-1])

        return circuit
