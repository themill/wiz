# :coding: utf-8

from __future__ import print_function
import os
import json
import itertools
import collections
import datetime

import mlog
import click

import wiz.registry
import wiz.symbol
import wiz.definition
import wiz.package
import wiz.spawn
import wiz.exception
import wiz.filesystem
import wiz.history
import wiz.utility
from wiz import __version__


#: Click default context for all commands.
CONTEXT_SETTINGS = dict(
    max_content_width=90,
    help_option_names=["-h", "--help"],
)


class _MainGroup(click.Group):
    """Extended click Group for Wiz command line main entry point."""

    def parse_args(self, context, arguments):
        """Update *context* from passed *arguments*.

        Record initial command from *info_name* and *args* and identify
        extra arguments after the "--" symbol.

        We cannot only rely on the 'allow_extra_args' option of the click
        Context as it fails to recognize extra arguments when placed after
        an argument with "nargs=-1".

        """
        extra_args = []

        if wiz.symbol.COMMAND_SEPARATOR in arguments:
            index = arguments.index(wiz.symbol.COMMAND_SEPARATOR)
            extra_args = arguments[index + 1:]
            arguments = arguments[:index]

        context.obj = {
            "initial_input": wiz.utility.combine_command(["wiz"] + arguments),
            "extra_arguments": extra_args
        }

        return super(_MainGroup, self).parse_args(context, arguments)


@click.group(
    context_settings=CONTEXT_SETTINGS,
    cls=_MainGroup,
    help=(
        """
        Wiz is a package manager which can resolve a context or execute a 
        command from one or several package requests. The resolved context
        contains the environment mapping and a list of accessible command 
        aliases.
        
        Example::

            \b
            wiz use python
            wiz use nuke ldpk-nuke
            wiz use nuke -- /path/to/script.nk

        A command can also be executed from a resolved context via a command
        alias which is extracted from its corresponding package.
                
        Example::

            \b
            wiz run nuke
            wiz run nuke -- /path/to/script.nk
            wiz run python 


        All available packages and command can be listed as follow::

            \b
            wiz list package
            wiz list command

        It is also possible to search a specific package or command as follow::
        
            \b
            wiz search python

        """
    ),
)
@click.version_option(version=__version__)
@click.option(
    "-v", "--verbosity",
    help="Set the logging output verbosity.",
    type=click.Choice(mlog.levels),
    default="info",
    show_default=True
)
@click.option(
    "--no-local",
    help="Skip local registry.",
    is_flag=True,
    default=False
)
@click.option(
    "--no-cwd",
    help=(
        "Do not attempt to discover definitions from current "
        "working directory within project."
    ),
    is_flag=True,
    default=False
)
@click.option(
    "-dsd", "--definition-search-depth",
    help="Maximum depth to recursively search for definitions.",
    type=int,
    metavar="DEPTH_NUMBER",
)
@click.option(
    "-dsp", "--definition-search-paths",
    help="Search paths for package definitions.",
    default=wiz.registry.get_defaults(),
    multiple=True,
    metavar="PATHS",
    type=click.Path(),
    show_default=True
)
@click.option(
    "--ignore-implicit",
    help=(
        "Do not include implicit packages (with 'auto-use' set to true) "
        "in resolved context."
    ),
    is_flag=True,
    default=False
)
@click.option(
    "--platform",
    metavar="PLATFORM",
    help="Override detected platform."
)
@click.option(
    "--architecture",
    metavar="ARCHITECTURE",
    help="Override detected architecture."
)
@click.option(
    "--os-name",
    metavar="NAME",
    help="Override detected operating system name."
)
@click.option(
    "--os-version",
    metavar="VERSION",
    help="Override detected operating system version."
)
@click.option(
    "--record",
    help="Record resolution context process for debugging.",
    type=click.Path()
)
@click.pass_context
def main(click_context, **kwargs):
    """Main entry point for the command line interface."""
    mlog.configure()
    logger = mlog.Logger(__name__ + ".main")

    if kwargs["record"] is not None:
        wiz.history.start_recording(
            command=click_context.obj["initial_input"]
        )

    # Set verbosity level.
    mlog.root.handlers["stderr"].filterer.filterers[0].min = kwargs["verbosity"]

    # Identify system mapping.
    system_mapping = wiz.system.query(
        platform=kwargs["platform"],
        architecture=kwargs["architecture"],
        os_name=kwargs["os_name"],
        os_version=kwargs["os_version"],
    )
    logger.debug("System: {}".format(system_mapping))

    # Fetch all registries.
    registries = wiz.registry.fetch(
        kwargs["definition_search_paths"],
        include_local=not kwargs["no_local"],
        include_working_directory=not kwargs["no_cwd"]
    )
    logger.debug("Registries: " + ", ".join(registries))

    # Update user data within click context.
    click_context.obj.update({
        "system_mapping": system_mapping,
        "registry_paths": registries,
        "registry_search_depth": kwargs["definition_search_depth"],
        "ignore_implicit_packages": kwargs["ignore_implicit"],
        "recording_path": kwargs["record"]
    })


@main.group(
    name="list",
    help=(
        """
        Display all available commands or package definitions.
        
        Example::
        
            \b
            wiz list command
            wiz list package
            wiz list command --all
            wiz list package --all
        
        """
    ),
    short_help="List commands or package definitions.",
    context_settings=CONTEXT_SETTINGS
)
@click.pass_context
def wiz_list_group(click_context):
    """Group command which list available commands or package definitions."""
    # Ensure that context fail if extra arguments were passed.
    _fail_on_extra_arguments(click_context)

    click_context.obj["definition_mapping"] = (
        _fetch_definition_mapping_from_context(click_context)
    )


@wiz_list_group.command(
    name="package",
    help=(
        """
        Display all available package definitions.

        Example::

            \b
            wiz list package
            wiz list package --all

        """
    ),
    short_help="Display available packages.",
    context_settings=CONTEXT_SETTINGS
)
@click.option(
    "-a", "--all",
    help="Display all package versions, not just the latest one.",
    is_flag=True,
    default=False
)
@click.pass_context
def wiz_list_package(click_context, **kwargs):
    """Command to list available package definitions."""
    registry_paths = click_context.obj["registry_paths"]
    definition_mapping = click_context.obj["definition_mapping"]

    # Display available registries.
    display_registries(registry_paths)

    # Display available definitions.
    display_definition_mapping(
        definition_mapping[wiz.symbol.PACKAGE_REQUEST_TYPE],
        registry_paths,
        all_versions=kwargs["all"],
    )

    _export_history_if_requested(click_context)


@wiz_list_group.command(
    name="command",
    help=(
        """
        Display all available commands.

        Example::

            \b
            wiz list command
            wiz list command --all

        """
    ),
    short_help="Display available commands.",
    context_settings=CONTEXT_SETTINGS
)
@click.option(
    "-a", "--all",
    help="Display all command versions, not just the latest one.",
    is_flag=True,
    default=False
)
@click.pass_context
def wiz_list_command(click_context, **kwargs):
    """Command to list available commands."""
    registry_paths = click_context.obj["registry_paths"]
    definition_mapping = click_context.obj["definition_mapping"]

    # Display available registries.
    display_registries(registry_paths)

    # Retrieve commands from definition mapping.
    command_mapping = {
        command: definition_mapping[wiz.symbol.PACKAGE_REQUEST_TYPE][_id]
        for (command, _id)
        in definition_mapping[wiz.symbol.COMMAND_REQUEST_TYPE].items()
    }

    # Display available commands.
    display_definition_mapping(
        command_mapping, registry_paths,
        all_versions=kwargs["all"],
        command=True
    )

    _export_history_if_requested(click_context)


@main.command(
    name="search",
    help=(
        """
        Search and display definitions from request(s).

        Example::

            \b
            wiz search foo
            wiz search foo --all
            wiz search foo>=2
            wiz search foo bar

        """
    ),
    short_help="Search package definitions.",
    context_settings=CONTEXT_SETTINGS
)
@click.option(
    "-a", "--all",
    help="Display all package versions, not just the latest one.",
    is_flag=True,
    default=False
)
@click.option(
    "-t", "--type",
    help="Set the request type.",
    type=click.Choice([
        "all",
        wiz.symbol.PACKAGE_REQUEST_TYPE,
        wiz.symbol.COMMAND_REQUEST_TYPE
    ]),
    default="all",
    show_default=True
)
@click.argument(
    "requests",
    nargs=-1,
    required=True
)
@click.pass_context
def wiz_search(click_context, **kwargs):
    """Search and display definitions from request(s)."""
    logger = mlog.Logger(__name__ + ".wiz_search")

    # Ensure that context fail if extra arguments were passed.
    _fail_on_extra_arguments(click_context)

    registry_paths = click_context.obj["registry_paths"]
    definition_mapping = _fetch_definition_mapping_from_context(
        click_context, requests=list(kwargs["requests"])
    )

    display_registries(registry_paths)
    results_found = False

    if (
        kwargs["type"] in ["command", "all"] and
        len(definition_mapping[wiz.symbol.COMMAND_REQUEST_TYPE]) > 0
    ):
        results_found = True
        command_mapping = {
            command: definition_mapping[wiz.symbol.PACKAGE_REQUEST_TYPE][_id]
            for (command, _id)
            in definition_mapping[wiz.symbol.COMMAND_REQUEST_TYPE].items()
        }

        display_definition_mapping(
            command_mapping,
            registry_paths,
            all_versions=kwargs["all"],
            command=True
        )

    if (
        kwargs["type"] in ["package", "all"] and
        len(definition_mapping[wiz.symbol.PACKAGE_REQUEST_TYPE]) > 0
    ):
        results_found = True

        display_definition_mapping(
            definition_mapping[wiz.symbol.PACKAGE_REQUEST_TYPE],
            registry_paths,
            all_versions=kwargs["all"],
        )

    if not results_found:
        logger.warning("No results found.\n")

    _export_history_if_requested(click_context)


@main.command(
    name="view",
    help=(
        """
        Display content of a package definition from definition identifier or
        command.
        
        Example::

            \b
            wiz view foo
            wiz view foo --json

        """
    ),
    short_help="View content of a package definition.",
    context_settings=CONTEXT_SETTINGS
)
@click.option(
    "--json",
    help="Display definition in JSON.",
    is_flag=True,
    default=False
)
@click.argument(
    "request",
    nargs=1,
    required=True
)
@click.pass_context
def wiz_view(click_context, **kwargs):
    """Display definition from identifier or command."""
    logger = mlog.Logger(__name__ + ".wiz_view")

    # Ensure that context fail if extra arguments were passed.
    _fail_on_extra_arguments(click_context)

    definition_mapping = _fetch_definition_mapping_from_context(click_context)

    results_found = False

    # Display the corresponding definition if the request is a command.
    try:
        request = wiz.fetch_package_request_from_command(
            kwargs["request"], definition_mapping
        )
        definition = wiz.fetch_definition(request, definition_mapping)

    except wiz.exception.RequestNotFound as exception:
        logger.debug(
            "Impossible to query definition from command request: "
            "{}\n".format(exception)
        )

    else:
        logger.info(
            "Command found in definition: {}".format(
                wiz.package.generate_identifier(definition)
            )
        )
        results_found = True

    # Display the full definition if the request is a package.
    try:
        definition = wiz.fetch_definition(kwargs["request"], definition_mapping)

    except wiz.exception.RequestNotFound as exception:
        logger.debug(
            "Impossible to query definition from package request: "
            "{}\n".format(exception)
        )

    else:
        logger.info(
            "View definition: {}".format(
                wiz.package.generate_identifier(definition)
            )
        )

        if kwargs["json"]:
            click.echo(definition.encode())
        else:
            display_definition(definition)

        results_found = True

    # Otherwise, display a warning...
    if not results_found:
        logger.warning("No definition found.\n")

    _export_history_if_requested(click_context)


@main.command(
    name="use",
    help=(
        """
        Spawn shell with resolved context from requested packages, or run
        a command within the resolved context.
        
        Example::

            \b
            wiz use package1>=1 package2==2.3.0 package3
            wiz use package1>=1 package2==2.3.0 package3 -- app --option value
            wiz use --view command

        """
    ),
    short_help="Use resolved context from package definition.",
    context_settings=dict(
        allow_extra_args=True,
        **CONTEXT_SETTINGS
    )
)
@click.option(
    "--view",
    help="Only view the resolved context without loading it.",
    is_flag=True,
    default=False
)
@click.argument(
    "requests",
    nargs=-1,
    required=True
)
@click.pass_context
def wiz_use(click_context, **kwargs):
    """Resolve and use context from command."""
    logger = mlog.Logger(__name__ + ".wiz_use")

    definition_mapping = _fetch_definition_mapping_from_context(click_context)
    ignore_implicit = click_context.obj["ignore_implicit_packages"]

    # Fetch extra arguments from context.
    extra_arguments = _fetch_extra_arguments(click_context)

    try:
        wiz_context = wiz.resolve_context(
            list(kwargs["requests"]), definition_mapping,
            ignore_implicit=ignore_implicit
        )

        # Only view the resolved context without spawning a shell nor
        # running any commands.
        if kwargs["view"]:
            display_registries(wiz_context["registries"])
            display_packages(wiz_context["packages"], wiz_context["registries"])
            display_command_mapping(wiz_context.get("command", {}))
            display_environ_mapping(wiz_context.get("environ", {}))

        # If no commands are indicated, spawn a shell.
        elif len(extra_arguments) == 0:
            wiz.spawn.shell(wiz_context["environ"])

        # Otherwise, resolve the command and run it within the resolved context.
        else:
            command_elements = wiz.resolve_command(
                extra_arguments, wiz_context.get("command", {})
            )
            wiz.spawn.execute(command_elements, wiz_context["environ"])

    except wiz.exception.WizError as error:
        logger.error(str(error), traceback=True)

        wiz.history.record_action(
            wiz.symbol.EXCEPTION_RAISE_ACTION, error=error
        )

    except KeyboardInterrupt:
        logger.warning("Aborted.")

    _export_history_if_requested(click_context)


@main.command(
    "run",
    help=(
        """
        Run command from resolved context.

        Example::

            \b
            wiz run command
            wiz run command -- --option value /path/to/output
        
        """
    ),
    short_help="Run command from package definition.",
    context_settings=dict(
        allow_extra_args=True,
        ignore_unknown_options=True,
        **CONTEXT_SETTINGS
    )
)
@click.option(
    "--view",
    help="Only view the resolved context without loading it.",
    is_flag=True,
    default=False
)
@click.argument(
    "request",
    nargs=1,
    required=True
)
@click.pass_context
def wiz_run(click_context, **kwargs):
    """Run application from resolved context."""
    logger = mlog.Logger(__name__ + ".wiz_run")

    definition_mapping = _fetch_definition_mapping_from_context(click_context)
    ignore_implicit = click_context.obj["ignore_implicit_packages"]

    # Fetch extra arguments from context.
    extra_arguments = _fetch_extra_arguments(click_context)

    try:

        requirement = wiz.utility.get_requirement(kwargs["request"])
        request = wiz.fetch_package_request_from_command(
            kwargs["request"], definition_mapping
        )

        wiz_context = wiz.resolve_context(
            [request], definition_mapping,
            ignore_implicit=ignore_implicit
        )

        # Only view the resolved context without spawning a shell nor
        # running any commands.
        if kwargs["view"]:
            display_registries(wiz_context["registries"])
            display_packages(wiz_context["packages"], wiz_context["registries"])
            display_command_mapping(wiz_context.get("command", {}))
            display_environ_mapping(wiz_context.get("environ", {}))

        else:
            command_elements = wiz.resolve_command(
                [requirement.name] + extra_arguments,
                wiz_context.get("command", {})
            )
            wiz.spawn.execute(command_elements, wiz_context["environ"])

    except wiz.exception.WizError as error:
        logger.error(str(error), traceback=True)

        wiz.history.record_action(
            wiz.symbol.EXCEPTION_RAISE_ACTION, error=error
        )

    except KeyboardInterrupt:
        logger.warning("Aborted.")

    _export_history_if_requested(click_context)


@main.command(
    "freeze",
    help=(
        """
        Export resolved context into a package definition or a script.
        
        Example::

            \b
            wiz freeze foo>=1 bar==2.3.0 baz -o /tmp
            wiz freeze --format bash foo>=1 bar==2.3.0 baz -o /tmp
            wiz freeze --format tcsh foo>=1 bar==2.3.0 baz -o /tmp
        """
    ),
    short_help="Export resolved context.",
    context_settings=CONTEXT_SETTINGS
)
@click.option(
    "-o", "--output",
    help="Indicate the output directory.",
    type=click.Path(),
    required=True
)
@click.option(
    "-f", "--format",
    help="Indicate the output format.",
    type=click.Choice(["wiz", "tcsh", "bash"]),
    default="wiz",
    show_default=True
)
@click.argument(
    "requests",
    nargs=-1,
    required=True
)
@click.pass_context
def wiz_freeze(click_context, **kwargs):
    """Freeze resolved context into a package definition or a script."""
    logger = mlog.Logger(__name__ + ".wiz_freeze")

    # Ensure that context fail if extra arguments were passed.
    _fail_on_extra_arguments(click_context)

    definition_mapping = _fetch_definition_mapping_from_context(click_context)
    ignore_implicit = click_context.obj["ignore_implicit_packages"]

    try:
        _context = wiz.resolve_context(
            list(kwargs["requests"]), definition_mapping,
            ignore_implicit=ignore_implicit
        )
        identifier = _query_identifier()

        if kwargs["format"] == "wiz":
            description = _query_description()
            version = _query_version()

            definition_data = {
                "identifier": identifier,
                "description": description,
                "version": str(version)
            }

            command_mapping = _context.get("command")
            if command_mapping is not None:
                definition_data["command"] = command_mapping

            environ_mapping = _context.get("environ")
            if environ_mapping is not None:
                definition_data["environ"] = environ_mapping

            wiz.export_definition(kwargs["output"], definition_data)

        elif kwargs["format"] == "bash":
            command = _query_command(_context.get("command", {}).values())
            wiz.export_script(
                kwargs["output"], "bash",
                identifier,
                environ=_context.get("environ", {}),
                command=command,
                packages=_context.get("packages")
            )

        elif kwargs["format"] == "tcsh":
            command = _query_command(_context.get("command", {}).values())
            wiz.export_script(
                kwargs["output"], "tcsh",
                identifier,
                environ=_context.get("environ", {}),
                command=command,
                packages=_context.get("packages")
            )

    except wiz.exception.WizError as error:
        logger.error(str(error), traceback=True)

        wiz.history.record_action(
            wiz.symbol.EXCEPTION_RAISE_ACTION, error=error
        )

    except KeyboardInterrupt:
        logger.warning("Aborted.")

    _export_history_if_requested(click_context)


@main.command(
    "install",
    help=(
        """
        Install a package definition to a registry. A registry can be a
        local path to the file system or a VCS registry.
        
        Example::

            \b
            wiz install foo.json bar.json --registry-id primary-registry
            wiz install /path/to/foo.json --registry-path /path/to/registry
            wiz install /all/definitions/* --registry-path /path/to/registry

        """
    ),
    short_help="Install a package definition to a registry.",
    context_settings=CONTEXT_SETTINGS
)
@click.option(
    "-p", "--registry-path",
    help="Registry path to install the package to.",
    type=click.Path(),
)
@click.option(
    "-r", "--registry-id",
    help="VCS registry identifier to install the package to.",
    metavar="ID",
)
@click.option(
    "--install-location",
    help=(
        "Update definition(s) with new 'install-location' value during "
        "installation."
    ),
    metavar="VALUE",
)
@click.option(
    "--overwrite",
    help="Always overwrite existing definitions.",
    is_flag=True,
    default=False
)
@click.argument(
    "definitions",
    nargs=-1,
    required=True
)
@click.pass_context
def wiz_install(click_context, **kwargs):
    """Install a definition to a registry."""
    logger = mlog.Logger(__name__ + ".wiz_install")

    # Ensure that context fail if extra arguments were passed.
    _fail_on_extra_arguments(click_context)

    overwrite = kwargs["overwrite"]

    while True:
        try:
            if kwargs["registry_path"] is not None:
                wiz.install_definitions_to_path(
                    kwargs["definitions"], kwargs["registry_path"],
                    install_location=kwargs["install_location"],
                    overwrite=overwrite
                )
            elif kwargs["registry_id"] is not None:
                wiz.install_definitions_to_vcs(
                    kwargs["definitions"], kwargs["registry_id"],
                    install_location=kwargs["install_location"],
                    overwrite=overwrite
                )
            break

        except wiz.exception.DefinitionsExist as error:
            if not click.confirm(
                "{message}\n{definitions}\nOverwrite?".format(
                    message=str(error),
                    definitions="\n".join([
                        "- {}".format(definition)
                        for definition in error.definitions
                    ])
                )
            ):
                break

            overwrite = True

        except wiz.exception.InstallNoChanges:
            logger.warning("No changes detected in release.")
            break

        except Exception as error:
            logger.error(error, traceback=True)

            wiz.history.record_action(
                wiz.symbol.EXCEPTION_RAISE_ACTION, error=error
            )
            break

    _export_history_if_requested(click_context)


@main.command(
    "edit",
    help=(
        """
        Edit one or several definition(s) with default editor or with operation
        option(s).

        If an output is specified, the original definition(s) will not be
        mutated. Otherwise, the original definition file(s) will be updated with
        edited data.

        The edited definition(s) will be validated before export.

        Example::

            \b
            wiz edit foo.json
            wiz edit foo.json --output /tmp/target
            wiz edit foo.json --set install-location --value /path/data
            wiz edit foo.json --update environ --value '{"KEY": "VALUE"}'
            wiz edit * --extend requirements --value "bar > 0.1.0"

        """
    ),
    short_help="Edit one or several definition(s).",
    context_settings=CONTEXT_SETTINGS
)
@click.option(
    "--set",
    help="Set a new value to a keyword.",
    nargs=2,
    type=click.Tuple([str, lambda x: _casted_argument(x)]),
    metavar="<KEYWORD VALUE>",
    default=(None, None),
)
@click.option(
    "--update",
    help="Update mapping keyword with mapping value.",
    nargs=2,
    type=click.Tuple([str, lambda x: _casted_argument(x)]),
    metavar="<KEYWORD VALUE>",
    default=(None, None),
)
@click.option(
    "--extend",
    help="Extend list keyword with list value.",
    nargs=2,
    type=click.Tuple([str, lambda x: _casted_argument(x)]),
    metavar="<KEYWORD VALUE>",
    default=(None, None),
)
@click.option(
    "--insert",
    help="Insert value to keyword with.",
    nargs=3,
    type=click.Tuple([str, str, int]),
    metavar="<KEYWORD VALUE INDEX>",
    default=(None, None, None),
)
@click.option(
    "--remove",
    help="Remove keyword.",
    nargs=1,
    type=lambda x: x if isinstance(x, tuple) else (str(x),),
    metavar="<KEYWORD>",
    default=(None,),
)
@click.option(
    "--remove-key",
    help="Remove value from mapping keyword.",
    nargs=2,
    type=click.Tuple([str, str]),
    metavar="<KEYWORD NAME>",
    default=(None, None),
)
@click.option(
    "--remove-index",
    help="Remove index from list keyword.",
    nargs=2,
    type=click.Tuple([str, int]),
    metavar="<KEYWORD INDEX>",
    default=(None, None),
)
@click.option(
    "--overwrite",
    help="Always overwrite existing definitions.",
    is_flag=True,
    default=False
)
@click.option(
    "-o", "--output",
    help=(
        "Indicate an output directory for updated definition(s). "
        "By default, original definition will be modified."
    ),
    type=click.Path(),
)
@click.argument(
    "definitions",
    nargs=-1,
    required=True
)
@click.pass_context
def wiz_edit(click_context, **kwargs):
    """Edit one or several definition(s)."""
    logger = mlog.Logger(__name__ + ".wiz_edit")

    # Ensure that context fail if extra arguments were passed.
    _fail_on_extra_arguments(click_context)

    # Fetch operations from arguments
    all_operations = [
        "set", "update", "extend", "insert", "remove", "remove_key",
        "remove_index"
    ]

    operations = [_id for _id in all_operations if kwargs[_id][0] is not None]

    try:
        # Fetch definitions from arguments.
        definitions = [
            wiz.load_definition(path) for path in kwargs["definitions"]
        ]

        for definition in definitions:
            label = wiz.utility.compute_label(definition)
            logger.info("Edit {}.".format(label))

            if len(operations) == 0:
                data = click.edit(definition.encode(), extension=".json")
                if data is None:
                    logger.warning("Skip edition for {}.".format(label))
                    continue

                definition = wiz.definition.Definition(**json.loads(data))

            else:
                for name in operations:
                    args = kwargs[name]
                    definition = getattr(definition, name)(*args)

            path = definition["definition-location"]

            if kwargs["output"] is not None:
                name = os.path.basename(definition["definition-location"])
                path = os.path.join(kwargs["output"], name)

            overwrite = kwargs["overwrite"]

            while True:
                try:
                    # Sanitized definition before exporting it.
                    definition = definition.sanitized()

                    wiz.filesystem.export(
                        path, definition.encode(), overwrite=overwrite
                    )
                    logger.info("Saved {} in {}.".format(label, path))
                    break

                except wiz.exception.FileExists:
                    if not click.confirm("Overwrite {}?".format(label)):
                        logger.warning("Skip edition for {}.".format(label))
                        break

                    overwrite = True

    except Exception as error:
        logger.error(str(error), traceback=True)

        wiz.history.record_action(
            wiz.symbol.EXCEPTION_RAISE_ACTION, error=error
        )

    _export_history_if_requested(click_context)


def _casted_argument(argument):
    """Return *argument* casted into a proper type from JSON decoder."""
    # Ensure that boolean value are in JSON format.
    argument = argument.replace("True", "true").replace("False", "false")

    try:
        return json.loads(argument)
    except ValueError:
        return argument


def _fail_on_extra_arguments(click_context):
    """Raise an error if extra arguments are found in command."""
    arguments = _fetch_extra_arguments(click_context)
    if len(arguments):
        click_context.fail(
            "Got unexpected extra argument(s) ({})".format(" ".join(arguments))
        )


def _fetch_extra_arguments(click_context):
    """Return extra arguments from context.

    If extra arguments have not been recorded after the "--" symbol, we check
    if leftover arguments remain in context.

    """
    return click_context.obj["extra_arguments"] or click_context.args


def _fetch_definition_mapping_from_context(click_context, requests=None):
    """Return definition mapping from elements stored in *click_context*."""
    return wiz.fetch_definition_mapping(
        click_context.obj["registry_paths"],
        requests=requests,
        system_mapping=click_context.obj["system_mapping"],
        max_depth=click_context.obj["registry_search_depth"]
    )


def _export_history_if_requested(click_context):
    """Return definition mapping from elements stored in *click_context*."""
    logger = mlog.Logger(__name__ + "._export_history_if_requested")

    if click_context.obj["recording_path"] is None:
        return

    history = wiz.history.get(serialized=True)
    path = os.path.join(
        os.path.abspath(click_context.obj["recording_path"]),
        "wiz-{}.dump".format(datetime.datetime.now().isoformat())
    )
    wiz.filesystem.export(path, history, compressed=True)
    logger.info("History recorded and exported in '{}'".format(path))


def display_registries(paths):
    """Display all registries from *paths* with an identifier.

    Example::

        >>> display_registries(paths)

        [0] /path/to/registry-1
        [1] /path/to/registry-2

    """
    title = "Registries"
    columns = [
        {"size": len(title), "rows": [], "title": title}
    ]

    for index, path in enumerate(paths):
        item = "[{}] {}".format(index, path)
        columns[0]["rows"].append(item)
        columns[0]["size"] = max(len(item), columns[0]["size"])

    if len(paths) == 0:
        item = "No registries to display."
        columns[0]["rows"].append(item)

    _display_table(columns)


def display_definition(definition):
    """Display *definition* instance.

    *definition* should be a :class:`wiz.definition.Definition` instance.

    """
    def _display(item, level=0):
        """Display *mapping*"""
        indent = " "*level

        if isinstance(item, collections.OrderedDict) or isinstance(item, dict):
            for key, value in item.items():
                if isinstance(value, basestring) or isinstance(value, int):
                    click.echo("{}{}: {}".format(indent, key, value))
                else:
                    click.echo("{}{}:".format(indent, key))
                    _display(value, level=level + 4)

        elif isinstance(item, list) or isinstance(item, tuple):
            for _item in item:
                if isinstance(_item, collections.OrderedDict):
                    click.echo("{}identifier: {}".format(
                        indent, _item.pop("identifier")
                    ))
                    _display(_item, level=level + 4)
                else:
                    _display(_item, level=level)

        else:
            click.echo("{}{}".format(indent, item))

    _display(definition.to_ordered_dict(serialize_content=True))


def display_definition_mapping(
    mapping, registries, all_versions=False, command=False
):
    """Display definition contained in *mapping*.

    *mapping* is a mapping regrouping all available definition versions
    associated with their unique identifier.

    *registries* should be a list of available registry paths.

    *all_versions* indicate whether all versions from the definition must be
    returned. If not, only the latest version of each definition identifier is
    displayed.

    *command* indicate whether the mapping identifiers represent commands.

    """
    identifiers = []
    definitions = []

    for identifier in sorted(mapping.keys()):
        versions = sorted(
            map(lambda d: d.version, mapping[identifier].values()),
            reverse=True
        )

        for index in range(len(versions)):
            if index > 0 and not all_versions:
                break

            identifiers.append(identifier)
            definitions.append(mapping[identifier][str(versions[index])])

    header = "Command" if command else "Package"
    titles = [header, "Version", "Registry", "Description"]
    columns = [
        {"size": len(title), "rows": [], "title": title} for title in titles
    ]

    def _format_unit(_identifier, _definition, _variant=None):
        """Format row unit."""
        if _variant is not None:
            _identifier += " [{}]".format(_variant)

        columns[0]["rows"].append(_identifier)
        columns[0]["size"] = max(len(_identifier), columns[0]["size"])

        _version = str(_definition.version)
        columns[1]["rows"].append(_version)
        columns[1]["size"] = max(len(_version), columns[1]["size"])

        registry_index = str(registries.index(_definition.get("registry")))
        columns[2]["rows"].append(registry_index)
        columns[2]["size"] = max(len(registry_index), columns[2]["size"])

        _description = _definition.description
        columns[3]["rows"].append(_description)
        columns[3]["size"] = max(len(_description), columns[3]["size"])

    for identifier, definition in itertools.izip_longest(
        identifiers, definitions
    ):
        if len(definition.variants) > 0:
            for variant in definition.variants:
                _variant = variant.identifier
                _format_unit(identifier, definition, _variant)

        else:
            _format_unit(identifier, definition)

    if len(identifiers) == 0:
        item = (
            "No commands to display." if command else "No packages to display."
        )
        columns[0]["rows"].append(item)

    _display_table(columns)


def display_packages(packages, registries):
    """Display *packages*.

    *packages* should be a list of :class:`wiz.package.Package` instances.

    *registries* should be a list of available registry paths.

    """
    titles = ["Package", "Version", "Registry", "Description"]
    columns = [
        {"size": len(title), "rows": [], "title": title} for title in titles
    ]

    for package in packages:
        _identifier = package.definition_identifier
        if package.variant_name is not None:
            _identifier += " [{}]".format(package.variant_name)

        columns[0]["rows"].append(_identifier)
        columns[0]["size"] = max(len(_identifier), columns[0]["size"])

        _version = str(package.version)
        columns[1]["rows"].append(_version)
        columns[1]["size"] = max(len(_version), columns[1]["size"])

        registry_index = str(
            registries.index(package.get("registry"))
        )
        columns[2]["rows"].append(registry_index)
        columns[2]["size"] = max(len(registry_index), columns[2]["size"])

        _description = package.description
        columns[3]["rows"].append(_description)
        columns[3]["size"] = max(len(_description), columns[3]["size"])

    if len(packages) == 0:
        item = "No packages to display."
        columns[0]["rows"].append(item)

    _display_table(columns)


def display_command_mapping(mapping):
    """Display commands contained in *mapping*.

    *mapping* should be in the form of::

        {
            "app": "App0.1.0",
            "appX": "App0.1.0 --option value"
        }

    """
    titles = ["Command", "Value"]
    columns = [
        {"size": len(title), "rows": [], "title": title} for title in titles
    ]

    for command, value in sorted(mapping.items()):
        columns[0]["rows"].append(command)
        columns[0]["size"] = max(len(command), columns[0]["size"])

        columns[1]["rows"].append(value)
        columns[1]["size"] = max(len(value), columns[1]["size"])

    if len(mapping) == 0:
        item = "No commands to display."
        columns[0]["rows"].append(item)

    _display_table(columns)


def display_environ_mapping(mapping):
    """Display environment variables contained in *mapping*.

    *mapping* should be in the form of::

        {
            "KEY1": "VALUE1",
            "KEY2": "VALUE2"
        }

    """
    titles = ["Environment Variable", "Environment Value"]
    columns = [
        {"size": len(title), "rows": [], "title": title} for title in titles
    ]

    def _compute_value(_variable, value):
        """Compute value to display."""
        if _variable == "DISPLAY":
            return [value]
        if _variable == "WIZ_CONTEXT":
            return [value[:50] + "..."]
        return str(value).split(os.pathsep)

    for variable in sorted(mapping.keys()):
        for key, _value in itertools.izip_longest(
            [variable], _compute_value(variable, mapping[variable])
        ):
            _key = key or ""
            columns[0]["rows"].append(_key)
            columns[0]["size"] = max(len(_key), columns[0]["size"])

            columns[1]["rows"].append(_value)
            columns[1]["size"] = max(len(_value), columns[1]["size"])

    if len(mapping) == 0:
        item = "No environment variables to display."
        columns[0]["rows"].append(item)

    _display_table(columns)


def _query_identifier():
    """Query an identifier for a resolved context."""
    logger = mlog.Logger(__name__ + "._query_identifier")

    while True:
        value = click.prompt("Please enter a definition identifier")
        identifier = wiz.filesystem.sanitise_value(value.strip())
        if len(identifier) > 2:
            return identifier

        logger.warning(
            "'{}' is an incorrect identifier (It must be at least 3 "
            "characters long.)".format(identifier)
        )


def _query_description():
    """Query an description for a resolved context."""
    logger = mlog.Logger(__name__ + "._query_description")

    while True:
        value = click.prompt("Please enter a description:")
        description = value.strip()

        if len(description) > 5:
            return description

        logger.warning(
            "'{}' is an incorrect description (It must be at least 5 "
            "characters long.)".format(description)
        )


def _query_version(default="0.1.0"):
    """Query a version for a resolved context."""
    logger = mlog.Logger(__name__ + "._query_version")

    while True:
        content = click.prompt("Please indicate a version", default=default)

        try:
            version = wiz.utility.get_version(content)
        except wiz.exception.InvalidVersion as error:
            logger.warning(error)
            continue
        else:
            return version


def _query_command(aliases=None):
    """Query the commands to run within the exported wrapper."""
    if aliases is not None and len(aliases) > 0:
        click.echo("Available aliases:")
        for _command in aliases:
            click.echo("- {}".format(_command))

    return click.prompt(
        "Please indicate a command if necessary", default=None
    )


def _display_table(columns):
    """Display table of *rows*."""
    spaces = []
    for column in columns:
        space = column["size"] - len(column["title"])
        spaces.append(space)

    # Print titles.
    click.echo(
        "\n" + "   ".join([
            columns[i]["title"] + " " * spaces[i]
            for i in range(len(columns))
        ])
    )

    # Print underlines.
    click.echo(
        "   ".join([
            "-" * (len(columns[i]["title"]) + spaces[i])
            for i in range(len(columns))
        ])
    )

    # Print elements.
    for row in itertools.izip_longest(*[column["rows"] for column in columns]):
        click.echo(
            "   ".join([
                row[i] + " " * (columns[i]["size"] - len(row[i]))
                for i in range(len(row))
                if row[i] is not None
            ])
        )

    # Print final blank line.
    click.echo()
