# :coding: utf-8

from __future__ import absolute_import
import collections
import datetime
import functools
import io
import logging
import os
import textwrap
import time

import click
import six
import six.moves
import ujson

import wiz.config
import wiz.definition
import wiz.exception
import wiz.filesystem
import wiz.history
import wiz.logging
import wiz.registry
import wiz.spawn
import wiz.symbol
import wiz.utility
from wiz import __version__

# Initiate logging handler to display potential warning when fetching config.
wiz.logging.initiate()

#: Retrieve configuration mapping to initialize default values.
_CONFIG = wiz.config.fetch()

#: Click default context for all commands.
CONTEXT_SETTINGS = dict(
    max_content_width=_CONFIG.get("command", {}).get("max_content_width", 80),
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
    help=textwrap.dedent(
        """
        Wiz is an environment management framework which resolves an environment
        context or executes a command from one or several package requests.

        Example:

        \b
        >>> wiz use "app==2.*" my-plugin -- AppExe /path/to/script

        A command can also be executed from a resolved context via a command
        alias which is extracted from its corresponding package.

        Example:

        \b
        >>> wiz run python

        All available packages and command can be listed as follow:

        \b
        >>> wiz list package
        >>> wiz list command

        It is also possible to search a specific package or command as follow:

        \b
        >>> wiz search python

        """
    ),
)
@click.version_option(version=__version__)
@click.option(
    "-v", "--verbosity",
    help="Set the logging output verbosity.",
    type=click.Choice(wiz.logging.LEVEL_MAPPING.keys()),
    default=_CONFIG.get("command", {}).get("verbosity", "info"),
    show_default=True
)
@click.option(
    "--no-local",
    help="Skip local registry.",
    is_flag=True,
    default=_CONFIG.get("command", {}).get("no_local", False),
)
@click.option(
    "--no-cwd",
    help=(
        "Do not attempt to discover definitions from current "
        "working directory within project."
    ),
    is_flag=True,
    default=_CONFIG.get("command", {}).get("no_cwd", False),
)
@click.option(
    "-rd", "--registry-depth",
    help="Maximum depth to recursively search for definitions.",
    default=_CONFIG.get("command", {}).get("depth"),
    type=int,
    metavar="NUMBER",
)
@click.option(
    "-r", "--registry",
    help="Set registry path for package definitions.",
    default=wiz.registry.get_defaults(),
    multiple=True,
    metavar="PATH",
    type=click.Path(),
    show_default=True
)
@click.option(
    "-add", "--add-registry",
    help="Prepend registry path to default registries.",
    multiple=True,
    metavar="PATH",
    type=click.Path()
)
@click.option(
    "--ignore-implicit",
    help=(
        "Do not include implicit packages (with 'auto-use' set to true) "
        "in resolved context."
    ),
    is_flag=True,
    default=_CONFIG.get("command", {}).get("ignore_implicit", False),
)
@click.option(
    "--init",
    help=(
        "Initial Environment which will be augmented by the resolved "
        "environment."
    ),
    type=lambda x: tuple(x.split("=", 1)),
    metavar="VARIABLE=VALUE",
    default=[],
    multiple=True,
)
@click.option(
    "--platform",
    metavar="PLATFORM",
    help="Override detected platform.",
    default=_CONFIG.get("command", {}).get("platform"),
)
@click.option(
    "--architecture",
    metavar="ARCHITECTURE",
    help="Override detected architecture.",
    default=_CONFIG.get("command", {}).get("architecture"),
)
@click.option(
    "--os-name",
    metavar="NAME",
    help="Override detected operating system name.",
    default=_CONFIG.get("command", {}).get("os_name"),
)
@click.option(
    "--os-version",
    metavar="VERSION",
    help="Override detected operating system version.",
    default=_CONFIG.get("command", {}).get("os_version"),
)
@click.option(
    "--record",
    help="Record resolution context process for debugging.",
    type=click.Path(exists=True)
)
@click.pass_context
def main(click_context, **kwargs):
    """Main entry point for the command line interface."""
    wiz.logging.initiate(console_level=kwargs["verbosity"])
    logger = logging.getLogger(__name__ + ".main")

    if kwargs["record"] is not None:
        wiz.history.start_recording(
            command=click_context.obj["initial_input"]
        )

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
        kwargs["registry"] + kwargs["add_registry"],
        include_local=not kwargs["no_local"],
        include_working_directory=not kwargs["no_cwd"]
    )
    logger.debug("Registries: " + ", ".join(registries))

    # Extract initial environment.
    initial_environment = {x[0]: x[1] for x in kwargs["init"] if len(x) == 2}
    logger.debug("Initial environment: {}".format(initial_environment))

    # Update user data within click context.
    click_context.obj.update({
        "system_mapping": system_mapping,
        "registry_paths": registries,
        "registry_search_depth": kwargs["registry_depth"],
        "ignore_implicit_packages": kwargs["ignore_implicit"],
        "initial_environment": initial_environment,
        "recording_path": kwargs["record"],
    })


@main.group(
    name="list",
    help=textwrap.dedent(
        """
        Display all available commands or package definitions.

        Example:

        \b
        >>> wiz list command
        >>> wiz list package
        >>> wiz list command --all
        >>> wiz list package --all

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


@wiz_list_group.command(
    name="package",
    help=textwrap.dedent(
        """
        Display all available package definitions.

        Example:

        \b
        >>> wiz list package
        >>> wiz list package --all

        """
    ),
    short_help="Display available packages.",
    context_settings=CONTEXT_SETTINGS
)
@click.option(
    "-a", "--all",
    help="Display all package versions, not just the latest one.",
    is_flag=True,
    default=(
        _CONFIG.get("command", {}).get("list", {}).get("package", {})
        .get("all", False)
    )
)
@click.option(
    "--no-arch",
    help="Display packages for all platforms.",
    is_flag=True,
    default=(
        _CONFIG.get("command", {}).get("list", {}).get("package", {})
        .get("no_arch", False)
    )
)
@click.pass_context
def wiz_list_package(click_context, **kwargs):
    """Command to list available package definitions."""
    package_mapping = {}

    system_mapping = (
        None if kwargs["no_arch"] else click_context.obj["system_mapping"]
    )

    for definition in wiz.definition.discover(
        click_context.obj["registry_paths"],
        system_mapping=system_mapping,
        max_depth=click_context.obj["registry_search_depth"]
    ):
        _add_to_mapping(definition, package_mapping)

    display_registries(click_context.obj["registry_paths"])

    display_package_mapping(
        package_mapping,
        click_context.obj["registry_paths"],
        all_versions=kwargs["all"],
        with_system=kwargs["no_arch"]
    )

    _export_history_if_requested(click_context)


@wiz_list_group.command(
    name="command",
    help=textwrap.dedent(
        """
        Display all available commands.

        Example:

        \b
        >>> wiz list command
        >>> wiz list command --all

        """
    ),
    short_help="Display available commands.",
    context_settings=CONTEXT_SETTINGS
)
@click.option(
    "-a", "--all",
    help="Display all command versions, not just the latest one.",
    is_flag=True,
    default=(
        _CONFIG.get("command", {}).get("list", {}).get("command", {})
        .get("all", False)
    )
)
@click.option(
    "--no-arch",
    help="Display commands for all platforms.",
    is_flag=True,
    default=(
        _CONFIG.get("command", {}).get("list", {}).get("command", {})
        .get("no_arch", False)
    )
)
@click.pass_context
def wiz_list_command(click_context, **kwargs):
    """Command to list available commands."""
    package_mapping = {}
    command_mapping = {}

    system_mapping = (
        None if kwargs["no_arch"] else click_context.obj["system_mapping"]
    )

    for definition in wiz.definition.discover(
        click_context.obj["registry_paths"],
        system_mapping=system_mapping,
        max_depth=click_context.obj["registry_search_depth"]
    ):
        _add_to_mapping(definition, package_mapping)

        for command in definition.command.keys():
            command_mapping.setdefault(command, [])
            command_mapping[command] = definition.qualified_identifier

    display_registries(click_context.obj["registry_paths"])

    display_command_mapping(
        command_mapping,
        package_mapping,
        click_context.obj["registry_paths"],
        all_versions=kwargs["all"],
        with_system=kwargs["no_arch"]
    )

    _export_history_if_requested(click_context)


@main.command(
    name="search",
    help=textwrap.dedent(
        """
        Search and display definitions from a list of filters.

        Example:

        \b
        >>> wiz search foo
        >>> wiz search foo --all
        >>> wiz search foo --no-arch
        >>> wiz search foo bar

        """
    ),
    short_help="Search package definitions.",
    context_settings=CONTEXT_SETTINGS
)
@click.option(
    "-a", "--all",
    help="Display all package versions, not just the latest one.",
    is_flag=True,
    default=_CONFIG.get("command", {}).get("search", {}).get("all", False)
)
@click.option(
    "--no-arch",
    help="Display results for all platforms.",
    is_flag=True,
    default=_CONFIG.get("command", {}).get("search", {}).get("no_arch", False)
)
@click.option(
    "-t", "--type",
    help="Set the request type.",
    type=click.Choice([
        "all",
        wiz.symbol.PACKAGE_REQUEST_TYPE,
        wiz.symbol.COMMAND_REQUEST_TYPE
    ]),
    default=_CONFIG.get("command", {}).get("search", {}).get("type", "all"),
    show_default=True
)
@click.argument(
    "filters",
    nargs=-1,
    required=True
)
@click.pass_context
def wiz_search(click_context, **kwargs):
    """Search and display definitions from request(s)."""
    logger = logging.getLogger(__name__ + ".wiz_search")

    # Ensure that context fail if extra arguments were passed.
    _fail_on_extra_arguments(click_context)

    # Display registries.
    display_registries(click_context.obj["registry_paths"])

    # Fetch all definitions.
    package_mapping = {}
    command_mapping = {}

    # Keyword elements to filter.
    keywords = ["identifier", "version", "description"]

    system_mapping = (
        None if kwargs["no_arch"] else click_context.obj["system_mapping"]
    )

    _filters = kwargs["filters"]

    for definition in wiz.definition.discover(
        click_context.obj["registry_paths"],
        system_mapping=system_mapping,
        max_depth=click_context.obj["registry_search_depth"]
    ):
        values = [str(getattr(definition, keyword)) for keyword in keywords]
        values += definition.command.keys()

        if any(_filter in value for value in values for _filter in _filters):
            _add_to_mapping(definition, package_mapping)

        for command in definition.command.keys():
            if any(_filter in command for _filter in kwargs["filters"]):
                command_mapping.setdefault(command, [])
                command_mapping[command] = definition.qualified_identifier

    results_found = False

    if kwargs["type"] in ["command", "all"] and len(command_mapping) > 0:
        results_found = True

        display_command_mapping(
            command_mapping,
            package_mapping,
            click_context.obj["registry_paths"],
            all_versions=kwargs["all"],
            with_system=kwargs["no_arch"]
        )

    if kwargs["type"] in ["package", "all"] and len(package_mapping) > 0:
        results_found = True

        display_package_mapping(
            package_mapping,
            click_context.obj["registry_paths"],
            all_versions=kwargs["all"],
            with_system=kwargs["no_arch"]
        )

    if not results_found:
        logger.warning("No results found.\n")

    _export_history_if_requested(click_context)


@main.command(
    name="view",
    help=textwrap.dedent(
        """
        Display content of a package definition from definition identifier or
        command.

        Example:

        \b
        >>> wiz view foo
        >>> wiz view foo --json

        """
    ),
    short_help="View content of a package definition.",
    context_settings=CONTEXT_SETTINGS
)
@click.option(
    "--json",
    help="Display definition in JSON.",
    is_flag=True,
    default=_CONFIG.get("command", {}).get("view", {}).get("json_view", False),
)
@click.argument(
    "request",
    nargs=1,
    required=True
)
@click.pass_context
def wiz_view(click_context, **kwargs):
    """Display definition from identifier or command."""
    logger = logging.getLogger(__name__ + ".wiz_view")

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
                definition.qualified_version_identifier
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
                definition.qualified_version_identifier
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
    help=textwrap.dedent(
        """
        Spawn shell with resolved context from requested packages, or run
        a command within the resolved context.

        Example:

        \b
        >>> wiz use package1>=1 package2==2.3.0 package3
        >>> wiz use package1>=1 package2==2.3.0 package3 -- app --option value
        >>> wiz use --view command

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
@click.option(
    "-mc", "--max-combinations",
    help=(
        "Maximum number of combinations which can be generated from "
        "conflicting variants during the context resolution process."
    ),
    default=_CONFIG.get("resolver", {}).get("maximum_combinations"),
    type=int,
    metavar="NUMBER",
    show_default=True
)
@click.option(
    "-ma", "--max-attempts",
    help=(
        "Maximum number of attempts to resolve the context before raising an "
        "error."
    ),
    default=_CONFIG.get("resolver", {}).get("maximum_attempts"),
    type=int,
    metavar="NUMBER",
    show_default=True
)
@click.argument(
    "requests",
    nargs=-1,
    required=True
)
@click.pass_context
def wiz_use(click_context, **kwargs):
    """Resolve and use context from command."""
    logger = logging.getLogger(__name__ + ".wiz_use")

    definition_mapping = _fetch_definition_mapping_from_context(click_context)
    ignore_implicit = click_context.obj["ignore_implicit_packages"]
    environ_mapping = click_context.obj["initial_environment"]

    # Fetch extra arguments from context.
    extra_arguments = _fetch_extra_arguments(click_context)

    try:
        wiz_context = wiz.resolve_context(
            list(kwargs["requests"]), definition_mapping,
            ignore_implicit=ignore_implicit,
            environ_mapping=environ_mapping,
            maximum_combinations=kwargs["max_combinations"],
            maximum_attempts=kwargs["max_attempts"],
        )

        # Only view the resolved context without spawning a shell nor
        # running any commands.
        if kwargs["view"]:
            display_registries(wiz_context["registries"])
            display_resolved_context(wiz_context)

        # Do not execute any command if history is being recorded.
        elif not kwargs["view"] and click_context.obj["recording_path"]:
            pass

        # If no commands are indicated, spawn a shell.
        elif len(extra_arguments) == 0:
            wiz.spawn.shell(wiz_context["environ"], wiz_context["command"])

        # Otherwise, resolve the command and run it within the resolved context.
        else:
            command_elements = wiz.resolve_command(
                extra_arguments, wiz_context.get("command", {})
            )
            wiz.spawn.execute(command_elements, wiz_context["environ"])

    except wiz.exception.WizError as error:
        logger.error(str(error))

        wiz.history.record_action(
            wiz.symbol.EXCEPTION_RAISE_ACTION, error=error
        )

    except KeyboardInterrupt:
        logger.warning("Aborted.")

    _export_history_if_requested(click_context)


@main.command(
    "run",
    help=textwrap.dedent(
        """
        Run command from resolved context.

        Example:

        \b
        >>> wiz run command
        >>> wiz run command -- --option value /path/to/output

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
@click.option(
    "-mc", "--max-combinations",
    help=(
        "Maximum number of combinations which can be generated from "
        "conflicting variants during the context resolution process."
    ),
    default=_CONFIG.get("resolver", {}).get("maximum_combinations"),
    type=int,
    metavar="NUMBER",
    show_default=True
)
@click.option(
    "-ma", "--max-attempts",
    help=(
        "Maximum number of attempts to resolve the context before raising an "
        "error."
    ),
    default=_CONFIG.get("resolver", {}).get("maximum_attempts"),
    type=int,
    metavar="NUMBER",
    show_default=True
)
@click.argument(
    "request",
    nargs=1,
    required=True
)
@click.pass_context
def wiz_run(click_context, **kwargs):
    """Run application from resolved context."""
    logger = logging.getLogger(__name__ + ".wiz_run")

    definition_mapping = _fetch_definition_mapping_from_context(click_context)
    ignore_implicit = click_context.obj["ignore_implicit_packages"]
    environ_mapping = click_context.obj["initial_environment"]

    # Fetch extra arguments from context.
    extra_arguments = _fetch_extra_arguments(click_context)

    try:
        requirement = wiz.utility.get_requirement(kwargs["request"])
        request = wiz.fetch_package_request_from_command(
            kwargs["request"], definition_mapping
        )

        wiz_context = wiz.resolve_context(
            [request], definition_mapping,
            ignore_implicit=ignore_implicit,
            environ_mapping=environ_mapping,
            maximum_combinations=kwargs["max_combinations"],
            maximum_attempts=kwargs["max_attempts"],
        )

        # Only view the resolved context without spawning a shell nor
        # running any commands.
        if kwargs["view"]:
            display_registries(wiz_context["registries"])
            display_resolved_context(wiz_context)

        # Do not execute any command if history is being recorded.
        elif not kwargs["view"] and click_context.obj["recording_path"]:
            pass

        else:
            command_elements = wiz.resolve_command(
                [requirement.name] + extra_arguments,
                wiz_context.get("command", {})
            )
            wiz.spawn.execute(command_elements, wiz_context["environ"])

    except wiz.exception.WizError as error:
        logger.error(str(error))

        wiz.history.record_action(
            wiz.symbol.EXCEPTION_RAISE_ACTION, error=error
        )

    except KeyboardInterrupt:
        logger.warning("Aborted.")

    _export_history_if_requested(click_context)


@main.command(
    "freeze",
    help=textwrap.dedent(
        """
        Export resolved context into a package definition or a script.

        Example:

        \b
        >>> wiz freeze foo>=1 bar==2.3.0 baz -o /tmp
        >>> wiz freeze --format bash foo>=1 bar==2.3.0 baz -o /tmp
        >>> wiz freeze --format tcsh foo>=1 bar==2.3.0 baz -o /tmp

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
    "-F", "--format",
    help="Indicate the output format.",
    type=click.Choice(["wiz", "tcsh", "bash"]),
    default=_CONFIG.get("command", {}).get("freeze", {}).get("format", "wiz"),
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
    logger = logging.getLogger(__name__ + ".wiz_freeze")

    # Ensure that context fail if extra arguments were passed.
    _fail_on_extra_arguments(click_context)

    definition_mapping = _fetch_definition_mapping_from_context(click_context)
    ignore_implicit = click_context.obj["ignore_implicit_packages"]
    environ_mapping = click_context.obj["initial_environment"]

    try:
        _context = wiz.resolve_context(
            list(kwargs["requests"]), definition_mapping,
            ignore_implicit=ignore_implicit,
            environ_mapping=environ_mapping,
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
        logger.error(str(error))

        wiz.history.record_action(
            wiz.symbol.EXCEPTION_RAISE_ACTION, error=error
        )

    except KeyboardInterrupt:
        logger.warning("Aborted.")

    _export_history_if_requested(click_context)


@main.command(
    "install",
    help=textwrap.dedent(
        """
        Install a package definition to a registry.

        Example:

        \b
        >>> wiz install /path/to/foo.json -o /path/to/registry
        >>> wiz install /all/definitions/* -o /path/to/registry

        """
    ),
    short_help="Install a package definition to a registry.",
    context_settings=CONTEXT_SETTINGS
)
@click.option(
    "-o", "--output",
    help="Registry target to install the package to.",
    type=click.Path(),
    required=True
)
@click.option(
    "-f", "--overwrite",
    help="Always overwrite existing definitions.",
    is_flag=True,
    default=(
        _CONFIG.get("command", {}).get("install", {}).get("overwrite", False)
    )
)
@click.argument(
    "definitions",
    nargs=-1,
    required=True
)
@click.pass_context
def wiz_install(click_context, **kwargs):
    """Install a definition to a registry."""
    logger = logging.getLogger(__name__ + ".wiz_install")

    # Ensure that context fail if extra arguments were passed.
    _fail_on_extra_arguments(click_context)

    overwrite = kwargs["overwrite"]

    callback = _CONFIG.get("callback", {}).get("install")
    if callback is None:
        logger.error("There are no available callback to install definitions.")
        return

    while True:
        try:
            callback(
                kwargs["definitions"], kwargs["output"],
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
            logger.error(error)

            wiz.history.record_action(
                wiz.symbol.EXCEPTION_RAISE_ACTION, error=error
            )
            break

    _export_history_if_requested(click_context)


@main.command(
    "edit",
    help=textwrap.dedent(
        """
        Edit one or several definitions with default editor or with operation
        option(s).

        If an output is specified, the original definition(s) will not be
        mutated. Otherwise, the original definition file(s) will be updated with
        edited data.

        The edited definition(s) will be validated before export.

        Example:

        \b
        >>> wiz edit foo.json
        >>> wiz edit foo.json --output /tmp/target
        >>> wiz edit foo.json --set install-location --value /path/data
        >>> wiz edit foo.json --update environ --value '{"KEY": "VALUE"}'
        >>> wiz edit * --extend requirements --value "bar > 0.1.0"

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
    "-f", "--overwrite",
    help="Always overwrite existing definitions.",
    is_flag=True,
    default=_CONFIG.get("command", {}).get("edit", {}).get("overwrite", False)
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
    logger = logging.getLogger(__name__ + ".wiz_edit")

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

                definition = wiz.definition.Definition(
                    ujson.loads(data), path=definition.path
                )

            else:
                for name in operations:
                    args = kwargs[name]
                    definition = getattr(definition, name)(*args)

            path = definition.path

            if kwargs["output"] is not None:
                name = os.path.basename(definition.path)
                path = os.path.join(kwargs["output"], name)

            overwrite = kwargs["overwrite"]

            while True:
                try:
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
        logger.error(str(error))

        wiz.history.record_action(
            wiz.symbol.EXCEPTION_RAISE_ACTION, error=error
        )

    _export_history_if_requested(click_context)


@main.command(
    "analyze",
    help=textwrap.dedent(
        """
        Analyze reachable definitions and display corresponding errors and
        warnings. A filter can be set to target specific definitions.

        Example:

        \b
        >>> wiz analyze
        >>> wiz analyze foo bar
        >>> wiz analyze --verbose
        >>> wiz -r /path/to/registry analyze
        >>> wiz -add /path/to/additional/registry analyze

        """
    ),
    short_help="Analyze reachable definitions.",
    context_settings=CONTEXT_SETTINGS
)
@click.option(
    "-d", "--duration-threshold",
    help="Update duration threshold (in seconds)",
    type=int,
    metavar="SECONDS",
    default=1
)
@click.option(
    "-e", "--extraction-threshold",
    help="Update combination extraction threshold",
    type=int,
    metavar="NUMBER",
    default=5
)
@click.option(
    "-mc", "--max-combinations",
    help=(
        "Maximum number of combinations which can be generated from "
        "conflicting variants during the context resolution process."
    ),
    default=_CONFIG.get("resolver", {}).get("maximum_combinations"),
    type=int,
    metavar="NUMBER",
    show_default=True
)
@click.option(
    "-ma", "--max-attempts",
    help=(
        "Maximum number of attempts to resolve the context before raising an "
        "error."
    ),
    default=_CONFIG.get("resolver", {}).get("maximum_attempts"),
    type=int,
    metavar="NUMBER",
    show_default=True
)
@click.option(
    "-V", "--verbose",
    help="Increase verbosity of analysis.",
    is_flag=True,
    default=_CONFIG.get("command", {}).get("analyze", {}).get("verbose", False)
)
@click.argument(
    "filters",
    nargs=-1,
)
@click.pass_context
def wiz_analyze(click_context, **kwargs):
    """Display warning and error for each registry."""
    logger = logging.getLogger(__name__ + ".wiz_analyze")
    if click_context.obj["recording_path"] is not None:
        logger.error("Impossible to record history during analysis.")
        return

    definition_mapping = _fetch_definition_mapping_from_context(click_context)

    definitions = [
        definition for key, mapping
        in definition_mapping[wiz.symbol.PACKAGE_REQUEST_TYPE].items()
        for definition in mapping.values()
        if key != "__namespace__"
        and not any(
            _filter.lower() not in definition.qualified_identifier
            for _filter in kwargs["filters"]
        )
    ]

    extraction_threshold = kwargs["extraction_threshold"]
    duration_threshold = kwargs["duration_threshold"]

    with_errors = []
    with_warnings = []
    with_version_dropdown = []
    over_combination_threshold = []
    over_duration_threshold = []
    max_version_dropdown = 0
    max_combinations = 0
    max_duration = 0

    with click.progressbar(
        definitions, show_pos=True, show_eta=False
    ) as _definitions:
        for definition in _definitions:
            result = _fetch_validation_mapping(
                definition, definition_mapping,
                maximum_combinations=kwargs["max_combinations"],
                maximum_attempts=kwargs["max_attempts"],
            )

            identifier = definition.qualified_version_identifier
            if len(result["errors"]):
                with_errors.append((identifier, result["errors"]))

            if len(result["warnings"]):
                with_warnings.append((identifier, result["warnings"]))

            action = wiz.symbol.GRAPH_NODES_REPLACEMENT_ACTION
            value = result["history"].get(action)
            if value:
                with_version_dropdown.append((value, identifier))
                max_version_dropdown = max(max_version_dropdown, value)

            action = wiz.symbol.GRAPH_COMBINATION_EXTRACTION_ACTION
            value = result["history"].get(action)
            if value:
                max_combinations = max(max_combinations, value)

                if value >= extraction_threshold:
                    over_combination_threshold.append((value, identifier))

            max_duration = max(max_duration, result["duration"])

            if result["duration"] >= duration_threshold:
                over_duration_threshold.append((result["duration"], identifier))

    columns = _create_columns(["Metrics", "Values"])

    rows = [
        ("Total", len(definitions)),
        ("Errors", len(with_errors)),
        ("Warnings", len(with_warnings)),
        ("With version dropdown", len(with_version_dropdown)),
        (
            "≥ {} combination(s)".format(extraction_threshold),
            len(over_combination_threshold)
        ),
        (
            "≥ {} second(s)".format(duration_threshold),
            len(over_duration_threshold)
        ),
        ("Max resolution time", "{:0.4f}s".format(max_duration)),
        ("Max combinations", max_combinations),
        ("Max version dropdown", max_version_dropdown)
    ]

    for key, value in rows:
        _create_row(key, columns[0])
        _create_row(value, columns[1])

    _display_table(columns)

    if kwargs["verbose"]:
        click.echo(click.style("Errors", bold=True))
        for _id, errors in sorted(with_errors):
            click.echo("- {}".format(_id))
            for error in errors:
                click.echo(click.style(error, fg="red"))

        if not len(with_errors):
            click.echo("None")

        click.echo(click.style("\nWarning", bold=True))
        for _id, warnings in sorted(with_warnings):
            click.echo("- {}".format(_id))
            for warning in warnings:
                click.echo(click.style(warning, fg="yellow"))

        if not len(with_warnings):
            click.echo("None")

        click.echo(click.style("\nWith version dropdown", bold=True))
        for value, _id in sorted(with_version_dropdown):
            click.echo("- {} [{}]".format(_id, value))

        if not len(with_version_dropdown):
            click.echo("None")

        click.echo(click.style(
            "\n≥ {} combination(s)".format(extraction_threshold), bold=True
        ))
        for value, _id in sorted(over_combination_threshold):
            click.echo("- {} [{}]".format(_id, value))

        if not len(over_combination_threshold):
            click.echo("None")

        click.echo(click.style(
            "\n≥ {} second(s)".format(duration_threshold), bold=True
        ))
        for duration, _id in sorted(over_duration_threshold):
            click.echo("- {} [{:0.4f}s]".format(_id, duration))

        if not len(over_duration_threshold):
            click.echo("None")

        click.echo()


def _fetch_validation_mapping(
    definition, definition_mapping, maximum_combinations, maximum_attempts
):
    """Fetch validation mapping for *definition*.

    :param definition: instance of :class:`wiz.definition.Definition`.

    :param definition_mapping: Mapping regrouping all available definitions. It
        could be fetched with :func:`fetch_definition_mapping`.

    :param maximum_combinations: Maximum number of combinations which can be
        generated from conflicting variants. Default is None, which means
        that the default value will be picked from the :ref:`configuration
        <configuration>`.

    :param maximum_attempts: Maximum number of resolution attempts before
        raising an error. Default is None, which means  that the default
        value will be picked from the :ref:`configuration <configuration>`.

    :return: Validation mapping.

    """
    result = {"errors": [], "warnings": [], "history": {}}
    context = {}

    error_stream, warning_stream = io.StringIO(), io.StringIO()
    wiz.logging.capture_logs(error_stream, warning_stream)

    wiz.history.start_recording(minimal_actions=True)

    time_start = time.time()

    try:
        context = wiz.resolve_context(
            [definition.qualified_version_identifier], definition_mapping,
            maximum_combinations=maximum_combinations,
            maximum_attempts=maximum_attempts,
            ignore_implicit=True,
        )

    except wiz.exception.WizError as error:
        result["errors"].append(str(error))

    result["duration"] = time.time() - time_start

    recorded = error_stream.getvalue()
    if len(recorded) > 0:
        result["errors"].append(recorded)

    recorded = warning_stream.getvalue()
    if len(recorded) > 0:
        result["warnings"].append(recorded)

    error_stream.close()
    warning_stream.close()

    for key, value in context.get("environ", {}).items():
        unresolved = wiz.environ.ENV_PATTERN.findall(value)
        unresolved = ["".join(res) for res in unresolved]

        if len(unresolved) > 0:
            result["warnings"].append(
                "warning: the '{}' environment variable contains "
                "unresolved elements: {}".format(key, ", ".join(unresolved))
            )

    for action in wiz.history.get().get("actions", []):
        identifier = action.get("identifier")
        result["history"].setdefault(identifier, 0)
        result["history"][identifier] += 1

    return result


def display_registries(paths):
    """Display *paths* for each registry.

    Example::

        >>> display_registries(paths)

        [0] /path/to/registry-1
        [1] /path/to/registry-2

    :param paths: List of registry paths.

    """
    columns = _create_columns(["Registries"])

    for index, path in enumerate(paths):
        _create_row("[{}] {}".format(index, path), columns[0])

    if len(paths) == 0:
        message = "No registries to display."
        _create_row(message, columns[0], resize=False)

    _display_table(columns)


def display_definition(definition):
    """Display *definition*.

    Example::

        >>> display_definition(definition)

        path: /path/to/foo.json
        registry: /path/to/registry
        identifier: Foo
        version: 0.1.0
        description: Description of Foo
        install-location: /path/to/foo
        system:
            os: el >= 7, < 8
            arch: x86_64
        command:
            foo: FooExe
        environ:
            PATH: ${INSTALL_LOCATION}/bin:${PATH}
            LD_LIBRARY_PATH: ${INSTALL_LOCATION}/lib:${LD_LIBRARY_PATH}

    :param definition: Instance of :class:`wiz.definition.Definition`.

    """

    def _display(item, level=0):
        """Display *item*"""
        indent = " " * level

        if isinstance(item, collections.OrderedDict) or isinstance(item, dict):
            for key, value in item.items():
                if (
                    isinstance(value, six.string_types) or
                    isinstance(value, int)
                ):
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

    click.echo("path: {}".format(definition.path))
    click.echo("registry: {}".format(definition.registry_path))
    _display(definition.ordered_data())


def display_command_mapping(
    command_mapping, package_mapping, registries, all_versions=False,
    with_system=False
):
    """Display command mapping.

    Example::

        >>> display_command_mapping(
        ...     command_mapping, package_mapping, registries, all_versions=True
        ... )

        Command   Version   System                Registry   Description
        -------   -------   -------------------   --------   ------------------
        fooExe    1.0.0     noarch                0          Description of Foo
        fooExe    0.1.0     noarch                0          Description of Foo
        python    3.6.6     linux : el >= 6, <7   1          Python interpreter
        python    2.7.4     linux : el >= 6, <7   1          Python interpreter

    :param command_mapping: Mapping which associates all available commands with
        a package definition. It should be in the form of::

            {
                "fooExe": "foo",
                ...
            }

    :param package_mapping: Mapping which associates each package definition
        with an identifier, a version and a system label. It should be in the
        form of::

            {
                "foo": {
                    "1.1.0": {
                        "linux : el >=6, <7": <Definition(identifier="foo")>,
                        "linux : el >=7, <8": <Definition(identifier="foo")>,
                    "0.1.0": {
                        "linux : el >=6, <7": <Definition(identifier="foo")>,
                    ...
                },
                ...
            }

    :param registries: List of registry paths from which definitions were
        fetched.

    :param all_versions: Indicate whether all package definition versions should
        be displayed. Default is False, which means that only the latest version
        will be displayed.

    :param with_system: Indicate whether the package system should be displayed.
        Default is False.

    """
    headers = ["Command", "Version", "Registry", "Description"]
    if with_system:
        headers.insert(2, "System")

    columns = _create_columns(headers)

    success = False

    for command, identifier in sorted(command_mapping.items()):
        versions = sorted(
            package_mapping[identifier].keys(),
            key=functools.cmp_to_key(wiz.utility.compare_versions),
            reverse=True
        )

        # Filter latest version if requested.
        if not all_versions:
            versions = [versions[0]]

        for version in versions:
            for system_label in sorted(
                package_mapping[identifier][version].keys()
            ):
                definition = package_mapping[identifier][version][system_label]

                identifiers = [
                    "{} [{}]".format(command, variant.identifier)
                    for variant in definition.variants
                ] or [command]

                for _identifier in identifiers:
                    rows = [
                        _identifier,
                        definition.version,
                        registries.index(definition.registry_path),
                        definition.description
                    ]

                    if with_system:
                        rows.insert(2, system_label)

                    for index, row in enumerate(rows):
                        _create_row(row, columns[index])

        success = True

    if not success:
        message = "No commands to display."
        _create_row(message, columns[0], resize=False)

    _display_table(columns)


def display_package_mapping(
    package_mapping, registries, all_versions=False, with_system=False
):
    """Display package mapping

    Example::

        >>> display_command_mapping(
        ...     package_mapping, registries, all_versions=True
        ... )

        Package    Version   System                Registry   Description
        --------   -------   -------------------   --------   ------------------
        foo        1.0.0     noarch                0          Description of Foo
        foo        0.1.0     noarch                0          Description of Foo
        bar [V1]   0.1.0     linux                 0          Description of Bar
        bar [V2]   0.1.0     linux                 0          Description of Bar
        bar [V3]   0.1.0     linux                 0          Description of Bar
        python     3.6.6     linux : el >= 6, <7   0          Python interpreter
        python     2.7.4     linux : el >= 6, <7   0          Python interpreter

    :param package_mapping: Mapping which associates each package definition
        with an identifier, a version and a system label. It should be in the
        form of::

            {
                "foo": {
                    "1.1.0": {
                        "linux : el >=6, <7": <Definition(identifier="foo")>,
                        "linux : el >=7, <8": <Definition(identifier="foo")>,
                    "0.1.0": {
                        "linux : el >=6, <7": <Definition(identifier="foo")>,
                    ...
                },
                ...
            }

    :param registries: List of registry paths from which definitions were
        fetched.

    :param all_versions: Indicate whether all package definition versions should
        be displayed. Default is False, which means that only the latest version
        will be displayed.

    :param with_system: Indicate whether the package system should be displayed.
        Default is False.

    """
    headers = ["Package", "Version", "Registry", "Description"]
    if with_system:
        headers.insert(2, "System")

    columns = _create_columns(headers)

    success = False

    for identifier in sorted(package_mapping.keys()):
        versions = sorted(
            package_mapping[identifier].keys(),
            key=functools.cmp_to_key(wiz.utility.compare_versions),
            reverse=True
        )

        # Filter latest version if requested.
        if not all_versions:
            versions = [versions[0]]

        for version in versions:
            for system_label in sorted(
                package_mapping[identifier][version].keys()
            ):
                definition = package_mapping[identifier][version][system_label]

                identifiers = [
                    "{} [{}]".format(identifier, variant.identifier)
                    for variant in definition.variants
                ] or [identifier]

                for _identifier in identifiers:
                    rows = [
                        _identifier,
                        definition.version,
                        registries.index(definition.registry_path),
                        definition.description
                    ]

                    if with_system:
                        rows.insert(2, system_label)

                    for index, row in enumerate(rows):
                        _create_row(row, columns[index])

        success = True

    if not success:
        message = "No packages to display."
        _create_row(message, columns[0], resize=False)

    _display_table(columns)


def display_resolved_context(context):
    """Display resolved *context* mapping.

    Example::

        >>> display_resolved_context(context)

        Package   Version   Registry   Description
        -------   -------   --------   -------------------
        foo       0.1.0     0          Description of Foo.
        bar       1.1.0     0          Description of Bar.

        Command   Value
        -------   ------
        foo       fooExe


        Environment Variable   Environment Value
        --------------------   --------------------
        HOME                   /usr/people/john-doe
        LD_LIBRARY_PATH        /path/to/foo/lib
                               /path/to/bar/lib
        PATH                   /path/to/foo/bin
                               /path/to/bar/bin
                               /usr/local/sbin
                               /usr/local/bin
                               /usr/sbin
                               /usr/bin
                               /sbin
                               /bin
        USER                   john-doe

    :param context: Context mapping as resolved by :func:`wiz.resolve_context`.

    """
    _display_packages_from_context(context)
    _display_command_from_context(context)
    _display_environ_from_context(context)


def _display_packages_from_context(context):
    """Display packages contained in *context* mapping.

    :param context: Context mapping as resolved by :func:`wiz.resolve_context`.

    """
    columns = _create_columns(["Package", "Version", "Registry", "Description"])
    registries = context.get("registries", [])

    success = False

    for package in context.get("packages", []):
        _identifier = package.definition.qualified_identifier
        if package.variant_identifier is not None:
            _identifier += " [{}]".format(package.variant_identifier)

        rows = [
            _identifier,
            package.version,
            registries.index(package.definition.registry_path),
            package.description
        ]

        for index, row in enumerate(rows):
            _create_row(row, columns[index])

        success = True

    if not success:
        message = "No packages to display."
        _create_row(message, columns[0], resize=False)

    _display_table(columns)


def _display_command_from_context(context):
    """Display commands contained in *context* mapping.

    :param context: Context mapping as resolved by :func:`wiz.resolve_context`.

    """
    columns = _create_columns(["Command", "Value"])

    command_mapping = context.get("command", {})

    success = False

    for command, value in sorted(command_mapping.items()):
        _create_row(command, columns[0])
        _create_row(value, columns[1])

        success = True

    if not success:
        message = "No commands to display."
        _create_row(message, columns[0], resize=False)

    _display_table(columns)


def _display_environ_from_context(context):
    """Display environment variables contained in *context* mapping.

    :param context: Context mapping as resolved by :func:`wiz.resolve_context`.

    """
    columns = _create_columns(["Environment Variable", "Environment Value"])

    environ_mapping = context.get("environ", {})

    def _compute_value(_variable, value):
        """Compute value to display."""
        if _variable == "DISPLAY":
            return [value]
        if _variable == "WIZ_CONTEXT":
            return [str(value[:50]) + "..."]
        return str(value).split(os.pathsep)

    success = False

    for variable in sorted(environ_mapping.keys()):
        for key, _value in six.moves.zip_longest(
            [variable], _compute_value(variable, environ_mapping[variable])
        ):
            _create_row(key or "", columns[0])
            _create_row(_value, columns[1])

        success = True

    if not success:
        message = "No environment variables to display."
        _create_row(message, columns[0], resize=False)

    _display_table(columns)


def _casted_argument(argument):
    """Return *argument* casted into a proper type from JSON decoder."""
    # Ensure that boolean value are in JSON format.
    argument = argument.replace("True", "true").replace("False", "false")

    try:
        return ujson.loads(argument)
    except ValueError:
        return argument


def _query_identifier():
    """Query an identifier for a resolved context."""
    logger = logging.getLogger(__name__ + "._query_identifier")

    while True:
        value = click.prompt("Please enter a definition identifier")
        identifier = wiz.filesystem.sanitize_value(value.strip())
        if len(identifier) > 2:
            return identifier

        logger.warning(
            "'{}' is an incorrect identifier (It must be at least 3 "
            "characters long.)".format(identifier)
        )


def _query_description():
    """Query an description for a resolved context."""
    logger = logging.getLogger(__name__ + "._query_description")

    while True:
        value = click.prompt("Please enter a description")
        description = value.strip()

        if len(description) > 5:
            return description

        logger.warning(
            "'{}' is an incorrect description (It must be at least 5 "
            "characters long.)".format(description)
        )


def _query_version(default="0.1.0"):
    """Query a version for a resolved context."""
    logger = logging.getLogger(__name__ + "._query_version")

    while True:
        content = click.prompt("Please indicate a version", default=default)

        try:
            version = wiz.utility.get_version(content)
        except wiz.exception.VersionError as error:
            logger.warning(error)
            continue
        else:
            return version


def _query_command(aliases=None):
    """Query the commands to run within the exported wrapper."""
    if aliases is not None and len(aliases) > 0:
        click.echo("Available aliases:")
        for _command in sorted(aliases):
            click.echo("- {}".format(_command))

    return click.prompt(
        "Please indicate a command if necessary", default=None
    )


def _create_columns(titles):
    """Create columns from *titles*."""
    return [
        {"size": len(title), "rows": [], "title": title} for title in titles
    ]


def _create_row(element, column, resize=True):
    """Add row with *element* in *column*."""
    _element = str(element)
    column["rows"].append(_element)

    if resize:
        column["size"] = max(len(_element), column["size"])


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
    for row in six.moves.zip_longest(*[column["rows"] for column in columns]):
        click.echo(
            "   ".join([
                row[i] + " " * (columns[i]["size"] - len(row[i]))
                for i in range(len(row))
                if row[i] is not None
            ])
        )

    # Print final blank line.
    click.echo()


def _add_to_mapping(definition, mapping):
    """Mutate package *mapping* to add *definition*

    The mutated mapping should be in the form of::

        {
            "foo": {
                "1.1.0": {
                    "linux : el >=6, <7": <Definition(identifier="foo")>,
                    "linux : el >=7, <8": <Definition(identifier="foo")>,
                "0.1.0": {
                    "linux : el >=6, <7": <Definition(identifier="foo")>,
                ...
            },
            "bar": {
                "1.1.0": {
                    "noarch": <Definition(identifier="bar")>
                }
                ...
            },
            ...
        }

    :param definition: Instance of :class:`wiz.definition.Definition`.

    :param mapping: Mapping to mutate.

    """
    identifier = definition.qualified_identifier
    version = str(definition.version)
    system_label = wiz.utility.compute_system_label(definition)

    mapping.setdefault(identifier, {})
    mapping[identifier].setdefault(version, {})
    mapping[identifier][version].setdefault(system_label, {})
    mapping[identifier][version][system_label] = definition


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


def _fetch_definition_mapping_from_context(click_context):
    """Return definition mapping from elements stored in *click_context*."""
    return wiz.fetch_definition_mapping(
        click_context.obj["registry_paths"],
        system_mapping=click_context.obj["system_mapping"],
        max_depth=click_context.obj["registry_search_depth"]
    )


def _export_history_if_requested(click_context):
    """Return definition mapping from elements stored in *click_context*."""
    logger = logging.getLogger(__name__ + "._export_history_if_requested")

    if click_context.obj["recording_path"] is None:
        return

    history = wiz.history.get(serialized=True)
    path = os.path.join(
        os.path.abspath(click_context.obj["recording_path"]),
        "wiz-{}.dump".format(datetime.datetime.now().isoformat())
    )
    wiz.filesystem.export(path, history, compressed=True)
    logger.info("History recorded and exported in '{}'".format(path))
