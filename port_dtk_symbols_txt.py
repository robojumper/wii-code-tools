import argparse
from pathlib import Path
from typing import List, Optional

from lib_dtk_code_tools.splits_txt import parse_splits_file, serialize_splits_file
from lib_wii_code_tools import address_maps as lib_address_maps, common
from lib_wii_code_tools.symbol_map_formats import DtkSymbolsTxtMap

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
    parser.add_argument('symbols_file_1', type=Path,
        help='the base symbols file')
    parser.add_argument('symbols_file_2', type=Path,
        help='the output symbols file')

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

    with parsed_args.symbols_file_1.open('r', encoding='utf-8') as f:
        symbols_file = DtkSymbolsTxtMap.load(f)

        for symbol in symbols_file.symbols:
            start = symbol.addr
            if symbol.size:
                end = symbol.addr + symbol.size

            # TODO - globalized REL symbols

            new_start = lib_address_maps.map_addr_from_to(
                mapper_from,
                mapper_to,
                start,
                error_handling=error_handling)
            if symbol.size:
                new_end = lib_address_maps.map_addr_from_to(
                    mapper_from,
                    mapper_to,
                    end - 1,
                    error_handling=error_handling)

            symbol.addr = new_start
            if symbol.size:
                symbol.size = new_end + 1 - new_start

    with parsed_args.symbols_file_2.open('w', encoding='utf-8') as f:
        symbols_file.write(f)

if __name__ == '__main__':
    main()
