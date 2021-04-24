import sys

#AUTOREDUCTION_DIR = "/isis/NDXINTER/user/scripts/autoreduction"
#sys.path.append(AUTOREDUCTION_DIR)

from mantid.simpleapi import SaveNexus, Load, FilterLogByTime, AlgorithmManager, config
import matplotlib.pyplot as plt
import numpy as np
import reduce_vars as web_var
import os
import json
from shutil import copy

instrument = 'INTER'


# Main funcion that gets called by the reduction
def main(input_file, output_dir):
    standard_params = web_var.standard_vars
    advanced_params = web_var.advanced_vars
    config['defaultsave.directory'] = output_dir

    # Get the angle
    angle, input_run = get_angle(input_file)
    # Parse settings from JSON file
    #json_input = standard_params['path_to_json_settings_file']
    json_input = r"C:\Users\qbr77747\Desktop\settings.json"
    params = parse_json_settings(json_input, angle)

    # Run reduction
    alg = AlgorithmManager.create("ReflectometryISISLoadAndProcess")
    properties = {
        "InputRunList": input_run,
        "FirstTransmissionRunList": params.first_transmission_run_list,
        "SecondTransmissionRunList": params.second_transmission_run_list,
        "ThetaIn": angle,
        "DetectorCorrectionType": params.detector_correction_type,
        "MonitorBackgroundWavelengthMin":
        params.monitor_background_wavelength_min,
        "MonitorBackgroundWavelengthMax":
        params.monitor_background_wavelength_max,
        "MonitorIntegrationWavelengthMin":
        params.monitor_integration_wavelength_min,
        "MonitorIntegrationWavelengthMax":
        params.monitor_integration_wavelength_max,
        "WavelengthMin": params.wavelength_min,
        "WavelengthMax": params.wavelength_max,
        "I0MonitorIndex": params.i_zero_monitor_index,
        "AnalysisMode": params.analysis_mode,
        "StartOverlap": params.start_overlap,
        "EndOverlap": params.end_overlap,
        "ScaleRHSWorkspace": params.scale_rhs_workspace,
        "TransmissionProcessingInstructions":
        params.transmission_processing_instructions,
        "ProcessingInstructions": params.processing_instructions
    }
    alg.setProperties(properties)
    alg.execute()

    # Save reduced data as Nexus files
    OutputWorkspace = alg.getPropertyValue("OutputWorkspace")
    OutputWorkspaceBinned = alg.getPropertyValue("OutputWorkspaceBinned")
    SaveNexus(OutputWorkspace,
              os.path.join(output_dir, OutputWorkspace + ".nxs"))
    SaveNexus(OutputWorkspaceBinned,
              os.path.join(output_dir, OutputWorkspaceBinned + ".nxs"))

    # Save a copy of the .json settings file
    copy(json_input, output_dir)


def get_angle(input_file):
    """
    Get the average angle from logs of motor position
    :param input_file: The input Nexus file
    :return: Average (mean) angle from motor position readback
    """
    filename = os.path.basename(input_file)
    run_str = filename.split("INTER")[1].split(".")[0].strip("0")
    name = instrument + run_str
    ws = Load(Filename=name, OutputWorkspace='TOF_' + run_str)
    # Filter the logs for all angles starting from time 0 and use the average of the returned angles
    (angle_list, average_angle) = FilterLogByTime(ws, 'Theta', StartTime=0)
    return average_angle, name


def parse_json_settings(json_input, angle):
    """
    Get experiment settings and instrument settings from JSON file
    :param angle: Angle passed in and used to select "per angle defaults"
    :return: Returns all of the parameters needed to do the reduction
    """
    params = INTERParams()

    with open(json_input, "r") as read_file:
        data = json.load(read_file)

    #========================================================================================
    # Experiment Settings
    #========================================================================================

    experimentView = data["experimentView"]

    # Set a string based on what integer value is found
    if experimentView["analysisModeComboBox"] == 1:
        params.analysis_mode = "MultiDetectorAnalysis"
    elif experimentView["analysisModeComboBox"] == 0:
        params.analysis_mode = "PointDetectorAnalysis"
    else:
        raise Exception  # If the value isn't 1 or 0 then it isn't valid

    perAngleDefaults = experimentView["perAngleDefaults"]
    rows = perAngleDefaults["rows"]

    # This looks for the run angle and set other parameters accordingly
    # Using a tolerance of +-0.5% of the motor readback angle
    min = angle * 0.995
    max = angle * 1.005
    angle_found = False
    for row in rows:
        # If the value is within -0.5% to +0.5% it is counted as a match
        if min <= float(row[0]) <= max:
            angle_found, params = get_per_angle_defaults_params(row, params)
            break

    # This is the default case
    if not angle_found:
        for row in rows:
            if row[0] == "":
                angle_found, params = get_per_angle_defaults_params(
                    row, params)
                break

    if not angle_found:
        raise Exception  # Excpetion for if neither a pre-defined angle nor the default case are found

    params.start_overlap = experimentView["startOverlapEdit"]
    params.end_overlap = experimentView["endOverlapEdit"]
    params.scale_rhs_workspace = experimentView["transScaleRHSCheckBox"]

    #========================================================================================
    # Instrument Settings
    #========================================================================================

    instrumentView = data["instrumentView"]

    params.monitor_integration_wavelength_min = instrumentView["monIntMinEdit"]
    params.monitor_integration_wavelength_max = instrumentView["monIntMaxEdit"]
    params.monitor_background_wavelength_min = instrumentView["monBgMinEdit"]
    params.monitor_background_wavelength_max = instrumentView["monBgMaxEdit"]
    params.wavelength_min = instrumentView["lamMinEdit"]
    params.wavelength_max = instrumentView["lamMaxEdit"]
    params.i_zero_monitor_index = instrumentView["I0MonitorIndex"]

    # Set a string based on what integer value is found
    if instrumentView["detectorCorrectionTypeComboBox"] == 1:
        params.detector_correction_type = "RotateAroundSample"
    elif instrumentView["detectorCorrectionTypeComboBox"] == 0:
        params.detector_correction_type = "VerticalShift"
    else:
        raise Exception  # If the value isn't 1 or 0 then it isn't valid

    return params


def get_per_angle_defaults_params(row, params):
    """
    Get parameters that are dependant on the angle
    :param row: The row for the angle that has been selected (or the row for the default case if no angle was matched)
    :return: Returns all of the parameters that are dependant on the angle
    """
    angle_found = True
    params.first_transmission_run_list = instrument + row[1]
    params.second_transmission_run_list = instrument + row[2]
    params.transmission_processing_instructions = row[3]
    # Skipping over parameters that are present in the JSON file but not currently used in the reduction
    params.processing_instructions = row[8]
    return angle_found, params


class INTERParams:
    analysis_mode: str
    first_transmission_run_list: str
    second_transmission_run_list: str
    transmission_processing_instructions: str
    processing_instructions: str
    start_overlap: str
    end_overlap: str
    scale_rhs_workspace: str
    monitor_integration_wavelength_min: str
    monitor_integration_wavelength_max: str
    monitor_background_wavelength_min: str
    monitor_background_wavelength_max: str
    wavelength_min: str
    wavelength_max: str
    i_zero_monitor_index: str
    detector_correction_type: str


main('INTER61667.nxs', '')
