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
import json

def main(input_file, output_dir):
    standard_params = web_var.standard_vars
    advanced_params = web_var.advanced_vars

    config['defaultsave.directory'] = output_dir

    angle = get_angle()
    analysis_mode,first_transmission_run_list,second_transmission_run_list,transmission_processing_instructions,processing_instructions,start_overlap,end_overlap,monitor_integration_wavelength_min,monitor_integration_wavelength_max,monitor_background_wavelength_min,monitor_background_wavelength_max,wavelength_min,wavelength_max,i_zero_monitor_index,detector_correction_type = parse_json_settings(angle)

    alg=AlgorithmManager.create("ReflectometryISISLoadAndProcess")
    properties = {
    "InputRunList" : input_file,
    "FirstTransmissionRunList" : first_transmission_run_list,
    "SecondTransmissionRunList" : second_transmission_run_list,
    "ThetaIn" : angle,
    "DetectorCorrectionType" : detector_correction_type,
    "MonitorBackgroundWavelengthMin" : monitor_background_wavelength_min,
    "MonitorBackgroundWavelengthMax" : monitor_background_wavelength_max,
    "MonitorIntegrationWavelengthMin" : monitor_integration_wavelength_min,
    "MonitorIntegrationWavelengthMax" : monitor_integration_wavelength_max,
    "WavelengthMin" : wavelength_min,
    "WavelengthMax" : wavelength_max,
    "I0MonitorIndex" : i_zero_monitor_index,
    "AnalysisMode" : analysis_mode,
    "StartOverlap" : start_overlap,
    "EndOverlap" : end_overlap,
    "TransmissionProcessingInstructions" : transmission_processing_instructions,
    "ProcessingInstructions" : processing_instructions
    }

    alg.setProperties(properties)
    alg.execute()

    OutputWorkspace=alg.getPropertyValue("OutputWorkspace")
    OutputWorkspaceBinned=alg.getPropertyValue("OutputWorkspaceBinned")

    SaveNexus(OutputWorkspace, os.path.join(output_dir, OutputWorkspace+".nxs"))
    SaveNexus(OutputWorkspaceBinned, os.path.join(output_dir, OutputWorkspaceBinned+".nxs"))

def get_angle():
    ws=Load('INTER61668')
    title = (ws.run().getProperty('run_title').value)
    angle = title.split(" th=")[1].split()[0]
    return angle

def parse_json_settings(angle):
    """
    Autoreduction get settings from JSON file
    """
    json_input = r"C:\Users\wyf59278\Documents\repos\reflectometry_reduction\settings.json"

    with open(json_input, "r") as read_file:
        data = json.load(read_file)

    experimentView = data["experimentView"]

    if experimentView["analysisModeComboBox"] == 1:
        analysis_mode = "MultiDetectorAnalysis"
    elif experimentView["analysisModeComboBox"] == 0:
        analysis_mode = "PointDetectorAnalysis"
    else:
        raise Exception # If the value isn't 1 or 0 then it isn't valid

    perAngleDefaults = experimentView["perAngleDefaults"]
    rows = perAngleDefaults["rows"]

    # This looks for the run angle and set other parameters accordingly
    angle_found = False
    for i in rows:
        if i[0] == angle:
            angle_found = True
            first_transmission_run_list = i[1]
            second_transmission_run_list = i[2]
            transmission_processing_instructions = i[3]
            processing_instructions = i[8]
            break

    # This is the default case
    if not angle_found:
        for i in rows:
            if i[0] == "":
                angle_found = True
                first_transmission_run_list = i[1]
                second_transmission_run_list = i[2]
                transmission_processing_instructions = i[3]
                processing_instructions = i[8]
                break

    if not angle_found:
        raise Exception # Excpetion for if neither a pre-defined angle or the default case are found

    start_overlap = experimentView["startOverlapEdit"]

    end_overlap = experimentView["endOverlapEdit"]

    instrumentView = data["instrumentView"]

    monitor_integration_wavelength_min = instrumentView["monIntMinEdit"]
    monitor_integration_wavelength_max = instrumentView["monIntMaxEdit"]
    monitor_background_wavelength_min = instrumentView["monBgMinEdit"]
    monitor_background_wavelength_max = instrumentView["monBgMaxEdit"]
    wavelength_min = instrumentView["lamMinEdit"]
    wavelength_max = instrumentView["lamMaxEdit"]
    i_zero_monitor_index = instrumentView["I0MonitorIndex"]

    if instrumentView["detectorCorrectionTypeComboBox"] == 1:
        detector_correction_type = "RotateAroundSample"
    elif instrumentView["detectorCorrectionTypeComboBox"] == 0:
        detector_correction_type = "VerticalShift"
    else:
        raise Exception # If the value isn't 1 or 0 then it isn't valid

    return analysis_mode,first_transmission_run_list,second_transmission_run_list,transmission_processing_instructions,processing_instructions,start_overlap,end_overlap,monitor_integration_wavelength_min,monitor_integration_wavelength_max,monitor_background_wavelength_min,monitor_background_wavelength_max,wavelength_min,wavelength_max,i_zero_monitor_index,detector_correction_type

if __name__ == "__main__":
    main('', '')
