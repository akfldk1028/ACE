from cplex import Cplex


def get_park0_var(i, j):
    """Returns the variable name for a 0 degree parking field at cell (i, j).

    Parameters:
        i (int): Row index of the cell.
        j (int): Column index of the cell.

    Returns:
        str: Variable name for a 0 degree parking field at cell (i, j).
    """
    return f"x0({i},{j})"


def get_park90_var(i, j):
    """Returns the variable name for a 90 degree parking field at cell (i, j).

    Parameters:
        i (int): Row index of the cell.
        j (int): Column index of the cell.

    Returns:
        str: Variable name for a 90 degree parking field at cell (i, j).
    """
    return f"x90({i},{j})"


def get_drive_var(i, j):
    """Returns the variable name for the drive field at cell (i, j).

    Parameters:
        i (int): Row index of the cell.
        j (int): Column index of the cell.

    Returns:
        str: Variable name for the drive field at cell (i, j).
    """
    return f"y({i},{j})"


def get_entry_flow_var(i, j, k, l):
    """Returns the variable name for the flow from cell (i, j) to cell (k, l), which corresponds to the entrance.

    Parameters:
        i (int): Row index of the source cell.
        j (int): Column index of the source cell.
        k (int): Row index of the destination cell.
        l (int): Column index of the destination cell.

    Returns:
        str: Variable name for the entry-based flow from cell (i, j) to cell (k, l).
    """
    return f"f({i},{j},{k},{l})"


def get_exit_flow_var(i, j, k, l):
    """Returns the variable name for the alternate flow from cell (i, j) to cell (k, l), which corresponds exit.
    These are used only for the one-way model.

    Parameters:
        i (int): Row index of the source cell.
        j (int): Column index of the source cell.
        k (int): Row index of the destination cell.
        l (int): Column index of the destination cell.

    Returns:
        str: Variable name for the exit-based flow from cell (i, j) to cell (k, l).
    """
    return f"g({i},{j},{k},{l})"


def get_lane_direction_var(i, j, k, l):
    """Returns the variable name for the direction variable between cell (i, j) and cell (k, l).
    These are used only for the one-way model.

    Parameters:
        i (int): Row index of the source cell.
        j (int): Column index of the source cell.
        k (int): Row index of the destination cell.
        l (int): Column index of the destination cell.

    Returns:
        str: Variable name for the direction between cell (i, j) and cell (k, l).
    """
    return f"z({i},{j},{k},{l})"


def set_park_variables(problem, valid_park0_fields, valid_park90_fields):
    """Sets the park variables in the problem for perpendicular parking.

    Parameters:
        problem (Cplex): The CPLEX problem object.
        valid_park0_fields (list): List of valid 0 degree parking fields.
        valid_park90_fields (list): List of valid 90 degree parking fields.

    Returns:
        park0_variables (Cplex variables): The 0 degree park variables.
        park90_variables (Cplex variables): The 90 degree park variables.
    """
    print("--Setting park variables")
    park0_cells = [get_park0_var(i, j) for (i, j) in valid_park0_fields]
    park90_cells = [get_park90_var(i, j) for (i, j) in valid_park90_fields]

    park0_variables = problem.variables.add(
        obj=[1] * len(park0_cells),
        types="B" * len(park0_cells),
        lb=[0.0] * len(park0_cells),
        ub=[1.0] * len(park0_cells),
        names=park0_cells)

    park90_variables = problem.variables.add(
        obj=[1] * len(park90_cells),
        types="B" * len(park90_cells),
        lb=[0.0] * len(park90_cells),
        ub=[1.0] * len(park90_cells),
        names=park90_cells)

    return park0_variables, park90_variables


def set_drive_variables(problem, valid_drive_fields):
    """Sets the drive variables in the problem.

    Parameters:
        problem (Cplex): The CPLEX problem object.
        valid_drive_fields (list): List of valid driving fields.

    Returns:
        drive_variables (Cplex variables): The drive variables.
    """
    print("--Setting drive variables")
    drive_cells = [get_drive_var(i, j) for (i, j) in valid_drive_fields]

    drive_variables = problem.variables.add(
        types="B" * (len(drive_cells)),
        lb=[0.0] * len(drive_cells),
        ub=[1.0] * len(drive_cells),
        names=drive_cells)

    return drive_variables


def set_entry_flow_variables(problem, G):
    """This function adds the flow variables to the problem. The flows are associated with the entry cells and are
    defined for every pair of nodes in the grid. They have the form f(i,j,k,l) where (i,j) is the tail node and
    (k,l) is the head node.

    Parameters:
        problem (Cplex): The CPLEX problem object.
        G (NetworkX graph): Graph of the grid.

    Returns:
        entry_flow_variables (Cplex variables): The entry flow variables.
    """
    print("--Setting entry flow variables")
    entry_flow_variables = problem.variables.add(
        types="C" * G.number_of_edges(),
        lb=[0.0] * G.number_of_edges(),
        names=[get_entry_flow_var(tail[0], tail[1], head[0], head[1]) for tail, head in G.edges()])

    return entry_flow_variables


def set_exit_flow_variables(problem, G):
    """
    This function adds the flow variables to the problem. The flows are associated with the exit cells and are defined
    for every pair of nodes in the grid. They have the form g(i,j,k,l) where (i,j) is the tail node and (k,l) is the
    head node. These are used only for the one-way model.

    Parameters:
        problem (Cplex): The Cplex problem to which the variables are added.
        G (NetworkX graph): Graph of the grid.

    Returns:
        exit_flow_variables (Cplex variables): The exit flow variables.
    """
    print("--Setting exit flow variables")
    exit_flow_variables = problem.variables.add(
        types="C" * G.number_of_edges(),
        lb=[0.0] * G.number_of_edges(),
        names=[get_exit_flow_var(tail[0], tail[1], head[0], head[1]) for tail, head in G.edges()])

    return exit_flow_variables


def set_lane_direction_variables(problem, G):
    """The direction variables are used to model one-way flow of traffic. They have the form z(i,j,k,l) where (i,j) is
    the tail node and (k,l) is the head node. If they are one then the flow is allowed from (i,j) to (k,l).
    If they are zero then the flow is not allowed in that direction.

    Parameters:
        problem (Cplex): The Cplex problem to which the variables are added.
        G (NetworkX graph): Graph of the grid.

    Returns:
        None
    """
    print("--Setting lane direction variables")
    lane_direction_variables = problem.variables.add(
        types="B" * G.number_of_edges(),
        names=[get_lane_direction_var(tail[0], tail[1], head[0], head[1]) for tail, head in G.edges()])

    return lane_direction_variables
