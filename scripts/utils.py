#!/usr/bin/env python3
import json
import os
import sys
import logging as log
import re

log.basicConfig(level=log.INFO, format="%(levelname)s: %(message)s")

USAGE=f"""
usage: {sys.argv[0]} <command>

commands:
    build   build boot file
    convert <time> 
            converts <time> to unix timestamp
"""

def build_boot_file():
    log.info("started build-boot-file process...")
    boot_addrs = []
    boot_dir   = os.getenv("SHARED_BOOT_DIR")
    boot_nodes = int(os.getenv("EXP_TOTAL_BOOT_NODES"))

    for filename in os.listdir(boot_dir):
        log.debug("reading file: %s", filename)
        with open(f"{boot_dir}/{filename}") as file :
            addrs = file.read().strip().split('\n')
            boot_addrs.append(addrs)
            log.info("Proccessing %d address from %s", len(addrs), filename)

    if boot_nodes != len(boot_addrs) :
        log.fatal("Too early, expected %d peer address but found %d", boot_nodes, len(boot_addrs))
        sys.exit(1)

    boot_file = os.getenv("BOOT_FILE")
    with open(boot_file, "w+") as file:
        file.write(json.dumps(boot_addrs, indent=4))

    log.info("Saved %d peers address in %s", len(boot_addrs), boot_file)

def time_string_to_seconds(time_string):
    total_seconds = 0

    # Extract numeric values and units using regular expressions
    matches = re.findall(r'(\d+)([smh]?)', time_string)

    for value, unit in matches:
        value = int(value)
        # Convert values to seconds based on units
        if unit == 's' or unit == '':
            total_seconds += value
        elif unit == 'm':
            total_seconds += value * 60
        elif unit == 'h':
            total_seconds += value * 3600

    return total_seconds

def main(args):

    if len(args) < 2:
        print(USAGE)
        sys.exit(1)

    cmd = args[1]
    if cmd == "build":
        build_boot_file()
    elif cmd == "convert":
        if len(args) < 3:
            print(f"ERROR: missing <time> string\n{USAGE}")
            sys.exit(1)
        time_stamp = args[2]
        print(time_string_to_seconds(time_stamp), end='')
    else:
        print(f"ERROR: unknown command '{cmd}'\n{USAGE}")
        sys.exit(1)


if __name__ == '__main__':
    main(sys.argv)