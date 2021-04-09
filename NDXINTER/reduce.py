import sys

sys.path.append('/opt/Mantid/scripts')
sys.path.append('/opt/Mantid/scripts/SANS')
sys.path.append('/opt/Mantid/lib')
sys.path.append('/opt/Mantid/scripts/Inelastic')
sys.path.append('/opt/Mantid/scripts/Engineering')
sys.path.append('/opt/Mantid/scripts/Interface')
sys.path.append('/opt/Mantid/scripts/Diffraction')

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

    alg=AlgorithmManager.create("ReflectometryISISLoadAndProcess")
    properties = {
    "InputRunList" : standard_params['input_run_list'],
    "FirstTransmissionRunList" : standard_params['first_transmission_run_list'],
    "SecondTransmissionRunList" : standard_params['second_transmission_run_list'],
    "ThetaIn" : standard_params['theta_in'],
    "DetectorCorrectionType" : standard_params['detector_correction_type'],
    "MonitorBackgroundWavelengthMin" : standard_params['monitor_background_wavelength_min'],
    "MonitorBackgroundWavelengthMax" : standard_params['monitor_background_wavelength_max'],
    "MonitorIntegrationWavelengthMin" : standard_params['MonitorIntegrationWavelengthMin'],
    "MonitorIntegrationWavelengthMax" : standard_params['MonitorIntegrationWavelengthMax'],
    "WavelengthMin" : standard_params['WavelengthMin'],
    "WavelengthMax" : standard_params['WavelengthMax'],
    "I0MonitorIndex" : standard_params['IZeroMonitorIndex'],
    "AnalysisMode" : standard_params['analysis_mode'],
    "StartOverlap" : standard_params['StartOverlap'],
    "EndOverlap" : standard_params['EndOverlap'],
    "TransmissionProcessingInstructions" : standard_params['transmission_processing_instructions'],
    "ProcessingInstructions" : standard_params['processing_instructions']
    }
    alg.setProperties(properties)
    alg.execute()

    OutputWorkspace=alg.getPropertyValue("OutputWorkspace")
    OutputWorkspaceBinned=alg.getPropertyValue("OutputWorkspaceBinned")

    SaveNexus(OutputWorkspace, os.path.join(output_dir, OutputWorkspace+".nxs"))
    SaveNexus(OutputWorkspaceBinned, os.path.join(output_dir, OutputWorkspaceBinned+".nxs"))

if __name__ == "__main__":
    main('', '')

