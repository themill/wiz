# :coding: utf-8

import sys

import umwelt.command_line


def main():
    """Execute main command line interface passing command line arguments."""
    umwelt.command_line.main(sys.argv[1:])


if __name__ == "__main__":
    main()
