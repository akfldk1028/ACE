import itertools
import numpy as np
import config
import networkx as nx


def is_park0_field_inside(i, j):
    """Checks if a 0 degree parking field at cell (i, j) is within the boundaries.

    Parameters:
        i (int): Row index of the cell.
        j (int): Column index of the cell.

    Returns:
        bool: True if the 0 degree parking field at cell (i, j) is within the boundaries, False otherwise.
    """
    return i >= 0 and j >= 0 and \
        i + config.park_field_width <= config.num_rows and \
        j + config.park_field_length <= config.num_cols


def is_park90_field_inside(i, j):
    """Checks if a 90 degree parking field at cell (i, j) is within the boundaries.

    Parameters:
        i (int): Row index of the cell.
        j (int): Column index of the cell.

    Returns:
        bool: True if the  90 degree parking field at cell (i, j) is within the boundaries, False otherwise.
    """
    return i >= 0 and j >= 0 and \
        i + config.park_field_length <= config.num_rows and \
        j + config.park_field_width <= config.num_cols


def is_drive_field_inside(i, j):
    """Checks if the drive field at cell (i, j) is within the boundaries.

    Parameters:
        i (int): Row index of the cell.
        j (int): Column index of the cell.

    Returns:
        bool: True if the drive field at cell (i, j) is within the boundaries, False otherwise.
    """
    return i >= 0 and j >= 0 and \
        i + config.drive_field_width <= config.num_rows and \
        j + config.drive_field_width <= config.num_cols


def set_validity_matrix(valid_fields):
    """The validity matrix is a 2D matrix of the same size as the parking lot. It converts the list of valid fields into
    a boolean variable for each cell. This allows O(1) access to check if a field is valid or not.

    Parameters:
        valid_fields (list): List of valid fields (0 and 90 degree parking and driving fields).

    Returns:
        validity_matrix (np.array): Validity matrix of true and false for parking lot.
    """
    # Initialize validity matrix with boolean false for the entire parking lot
    validity_matrix = np.full((config.num_rows, config.num_cols), False)

    # Set the validity matrix to true for all valid fields
    for (i, j) in valid_fields:
        validity_matrix[i, j] = True

    return validity_matrix


def get_valid_perpendicular_fields():
    """Returns the list of valid 0 and 90 degree perpendicular parking fields by checking for boundaries as well as
    blocked cells.

    Parameters:
        None

    Returns:
        valid_park0_fields (list): List of valid 0 degree parking fields.
        valid_park90_fields (list): List of valid 90 degree parking fields.
    """
    blocked_park0_fields = []
    blocked_park90_fields = []
    # Initially the valid matrices are set to true since they are not yet populated
    for (i, j) in config.blocked_cells:
        blocked_park0_fields += get_park0_fields_containing_cell(i, j,
                                                                 np.full((
                                                                         config.num_rows,
                                                                         config.num_cols),
                                                                         True))
        blocked_park90_fields += get_park90_fields_containing_cell(i, j,
                                                                   np.full((
                                                                           config.num_rows,
                                                                           config.num_cols),
                                                                           True))

    # Remove duplicates
    blocked_park0_fields = list(set(blocked_park0_fields))
    blocked_park90_fields = list(set(blocked_park90_fields))

    valid_park0_fields = [(i, j) for i in range(config.num_rows) for j in
                          range(config.num_cols) if
                          is_park0_field_inside(i, j) and (
                          i, j) not in blocked_park0_fields]
    valid_park90_fields = [(i, j) for i in range(config.num_rows) for j in
                           range(config.num_cols) if
                           is_park90_field_inside(i, j) and (
                           i, j) not in blocked_park90_fields]

    return valid_park0_fields, valid_park90_fields


def get_valid_drive_fields():
    """Returns the list of valid driving fields by checking for boundaries as well as blocked cells.

    Parameters:
        None

    Returns:
        valid_drive_fields (list): List of valid driving fields.
    """
    # Removing all anchor cells that contains at least one blocked cell in its field
    blocked_drive_fields = []
    # Initially the valid matrices are set to true since they are not yet populated
    for (i, j) in config.blocked_cells:
        blocked_drive_fields += get_drive_fields_containing_cell(i, j,
                                                                 np.full((
                                                                         config.num_rows,
                                                                         config.num_cols),
                                                                         True))

    # Remove duplicates
    blocked_drive_fields = list(set(blocked_drive_fields))
    valid_drive_fields = [(i, j) for i in range(config.num_rows) for j in
                          range(config.num_cols)
                          if is_drive_field_inside(i, j) and (
                          i, j) not in blocked_drive_fields]

    return valid_drive_fields


def get_park0_fields_containing_cell(i, j, valid_park0_matrix):
    """Returns the 0 degree parking fields that contain the cell (i, j).

    Parameters:
        i (int): Row index of the cell
        j (int): Column index of the cell
        valid_park0_matrix: Matrix of 0s and 1s that represent valid 0 degree park fields.

    Returns:
        list: List of valid 0 degree park fields of the form (row, column) that contain cell (i, j)
    """
    return [(k, l) for k in range(i - config.park_field_width + 1, i + 1) for l
            in
            range(j - config.park_field_length + 1, j + 1) if
            is_park0_field_inside(k, l) and valid_park0_matrix[k, l]]


def get_park90_fields_containing_cell(i, j, valid_park90_matrix):
    """Returns the 90 degree parking fields that contain the cell (i, j).

    Parameters:
        i (int): Row index of the cell
        j (int): Column index of the cell
        valid_park90_matrix: Matrix of 0s and 1s that represent valid 90 degree park fields.

    Returns:
        list: List of valid 90 degree park fields of the form (row, column) that contain cell (i, j)
    """
    return [(k, l) for k in range(i - config.park_field_length + 1, i + 1) for l
            in
            range(j - config.park_field_width + 1, j + 1) if
            is_park90_field_inside(k, l) and valid_park90_matrix[k, l]]


def get_drive_fields_containing_cell(i, j, valid_drive_matrix):
    """Returns the drive fields that contain the cell (i, j).

    Parameters:
        i (int): Row index of the cell
        j (int): Column index of the cell
        valid_drive_matrix: Matrix of 0s and 1s that represent valid drive fields.

    Returns:
        list: List of valid driving fields of the form (row, column) that contain cell (i, j)
    """
    return [(k, l) for k in range(i - config.drive_field_width + 1, i + 1) for l
            in
            range(j - config.drive_field_width + 1, j + 1) if
            is_drive_field_inside(k, l) and valid_drive_matrix[k, l]]


def get_neighbors_of_park0_field(i, j, valid_drive_matrix):
    """Returns valid drive field neighbors of the park0 field at cell (i, j).

    Parameters:
        i (int): Row index of the cell.
        j (int): Column index of the cell.
        valid_drive_matrix: Matrix representing the valid driving fields.

    Returns:
        (list): List of valid left neighbors of the park0 field at cell (i, j).
        (list): List of valid right neighbors of the park0 field at cell (i, j).
    """
    # Drive fields on the left
    left_neighbors = [(k, j - config.drive_field_width) for k in
                      range(
                          i + config.park_field_width - config.drive_field_width,
                          i + 1) if
                      is_drive_field_inside(k, j - config.drive_field_width) and
                      valid_drive_matrix[
                          k, j - config.drive_field_width]]

    # Drive fields on the right
    right_neighbors = [(k, j + config.park_field_length) for k in
                       range(
                           i + config.park_field_width - config.drive_field_width,
                           i + 1) if
                       is_drive_field_inside(k,
                                             j + config.park_field_length) and
                       valid_drive_matrix[
                           k, j + config.park_field_length]]

    return left_neighbors, right_neighbors


def get_neighbors_of_park90_field(i, j, valid_drive_matrix):
    """Returns valid drive field neighbors of the park90 field at cell (i, j).

    Parameters:
        i (int): Row index of the cell.
        j (int): Column index of the cell.
        valid_drive_matrix: Matrix representing the valid driving fields.

    Returns:
        (list): List of valid top neighbors of the park90 field at cell (i, j).
        (list): List of valid bottom neighbors of the park90 field at cell (i, j).
    """
    # Driving fields at the top
    top_neighbors = [(i - config.drive_field_width, l) for l in
                     range(
                         j + config.park_field_width - config.drive_field_width,
                         j + 1) if
                     is_drive_field_inside(i - config.drive_field_width, l) and
                     valid_drive_matrix[
                         i - config.drive_field_width, l]]

    # Driving fields at the bottom
    bottom_neighbors = [(i + config.park_field_length, l) for l in
                        range(
                            j + config.park_field_width - config.drive_field_width,
                            j + 1) if
                        is_drive_field_inside(i + config.park_field_length,
                                              l) and valid_drive_matrix[
                            i + config.park_field_length, l]]

    return top_neighbors, bottom_neighbors


def create_grid_network(valid_drive_matrix):
    """Creates a NetworkX grid graph with the given number of rows and columns.

    Parameters:
        valid_drive_matrix (numpy array): Matrix representing the valid driving fields.

    Returns:
        G (Graph): The grid NetworkX graph
        pos (dict) : Positions of each node/cell in the grid with the origin in the top-right corner.
        labels (dict) : Labels of each node in the grid which specifies the row and column indices of the node.
    """
    Grid = nx.grid_2d_graph(config.num_rows,
                            config.num_cols)  # creates undirected graph
    Grid = nx.to_directed(Grid)  # creates bidirectional graph
    G = nx.DiGraph(Grid)  # unfreeze the grid graph

    # Delete nodes and adjacent edges for invalid driving fields
    for i, j in itertools.product(range(config.num_rows),
                                  range(config.num_cols)):
        if not (valid_drive_matrix[i, j]):
            G.remove_node((i, j))

    # Check for the connected component that is reachable from the entry
    # and remove the nodes and associated edges that are not reachable from the entry
    components = list(nx.strongly_connected_components(G))
    for component in components:
        if config.entry_drive_field not in component:
            G.remove_nodes_from(component)

    # For one-way driving case, remove edges that directly connect the entry and the exit (if present)
    if config.ARE_DRIVE_LANES_ONEWAY:
        if G.has_edge(config.entry_drive_field, config.exit_drive_field):
            G.remove_edge(config.entry_drive_field, config.exit_drive_field)
        if G.has_edge(config.exit_drive_field, config.entry_drive_field):
            G.remove_edge(config.exit_drive_field, config.entry_drive_field)

    pos = {(i, j): (j, -i) for i, j in G.nodes()}
    labels = dict(((i, j), (i, j)) for i, j in G.nodes())

    nx.set_node_attributes(G, pos, "pos")
    nx.set_node_attributes(G, labels, "labels")

    return G


def update_valid_drive_components(G, valid_drive_fields):
    """Updates the valid drive fields and valid drive matrix after removing any disconnected components in G.

    Parameters:
        G (Graph): The grid NetworkX graph
        valid_drive_fields (list): List of valid driving fields
        valid_drive_matrix (numpy array): Matrix representing the valid driving fields

    Returns:
        valid_drive_fields (list): Updated list of valid driving fields
        valid_drive_matrix (numpy array): Updated matrix representing the valid driving fields
    """
    valid_drive_fields = [(i, j) for i, j in valid_drive_fields if
                          (i, j) in G.nodes]
    valid_drive_matrix = set_validity_matrix(valid_drive_fields)

    return valid_drive_fields, valid_drive_matrix


def get_source_partition_hop_inequality(G, cut_set):
    # Find the set of nodes in G that do not contain the entrance cell after removing nodes in cut_set
    # Remove the nodes in cut_set from G
    G_copy = G.copy()
    G_copy.remove_nodes_from(cut_set)

    # Convert it into an undirected graph
    G_copy = G_copy.to_undirected()

    # Partition the nodes in G_copy and find the component that contains the entrance cell
    for partition in list(nx.connected_components(G_copy)):
        if config.entry_drive_field in partition:
            entry_partition = partition
            break

    # Find the immediate neighbors of the entry partition that are not in the entry partition
    neighbors = set()
    for node in entry_partition:
        neighbors.update(set(G.neighbors(node)))
    modified_cut_set = neighbors - entry_partition

    # Find the complement of the entry partition and the cut set
    source_partition = set(G.nodes) - modified_cut_set - entry_partition

    return source_partition, list(modified_cut_set)


def get_source_partitions_reverse_hop_inequality(G, cut_set):
    # Find the set of nodes in G that do not contain the entrance cell after removing nodes in cut_set
    # Remove the nodes in cut_set from G
    G_copy = G.copy()
    G_copy.remove_nodes_from(cut_set)

    source_partitions = []
    modified_cut_sets = []

    # Convert it into an undirected graph
    G_copy = G_copy.to_undirected()

    # Partition the nodes in G_copy and find the component(s) that do not contain the entrance cell
    for partition in list(nx.connected_components(G_copy)):
        if config.entry_drive_field not in partition:
            source_partitions.append(partition)

    # Find the immediate neighbors of the source partition that are not in the source partition
    for source_partition in source_partitions:
        neighbors = set()
        for node in source_partition:
            neighbors.update(set(G.neighbors(node)))
        modified_cut_sets.append(list(neighbors - source_partition))

    return source_partitions, modified_cut_sets


def get_augmented_lhs_vertex_version(i, j, source_partition, cut_set,
                                     valid_park0_matrix, valid_park90_matrix,
                                     valid_drive_matrix):
    park0_cells = []
    if valid_park0_matrix[i, j]:
        for k, l in get_park0_fields_containing_cell(i, j, valid_park0_matrix):
            if (k, l) in source_partition:
                # Check if all neighbors of (k, l) also belong to the source partition
                left_neighbors, right_neighbors = get_neighbors_of_park0_field(
                    k, l, valid_drive_matrix)
                if all([n in source_partition.union(set(cut_set)) for n in
                        left_neighbors + right_neighbors]):
                    park0_cells.append((k, l))
    park90_cells = []
    if valid_park90_matrix[i, j]:
        # park90_cells.append((i, j))
        for k, l in get_park90_fields_containing_cell(i, j,
                                                      valid_park90_matrix):
            if (k, l) in source_partition:
                # Check if all neighbors of (k, l) also belong to the source partition
                top_neighbors, bottom_neighbors = get_neighbors_of_park90_field(
                    k, l, valid_drive_matrix)
                if all([n in source_partition.union(set(cut_set)) for n in
                        top_neighbors + bottom_neighbors]):
                    park90_cells.append((k, l))

    return park0_cells, park90_cells


def get_augmented_lhs_edge_version(i, j, source_partition, valid_park0_matrix,
                                   valid_park90_matrix, valid_drive_matrix):
    park0_cells = []
    if valid_park0_matrix[i, j]:
        for k, l in get_park0_fields_containing_cell(i, j, valid_park0_matrix):
            if (k, l) in source_partition:
                # Check if all neighbors of (k, l) also belong to the source partition
                left_neighbors, right_neighbors = get_neighbors_of_park0_field(
                    k, l, valid_drive_matrix)
                if all([n in source_partition for n in
                        left_neighbors + right_neighbors]):
                    park0_cells.append((k, l))
    park90_cells = []
    if valid_park90_matrix[i, j]:
        # park90_cells.append((i, j))
        for k, l in get_park90_fields_containing_cell(i, j,
                                                      valid_park90_matrix):
            if (k, l) in source_partition:
                # Check if all neighbors of (k, l) also belong to the source partition
                top_neighbors, bottom_neighbors = get_neighbors_of_park90_field(
                    k, l, valid_drive_matrix)
                if all([n in source_partition for n in
                        top_neighbors + bottom_neighbors]):
                    park90_cells.append((k, l))

    return park0_cells, park90_cells
