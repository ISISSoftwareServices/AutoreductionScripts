import sys

AUTOREDUCTION_DIR = r"/autoreduce/data-archive/NDXINTER/user/scripts/autoreduction"
sys.path.append(AUTOREDUCTION_DIR)

# import mantid algorithms, numpy and matplotlib
from mantid.simpleapi import *
import matplotlib.pyplot as plt
import numpy as np
import reduce_vars as web_var
import os

def main(input_file, output_dir):
    standard_params = web_var.standard_vars
    advanced_params = web_var.advanced_vars
    
    config['defaultsave.directory'] = output_dir
    
    OutputWorkspaceBinned, OutputWorkspace, OutputWorkspaceFirstTransmission, OutputWorkspaceSecondTransmission = ReflectometryISISLoadAndProcess(InputRunList=input_file,
                                                        FirstTransmissionRunList=standard_params['first_transmission_run_list'],
                                                        SecondTransmissionRunList=standard_params['second_transmission_run_list'],
                                                        ThetaIn=standard_params['theta_in'],
                                                        DetectorCorrectionType=standard_params['detector_correction_type'],
                                                        AnalysisMode=standard_params['analysis_mode'],
                                                        TransmissionProcessingInstructions=standard_params['transmission_processing_instructions'],
                                                        ProcessingInstructions=standard_params['processing_instructions'])
    
    SaveNexus(OutputWorkspaceBinned, os.path.join(output_dir, OutputWorkspaceBinned.name()+".nxs"))
    SaveNexus(OutputWorkspace, os.path.join(output_dir, OutputWorkspace.name()+".nxs"))

if __name__ == "__main__":
    main('', '')

