import numpy  # Required due to Mantid4.0 import issue 
import sys
import os
from isis_powder import HRPD
sys.path.append("/isis/NDXHRPD/user/scripts/autoreduction") 
import reduce_vars as web_var

def validate(input_file, output_dir):
    """
    Autoreduction validate Function
    -------------------------------
    
    Function to ensure that the files we want to use in reduction exist.
    Please add any files/directories to the required_files/dirs lists.
    """
    print("Running validation")
    required_files = [input_file]
    required_dirs = [output_dir]
    for file_path in required_files:
        if not os.path.isfile(file_path):
            raise RuntimeError("Unable to find file: {}".format(file_path))
    for dir in required_dirs:
        if not os.path.isdir(dir):
            raise RuntimeError("Unable to find directory: {}".format(dir))
    print("Validation successful")


def main(input_file, output_dir):
    validate(input_file, output_dir)
    
    params = web_var.standard_vars    

    mapping_file = r"/archive/NDXHRPD/user/scripts/autoreduction/autoreduction_cycle_mapping.yaml"
    calib_dir = r"/archive/NDXHRPD/user/scripts/autoreduction/Calibration"
    
    user = "autoreduce"
    
    if params['window'] == '' or params['window'] == None:
        ws = Load(input_file)
        window = determine_window(ws)
        if window:
            print("Using {} window for reduction.".format(window))
            params['window'] = window
        else:
            raise ValueError("No window supplied and unable to determine from logs. " 
                             "Re-run and manually supply window in the parameters.")
    hrpd = HRPD(
        user_name=user,
        calibration_directory=calib_dir,
        output_directory=output_dir,
        calibration_mapping_file=mapping_file,
        do_absorb_corrections=params['do_absorb_corrections'], 
        vanadium_normalisation=params['vanadium_normalisation'], 
        mode=params['mode'], 
        multiple_scattering=params['multiple_scattering'],
        window=params['window'],
        )

    # Prior to running this script, you need to have created a vanadium for cycle 17_2 like so:
    hrpd.create_vanadium(first_cycle_run_no=77764, window=params['window'])

    # Focus run
    run_num = get_run_number(input_file)
    hrpd.focus(run_number=run_num,
               do_absorb_corrections=False,
               window=params['window'],)

# Returns the 5 digit run number of a HRPD run from a file path
def get_run_number(path):
    return path.split(os.sep)[-1][3:][:-4]

def determine_window(workspace):
    return '30-130' 

    
if __name__ == "__main__":
    main(r"/tmp/hrpdtest ", "Output")
