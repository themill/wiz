# :coding: utf-8

"""Common symbols."""

#: Separator between the normal arguments and the command to run.
COMMAND_SEPARATOR = "--"

#: Default value when a definition value is unknown.
UNKNOWN_VALUE = "unknown"

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

#: History action for requirement graph creation.
GRAPH_CREATION_ACTION = "CREATE_GRAPH"

#: History action for computation of graph distance mapping.
GRAPH_DISTANCE_COMPUTATION_ACTION = "CREATE_DISTANCE_MAPPING"

#: History action for node creation within requirement graph.
GRAPH_NODE_CREATION_ACTION = "CREATE_NODE"

#: History action for node removal within requirement graph.
GRAPH_NODE_REMOVAL_ACTION = "REMOVE_NODE"

#: History action for link creation within requirement graph.
GRAPH_LINK_CREATION_ACTION = "CREATE_LINK"

#: History action for conflicts identification within requirement graph.
GRAPH_CONFLICTS_IDENTIFICATION_ACTION = "IDENTIFY_CONFLICTS"

#: History action for requirement graph division.
GRAPH_DIVISION_ACTION = "DIVIDE_GRAPH"

#: History action for package extraction from requirement graph.
GRAPH_PACKAGES_EXTRACTION_ACTION = "EXTRACT_PACKAGES"

#: History action for context extraction packages list.
CONTEXT_EXTRACTION_ACTION = "EXTRACT_CONTEXT"

#: History action for exception raised.
EXCEPTION_RAISE_ACTION = "RAISE_EXCEPTION"
