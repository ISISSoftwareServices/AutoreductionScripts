import sys

# For headless usage
import matplotlib
matplotlib.use('Agg')

AUTOREDUCTION_DIR = "/isis/NDXINTER/user/scripts/autoreduction"

sys.path.append(AUTOREDUCTION_DIR)

from mantid.simpleapi import SaveNexus, LoadISISNexus, FilterLogByTime, AlgorithmManager, Integration, Transpose, config, ISISJournalGetExperimentRuns
from mantid.dataobjects import EventWorkspace
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

    input_workspace, datafile_name = load_workspace(input_file)
    save_detector_image(input_workspace, datafile_name, output_dir)
    save_specular_pixel_check(input_workspace, datafile_name, output_dir)

    run_title = input_workspace.getTitle()
    run_rb = str(input_workspace.getRun().getLogData("rb_proposal").value)
    print("Run title:", run_title, "RB:", run_rb)
    settings_file = find_settings_json(
        input_file, standard_params['path_to_json_settings_file'])
    print(find_group_runs(run_title, run_rb))
    run_reduction(input_workspace, datafile_name, settings_file, output_dir)


def run_reduction(input_workspace: EventWorkspace, workspace_name: str,
                  settings_file: str, output_dir: str):  # Run reduction
    # Get the angle
    angle = get_angle(input_workspace)
    params = find_angle_parameters_from_settings_json(settings_file, angle)

    alg = AlgorithmManager.create("ReflectometryISISLoadAndProcess")
    properties = {
        "InputRunList": workspace_name,
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
    copy(settings_file, output_dir)


def load_workspace(input_file) -> EventWorkspace:
    """
    Get the average angle from logs of motor position
    :param input_file: The input Nexus file
    :return: Average (mean) angle from motor position readback
    """
    filename = os.path.basename(input_file)
    run_str = filename.split("INTER")[1].split(".")[0].strip("0")
    name = instrument + run_str
    ws = LoadISISNexus(Filename=name, OutputWorkspace='TOF_' + run_str)
    return ws, filename


def get_angle(workspace: EventWorkspace):
    # Filter the logs for all angles starting from time 0 and use the average of the returned angles
    (angle_list, average_angle) = FilterLogByTime(workspace,
                                                  'Theta',
                                                  StartTime=0)
    return average_angle


def find_angle_parameters_from_settings_json(json_input, angle):
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
        if row[0] and min <= float(row[0]) <= max:
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


def save_detector_image(input_workspace, name: str, output_dir):
    fig, ax = plt.subplots(subplot_kw={'projection': 'mantid'})
    ax.imshow(input_workspace,
              aspect='auto',
              cmap='viridis',
              distribution=True,
              origin='lower')
    fig.savefig(os.path.join(output_dir, f"{name}_detector_image.png"))


def save_specular_pixel_check(input_workspace, name, output_dir):
    integrated = Integration(input_workspace,
                             RangeLower=9000,
                             RangeUpper=88000,
                             StartWorkspaceIndex=70,
                             EndWorkspaceIndex=95)

    integrated_transposed = Transpose(integrated)
    fig, ax = plt.subplots(subplot_kw={'projection': 'mantid'})
    ax.plot(integrated_transposed)
    fig.savefig(os.path.join(output_dir, f"{name}_specular.png"))


def find_group_runs(current_run_title, run_rb):
    """
    Queries the JournalViewer to find runs in the RB number that have the same title
    """
    print(current_run_title)
    if "th" in current_run_title:
        current_title, _ = current_run_title.split(" th")
        journal_ws = ISISJournalGetExperimentRuns("20_3", run_rb, "INTER")

        group_runs = []
        for group_run_filename, group_run_title in zip(journal_ws.column(0),
                                                       journal_ws.column(2)):
            if current_title in group_run_title:
                group_runs.append(group_run_filename)
        return group_runs


def find_settings_json(input_file: str, web_settings_json: str):
    if web_settings_json:
        return web_settings_json

    rb_dir, autoreduce_dir = input_file.split("autoreduced")
    return rb_dir


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


# if __name__=="__main__":
# main('INTER61667.nxs', '')
