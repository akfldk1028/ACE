import cplex
from grid_utils import *
import networkx as nx
import itertools
import time
from variables import *
from constraints import *
from valid_inequalities import *
import config


def optimize_two_way_parking(G, problem, valid_park0_fields,
                             valid_park90_fields, valid_drive_fields,
                             valid_park0_matrix, valid_park90_matrix,
                             valid_drive_matrix):
    """Function to create variables and constraints and solve the perpendicular parking layout problem.

    Parameters:
        problem (Cplex): The Cplex problem to be solved
        G (networkx graph): The graph of the parking lot
        valid_park0_fields (list): List of valid park 0 fields
        valid_park90_fields (list): List of valid park 90 fields
        valid_drive_fields (list) : List of tuples which specify the valid drive fields in the grid
        valid_park0_matrix (numpy array): Matrix of valid park 0 fields
        valid_park90_matrix (numpy array): Matrix of valid park 90 fields
        valid_drive_matrix (numpy array): Matrix representing the valid driving fields.

    Returns:
        None
    """
    print("Running the parking lot optimization model for two-way lanes...")
    print("Creating variables...")
    # Add driving, parking, and flow variables
    park0_variables, park90_variables = set_park_variables(problem,
                                                           valid_park0_fields,
                                                           valid_park90_fields)
    drive_variables = set_drive_variables(problem, valid_drive_fields)
    if config.SOLVE_USING_FLOW_VARIABLES:
        entry_flow_variables = set_entry_flow_variables(problem, G)

    # Add constraints
    print("Adding constraints...")
    # Constraints for existing park and drive fields and for
    # the drive fields for the entry cells
    add_existing_park_field_constraint(problem, valid_park0_matrix,
                                       valid_park90_matrix)
    add_existing_drive_field_constraint(problem, valid_drive_matrix)
    add_entry_drive_field_constraint(problem, valid_drive_matrix)

    # Constraints to ensure connectivity between park and drive variables
    # and to ensure a single purpose for cells
    add_disaggregate_single_purpose_constraints(problem, valid_park0_matrix,
                                                valid_park90_matrix,
                                                valid_drive_matrix)
    add_park_accessibility_constraints(problem, valid_park0_fields,
                                       valid_park90_fields, valid_drive_matrix)

    if config.SOLVE_USING_FLOW_VARIABLES:
        # Constraints for connecting the drive variables using
        # directed flow variables
        add_entry_flow_conservation_constraints(problem, G, valid_drive_fields)

    # Add valid inequalities
    if config.INCLUDE_VALID_INEQUALITIES:
        print("Adding valid inequalities...")
        add_hop_inequalities(problem, G, valid_drive_fields, valid_park0_matrix,
                             valid_park90_matrix,
                             valid_drive_matrix)
        add_reverse_hop_inequalities(problem, G, valid_drive_fields,
                                     valid_park0_matrix,
                                     valid_park90_matrix, valid_drive_matrix)

    # Solve the model using CPLEX and write outputs to a file
    print("Solving the model...")
    if config.SOLVE_USING_FLOW_VARIABLES:
        problem.solve()
        problem.write(f"./{config.output_folder}/perpendicular.lp")
    else:  # solve using cutting planes
        # Create a map of 2D drive field indices to 1D drive field indices
        drive_variable_index_map = {}
        min_index = sys.maxsize  # set it to the largest int
        for i, j in valid_drive_fields:
            drive_variable_index_map[(i, j)] = problem.variables.get_indices(
                get_drive_var(i, j))
            min_index = min(min_index, drive_variable_index_map[(i, j)])

        # Subtract the minimum index from all indices to make them 0-based
        for key in drive_variable_index_map:
            drive_variable_index_map[key] -= min_index

        park0_variable_index_map = {}
        min_index = sys.maxsize
        for i, j in valid_park0_fields:
            park0_variable_index_map[(i, j)] = problem.variables.get_indices(
                get_park0_var(i, j))
            min_index = min(min_index, park0_variable_index_map[(i, j)])

        for key in park0_variable_index_map:
            park0_variable_index_map[key] -= min_index

        park90_variable_index_map = {}
        min_index = sys.maxsize
        for i, j in valid_park90_fields:
            park90_variable_index_map[(i, j)] = problem.variables.get_indices(
                get_park90_var(i, j))
            min_index = min(min_index, park90_variable_index_map[(i, j)])

        for key in park90_variable_index_map:
            park90_variable_index_map[key] -= min_index

        connectivity_cb = RejectDisconnectedSolution(G, drive_variables,
                                                     drive_variable_index_map,
                                                     park0_variables,
                                                     park90_variables,
                                                     park0_variable_index_map,
                                                     park90_variable_index_map,
                                                     valid_park0_matrix,
                                                     valid_park90_matrix,
                                                     valid_drive_matrix)
        contextmask = 0
        # contextmask |= cplex.callbacks.Context.id.relaxation
        contextmask |= cplex.callbacks.Context.id.candidate

        # If contextMask is not zero we add the callback.
        if contextmask:
            problem.set_callback(connectivity_cb, contextmask)

        problem.solve()

        config.num_rejection_cuts = connectivity_cb.num_rejection_cuts
        print("Number of rejection cuts added ",
              connectivity_cb.num_rejection_cuts)

        problem.write(f"./{config.output_folder}/perpendicular.lp")


def optimize_one_way_parking(G, problem, valid_park0_fields,
                             valid_park90_fields, valid_drive_fields,
                             valid_park0_matrix, valid_park90_matrix,
                             valid_drive_matrix):
    """Function to create variables and constraints and solve the perpendicular
    parking layout problem.

    Parameters:
        problem (Cplex): The Cplex problem to be solved
        G (networkx graph): The graph of the parking lot
        valid_park0_fields (list): List of valid park 0 fields
        valid_park90_fields (list): List of valid park 90 fields
        valid_drive_fields (list) : List of tuples which specify the valid drive fields in the grid
        valid_park0_matrix (numpy array): Matrix of valid park 0 fields
        valid_park90_matrix (numpy array): Matrix of valid park 90 fields
        valid_drive_matrix (numpy array): Matrix representing the valid driving fields.
        output_folder_name: name of folder to which output dtat is written

    Returns:
        None
    """
    print("Setting up the parking lot optimization model for one-way lanes using cutting planes...")

    # Add driving, parking, and flow variables
    park0_variables, park90_variables = set_park_variables(problem,
                                                           valid_park0_fields,
                                                           valid_park90_fields)
    drive_variables = set_drive_variables(problem, valid_drive_fields)
    lane_direction_variables = set_lane_direction_variables(problem, G)

    if config.SOLVE_USING_FLOW_VARIABLES:
        entry_flow_variables = set_entry_flow_variables(problem, G)
        exit_flow_variables = set_exit_flow_variables(problem, G)

    # Add constraints
    print("Adding constraints...")
    # Constraints for existing park and drive fields and for the drive
    # fields for the entry cells
    add_existing_park_field_constraint(problem, valid_park0_matrix,
                                       valid_park90_matrix)
    add_existing_drive_field_constraint(problem, valid_drive_matrix)
    add_entry_drive_field_constraint(problem, valid_drive_matrix)
    add_exit_drive_field_constraint(problem, valid_drive_matrix)

    # Constraints to ensure connectivity between park and drive variables
    # and to ensure a single purpose for cells
    add_disaggregate_single_purpose_constraints(problem, valid_park0_matrix,
                                                valid_park90_matrix,
                                                valid_drive_matrix)
    add_park_accessibility_constraints(problem, valid_park0_fields,
                                       valid_park90_fields, valid_drive_matrix)

    # Constraints for connecting lane direction variables and drive variables
    # and for activating lanes on one side
    add_one_way_direction_constraints(problem, G)
    add_lane_direction_drive_bounds(problem, G)

    if config.SOLVE_USING_FLOW_VARIABLES:
        # Constraints for connecting the drive variables
        # using directed flow variables
        add_entry_flow_conservation_constraints(problem, G, valid_drive_fields)
        add_exit_flow_conservation_constraints(problem, G, valid_drive_fields)

        # Constraints for connecting lane direction variables
        # and the flow variables
        add_lane_direction_flow_bounds(problem, G)

    # Add valid inequalities
    if config.INCLUDE_VALID_INEQUALITIES:
        print("Adding valid inequalities...")
        avoid_dead_ends_using_drive_variables(problem, G, valid_drive_fields)
        avoid_dead_ends_using_lane_direction_variables(problem, G,
                                                       valid_drive_fields)
        add_hop_inequalities(problem, G, valid_drive_fields, valid_park0_matrix,
                             valid_park90_matrix,
                             valid_drive_matrix)
        add_reverse_hop_inequalities(problem, G, valid_drive_fields,
                                     valid_park0_matrix,
                                     valid_park90_matrix, valid_drive_matrix)

    # Solve the model using CPLEX and write outputs to a file
    print("Solving the model...")
    if config.SOLVE_USING_FLOW_VARIABLES:
        problem.solve()
        problem.write(f"./{config.output_folder}/perpendicular.lp")
    else:
        # Create a map of 2D drive field indices to 1D drive field indices
        drive_variable_index_map = {}
        # Set to the largest int
        min_index = sys.maxsize
        for i, j in valid_drive_fields:
            drive_variable_index_map[(i, j)] = problem.variables.get_indices(
                get_drive_var(i, j))
            min_index = min(min_index, drive_variable_index_map[(i, j)])

        # Subtract the minimum index from all indices to make them 0-based
        for key in drive_variable_index_map:
            drive_variable_index_map[key] -= min_index

        park0_variable_index_map = {}
        min_index = sys.maxsize
        for i, j in valid_park0_fields:
            park0_variable_index_map[(i, j)] = problem.variables.get_indices(
                get_park0_var(i, j))
            min_index = min(min_index, park0_variable_index_map[(i, j)])

        for key in park0_variable_index_map:
            park0_variable_index_map[key] -= min_index

        park90_variable_index_map = {}
        min_index = sys.maxsize
        for i, j in valid_park90_fields:
            park90_variable_index_map[(i, j)] = problem.variables.get_indices(
                get_park90_var(i, j))
            min_index = min(min_index, park90_variable_index_map[(i, j)])

        for key in park90_variable_index_map:
            park90_variable_index_map[key] -= min_index

        lane_direction_variable_index_map = {}
        min_index = sys.maxsize
        for (i, j), (k, l) in G.edges:
            lane_direction_variable_index_map[
                (i, j, k, l)] = problem.variables.get_indices(
                get_lane_direction_var(i, j, k, l))
            min_index = min(min_index,
                            lane_direction_variable_index_map[(i, j, k, l)])

        # Subtract the minimum index from all indices to make them 0-based
        for key in lane_direction_variable_index_map:
            lane_direction_variable_index_map[key] -= min_index

        connectivity_cb = RejectDisconnectedSolutionOneWay(G, drive_variables,
                                                           drive_variable_index_map,
                                                           park0_variables,
                                                           park90_variables,
                                                           lane_direction_variables,
                                                           park0_variable_index_map,
                                                           park90_variable_index_map,
                                                           lane_direction_variable_index_map,
                                                           valid_park0_matrix,
                                                           valid_park90_matrix,
                                                           valid_drive_matrix)
        contextmask = 0
        # contextmask |= cplex.callbacks.Context.id.relaxation
        contextmask |= cplex.callbacks.Context.id.candidate

        # If contextMask is not zero we add the callback.
        if contextmask:
            problem.set_callback(connectivity_cb, contextmask)

        problem.set_error_stream(None)
        problem.solve()

        config.num_rejection_cuts = connectivity_cb.num_rejection_cuts
        print("Number of rejection cuts added ",
              connectivity_cb.num_rejection_cuts)

        problem.write(f"{config.output_folder}/perpendicular_oneway.lp")

