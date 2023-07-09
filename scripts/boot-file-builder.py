#!/usr/bin/env python3
import json
import os
import sys
import logging as log

log.basicConfig(level=log.INFO, format="%(levelname)s: %(message)s")

def main():
    log.info("started bfile-builder.py")
    boot_addrs = []
    boot_dir   = os.getenv("EXP_BOOT_DIR")
    boot_nodes = int(os.getenv("EXP_BOOT_NODES"))

    for filename in os.listdir(boot_dir):
        log.debug("reading file: %s", filename)
        with open(f"{boot_dir}/{filename}") as file :
            addrs = file.read().strip().split('\n')
            boot_addrs.append(addrs)
            log.info("Proccessing %d address from %s", len(addrs), filename)

    if boot_nodes != len(boot_addrs) :
        log.fatal("Too early, expected %d peer address but found %d", boot_nodes, len(boot_addrs))
        sys.exit(1)

    boot_file = os.getenv("EXP_BOOT_FILE")
    with open(boot_file, "w+") as file:
        file.write(json.dumps(boot_addrs, indent=4))

    log.info("Saved %d peers address in %s", len(boot_addrs), boot_file)

if __name__ == '__main__':
    main()