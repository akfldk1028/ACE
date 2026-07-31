from mip import *
from helpers import *

if __name__ == '__main__':
    instance_obj_summary = []  # store a list of (instance, objective) pairs

    # Display configuration settings and allow user to verify it
    display_problem_settings()

    # For instances other than the NYC parking lot, set index list to 1
    if config.INPUT_CATEGORY != 'n':
        config.PARKING_LOT_INDEX_LIST = [1]

    for index in config.PARKING_LOT_INDEX_LIST:
        create_input_directories()  # create input dir if it does not exist
        config.set_parking_lot(index)  # set the parking lot instance
        create_output_directories()  # create output dir if it does not exist

        # Read inputs and run sanity checks
        print("Running sanity checks on inputs...")
        config.run_sanity_checks()

        # Get valid driving fields and create a grid network to model driveways
        print("Populating valid driving and parking fields...")
        valid_drive_fields = get_valid_drive_fields()
        valid_drive_matrix = set_validity_matrix(valid_drive_fields)
        G = create_grid_network(valid_drive_matrix)

        # Update valid drive fields and valid drive matrix
        # after removing any disconnected components in G
        valid_drive_fields, valid_drive_matrix = update_valid_drive_components(
            G, valid_drive_fields)

        # Get valid parking as lists and boolean matrices
        valid_park0_fields, valid_park90_fields = get_valid_perpendicular_fields()
        valid_park0_matrix = set_validity_matrix(valid_park0_fields)
        valid_park90_matrix = set_validity_matrix(valid_park90_fields)

        start = time.time()  # record start time

        # Set CPLEX optimization parameters
        problem = cplex.Cplex()
        problem.objective.set_sense(problem.objective.sense.maximize)

        # Set CPLEX parameters such as time limit
        problem.parameters.timelimit.set(config.CPLEX_TIME_LIMIT_OPTIMIZATION)
        problem.set_error_stream(None)

        # Choose an optimization model based on user specified parameters
        if config.ARE_DRIVE_LANES_ONEWAY:
            optimize_one_way_parking(G, problem, valid_park0_fields,
                                     valid_park90_fields, valid_drive_fields,
                                     valid_park0_matrix, valid_park90_matrix,
                                     valid_drive_matrix)
        else:
            optimize_two_way_parking(G, problem, valid_park0_fields,
                                     valid_park90_fields, valid_drive_fields,
                                     valid_park0_matrix, valid_park90_matrix,
                                     valid_drive_matrix)

        end = time.time()  # record end time

        # Write the solution to a file
        problem.solution.write(f"{config.output_folder}/perpendicular.sol")

        # Log objective and summarize
        print("ID No.", index, "Objective",
              problem.solution.get_objective_value())
        instance_obj_summary.append(
            (index, problem.solution.get_objective_value()))
        log_summary_for_successful_instance(problem, end - start,
                                            valid_park0_fields,
                                            valid_park90_fields,
                                            valid_drive_fields)

    # Print the objective values for the instances
    print("Instance, Objective Value:")
    print(instance_obj_summary)
