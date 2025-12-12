import dataclasses
import re
from typing import Dict, List, TextIO


class SymbolsTweaker:
    """
    Represents one section of a symbols tweak file, corresponding to one version of the game.
    """
    additions: List['Addition']
    deletions: List['Deletion']

    @dataclasses.dataclass
    class Addition:
        module: int
        line: str

        def __str__(self):
            return f'{self.line}'

        def __repr__(self):
            return f'<add {self!s}>'

    @dataclasses.dataclass
    class Deletion:
        module: int
        line: str

        def __str__(self):
            return f'{self.line}'

        def __repr__(self):
            return f'<delete {self!s}>'

    def __init__(self):
        self.additions = []
        self.deletions = []


# Type alias
SymbolsTweakMap = Dict[str, SymbolsTweaker]


def read_symbols_tweak_file(f: TextIO) -> SymbolsTweakMap:
    """
    Read a symbols tweak.txt file
    """
    tweaks = {'default': SymbolsTweaker()}

    comment_regex = re.compile(r'^\s*#')
    empty_line_regex = re.compile(r'^\s*$')
    section_regex = re.compile(r'^\s*\[([a-zA-Z0-9_.]+)\]$')
    section_add_regex = re.compile(r'^\s*add:\s*$')
    section_delete_regex = re.compile(r'^\s*delete:\s*$')
    section_module_id_regex = re.compile(r'^\s*module:\s*([0-9]+)\s*$')

    current_version_name = None
    current_version = None
    current_mode = None
    current_module_id = None

    for line in f:
        line = line.rstrip('\n')

        if empty_line_regex.match(line):
            continue
        if comment_regex.match(line):
            continue

        match = section_regex.match(line)
        if match:
            # New version
            current_version_name = match.group(1)
            if current_version_name in tweaks:
                raise ValueError(f'tweaks file contains duplicate version name {current_version_name}')

            current_version = SymbolsTweaker()
            tweaks[current_version_name] = current_version
            current_mode = None
            continue

        if current_version is not None:
            # Try to associate something with the current version

            if section_add_regex.match(line):
                current_mode = 'add'
                continue
            if section_delete_regex.match(line):
                current_mode = 'delete'
                continue
            if m := section_module_id_regex.match(line):
                current_module_id = int(m.group(1))
                continue

            if current_mode == 'add':
                current_version.additions.append(SymbolsTweaker.Addition(current_module_id, line))
                continue
            elif current_mode == 'delete':
                current_version.deletions.append(SymbolsTweaker.Deletion(current_module_id, line))
                continue
            else:
                raise ValueError(f'line "{line}" in version {current_version_name} is not in any section (add/delete)')

        print(f'unrecognized line in tweaks file: {line}')

    return tweaks
