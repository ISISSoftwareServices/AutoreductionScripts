import numpy  # Required due to Mantid4.0 import issue 
import sys
import os
sys.path.append("/isis/NDXPOLARIS/user/scripts/autoreduction")
from isis_powder import Polaris, SampleDetails
import reduce_vars as web_var
import time

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
    correction_params = web_var.advanced_vars
    
    mapping_file = r"/archive/NDXPOLARIS/user/scripts/autoreduction/Calibration/polaris_cycle_mapping.yaml"
    calib_dir = r"/archive/NDXPOLARIS/user/scripts/autoreduction/Calibration"
    
    user = "autoreduce"    
    # If performing absorption corrections add a workspace suffix of _abs
    output_suffix = '_abs' if params['do_absorb_corrections'] else ''
    
    instrument_args = {
        'user_name': user,
        'calibration_directory': calib_dir,
        'output_directory': output_dir,
        'calibration_mapping_file': mapping_file,
        'do_absorb_corrections': params['do_absorb_corrections'], 
        'do_van_normalisation': params['do_van_normalisation'],
        'input_mode': params['input_mode'], 
        'suffix':output_suffix,
        'sample_empty': 113677,
        'sample_empty_scale':1.0, 
    }
    
    # Only use the mode if specified by the user
    if params['mode']:
        instrument_args['mode'] = params['mode']
    
    
    polaris = Polaris(**instrument_args)

    
    # Add the sample object if we are applying absorption corrections
    if params['do_absorb_corrections']:
        sample_obj = SampleDetails(shape=correction_params['shape'],
                                   center=correction_params['center'],
                                   height=correction_params['height'],
                                   radius=correction_params['radius'])
        sample_obj.set_material(chemical_formula=correction_params['composition'],
                                number_density=correction_params['number_density'])
        polaris.set_sample_details(sample=sample_obj)                           
    
        
    # Prior to running this script, you need to have created a vanadium for cycle 17_2 like so:
    #polaris.create_vanadium(first_cycle_run_no=83881)

    # Focus run
    run_num = get_run_number(input_file)
    polaris.focus(run_number=run_num,
                  multiple_scattering=False)

# Returns the 5 digit run number of a POLARIS run from a file path
def get_run_number(path):
    if(isinstance(path, int)):
        return path
    return path.split(os.sep)[-1][7:][:-4]

if __name__ == "__main__":
    main(106862, "/tmp/powdertesting/Output")
