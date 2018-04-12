# :coding: utf-8

import os
import platform
import datetime
import json
import time

from packaging.requirements import Requirement

from wiz import __version__


#: Indicate whether the history should be recorded.
_IS_HISTORY_RECORDED = False

#: Mapping containing the entire context resolution history report.
_HISTORY = {
    "version": __version__,
    "user": os.environ.get("USER"),
    "hostname": platform.node(),
    "timestamp": datetime.datetime.now().isoformat(),
    "timezone": time.tzname[1],
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

    action = {"identifier": action_identifier}
    action.update(**kwargs)

    _action = json.dumps(action, default=_json_default)

    global _HISTORY
    _HISTORY["actions"].append(_action)


def _json_default(_object):
    """Override :func:`JSONEncoder.default` to serialize all objects."""
    import wiz.mapping
    import wiz.graph
    import wiz.exception

    if isinstance(_object, wiz.graph.Graph):
        return _object.to_dict()

    elif isinstance(_object, wiz.mapping.Mapping):
        return _object.to_dict(serialize_content=True)

    elif isinstance(_object, Requirement) or isinstance(_object, Exception):
        return str(_object)

    raise TypeError("{} is not JSON serializable.".format(obj))
