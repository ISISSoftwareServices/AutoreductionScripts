import os
import sys
import shutil
import time
sys.path.append("/isis/NDXOSIRIS/user/scripts/autoreduction") 
import reduce_vars as web_var

import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

# line added to test PR #928 and backing up of reduce.py script

def validate(file, dir):
    """
    Function that validates if a file and/or directory exist. If not a
    RunTimeError is raised which is picked up by Autoreduction.

    :param file: full path of data file. Provide empty string to ignore
    :type file: str
    :param dir: full path of a directory. Provide empty string to ignore
    :type dir: str
    """
    print("Running validation")
    if file:
        if not os.path.isfile(file):
            raise RuntimeError("Unable to find file: {}".format(file))
    if dir:
        if not os.path.isdir(dir):
            raise RuntimeError("Unable to find directory: {}".format(dir))
    print("Validation successful")
        

def main(input_file, output_dir):
    """
    Method called by Autoreduction to a reduction job.

    :param input_file: full path of raw data file
    :type input_file: str
    :param output_dir: directory where reduced data will be stored and a
        location which user can access
    :type output_dir: str
    """
    validate(input_file, output_dir)

    # Example of printing some stuff which is captured in autoreduction
    # output log file
    print(web_var.standard_vars)
    print(web_var.advanced_vars)
    print("input_file = " + str(input_file))
    print("output_dir = " + str(output_dir))

    # Copy raw data to output dir.
    # Note this should only be done if raw files are small and for specific
    # purpose such as testing
    shutil.copy(input_file, output_dir)
	
	# Some code to demonstrate plotting
    t = np.arange(0.0, 2.0, 0.01)
    s = 1 + np.sin(2 * np.pi * t)

    fig, ax = plt.subplots()
    ax.plot(t, s)

    ax.set(xlabel='time (s)', ylabel='voltage (mV)',
        title='About as simple as it gets, folks')
    ax.grid()

    fig.savefig(os.path.join(output_dir, "TEST_PLOT.png"), dpi=None)	

    # And of course, here and below insert your reduction code!


if __name__ == "__main__":
    main("some input file", "some output dir")
