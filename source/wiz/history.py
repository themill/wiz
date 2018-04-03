# :coding: utf-8

import platform


#: Indicate whether the history should be recorded.
_IS_HISTORY_RECORDED = False

#: Mapping containing the entire context resolution history report.
HISTORY = {
    "hostname": platform.node(),
    "command": None,
    "actions": []
}


def start_recording(command=None):
    """Start recording the context resolution actions.

    *command* can indicate the command which is being run via the command line.

    """
    global _IS_HISTORY_RECORDED
    _IS_HISTORY_RECORDED = True

    if command is not None:
        global HISTORY
        HISTORY["command"] = command


def stop_recording():
    """Stop recording the context resolution actions."""
    global _IS_HISTORY_RECORDED
    _IS_HISTORY_RECORDED = False
