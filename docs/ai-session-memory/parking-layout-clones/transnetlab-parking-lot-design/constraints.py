from cplex import Cplex
from grid_utils import *
from variables import *
import config


def add_existing_park_field_constraint(problem, valid_park0_matrix,
                                       valid_park90_matrix):
    """Constraint to ensure that variables associated with existing perpendicular parking fields are set to 1.
    This constraint can also help debug code.

    Parameters:
        problem (Cplex): The CPLEX problem object.
        valid_park0_matrix (numpy array): Matrix representing the valid 0 degree parking fields.
        valid_park90_matrix (numpy array): Matrix representing the valid 90 degree parking fields.

    Returns:
        None
    """
    # Constraint to set the park variable values of 0 degree parking fields to 1.
    print("--Adding constraints for existing parking fields (if any)")
    if not np.all([valid_park0_matrix[index] for index in
                   config.existing_park0_fields]):
        raise ValueError("Invalid existing park0 fields")
    else:
        if len(config.existing_park0_fields) > 0:
            problem.linear_constraints.add(
                lin_expr=[[[get_park0_var(i, j) for (i, j) in
                            config.existing_park0_fields],
                           [1] * len(config.existing_park0_fields)]],
                senses="E",
                rhs=[len(config.existing_park0_fields)],
                names=["ExistingPark0Fields"])

    # Constraint to set the park variable values of 90 degree parking fields to 1.
    if not np.all([valid_park90_matrix[index] for index in
                   config.existing_park90_fields]):
        raise ValueError("Invalid existing park90 fields")
    else:
        if len(config.existing_park90_fields) > 0:
            problem.linear_constraints.add(
                lin_expr=[[[get_park90_var(i, j) for (i, j) in
                            config.existing_park90_fields],
                           [1] * len(config.existing_park90_fields)]],
                senses="E",
                rhs=[len(config.existing_park90_fields)],
                names=["ExistingPark90Fields"])


def add_existing_drive_field_constraint(problem, valid_drive_matrix):
    """Constraint to ensure that variables associated with existing drive fields are set to 1.

    Parameters:
        problem (Cplex): The CPLEX problem object.
        valid_drive_matrix (numpy array): Matrix representing the valid driving fields.

    Returns:
        None
    """
    if not np.all([valid_drive_matrix[index] for index in
                   config.existing_drive_fields]):
        raise ValueError("Invalid existing drive fields")
    else:
        print("--Adding constraints for existing driving fields (if any)")
        if len(config.existing_drive_fields) > 0:
            problem.linear_constraints.add(
                lin_expr=[[[get_drive_var(i, j) for (i, j) in
                            config.existing_drive_fields],
                           [1] * len(config.existing_drive_fields)]],
                senses="E",
                rhs=[len(config.existing_drive_fields)],
                names=["ExistingDriveFields"])


def add_entry_drive_field_constraint(problem, valid_drive_matrix):
    """Adds a constraint to assign a driving field at the entrance cell.

    Parameters:
        problem (Cplex): The CPLEX problem object.
        valid_drive_matrix (numpy array): Matrix representing the valid driving fields.

    Returns:
        None
    """
    if valid_drive_matrix[
        config.entry_drive_field[0], config.entry_drive_field[1]]:
        print("--Adding entry drive field constraint")
        problem.linear_constraints.add(
            lin_expr=[[[get_drive_var(config.entry_drive_field[0],
                                      config.entry_drive_field[1])], [1]]],
            senses="E",
            rhs=[1],
            names=[f"EntryDriveField"])
    else:
        raise ValueError("Invalid entry drive field")


def add_exit_drive_field_constraint(problem, valid_drive_matrix):
    """Adds the constraint to assign a driving field at the exit. This is used only for the one-way model.

    Parameters:
        problem (Cplex): The CPLEX problem object.
        valid_drive_matrix (numpy array): Matrix representing the valid driving fields.

    Returns:
        None
    """
    if valid_drive_matrix[
        config.exit_drive_field[0], config.exit_drive_field[1]]:
        print("--Adding exit drive field constraint")
        problem.linear_constraints.add(
            lin_expr=[[[get_drive_var(config.exit_drive_field[0],
                                      config.exit_drive_field[1])], [1]]],
            senses="E",
            rhs=[1],
            names=[f"ExitDriveField"])
    else:
        raise ValueError("Invalid exit drive field")


def add_aggregate_single_purpose_constraints(problem, valid_park0_matrix,
                                             valid_park90_matrix,
                                             valid_drive_matrix):
    """These constraints ensure that every non-blocked cell in the grid can only have a single purpose, i.e., either
    park, drive or be empty. The drive variables are aggregated and added as a single constraint for each cell.

    Parameters:
        problem (Cplex): The CPLEX problem object.
        valid_park0_matrix (numpy array): Matrix of 0s and 1s representing valid 0 degree park fields.
        valid_park90_matrix (numpy array): Matrix of 0s and 1s representing valid 90 degree park fields.
        valid_drive_matrix (numpy array): Matrix of 0s and 1s representing valid drive fields.

    Returns:
        None
    """
    # Each cell can have only one purpose -- parking, driving, blocked/empty
    print("--Adding aggregate single purpose constraints")
    for i, j in itertools.product(range(config.num_rows),
                                  range(config.num_cols)):
        if (i, j) not in config.blocked_cells:
            # Add parking expressions of variables which use cell (i, j)
            park_expr = []
            park_expr += [get_park0_var(k, l) for (k, l) in
                          get_park0_fields_containing_cell(i, j,
                                                           valid_park0_matrix)]
            park_expr += [get_park90_var(k, l) for (k, l) in
                          get_park90_fields_containing_cell(i, j,
                                                            valid_park90_matrix)]

            # Add driving expressions of variables which use cell (i, j)
            drive_expr = [get_drive_var(k, l) for (k, l) in
                          get_drive_fields_containing_cell(i, j,
                                                           valid_drive_matrix)]

            if len(drive_expr) != 0:
                lin_expr = [[park_expr + drive_expr, [1] * len(park_expr) + [
                    1.0 / len(drive_expr)] * len(drive_expr)]]
            else:
                lin_expr = [[park_expr, [1] * len(park_expr)]]

            # Add the aggregated constraint
            problem.linear_constraints.add(
                lin_expr=lin_expr,
                senses="L",
                rhs=[1],
                names=[f"AggregatedOnePurpose({i},{j})"])


def add_disaggregate_single_purpose_constraints(problem, valid_park0_matrix,
                                                valid_park90_matrix,
                                                valid_drive_matrix):
    """These constraints ensure that every non-blocked cell in the grid can only
    have a single purpose: either park, drive or be empty.

    Parameters:
        problem (Cplex): The CPLEX problem object.
        valid_park0_matrix (numpy array): Matrix of 0s and 1s representing valid 0 degree park fields.
        valid_park90_matrix (numpy array): Matrix of 0s and 1s representing valid 90 degree park fields.
        valid_drive_matrix (numpy array): Matrix of 0s and 1s representing valid drive fields.

    Returns:
        None
    """
    # Each cell can have only one purpose -- parking, driving, blocked/empty
    print("--Adding disaggregated single purpose constraints")
    for i, j in itertools.product(range(config.num_rows),
                                  range(config.num_cols)):
        if (i, j) not in config.blocked_cells:
            # Add parking expressions of variables which use cell (i, j)
            park_expr = []
            park_expr += [get_park0_var(k, l) for (k, l) in
                          get_park0_fields_containing_cell(i, j,
                                                           valid_park0_matrix)]
            park_expr += [get_park90_var(k, l) for (k, l) in
                          get_park90_fields_containing_cell(i, j,
                                                            valid_park90_matrix)]

            # Add driving expressions of variables which use cell (i, j)
            drive_expr = [get_drive_var(k, l) for (k, l) in
                          get_drive_fields_containing_cell(i, j,
                                                           valid_drive_matrix)]

            if len(drive_expr) != 0:
                count = 0
                for drive_var in drive_expr:
                    problem.linear_constraints.add(
                        lin_expr=[[park_expr + [drive_var],
                                   [1] * len(park_expr) + [1]]],
                        senses="L",
                        rhs=[1],
                        names=[f"DisaggregatedOnePurpose({i},{j},{count})"])
                    count += 1
            else:
                problem.linear_constraints.add(
                    lin_expr=[[park_expr, [1] * len(park_expr)]],
                    senses="L",
                    rhs=[1],
                    names=[f"DisaggregatedOnePurpose({i},{j})"])


def add_park_accessibility_constraints(problem, valid_park0_fields,
                                       valid_park90_fields, valid_drive_matrix):
    """These constraints ensure that each parking field can be reached via at least one driving field neighbor.

    Parameters:
        problem (Cplex): The CPLEX problem object.
        valid_park0_fields (list): List of valid 0 degree parking fields.
        valid_park90_fields (list): List of valid 90 degree parking fields.
        valid_drive_matrix (numpy array): Matrix representing the valid driving fields.

    Returns:
        None
    """
    print("--Adding accessibility constraints for parking fields")
    for (i, j) in valid_park0_fields:
        left_neighbor, right_neighbor = get_neighbors_of_park0_field(i, j,
                                                                     valid_drive_matrix)
        drive_expr = [get_drive_var(k, l) for (k, l) in
                      left_neighbor + right_neighbor]
        problem.linear_constraints.add(
            lin_expr=[[[get_park0_var(i, j)] + drive_expr,
                       [1] + [-1] * len(drive_expr)]],
            senses="L",
            rhs=[0],
            names=[f"Park0DriveConnector({i},{j})"])

    for (i, j) in valid_park90_fields:
        top_neighbor, bottom_neighbor = get_neighbors_of_park90_field(i, j,
                                                                      valid_drive_matrix)
        drive_expr = [get_drive_var(k, l) for (k, l) in
                      top_neighbor + bottom_neighbor]
        problem.linear_constraints.add(
            lin_expr=[[[get_park90_var(i, j)] + drive_expr,
                       [1] + [-1] * len(drive_expr)]],
            senses="L",
            rhs=[0],
            names=[f"Park90DriveConnector({i},{j})"])


def add_entry_flow_conservation_constraints(problem, G, valid_drive_fields):
    """These constraints ensure that driving fields are connected to the entry fields.

    Parameters:
        problem (Cplex) : The Cplex problem to which the constraints are added.
        G (Graph) : The grid NetworkX graph.
        valid_drive_fields (list): List of valid driving fields.

    Returns:
        None
    """
    print("--Adding flow conservation constraints for entry-based flows")
    # Flow conservation to ensure that inflows are equal to the outflows
    for i, j in valid_drive_fields:
        if (i, j) == config.entry_drive_field:  # constraint at the entry
            # drive field
            total_flow = [get_drive_var(k, l) for (k, l) in valid_drive_fields]
            in_flow = [get_entry_flow_var(k, l, i, j) for k, l in
                       G.neighbors(config.entry_drive_field)]
            problem.linear_constraints.add(
                lin_expr=[[in_flow + total_flow,
                           [1] * len(in_flow) + [-1] * len(total_flow)]],
                senses="E",
                rhs=[-1],
                names=[f"EntryFlowConservation({i},{j})"])
        else:  # constraint at other drive fields
            in_flow = [get_entry_flow_var(k, l, i, j) for k, l in
                       G.neighbors((i, j))]
            out_flow = [get_entry_flow_var(i, j, k, l) for k, l in
                        G.neighbors((i, j))]
            problem.linear_constraints.add(
                lin_expr=[[in_flow + out_flow + [get_drive_var(i, j)],
                           [-1] * len(in_flow) + [1] * len(out_flow) + [-1]]],
                senses="E",
                rhs=[0],
                names=[f"EntryFlowConservation({i},{j})"])

    if not config.ARE_DRIVE_LANES_ONEWAY:
        # Connect flow variables with the drive variables
        for tail, head in G.edges():
            problem.linear_constraints.add(
                lin_expr=[
                    [[get_entry_flow_var(tail[0], tail[1], head[0], head[1]),
                      get_drive_var(tail[0], tail[1])],
                     [1, -len(G.nodes()) + 1]],
                    [[get_entry_flow_var(tail[0], tail[1], head[0], head[1]),
                      get_drive_var(head[0], head[1])],
                     [1, -len(G.nodes()) + 1]]],
                senses="LL",
                rhs=[0, 0],
                names=[
                    f"EntryFlowDriveTail({tail[0]},{tail[1]},{head[0]},{head[1]})",
                    f"EntryFlowDriveHead({tail[0]},{tail[1]},{head[0]},{head[1]})"])


def add_exit_flow_conservation_constraints(problem, G, valid_drive_fields):
    """These constraints ensure that driving fields are connected to the exit fields.

    Parameters:
        problem (Cplex) : The Cplex problem to which the constraints are added.
        G (Graph) : The grid NetworkX graph.
        valid_drive_fields (list): List of valid driving fields.

    Returns:
        None
    """
    print("--Adding flow conservation constraints for exit-based flows")
    for i, j in valid_drive_fields:
        if (
        i, j) == config.exit_drive_field:  # constraint at the exit drive field
            total_flow = [get_drive_var(k, l) for (k, l) in valid_drive_fields]
            out_flow = [get_exit_flow_var(i, j, k, l) for k, l in
                        G.neighbors(config.exit_drive_field)]
            problem.linear_constraints.add(
                lin_expr=[[out_flow + total_flow,
                           [-1] * len(out_flow) + [1] * len(total_flow)]],
                senses="E",
                rhs=[1],
                names=[f"ExitFlowConservation({i},{j})"])
        else:  # constraint at other drive fields
            in_flow = [get_exit_flow_var(k, l, i, j) for k, l in
                       G.neighbors((i, j))]
            out_flow = [get_exit_flow_var(i, j, k, l) for k, l in
                        G.neighbors((i, j))]
            problem.linear_constraints.add(
                lin_expr=[[out_flow + in_flow + [get_drive_var(i, j)],
                           [-1] * len(out_flow) + [1] * len(in_flow) + [-1]]],
                senses="E",
                rhs=[0],
                names=[f"ExitFlowConservation({i},{j})"])

    """
    if not config.ARE_DRIVE_LANES_ONEWAY:
        # Connect flow variables with the drive variables
        for tail, head in G.edges():
            problem.linear_constraints.add(
                lin_expr=[
                    [[get_exit_flow_var(tail[0], tail[1], head[0], head[1]), get_drive_var(tail[0], tail[1])],
                     [1, -len(G.nodes()) + 1]],
                    [[get_exit_flow_var(tail[0], tail[1], head[0], head[1]), get_drive_var(head[0], head[1])],
                     [1, -len(G.nodes()) + 1]]
                ],
                senses="LL",
                rhs=[0, 0],
                names=[f"ExitFlowDriveTail({tail[0]},{tail[1]},{head[0]},{head[1]})",
                       f"ExitFlowDriveHead({tail[0]},{tail[1]},{head[0]},{head[1]})"])
    """


def add_one_way_direction_constraints(problem, G):
    """Add constraints to ensure that the lane direction variables to make sure only one of the directions is active.

    Parameters:
        problem (Cplex): The CPLEX problem object.
        G (NetworkX graph): Graph of the grid.

    Returns:
        None
    """
    print("--Adding lane directionality constraints")
    for tail, head in G.edges():
        # At most one of the two directions can be set to 1
        problem.linear_constraints.add(
            lin_expr=[
                [[get_lane_direction_var(tail[0], tail[1], head[0], head[1]),
                  get_lane_direction_var(head[0], head[1], tail[0], tail[1])],
                 [1, 1]]],
            senses="L",
            rhs=[1],
            names=[f"LaneDirection({tail[0]},{tail[1]},{head[0]},{head[1]})"])


def add_lane_direction_drive_bounds(problem, G):
    """This function relates the lane direction variables to the drive field variables. This function is used only
    for the one-way model.

    Parameters:
        problem (Cplex): The CPLEX problem object.
        G (NetworkX graph): Graph of the grid.

    Returns:
        None
    """
    print("--Adding lane directionality and drive field bounds")
    # Set the direction variables to zero if they do not connect active driving fields
    for tail, head in G.edges():
        problem.linear_constraints.add(
            lin_expr=[[[get_lane_direction_var(tail[0], tail[1], head[0],
                                               head[1]),
                        get_drive_var(tail[0], tail[1])],
                       [1, -1]],
                      [[get_lane_direction_var(tail[0], tail[1], head[0],
                                               head[1]),
                        get_drive_var(head[0], head[1])],
                       [1, -1]]],
            senses="LL",
            rhs=[0, 0],
            names=[
                f"DirectionDriveTail({tail[0]},{tail[1]},{head[0]},{head[1]})",
                f"DirectionDriveHead({tail[0]},{tail[1]},{head[0]},{head[1]})"])


def add_lane_direction_flow_bounds(problem, G):
    """Add constraints to ensure that the lane direction variables are set to one if the entry or exit flow is positive.

    Parameters:
        problem (Cplex): The CPLEX problem object.
        G (NetworkX graph): Graph of the grid.

    Returns:
        None
    """
    print("--Adding lane directionality flow bounds")
    for tail, head in G.edges():
        # Set lower bounds on the lane direction variable that force it to be one if entry flow is positive
        problem.linear_constraints.add(
            lin_expr=[
                [[get_lane_direction_var(tail[0], tail[1], head[0], head[1])] +
                 [get_entry_flow_var(tail[0], tail[1], head[0], head[1])],
                 [len(G.nodes()) - 1, -1]]],
            senses="G",
            rhs=[0],
            names=[
                f"LaneDirectionEntryFlowLB({tail[0]},{tail[1]},{head[0]},{head[1]})"])

        # Set upper bounds on the lane direction variable that force it to be zero if entry flow is zero
        problem.linear_constraints.add(
            lin_expr=[
                [[get_lane_direction_var(tail[0], tail[1], head[0], head[1])] +
                 [get_entry_flow_var(tail[0], tail[1], head[0], head[1])],
                 [1, -1]]],
            senses="L",
            rhs=[0],
            names=[
                f"LaneDirectionEntryFlowUB({tail[0]},{tail[1]},{head[0]},{head[1]})"])

        # Set lower bounds on the lane direction variable that force it to be one if exit flow is positive
        problem.linear_constraints.add(
            lin_expr=[
                [[get_lane_direction_var(tail[0], tail[1], head[0], head[1])] +
                 [get_exit_flow_var(tail[0], tail[1], head[0], head[1])],
                 [len(G.nodes()) - 1, -1]]],
            senses="G",
            rhs=[0],
            names=[
                f"LaneDirectionExitFlowLB({tail[0]},{tail[1]},{head[0]},{head[1]})"])

        # Set upper bounds on the lane direction variable that force it to be zero if exit flow is zero
        problem.linear_constraints.add(
            lin_expr=[
                [[get_lane_direction_var(tail[0], tail[1], head[0], head[1])] +
                 [get_exit_flow_var(tail[0], tail[1], head[0], head[1])],
                 [1, -1]]],
            senses="L",
            rhs=[0],
            names=[
                f"LaneDirectionExitFlowUB({tail[0]},{tail[1]},{head[0]},{head[1]})"])


def is_cell_inside_grid(i, j):
    if i >= 0 and i < config.num_rows and j >= 0 and j < config.num_cols:
        return True
    else:
        return False
