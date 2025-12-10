
from typing import List, Tuple


class RelAddrGlobalizationAlgorithm:
    """
    Most of the tooling works best when all addresses are in a flat address space.
    Base class for different algorithms that globalize REL addresses.
    """

    def globalize(self, module_id: int, section_index: int, offset: int) -> int:
        return NotImplementedError

    def deglobalize(self, flat_addr: int) -> Tuple[int, int, int]:
        return NotImplementedError


class RelAddrGlobalizationCmdLine(RelAddrGlobalizationAlgorithm):
    """
    Globalize addresses using externally given section offsets, e.g. when RELs are
    loaded at a fixed virtual memory address. Typically passed via command line.
    """
    def __init__(self, section_offsets: List[int]):
        self.section_offsets = section_offsets

    def globalize(self, module_id: int, section_index: int, offset: int) -> int:
        return self.section_offsets[section_index] + offset

    def deglobalize(self, flat_addr: int) -> Tuple[int, int, int]:
        found_idx = None
        for idx, offset in enumerate(self.section_offsets):
            if flat_addr <= offset:
                found_idx = idx
                break
        return 0, found_idx, flat_addr - self.section_offsets[found_idx]

class RelAddrGlobalizationPacked(RelAddrGlobalizationAlgorithm):
    """
    Globalize addresses by packing the relevant information into a 64-bit address.
    Since Module 0 is always the DOL, these REL addresses will always be larger
    than 32 bits and distinguishable from virtual memory addresses.
    """
    def __init__(self):
        pass

    def globalize(self, module_id: int, section_index: int, offset: int) -> int:
        assert 0 <= module_id <= 0xFFFF
        assert 0 <= section_index <= 0xFFFF
        assert 0 <= offset <= 0xFFFFFFFF
        return (module_id << 48) | (section_index << 32) | offset

    def deglobalize(self, flat_addr: int) -> Tuple[int, int, int]:
        return (flat_addr >> 48) & 0xFFFF, (flat_addr >> 32) & 0xFFFF, flat_addr & 0xFFFFFFFF
