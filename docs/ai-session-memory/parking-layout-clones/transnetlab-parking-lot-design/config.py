import sys
import pandas as pd
import shutil
import config

DESCRIPTION = 'Parking Optimization'
SUMMARY_FILE_PATH = 'summary.csv'
INT_TOLERANCE = 1e-06  # constant used to check if the solution is an integer
SCALE_FACTOR = 2  # factor used to resize matplotlib images
PADDING = 0.25  # padding used in marking the fields
AXIS_TICK_INTERVAL = 2  # interval between axis ticks
CPLEX_TIME_LIMIT_OPTIMIZATION = 90  # time limit for cplex to solve the

ARE_DRIVE_LANES_ONEWAY = True  # False for two-way, True for one-way
SOLVE_USING_FLOW_VARIABLES = False  # False sets it to cutting planes
INCLUDE_VALID_INEQUALITIES = True
HOP_THRESHOLD = 4  # threshold for number of hops
CUT_SIZE_THRESHOLD = 8  # threshold for the size of the cut
num_rejection_cuts = 0

# Type of parking lot to optimize.
# Default grids (d), Default NYC parking lot (n)
INPUT_CATEGORY = 'n'

# List of downtown and midtown NYC parking lots
# Read the parking lot index list from an input file
with open('downtown_nyc_lot_ids.txt', 'r') as f:
    PARKING_LOT_INDEX_LIST = [int(line.strip()) for line in f]

PARKING_LOT_INDEX_LIST = [12500000299]

# proportion of overlapping area below which a cell is marked as blocked
CUTOFF_INTERSECTION_AREA = 0.0
# neighborhood distance in degrees. Note 1 m = 1/111000 degree
NEIGHBORHOOD_DISTANCE = 300 / 111000
# a small value for float comparisons
EPSILON = 1e-06

VEHICLE_WIDTH = 3  # width of parking lot in m
DRIVEWAY_WIDTH = 3  # width of the driveways in m

RESOLUTION = 'R2'
CUSTOM_CELL_SIZE = 6  # gets activated for RESOLUTION ='CUSTOM'
CUSTOM_PARK_FIELD_WIDTH = 1  # gets activated for RESOLUTION ='CUSTOM'
CUSTOM_PARK_FIELD_LENGTH = 1  # gets activated for RESOLUTION ='CUSTOM'

# PREDEFINE INPUT PARAMETERS
instance = ' '  # reference of the instance to be solved.
cell_size = None  # width of square cells in the grid in m
num_rows = None  # number of rows in the grid
num_cols = None  # number of columns in the grid
entry_drive_field = None  # the cell where the entrance and a driving field is located
exit_drive_field = None  # the cell where the exit driving field is located for one-way configuration
park_field_width = None  # width of the parking field (in units of cell diagonal size for angular fields)
park_field_length = None  # length of the parking field (in units of cell diagonal size for angular fields)
drive_field_width = None  # width of the driving field in units of the cell size
blocked_cells = []  # cells that are blocked
existing_drive_fields = []  # cells that already anchors of a driving field
existing_park0_fields = []  # cells that already anchors of a 0 degree parking field
existing_park90_fields = []  # cells that already anchors of a 90 degree parking field
area = None  # area of the parking lot in sq.ft
output_folder = None  # folder to store the outputs


def set_default_grid_parameters():
    """Sets the default values of the grid parameters.
    """
    # Stephan et al.'s instance
    # num_rows = 14
    # num_cols = 14
    # entry_drive_field = (0, 12)
    # exit_drive_field = (0, 13)
    # blocked_cells = [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (0, 5), (0, 6),
    #                  (1, 0), (1, 1), (1, 2), (1, 3), (1, 4), (1, 5), (1, 6),
    #                  (2, 0), (2, 1), (2, 2), (2, 3), (2, 4), (2, 5), (2, 6),
    #                  (3, 0), (3, 1), (3, 2), (3, 3), (3, 4), (3, 5), (3, 6),
    #                  (4, 0), (4, 1), (4, 2),
    #                  (5, 0), (5, 1), (5, 2),
    #                  (6, 0), (6, 1), (6, 2),
    #                  (7, 0), (7, 1), (7, 2),
    #                  (8, 0), (8, 1),
    #                  (9, 0), (9, 1), (9, 3),
    #                  (10, 0),
    #                  (11, 0)]

    # Tetris instance
    # park_field_width = 2
    # park_field_length = 3
    # if ARE_DRIVE_LANES_ONEWAY:
    #     drive_field_width = 2
    # else:
    #     drive_field_width = 4

    park_field_width = 1
    park_field_length = 2
    if ARE_DRIVE_LANES_ONEWAY:
        drive_field_width = 1
    else:
        drive_field_width = 2

    num_rows = 14
    num_cols = 16
    entry_drive_field = (0, 5)
    exit_drive_field = (0, 6)
    blocked_cells = [(3, 0), (4, 0), (5, 0), (5, 1),
                     (9, 0), (10, 0), (10, 1), (11, 1),
                     (12, 0), (13, 0), (13, 1), (13, 2),
                     (12, 6), (13, 5), (13, 6), (13, 7),
                     (0, 9), (1, 9), (2, 9), (3, 9),
                     (3, 15), (4, 14), (4, 15), (5, 14),
                     (7, 13), (7, 14), (8, 13), (8, 14)]

    existing_park0_fields = []
    existing_park90_fields = []
    instance = f"Default_Grid_{num_rows}_{num_cols}"

    # Calculate area (in units of cells)
    area = num_rows * num_cols - len(blocked_cells)

    return [num_rows, num_cols,
            park_field_width, park_field_length,
            drive_field_width, area,
            entry_drive_field,
            exit_drive_field,
            blocked_cells,
            existing_drive_fields,
            existing_park0_fields,
            existing_park90_fields,
            instance]


def is_drive_field_inside_grid(i, j):
    """Checks if the drive field at cell (i, j) is valid. This doesn't check for validity due to blocked fields.
    We perform validity checks when we add the constraints from existing driving fields in the mixed-integer program.

    Parameters:
        i (int): Row index of the cell.
        j (int): Column index of the cell.

    Returns:
        bool: True if the drive field at cell (i, j) is valid, False otherwise.
    """

    return i >= 0 and j >= 0 and \
        i + drive_field_width <= num_rows and \
        j + drive_field_width <= num_cols


def run_sanity_checks():
    """Runs a few basic checks to see if the input parameters are valid.

    Returns:
        None

    Raises:
        ValueError: If the input parameters are invalid.
    """
    if park_field_length < 0 or park_field_width < 0:
        raise ValueError(
            "Input parking and/or driving field parameters are negative.")
    if drive_field_width < park_field_width:
        raise ValueError(
            "The driving lanes are too narrow. Please update the width of the driving fields.")
    if park_field_length < park_field_width:
        raise ValueError(
            "The length of the parking field is less than the width.")
    if not is_drive_field_inside_grid(entry_drive_field[0],
                                      entry_drive_field[1]):
        raise ValueError("The entry cell is not a valid driving field.")
    for i, j in existing_drive_fields:
        if not is_drive_field_inside_grid(i, j):
            raise ValueError(
                f"The existing drive cell ({i}, {j}) is not a valid driving field.")

    if len(set(blocked_cells) & set([entry_drive_field])) > 0:
        raise ValueError("The blocked and entry cells have elements in common.")
    if len(set(blocked_cells) & set(existing_drive_fields)) > 0:
        raise ValueError(
            "The blocked and existing drive cells have elements in common.")
    if len(set(blocked_cells) & set(existing_park0_fields)) > 0:
        raise ValueError(
            "The blocked and existing park0 cells have elements in common.")
    if len(set(blocked_cells) & set(existing_park90_fields)) > 0:
        raise ValueError(
            "The blocked and existing park90 cells have elements in common.")
    for i, j in blocked_cells:
        if i < 0 or i >= num_rows or j < 0 or j >= num_cols:
            raise ValueError(
                f"The blocked drive cell ({i}, {j}) is outside the plot boundaries.")


def set_grid_parameters():
    """Make adjustments to the entry cell and blocked cells to ensure that
    the driveway falls within the grid.

    Returns:
        cell_size (float): Width of individual cell in grid
        park_field_width (int) : Width of parking spot in units of no of cells
        park_field_length (int) : Length of parking spot in units of no of cells
        drive_field_width (int) : Width of driveway in units of no of cells
    """
    if RESOLUTION == 'R1':
        cell_size = VEHICLE_WIDTH * 2
        park_field_width = 1
        park_field_length = 1
    elif RESOLUTION == 'R2':
        cell_size = VEHICLE_WIDTH
        park_field_width = 1
        park_field_length = 2
    elif RESOLUTION == 'R3':
        raise ValueError(f"Unknown input <{RESOLUTION}> for RESOLUTION.")
        cell_size = VEHICLE_WIDTH * (2 / 3)
        park_field_width = 2
        park_field_length = 3
    elif RESOLUTION == 'CUSTOM':
        cell_size = CUSTOM_CELL_SIZE
        park_field_width = CUSTOM_PARK_FIELD_WIDTH
        park_field_length = CUSTOM_PARK_FIELD_LENGTH
    else:
        raise ValueError("R1 and R2 configurations are only supported.")

    if ARE_DRIVE_LANES_ONEWAY:
        drive_field_width = int(DRIVEWAY_WIDTH / cell_size)
    else:
        drive_field_width = int(DRIVEWAY_WIDTH * 2 / cell_size)

    return [cell_size,
            park_field_width, park_field_length,
            drive_field_width]


# Populate the input data based on the INSTANCE variable
# this line has to be here to avoid issues due to circular imports
from polygon_utils import *


def create_exit_field(entry_drive_field):
    """
    Create exit cell corresponding to the input entry cell.
    """
    exit_drive_field = (
        entry_drive_field[0], entry_drive_field[1] + drive_field_width)
    return exit_drive_field


def set_parking_lot(index):
    global num_rows, num_cols, park_field_width, park_field_length, drive_field_width, entry_drive_field, exit_drive_field, \
        blocked_cells, existing_drive_fields, existing_park0_fields, existing_park90_fields, instance, area, output_folder
    PARKING_LOT_INDEX = index
    if INPUT_CATEGORY == 'd':  # default instance is similar to Stephan's paper or the Tetris grid
        print("Running the default parking grid instance...")
        [num_rows, num_cols,
         park_field_width, park_field_length,
         drive_field_width, area,
         entry_drive_field,
         exit_drive_field,
         blocked_cells,
         existing_drive_fields,
         existing_park0_fields,
         existing_park90_fields,
         instance] = set_default_grid_parameters()
    else:
        # Decide the sizes of the parking and driving fields based on the resolution
        cell_size, park_field_width, park_field_length, drive_field_width = set_grid_parameters()

        if INPUT_CATEGORY == 'n':  # NYC parking lot instance
            print("Running a custom NYC parking lot instance...")
            polygon, area = get_parking_polygon_by_index(PARKING_LOT_INDEX,
                                                         'parking_lots_data.csv')
            instance = f"NYC_{PARKING_LOT_INDEX}"

        # Extract the OSM data for driving streets around the parking lot
        # and find the entry cell and blocked fields
        street_graph = extract_OSM_street_data(polygon)

        entry_edges, nearest_streets = set_entrance_newest(polygon,
                                                           street_graph,
                                                           instance)

        num_rows, num_cols, entry_drive_field, blocked_cells = generate_grid_from_polygon(
            polygon, entry_edges, cell_size)
        entry_drive_field, blocked_cells = adjust_entrance(num_rows, num_cols,
                                                           drive_field_width,
                                                           entry_drive_field,
                                                           blocked_cells)
        print("----------------------entry cell", entry_drive_field)

        if ARE_DRIVE_LANES_ONEWAY:
            exit_drive_field = create_exit_field(entry_drive_field)

        print("----------------------exit_drive_field", exit_drive_field)
        instance += f"_{num_rows}_{num_cols}"
