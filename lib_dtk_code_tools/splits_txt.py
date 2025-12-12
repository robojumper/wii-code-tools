from dataclasses import dataclass
import re
from typing import List

@dataclass
class SplitSection:
    name: str
    start: int
    end: int
    attrs: str


@dataclass
class SplitFile:
    path: str
    sections: List[SplitSection]


@dataclass
class ModuleSection:
    name: str
    section_type: str
    elf_index: int


@dataclass
class ModuleBlock:
    raw_block: str
    raw_block_no_comments: str
    module_id: int
    sections: List[ModuleSection]


@dataclass
class SplitsTxt:
    module_block: ModuleBlock
    files: List[SplitFile]


_ADDR_LINE_RE = re.compile(r"\t([\.a-z0-9]+)\s+start:0x([0-9A-F]+) end:0x([0-9A-F]+)( .*)?")
_MODULE_ID_RE = re.compile(r"# module_id: ([0-9]+)")
_MODULE_SECTION_RE = re.compile(r"\s*([\.a-z0-9]+)\s+type:([a-z]+)\s+align:([0-9]+)")
_COMMENT_RE = re.compile(r"^\s*#")

def _parse_split_file(file: str) -> SplitFile:
    file_line, *rest = file.split("\n")
    assert file_line.endswith(':')

    sections = []
    for line in rest:
        if line == "":
            continue
        match = _ADDR_LINE_RE.match(line)
        name_ = match.group(1)
        start_ = match.group(2)
        end_ = match.group(3)
        attrs_ = match.group(4)

        sections.append(SplitSection(
            name_,
            int(start_, 16),
            int(end_, 16),
            attrs_[1:] if attrs_ else ""
        ))

    return SplitFile(file_line[:-1], sections)

def _parse_module_block(file: str) -> ModuleBlock:
    lines = file.strip().split("\n")

    no_comment_text = "\n".join([line for line in lines if not _COMMENT_RE.match(line)])

    module_id_match = _MODULE_ID_RE.match(lines.pop(0))
    module_id = int(module_id_match.group(1))
    assert lines.pop(0) == "Sections:"

    sections: List[ModuleSection] = []

    while len(lines) > 0:
        attrs_line = lines.pop(0)
        sec_line = lines.pop(0)

        elf_index = None

        for pair in attrs_line.strip().split(' '):
            parts = pair.split(':')
            if parts[0] == "elf_index":
                elf_index = int(parts[1])

        module_sec_match = _MODULE_SECTION_RE.match(sec_line)
        name = module_sec_match.group(1)
        section_type = module_sec_match.group(2)

        sections.append(ModuleSection(name, section_type, elf_index))

    return ModuleBlock(file, no_comment_text, module_id, sections)


def parse_splits_file(file: str) -> SplitsTxt:
    sections_block, rest = file.split("\n\n", maxsplit=1)
    files = list(map(_parse_split_file, rest.split("\n\n")))

    module_block = _parse_module_block(sections_block)

    return SplitsTxt(module_block, files)


def serialize_splits_file(splits_file: SplitsTxt) -> str:
    result = splits_file.module_block.raw_block_no_comments
    result += "\n\n"

    for file in splits_file.files:
        result += file.path + ":\n"
        for section in file.sections:
            if not section.end:
                print(file)
            result += "\t" + section.name + " start:" + hex(section.start) + " end:" + hex(section.end)
            if section.attrs:
                result += " " + section.attrs

            result += "\n"

        result += "\n"

    return result
