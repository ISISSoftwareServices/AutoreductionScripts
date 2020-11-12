import os
import shutil
import sys
sys.path.append("/isis/NDXMUSR/user/scripts/autoreduction")
import reduce_vars as web_var

def validate(input_file, output_dir):
    """
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
    
    # Example of printing some stuff which is captured in autoreduction
    # output log file 
    print(web_var)
    print("input_file = " + str(input_file))
    print("output_dir = " + str(output_dir))
    
    # Copy raw data to output dir.
    # Note this should only be done if raw files are small and for specific
    # purpose such as testing 
    shutil.copy(input_file, output_dir)

    # And of course, here and below insert your reduction code!

if __name__ == "__main__":
    main("test", "test")
