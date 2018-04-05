# :coding: utf-8

import os
import platform
import datetime
import json

import wiz.definition
import wiz.graph
import wiz.mapping


#: Indicate whether the history should be recorded.
_IS_HISTORY_RECORDED = False

#: Mapping containing the entire context resolution history report.
_HISTORY = {
    "user": os.environ.get("USER"),
    "hostname": platform.node(),
    "timestamp": datetime.datetime.now().isoformat(),
    "command": None,
    "actions": []
}


def get(serialized=False):
    """Return mapping of recorded history.

    *serialized* indicate whether the returned history should be serialized as
    a :term:`JSON` string.

    """
    if serialized:
        return json.dumps(_HISTORY)
    return _HISTORY


def start_recording(command=None):
    """Start recording the context resolution actions.

    *command* can indicate the command which is being run via the command line.

    """
    global _IS_HISTORY_RECORDED
    _IS_HISTORY_RECORDED = True

    if command is not None:
        global _HISTORY
        _HISTORY["command"] = command


def stop_recording():
    """Stop recording the context resolution actions."""
    global _IS_HISTORY_RECORDED
    _IS_HISTORY_RECORDED = False


def record_action(action_identifier, **kwargs):
    """Add an action to the global history mapping.

    *action_identifier* should be the identifier of an action.

    .. warning::

        This operation will be discarded if the history is not being
        :func:`recorded <start_recording>`.

    """
    if not _IS_HISTORY_RECORDED:
        return

    mapping = {}

    for key, value in kwargs.items():
        if isinstance(value, wiz.graph.Graph):
            mapping[key] = value.to_dict()
        else:
            mapping[key] = wiz.mapping.serialize(value)

    action = {"identifier": action_identifier}
    action.update(**mapping)

    global _HISTORY
    _HISTORY["actions"].append(action)
