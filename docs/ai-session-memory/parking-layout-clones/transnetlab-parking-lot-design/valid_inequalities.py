import random
import cplex
from cplex.callbacks import LazyConstraintCallback
import matplotlib.pyplot as plt
from grid_utils import *
from variables import *
from variables import *
import config
import sys
import traceback


class RejectDisconnectedSolution(LazyConstraintCallback):
    def __init__(self, G, drive_variables, drive_variable_index_map,
                 park0_variables,
                 park90_variables, park0_variable_index_map,
                 park90_variable_index_map, valid_park0_matrix,
                 valid_park90_matrix, valid_drive_matrix):
        self.G = G
        self.G_drive = nx.DiGraph()
        self.G_contracted = nx.DiGraph()
        self.super_source = None
        self.super_destination = None
        self.drive_variables = drive_variables
        self.park0_variables = park0_variables
        self.park90_variables = park90_variables
        self.drive_variable_index_map = drive_variable_index_map
        self.park0_variable_index_map = park0_variable_index_map
        self.park90_variable_index_map = park90_variable_index_map
        self.valid_park0_matrix = valid_park0_matrix
        self.valid_park90_matrix = valid_park90_matrix
        self.valid_drive_matrix = valid_drive_matrix
        self.num_callback_calls = 0
        self.num_separation_cuts = 0
        self.num_rejection_cuts = 0

    def get_relaxation_point(self, context):
        # Write the above function such that it prints as a matrix
        for i in range(config.num_rows):
            for j in range(config.num_cols):
                if (i, j) in self.drive_variable_index_map:
                    print(context.get_relaxation_point(self.drive_variables[
                                                           self.drive_variable_index_map[
                                                               (i, j)]]),
                          end=" ")
                else:
                    print(0, end=" ")
            print()

        # Repeat the above steps for park0 and park90 variables
        for i in range(config.num_rows):
            for j in range(config.num_cols):
                if (i, j) in self.park0_variable_index_map:
                    print(context.get_relaxation_point(self.park0_variables[
                                                           self.park0_variable_index_map[
                                                               (i, j)]]),
                          end=" ")
                else:
                    print(0, end=" ")
            print()

        for i in range(config.num_rows):
            for j in range(config.num_cols):
                if (i, j) in self.park90_variable_index_map:
                    print(context.get_relaxation_point(self.park90_variables[
                                                           self.park90_variable_index_map[
                                                               (i, j)]]),
                          end=" ")
                else:
                    print(0, end=" ")
            print()

    def add_min_cut_connectivity_cut(self, context):
        drive_nodes = [(i, j) for i, j in self.G.nodes() if
                       context.get_candidate_point(
                           self.drive_variables[self.drive_variable_index_map[
                               (i, j)]]) > 1 - config.INT_TOLERANCE]

        self.G_drive = self.G.subgraph(drive_nodes)
        drive_components = list(nx.strongly_connected_components(self.G_drive))

        if len(drive_components) > 1:
            # Set the component in drive components which has
            # config.entry_drive_field as destination component
            # Delete this from the list of drive components
            source_components = []
            destination_component = None
            for component in drive_components:
                if config.entry_drive_field in component:
                    destination_component = component
                    self.super_destination = config.entry_drive_field
                    # drive_components.remove(component)
                else:
                    source_components.append(component)

            internal_callback_count = 0
            for source_component in source_components:
                self.G_contracted = self.G.copy()
                source_component_list = list(source_component)
                self.super_source = source_component_list[0]

                # Contract all nodes in the source component
                for source_node in source_component_list[1:]:
                    nx.contracted_nodes(self.G_contracted,
                                        source_component_list[0], source_node,
                                        copy=False)

                # Remove self loop if it exists
                if self.G_contracted.has_edge(self.super_source,
                                              self.super_source):
                    self.G_contracted.remove_edge(self.super_source,
                                                  self.super_source)

                # Contract all nodes in the destination component and other components
                nodes_in_other_components = set(
                    node for component in source_components if
                    component != source_component for node in component)
                for destination_node in destination_component | nodes_in_other_components:
                    if destination_node != config.entry_drive_field:
                        nx.contracted_nodes(self.G_contracted,
                                            self.super_destination,
                                            destination_node, copy=False)

                # Remove self loop if it exists
                if self.G_contracted.has_edge(self.super_destination,
                                              self.super_destination):
                    self.G_contracted.remove_edge(self.super_destination,
                                                  self.super_destination)

                minimum_node_cut = nx.minimum_node_cut(self.G_contracted,
                                                       self.super_source,
                                                       self.super_destination)
                min_cut_expr = [get_drive_var(k, l) for k, l in
                                minimum_node_cut]
                source_partition, minimum_node_cut = get_source_partition_hop_inequality(
                    self.G, list(minimum_node_cut))

                for source in source_component:
                    self.num_rejection_cuts += 1
                    park0_cells, park90_cells = get_augmented_lhs_vertex_version(
                        source[0], source[1], source_partition,
                        minimum_node_cut,
                        self.valid_park0_matrix,
                        self.valid_park90_matrix,
                        self.valid_drive_matrix)

                    lhs = [get_drive_var(source[0], source[1])]
                    lhs += [get_park0_var(k, l) for k, l in park0_cells]
                    lhs += [get_park90_var(k, l) for k, l in park90_cells]

                    context.reject_candidate(
                        constraints=[[min_cut_expr + lhs,
                                      [-1] * len(min_cut_expr) + [1] * len(
                                          lhs)]],
                        senses="L",
                        rhs=[0])

    def should_add_user_cuts(self, context):
        node_count = context.get_int_info(context.info.node_count)
        return node_count % 200000 == 0

    def invoke(self, context):
        # Implements the required invoke method.
        #
        # This is the method that we have to implement to fulfill the
        # generic callback contract. CPLEX will call this method during
        # the solution process at the places that we asked for.

        try:
            if context.in_candidate():
                self.add_min_cut_connectivity_cut(context)
            elif context.in_relaxation() and self.should_add_user_cuts(context):
                print("Printing LP solution values")
                self.get_relaxation_point(context)
                # print(context.get_int_info(context.info.time))
        except:
            info = sys.exc_info()
            print('#### Exception in callback: ', info[0])
            print('####                        ', info[1])
            print('####                        ', info[2])
            traceback.print_tb(info[2], file=sys.stdout)
            raise


class RejectDisconnectedSolutionOneWay(LazyConstraintCallback):
    def __init__(self, G, drive_variables, drive_variable_index_map,
                 park0_variables, park90_variables,
                 count_variables, park0_variable_index_map,
                 park90_variable_index_map,
                 lane_direction_variable_index_map, valid_park0_matrix,
                 valid_park90_matrix, valid_drive_matrix):
        self.G = G
        self.G_drive = nx.DiGraph()
        self.G_augmented = nx.DiGraph()
        self.super_drive = None
        self.super_entry = None
        self.drive_variables = drive_variables
        self.park0_variables = park0_variables
        self.park90_variables = park90_variables
        self.count_variables = count_variables
        self.drive_variable_index_map = drive_variable_index_map
        self.park0_variable_index_map = park0_variable_index_map
        self.park90_variable_index_map = park90_variable_index_map
        self.lane_direction_variable_index_map = lane_direction_variable_index_map
        self.valid_park0_matrix = valid_park0_matrix
        self.valid_park90_matrix = valid_park90_matrix
        self.valid_drive_matrix = valid_drive_matrix
        self.num_callback_calls = 0
        self.num_separation_cuts = 0
        self.num_rejection_cuts = 0
        self.num_grid_edges = G.number_of_edges()

    def add_min_cut_connectivity_cut(self, context):
        drive_nodes = [(i, j) for i, j in self.G.nodes() if
                       context.get_candidate_point(
                           self.drive_variables[self.drive_variable_index_map[
                               (i, j)]]) > 1 - config.INT_TOLERANCE]

        drive_edges = [((i, j), (k, l)) for (i, j), (k, l) in self.G.edges() if
                       context.get_candidate_point(
                           self.count_variables[
                               self.lane_direction_variable_index_map[
                                   (i, j, k, l)]]) > 1 - config.INT_TOLERANCE]

        # Add to G_drive edges belonging to drive_edges
        self.G_drive = nx.DiGraph()
        self.G_drive.add_nodes_from(drive_nodes)
        self.G_drive.add_edges_from(drive_edges)

        # Find all nodes that can be connected to the entry driving field
        entry_component = [node for node in self.G_drive.nodes() if
                           nx.has_path(self.G_drive, node,
                                       config.entry_drive_field)]

        if len(entry_component) != len(drive_nodes):
            # Constraints for the entrance
            # Select all nodes that are in G_drive that are not part of the source_nodes and contract them
            drive_component = [node for node in self.G_drive.nodes() if
                               node not in entry_component]
            self.G_augmented = self.G.copy()

            # Create a new node for super source and super destination in G_augmented
            self.super_entry = (-1, -1)
            self.super_drive = (-2, -2)

            self.G_augmented.add_node(self.super_entry, pos=(-1, 1), label="SS")
            self.G_augmented.add_node(self.super_drive, pos=(-2, 2), label="SD")

            # Assign weights of 1 to all edges in G_augmented
            for u, v in self.G_augmented.edges():
                self.G_augmented[u][v]['weight'] = 1

            # Assign weights of 1 to all edges and high weight to drive_edges in G_augmented
            for u, v in self.G_augmented.edges():
                self.G_augmented[u][v]['weight'] = self.num_grid_edges if (u,
                                                                           v) in drive_edges else 1

            # Add edges between the nodes in the graph and super drive and super entry nodes
            self.G_augmented.add_edges_from(
                (self.super_drive, node, {'weight': self.num_grid_edges}) for
                node in drive_component)
            self.G_augmented.add_edges_from(
                (node, self.super_entry, {'weight': self.num_grid_edges}) for
                node in entry_component)

            # Find min edge cut between super source and super destination
            cut_value, partition = nx.minimum_cut(self.G_augmented,
                                                  self.super_drive,
                                                  self.super_entry,
                                                  capacity='weight')

            if cut_value >= self.num_grid_edges:
                raise Exception(
                    "Cut value is greater than the number of edges in the grid")

            min_edge_cut = [(u, v) for u, v in self.G_augmented.edges() if
                            u in partition[0] and v in partition[1]]
            min_cut_expr = [get_lane_direction_var(i, j, k, l) for
                            (i, j), (k, l) in min_edge_cut]

            for node in drive_component:
                self.num_rejection_cuts += 1
                park0_cells, park90_cells = get_augmented_lhs_edge_version(
                    node[0], node[1], partition[0],
                    self.valid_park0_matrix,
                    self.valid_park90_matrix,
                    self.valid_drive_matrix)
                lhs = [get_drive_var(node[0], node[1])]
                lhs += [get_park0_var(k, l) for k, l in park0_cells]
                lhs += [get_park90_var(k, l) for k, l in park90_cells]

                context.reject_candidate(
                    constraints=[[min_cut_expr + lhs,
                                  [-1] * len(min_cut_expr) + [1] * len(lhs)]],
                    senses="L",
                    rhs=[0])

        # Repeat the process for the exit drive field
        exit_component = [node for node in self.G_drive.nodes() if
                          nx.has_path(self.G_drive, config.exit_drive_field,
                                      node)]

        if len(exit_component) != len(drive_nodes):
            # Constraints for the entrance
            # Select all nodes that are in G_drive that are not part of the source_nodes and contract them
            drive_component = [node for node in self.G_drive.nodes() if
                               node not in exit_component]
            self.G_augmented = self.G.copy()

            # Create a new node for super source and super destination in G_augmented
            self.super_exit = (-1, -1)
            self.super_drive = (-2, -2)

            self.G_augmented.add_node(self.super_exit, pos=(-1, 1), label="SS")
            self.G_augmented.add_node(self.super_drive, pos=(-2, 2), label="SD")

            # Assign weights of 1 to all edges in G_contracted
            for u, v in self.G_augmented.edges():
                self.G_augmented[u][v]['weight'] = 1

            # Assign weights to edges in G_augmented
            for u, v in self.G_augmented.edges():
                self.G_augmented[u][v]['weight'] = self.num_grid_edges if (u,
                                                                           v) in drive_edges else 1

            # Add edges from super source to source component
            self.G_augmented.add_edges_from(
                (node, self.super_drive, {'weight': self.num_grid_edges}) for
                node in drive_component)

            # Add edges from destination component to super destination
            self.G_augmented.add_edges_from(
                (self.super_exit, node, {'weight': self.num_grid_edges}) for
                node in exit_component)

            # Find min edge cut between super source and super destination
            cut_value, partition = nx.minimum_cut(self.G_augmented,
                                                  self.super_exit,
                                                  self.super_drive,
                                                  capacity='weight')

            if cut_value >= self.num_grid_edges:
                raise Exception(
                    "Cut value is greater than the number of edges in the grid")

            min_edge_cut = [(u, v) for u, v in self.G_augmented.edges() if
                            u in partition[0] and v in partition[1]]
            min_cut_expr = [get_lane_direction_var(i, j, k, l) for
                            (i, j), (k, l) in min_edge_cut]

            if cut_value >= self.num_grid_edges:
                raise Exception(
                    "Cut value is greater than the number of edges in the grid")

            for node in drive_component:
                self.num_rejection_cuts += 1
                park0_cells, park90_cells = get_augmented_lhs_edge_version(
                    node[0], node[1], partition[1],
                    self.valid_park0_matrix,
                    self.valid_park90_matrix,
                    self.valid_drive_matrix)
                lhs = [get_drive_var(node[0], node[1])]
                lhs += [get_park0_var(k, l) for k, l in park0_cells]
                lhs += [get_park90_var(k, l) for k, l in park90_cells]

                context.reject_candidate(
                    constraints=[[min_cut_expr + lhs,
                                  [-1] * len(min_cut_expr) + [1] * len(lhs)]],
                    senses="L",
                    rhs=[0])

    def invoke(self, context):
        # Implements the required invoke method.
        #
        # This is the method that we have to implement to fulfill the
        # generic callback contract. CPLEX will call this method during
        # the solution process at the places that we asked for.

        try:
            if context.in_candidate():
                self.add_min_cut_connectivity_cut(context)
        except:
            info = sys.exc_info()
            print('#### Exception in callback: ', info[0])
            print('####                        ', info[1])
            print('####                        ', info[2])
            traceback.print_tb(info[2], file=sys.stdout)
            raise


def add_hop_inequalities(problem, G, valid_drive_fields, valid_park0_matrix,
                         valid_park90_matrix, valid_drive_matrix):
    """This function adds the hop connectivity cuts to the problem.

    Parameters:
        problem (Cplex) : The Cplex problem to which the cuts are added
        G (Graph) : The grid NetworkX graph
        valid_drive_fields (list): List of valid driving fields
        valid_park0_matrix (numpy array): Matrix of valid park0 fields
        valid_park90_matrix (numpy array): Matrix of valid park90 fields
        valid_drive_matrix (numpy array): Matrix of valid drive fields

    Returns:
        None
    """
    print("--Adding hop connectivity inequalities")
    random_cell = random.choice(
        valid_drive_fields)  # Pick a random valid driving field for visualization

    for (i, j) in valid_drive_fields:
        if (i, j) == config.entry_drive_field:
            continue

        hop_limit = nx.shortest_path_length(G, (i, j), config.entry_drive_field)
        previous_hop_nodes = set()  # initialize an empty set for the previous hop's nodes

        for hop in range(1, hop_limit):
            current_hop_nodes = set((k, l) for k, l in
                                    nx.ego_graph(G, (i, j), radius=hop,
                                                 center=False).nodes()
                                    if (k, l) in valid_drive_fields)
            cut_set = list(current_hop_nodes - previous_hop_nodes)
            previous_hop_nodes = current_hop_nodes  # update previous_hop_nodes for the next iteration

            source_partition, cut_set = get_source_partition_hop_inequality(G,
                                                                            cut_set)
            cut_expr = [get_drive_var(k, l) for k, l in cut_set]

            if len(cut_expr) == 0:
                continue

            park0_cells, park90_cells = get_augmented_lhs_vertex_version(i, j,
                                                                         source_partition,
                                                                         cut_set,
                                                                         valid_park0_matrix,
                                                                         valid_park90_matrix,
                                                                         valid_drive_matrix)
            lhs = [get_drive_var(i, j)]
            lhs += [get_park0_var(k, l) for k, l in park0_cells]
            lhs += [get_park90_var(k, l) for k, l in park90_cells]

            if hop <= config.HOP_THRESHOLD or len(
                    cut_expr) <= config.CUT_SIZE_THRESHOLD:
                problem.linear_constraints.add(
                    lin_expr=[[lhs + cut_expr,
                               [1] * len(lhs) + [-1] * len(cut_expr)]],
                    senses="L",
                    rhs=[0],
                    names=[f"Hop{hop}Neighbor({i},{j})"])
            else:
                problem.linear_constraints.advanced.add_lazy_constraints(
                    # problem.linear_constraints.add(
                    lin_expr=[[lhs + cut_expr,
                               [1] * len(lhs) + [-1] * len(cut_expr)]],
                    senses="L",
                    rhs=[0],
                    names=[f"Hop{hop}Neighbor({i},{j})"])


def add_reverse_hop_inequalities(problem, G, valid_drive_fields,
                                 valid_park0_matrix, valid_park90_matrix,
                                 valid_drive_matrix):
    print("--Adding reverse hop connectivity inequalities")
    # Define a dictionary of the min hop distances from every drive field to the entrance
    hop_distances = nx.single_source_shortest_path_length(G,
                                                          config.entry_drive_field)

    max_hop = max(hop_distances.values())  # finds the maximum hop distance
    if max_hop <= 1:
        return

    # Create a dictionary of nodes with keys as hop distance and values as the nodes at that hop distance
    nodes_at_hop_distance = {hop: [] for hop in range(1, max_hop + 1)}
    for (i, j) in valid_drive_fields:
        try:
            if (i, j) != config.entry_drive_field:
                nodes_at_hop_distance[hop_distances[(i, j)]].append((i, j))
        except KeyError:
            print("Key error in reverse hop inequalities for node", (i, j))

    random_cell = random.choice(
        valid_drive_fields)  # Pick a random valid driving field for visualization
    for hop in range(1, max_hop):
        # Find all cells that are hop distance away from the entrance
        # cut_set = [(k, l) for k, l in hop_distances.keys() if hop_distances[(k, l)] == hop]
        cut_set = nodes_at_hop_distance[hop]
        source_partitions, cut_sets = get_source_partitions_reverse_hop_inequality(
            G, cut_set)
        for index in range(len(cut_sets)):
            source_partition = source_partitions[index]
            cut_set = cut_sets[index]
            cut_expr = [get_drive_var(k, l) for k, l in cut_set]

            if len(cut_expr) == 0:
                continue

            for i, j in source_partition:
                park0_cells, park90_cells = get_augmented_lhs_vertex_version(i,
                                                                             j,
                                                                             source_partition,
                                                                             cut_set,
                                                                             valid_park0_matrix,
                                                                             valid_park90_matrix,
                                                                             valid_drive_matrix)
                lhs = [get_drive_var(i, j)]
                lhs += [get_park0_var(k, l) for k, l in park0_cells]
                lhs += [get_park90_var(k, l) for k, l in park90_cells]

                if hop <= config.HOP_THRESHOLD or len(
                        cut_expr) <= config.CUT_SIZE_THRESHOLD:
                    problem.linear_constraints.add(
                        lin_expr=[[lhs + cut_expr,
                                   [1] * len(lhs) + [-1] * len(cut_expr)]],
                        senses="L",
                        rhs=[0],
                        names=[f"ReverseHop{hop}Neighbor({i},{j})"])
                else:
                    problem.linear_constraints.advanced.add_lazy_constraints(
                        # problem.linear_constraints.add(
                        lin_expr=[[lhs + cut_expr,
                                   [1] * len(lhs) + [-1] * len(cut_expr)]],
                        senses="L",
                        rhs=[0],
                        names=[f"ReverseHop{hop}Neighbor({i},{j})"])


def avoid_dead_ends_using_drive_variables(problem, G, valid_drive_fields):
    """Add constraints to avoid dead ends in the grid. A dead end is a cell that has only one neighbor.

    Parameters:
        problem (Cplex): The CPLEX problem object.
        G (NetworkX graph): Graph of the grid.
        valid_drive_fields (list): List of valid driving fields.

    Returns:
        None
    """
    print("--Adding dead end avoidance constraints using drive variables")
    for i, j in valid_drive_fields:
        if (i, j) == config.entry_drive_field or (
        i, j) == config.exit_drive_field:
            continue

        neighbors = list(G.neighbors((i, j)))
        if len(neighbors) == 1:
            # If a cell has only one neighbor, the drive variable must be set to 0
            problem.linear_constraints.add(
                lin_expr=[[[get_drive_var(i, j)], [1]]],
                senses="E",
                rhs=[0],
                names=[f"DeadEndSingleNeighbor({i},{j})"])
        else:
            neighbor_expr = [get_drive_var(k, l) for k, l in neighbors]
            # problem.linear_constraints.advanced.add_lazy_constraints(
            problem.linear_constraints.add(
                lin_expr=[[neighbor_expr + [get_drive_var(i, j)],
                           [1] * len(neighbors) + [-2]]],
                senses="G",
                rhs=[0],
                names=[f"DeadEndDriveVariables({i},{j})"])


def avoid_dead_ends_using_lane_direction_variables(problem, G,
                                                   valid_drive_fields):
    """This function relates the lane direction variables to the drive field variables. This function is used only
    for the one-way model.

    Parameters:
        problem (Cplex): The CPLEX problem object.
        G (NetworkX graph): Graph of the grid.
        valid_drive_fields (list): List of valid driving fields.

    Returns:
        None
    """
    print("--Adding lane directionality and drive field constraints")
    # Ensure that there is at least one outgoing edge and one incoming edge for all active driving cells
    for i, j in valid_drive_fields:
        if (i, j) == config.entry_drive_field or (
        i, j) == config.exit_drive_field:
            continue

        in_flow = [get_lane_direction_var(k, l, i, j) for k, l in
                   G.neighbors((i, j))]
        out_flow = [get_lane_direction_var(i, j, k, l) for k, l in
                    G.neighbors((i, j))]
        if (i,
            j) != config.exit_drive_field:  # for every cell except the exit, at least one inflow needs to be 1
            # problem.linear_constraints.advanced.add_lazy_constraints(
            problem.linear_constraints.add(
                lin_expr=[[in_flow + [get_drive_var(i, j)],
                           [1] * len(in_flow) + [-1]]],
                senses="G",
                rhs=[0],
                names=[f"LaneDirectionInFlow({i},{j})"])
        if (i,
            j) != config.entry_drive_field:  # for every cell except the entry, at least one outflow needs to be 1
            # problem.linear_constraints.advanced.add_lazy_constraints(
            problem.linear_constraints.add(
                lin_expr=[[out_flow + [get_drive_var(i, j)],
                           [1] * len(out_flow) + [-1]]],
                senses="G",
                rhs=[0],
                names=[f"LaneDirectionOutFlow({i},{j})"])
