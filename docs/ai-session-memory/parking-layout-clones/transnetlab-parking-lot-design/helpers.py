import csv
import shutil
import config
import datetime
import os


def create_input_directories():
    # Delete cache
    if os.path.exists('cache'):
        shutil.rmtree('cache')

    if not os.path.exists(f"./inputs/"):
        os.makedirs(f"./inputs/")
        print(f"Directory inputs created.")
    else:
        print(f"Directory inputs already exists.")


def create_output_directories():
    """Creates a directory for saving the outputs if they don't already exist.

    Parameters:
        directory_path (str): Path to the directory to be created

    Returns:
        None
    """
    # Delete cache
    if os.path.exists('cache'):
        shutil.rmtree('cache')

    # Create another directory called outputs and inputs for saving the layouts
    # from multiple instances if it is not already present
    if not os.path.exists(f"./outputs/"):
        os.makedirs(f"./outputs/")
        print(f"Directory outputs created.")
    else:
        print(f"Directory outputs already exists.")

    # Create a subdirectory called collages in outputs if it not already present
    if not os.path.exists(f"./outputs/collages/"):
        os.makedirs(f"./outputs/collages/")
        print(f"Directory outputs/collages created.")
    else:
        print(f"Directory outputs/collages already exists.")

    if config.ARE_DRIVE_LANES_ONEWAY:
        config.output_folder = f"./outputs/{config.instance}_{config.RESOLUTION}_OneWay"
    else:
        config.output_folder = f"./outputs/{config.instance}_{config.RESOLUTION}_TwoWay"

    if not os.path.exists(f"./{config.output_folder}/"):
        os.makedirs(f"./{config.output_folder}/")
        print(f"Directory {config.output_folder} created.")
    else:
        print(f"Directory {config.output_folder} already exists.")


def log_summary_for_successful_instance(problem, time_taken, valid_park0_fields,
                                        valid_park90_fields,
                                        valid_drive_fields):
    summary = {
        "description": config.DESCRIPTION,
        "instance": config.instance,
        "area": config.area,
        "lane_configuration": "One-way" if config.ARE_DRIVE_LANES_ONEWAY else "Two-way",
        "formulation": "Flow-based" if config.SOLVE_USING_FLOW_VARIABLES else "Cutting planes",
        "valid_inequalities": "Yes" if config.INCLUDE_VALID_INEQUALITIES else "No",
        "total_time_taken": time_taken,
        "optimal_number_of_parking_spaces": problem.solution.get_objective_value(),
        "best_upper_bound": problem.solution.MIP.get_best_objective(),
        "gap": problem.solution.MIP.get_mip_relative_gap(),
        "num_rows": config.num_rows,
        "num_cols": config.num_cols,
        "number_of_variables": problem.variables.get_num(),
        "number_of_constraints": problem.linear_constraints.get_num(),
        "number_of_rejection_cuts": config.num_rejection_cuts,
        "number_of_valid_drive_fields": len(valid_drive_fields),
        "number_of_valid_park0_fields": len(valid_park0_fields),
        "number_of_valid_park90_fields": len(valid_park90_fields),
        "number_of_blocked_fields": len(config.blocked_cells),
        "f": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    # Write the dictionary to CSV file and append to the summary file
    with open(config.SUMMARY_FILE_PATH, "a",
              newline="") as file:
        writer = csv.DictWriter(file, fieldnames=summary.keys())
        writer.writerow(summary)


def display_problem_settings():
    # Show the user all the config parameters that are not instance dependent
    # and ask to verify it
    print("----------------------------------------------------")
    print("The following are the problem settings for this run")
    print("----------------------------------------------------")
    print("Description:", config.DESCRIPTION)
    print("Summary file path:", config.SUMMARY_FILE_PATH)
    print("Input category:", config.INPUT_CATEGORY)
    print("CPLEX time limit (in sec):", config.CPLEX_TIME_LIMIT_OPTIMIZATION)
    print("Lane configuration:",
          "One-way" if config.ARE_DRIVE_LANES_ONEWAY else "Two-way")
    print("Formulation chosen:",
          "Flow-based" if config.SOLVE_USING_FLOW_VARIABLES else "Cutting planes")
    print("Include valid inequalities?", config.INCLUDE_VALID_INEQUALITIES)
    print("Hop threshold for VIs:", config.HOP_THRESHOLD)

    # Ask the user to verify the settings and type y to proceed and n to exit
    print("--------------------------------------")
    response = input("Proceed with these settings? (y/n): ")
    print("--------------------------------------")
    if response.lower() == "n":
        exit()
    elif response.lower() != "y":
        print("Invalid response. Please type 'y' to proceed or 'n' to exit.")
        display_problem_settings()
    else:
        print("Starting the optimization process...")
