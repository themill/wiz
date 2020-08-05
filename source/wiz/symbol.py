# :coding: utf-8

"""Common symbols."""

#: Environment variable corresponding to the 'install-location' definition key.
INSTALL_LOCATION = "INSTALL_LOCATION"

#: Environment variable corresponding to the 'install-root' definition key.
INSTALL_ROOT = "INSTALL_ROOT"

#: Separator between the normal arguments and the command to run.
COMMAND_SEPARATOR = "--"

#: Separator between namespaces and identifier.
NAMESPACE_SEPARATOR = "::"

#: Default value when a definition value is unknown.
UNSET_VALUE = "-"

#: Package request type.
PACKAGE_REQUEST_TYPE = "package"

#: Command request type.
COMMAND_REQUEST_TYPE = "command"

#: Identifier for packages which should be use implicitly in context.
IMPLICIT_PACKAGE = "implicit-packages"

#: History action for system identification.
SYSTEM_IDENTIFICATION_ACTION = "IDENTIFY_SYSTEM"

#: History action for definitions collection.
DEFINITIONS_COLLECTION_ACTION = "FETCH_DEFINITIONS"

#: History action for graph creation.
GRAPH_CREATION_ACTION = "CREATE_GRAPH"

#: History action for graph update.
GRAPH_UPDATE_ACTION = "UPDATE_GRAPH"

#: History action for graph combination extraction.
GRAPH_COMBINATION_EXTRACTION_ACTION = "EXTRACT_GRAPH_COMBINATION"

#: History action for node replacement in graph.
GRAPH_NODES_REPLACEMENT_ACTION = "REPLACE_NODES"

#: History action for computation of graph distance mapping.
GRAPH_DISTANCE_COMPUTATION_ACTION = "CREATE_DISTANCE_MAPPING"

#: History action for node creation within graph.
GRAPH_NODE_CREATION_ACTION = "CREATE_NODE"

#: History action for node removal within graph.
GRAPH_NODE_REMOVAL_ACTION = "REMOVE_NODE"

#: History action for link creation within graph.
GRAPH_LINK_CREATION_ACTION = "CREATE_LINK"

#: History action for version conflicts identification within graph.
GRAPH_VERSION_CONFLICTS_IDENTIFICATION_ACTION = "IDENTIFY_VERSION_CONFLICTS"

#: History action for variants conflicts identification within graph.
GRAPH_VARIANT_CONFLICTS_IDENTIFICATION_ACTION = "IDENTIFY_VARIANT_CONFLICTS"

#: History action for error identification within graph.
GRAPH_ERROR_IDENTIFICATION_ACTION = "IDENTIFY_ERROR"

#: History action for resolution error within graph.
GRAPH_RESOLUTION_FAILURE_ACTION = "RESOLUTION_ERROR"

#: History action for package extraction from graph.
GRAPH_PACKAGES_EXTRACTION_ACTION = "EXTRACT_PACKAGES"

#: History action for context extraction packages list.
CONTEXT_EXTRACTION_ACTION = "EXTRACT_CONTEXT"

#: History action for exception raised.
EXCEPTION_RAISE_ACTION = "RAISE_EXCEPTION"
