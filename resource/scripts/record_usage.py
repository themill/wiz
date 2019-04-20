# :coding: utf-8

import sys
import time
import getpass
import socket


#: Fully qualified hostname of the graphite server.
CARBON_SERVER = "graphite.themill.com"

#: Port of the graphite server.
CARBON_PORT = 2003


def record_usage():
    """Record usage to the Graphite server via :mod:`socket` connection."""
    try:
        sock = socket.create_connection((CARBON_SERVER, CARBON_PORT))

        lines = [
            "wiz.command.{location}.{username}.{usage} 1 {timestamp:d}".format(
                location=guess_location(),
                username=getpass.getuser(),
                usage=guess_usage(),
                timestamp=int(time.time())
            )
        ]

        # all lines must end in a newline
        message = "\n".join(lines) + "\n"

        sock.sendall(message)

    except socket.error as exception:
        print(
            "Impossible to record Wiz command line usage {hostname}:{port} "
            "[{error}]".format(
                hostname=CARBON_SERVER,
                port=CARBON_PORT,
                error=exception
            )
        )


def guess_location():
    """Guess site location from fully qualified hostname."""
    hostname = socket.getfqdn()

    mapping = {
        "london": ["ldn", "co.uk"],
        "new_york": ["ny"],
        "chicago": ["chi"],
        "los_angeles": ["la"],
        "bangalore": ["blr"]
    }

    for identifier, patterns in mapping.items():
        if any(pattern in hostname for pattern in patterns):
            return identifier

    return "unknown"


def guess_usage():
    """Guess usage from Wiz arguments."""
    arguments = sys.argv[1:]

    if any("houdini" in argument for argument in arguments):
        return "houdini"

    if any("nuke" in argument for argument in arguments):
        return "nuke"

    if any("mari" in argument for argument in arguments):
        return "mari"

    if any("maya" in argument for argument in arguments):
        return "maya"

    if any("discreet" in argument for argument in arguments):
        return "discreet"

    if any("flame" in argument for argument in arguments):
        return "flame"

    if any("rv" in argument for argument in arguments):
        return "rv"

    return "unknown"


# Automatically record command line usage.
record_usage()
