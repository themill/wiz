# :coding: utf-8

import os
import platform
import datetime
import json
import time
import traceback

from packaging.requirements import Requirement

from wiz import __version__
import wiz.symbol

#: Indicate whether the history should be recorded.
_IS_HISTORY_RECORDED = False

#: Mapping containing the entire context resolution history report.
_HISTORY = {
    "version": __version__,
    "user": None,
    "hostname": None,
    "timestamp": None,
    "timezone": None,
    "command": None,
    "actions": []
}


def get(serialized=False):
    """Return mapping of recorded history.

    *serialized* indicate whether the returned history should be serialized as
    a :term:`JSON` string.

    """
    if serialized:
        return json.dumps(_HISTORY, default=_json_default)
    return _HISTORY


def start_recording(command=None):
    """Start recording the context resolution actions.

    *command* can indicate the command which is being run via the command line.

    """
    global _IS_HISTORY_RECORDED
    _IS_HISTORY_RECORDED = True

    global _HISTORY
    _HISTORY["user"] = os.environ.get("USER")
    _HISTORY["hostname"] = platform.node()
    _HISTORY["command"] = datetime.datetime.now().isoformat()
    _HISTORY["timezone"] = time.tzname[1]

    if command is not None:
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

    action = {"identifier": action_identifier}
    action.update(**kwargs)

    if action_identifier == wiz.symbol.EXCEPTION_RAISE_ACTION:
        action["traceback"] = traceback.format_exc().splitlines()

    global _HISTORY
    _HISTORY["actions"].append(
        json.dumps(action, default=_json_default)
    )


def _json_default(_object):
    """Override :func:`JSONEncoder.default` to serialize all objects."""
    import wiz.mapping
    import wiz.graph

    if isinstance(_object, wiz.graph.Graph):
        return _object.to_dict()

    elif isinstance(_object, wiz.mapping.Mapping):
        return _object.to_dict(serialize_content=True)

    elif isinstance(_object, Requirement):
        return str(_object)

    raise TypeError("{} is not JSON serializable.".format(_object))
