import numpy  # Required due to Mantid4.0 import issue 
import sys
import os
sys.path.append("/isis/NDXGEM/user/scripts/autoreduction")
from isis_powder import Gem
import reduce_vars as web_var
import time

# Require to check mode of operation
from mantid.simpleapi import Load

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
    
    mapping_file = r"/archive/NDXGEM/user/scripts/autoreduction/gem_cycle_mapping.yaml"
    calib_dir = r"/archive/NDXGEM/user/scripts/autoreduction/Calibration"
    
    user = "autoreduce"

    if params['mode'] == '' or params['mode'] == None:
        ws = Load(input_file)
        mode = determine_mode(ws)
        if mode:
            print("Using {} mode for reduction.".format(mode))
            params['mode'] = mode
        else:
            raise ValueError("No mode supplied and unable to determine from logs please ensure "
                             "Phase T0, 6m and 9m are expected. " 
                             "Re-run and manually supply mode in the parameters.")
        
    
    cropping_values = [(550, 19900),  # Bank 1
                       (550, 19900),  # Bank 2
                       (550, 19900),  # Bank 3
                       (550, 19900),  # Bank 4
                       (550, 18500),  # Bank 5
                       (550, 16750)   # Bank 6
                      ]
    if params['mode'] == 'Rietveld':
        cropping_values = [(700, 19500),   # Bank 1
                           (1000, 19500),  # Bank 2
                           (1000, 19500),  # Bank 3
                           (1000, 19500),  # Bank 4
                           (1000, 18500),  # Bank 5
                           (1000, 18000)   # Bank 6
                          ]
    gem = Gem(
        user_name=user,
        calibration_directory=calib_dir,
        output_directory=output_dir,
        calibration_mapping_file=mapping_file,
        do_absorb_corrections=params['do_absorb_corrections'], 
        vanadium_normalisation=params['vanadium_normalisation'], 
        input_mode=params['input_mode'], 
        mode=params['mode'], 
        multiple_scattering=params['multiple_scattering'],
        focused_cropping_values=cropping_values,
        )

    # Prior to running this script, you need to have created a vanadium for cycle 17_2 like so:
    #gem.create_vanadium(do_absorb_corrections=True,
    #                    mode="PDF",
    #                    first_cycle_run_no=87568)

    # Focus run
    run_num = get_run_number(input_file)
    gem.focus(run_number=run_num,
              do_absorb_corrections=False)

# Returns the 5 digit run number of a GEM run from a file path
def get_run_number(path):
    return path.split(os.sep)[-1][3:][:-4]

# Determine if the mode of operation is PDF or Rietveld if this can't be determined, return None
def determine_mode(workspace):
    log_data = workspace.getRun()
    value_6m = log_data.getProperty('Phase_6m').value[0]
    value_9m = log_data.getProperty('Phase_9m').value[0]
    value_t0 = log_data.getProperty('Phase_T0').value[0]
    
    if value_6m == 503.0 and value_9m == 3.0 and value_t0 == 3.0:
        return 'Rietveld'
    if value_6m == 3.0 and value_9m == 19519.0 and value_t0 == 19803.0:
        return 'PDF'
    return None
    
    
    
if __name__ == "__main__":
    main(83890, "/tmp/powdertesting/Output")
