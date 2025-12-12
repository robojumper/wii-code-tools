import argparse
from pathlib import Path
from typing import List, Optional

from lib_dtk_code_tools.splits_txt import parse_splits_file, serialize_splits_file
from lib_wii_code_tools import address_maps as lib_address_maps, common
from rel_globalization import RelAddrGlobalizationAlgorithm, RelAddrGlobalizationIdentity, RelAddrGlobalizationPacked

def main(args: Optional[List[str]] = None) -> None:
    """
    Main function
    """

    parser = argparse.ArgumentParser(
        description='Map an address from one version to another.')

    parser.add_argument('address_map', type=Path,
        help='address map file')
    parser.add_argument('version_1',
        help='the "from" version code')
    parser.add_argument('version_2',
        help='the "to" version code')
    parser.add_argument('splits_file_1', type=Path,
        help='the base splits file')
    parser.add_argument('splits_file_2', type=Path,
        help='the output splits file')

    parsed_args = parser.parse_args(args)

    with parsed_args.address_map.open('r', encoding='utf-8') as f:
        mappers = lib_address_maps.load_address_map(f)

    if parsed_args.version_1 not in mappers:
        raise ValueError(f'Error: unknown region "{parsed_args.version_1}" (available regions: {", ".join(mappers)})')
    if parsed_args.version_2 not in mappers:
        raise ValueError(f'Error: unknown region "{parsed_args.version_2}" (available regions: {", ".join(mappers)})')

    mapper_from = mappers[parsed_args.version_1]
    mapper_to = mappers[parsed_args.version_2]

    error_handling = lib_address_maps.UnmappedAddressHandling(
        common.ErrorVolume.SILENT,
        lib_address_maps.UnmappedAddressHandling.Behavior.DROP)

    with parsed_args.splits_file_1.open('r', encoding='utf-8') as f:
        splits_file = parse_splits_file(f.read())

        globalizer: RelAddrGlobalizationAlgorithm = None
        if splits_file.module_block.module_id == 0:
            globalizer = RelAddrGlobalizationIdentity()
        else:
            globalizer = RelAddrGlobalizationPacked()

        for file in splits_file.files:
            for section in file.sections:

                module_section = next(s for s in splits_file.module_block.sections if s.name == section.name)
                mapped_start = globalizer.globalize(splits_file.module_block.module_id, module_section.elf_index, section.start)
                mapped_end_minus_1 = globalizer.globalize(splits_file.module_block.module_id, module_section.elf_index, section.end - 1)

                new_start = lib_address_maps.map_addr_from_to(
                    mapper_from,
                    mapper_to,
                    mapped_start,
                    error_handling=error_handling)
                new_end = lib_address_maps.map_addr_from_to(
                    mapper_from,
                    mapper_to,
                    mapped_end_minus_1,
                    error_handling=error_handling)

                if not new_end:
                    print("failed to map", mapped_end_minus_1)

                _, _, section.start = globalizer.deglobalize(new_start)
                _, _, section.end = globalizer.deglobalize(new_end)
                section.end += 1

    with parsed_args.splits_file_2.open('w', encoding='utf-8') as f:
        file_str = serialize_splits_file(splits_file)
        f.write(file_str)

if __name__ == '__main__':
    main()
