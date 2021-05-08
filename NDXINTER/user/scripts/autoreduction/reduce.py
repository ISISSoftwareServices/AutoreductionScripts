import sys
from typing import List, Optional, Tuple

# For headless usage
import matplotlib
matplotlib.use('Agg')

AUTOREDUCTION_DIR = "/isis/NDXINTER/user/scripts/autoreduction"

sys.path.append(AUTOREDUCTION_DIR)

from mantid.simpleapi import SaveNexus, Load, LoadISISNexus, FilterLogByTime, AlgorithmManager, Integration, Transpose, config, ISISJournalGetExperimentRuns, Fit, ApplyFloodWorkspace
from mantid.dataobjects import EventWorkspace
from matplotlib.colors import SymLogNorm
# from mantid.api import AnalysisDataService as ADS

import matplotlib.pyplot as plt
import numpy as np
import reduce_vars as web_var
import os
import json
from shutil import copy
from scipy import optimize

instrument = 'INTER'


# Main funcion that gets called by the reduction
def main(input_file, output_dir):
    standard_params = web_var.standard_vars
    advanced_params = web_var.advanced_vars
    config['defaultsave.directory'] = output_dir
    print("Input file", input_file, "output dir", output_dir)

    input_workspace, datafile_name = load_workspace(input_file)
    flood_workspace = Load(advanced_params["flood_workspace"])
    fig, (det_image_ax,
          spec_pixel_ax) = plt.subplots(figsize=(13, 4.8),
                                        ncols=2,
                                        subplot_kw={'projection': 'mantid'})
    fig.suptitle(input_workspace.getTitle())

    plot_detector_image(input_workspace, fig, det_image_ax)
    plot_specular_pixel_check(input_workspace, flood_workspace, spec_pixel_ax)
    fig.savefig(os.path.join(output_dir, f"{datafile_name}.png"))

    run_title = input_workspace.getTitle()
    run_rb = str(input_workspace.getRun().getLogData("rb_proposal").value)
    print("Run title:", run_title, "RB:", run_rb)
    settings_file = find_settings_json(
        standard_params['path_to_json_settings_file'],
        f"/instrument/INTER/RBNumber/RB{run_rb}")

    # only reduce if not a transmission run
    if settings_file and "trans" not in run_title.lower():
        run_reduction(input_workspace, datafile_name, settings_file,
                      output_dir)
    else:
        print(
            "Skipping reduction due to",
            "missing settings file" if settings_file is None else
            f"this having 'trans' in the title: {run_title}")

    group_run_numbers = find_group_runs(run_title, run_rb)
    print("Found group_run_numbers:", group_run_numbers)

    # if group_run_numbers:
    # group_run_ax = fig.add_subplot(223)
    # plot_group_runs(group_run_numbers, fig, group_run_ax)


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


def load_workspace(input_file) -> Tuple[EventWorkspace, str]:
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


def plot_detector_image(input_workspace: EventWorkspace, fig, ax):
    plot = ax.imshow(input_workspace,
                     aspect='auto',
                     cmap='viridis',
                     distribution=True,
                     origin='lower',
                     norm=SymLogNorm(1e-6))
    fig.colorbar(plot, ax=ax)
    ax.set_title("Detector image")


def plot_specular_pixel_check(input_workspace: EventWorkspace,
                              flood_workspace: EventWorkspace, ax):
    flooded_ws = ApplyFloodWorkspace(input_workspace, flood_workspace)

    integrated = Integration(flooded_ws,
                             RangeLower=9000,
                             RangeUpper=88000,
                             StartWorkspaceIndex=70,
                             EndWorkspaceIndex=95)

    integrated_transposed = Transpose(integrated)

    def _1gaussian(x, ampl, cent, sigma):
        return ampl * (1 / sigma *
                       (np.sqrt(2 * np.pi))) * (np.exp(-((x - cent)**2) /
                                                       (2 * sigma)**2))

    xval = integrated_transposed.readX(0)
    yval = integrated_transposed.readY(0)
    popt_gauss, pcov_gauss = optimize.curve_fit(_1gaussian,
                                                xval,
                                                yval,
                                                p0=[56000, 82, 0.8])
    perr_gauss = np.sqrt(np.diag(pcov_gauss))

    fit_yvals = _1gaussian(xval, *popt_gauss)

    ax.plot(xval, yval, "rx")
    ax.plot(xval, fit_yvals, 'k--')
    ax.axvline(x=82.0,color='b',linestyle='--')
    ax.set_xlabel("Spectrum")
    ax.set_ylabel("Counts")
    max_pos = fit_yvals.argmax()
    annot_y = fit_yvals[max_pos]
    annot_x = xval[max_pos]
    ax.annotate(f"X:{annot_x}, Y:{annot_y}",
                xy=(annot_x, annot_y),
                xytext=(annot_x * 1.02, annot_y))
    ax.minorticks_on()
    ax.grid(True, which="both")
    ax.set_title("Specular pixel")


def find_group_runs(current_run_title, run_rb):
    """
    Queries the JournalViewer to find runs in the RB number that have the same title
    """
    current_title, _ = current_run_title.split(" th")
    journal_ws = ISISJournalGetExperimentRuns("20_3", run_rb, "INTER")

    group_runs = []
    for i in range(journal_ws.rowCount()):
        _, group_run_number, group_run_title = journal_ws.row(i).values()

        if current_title in group_run_title:
            group_runs.append(group_run_number)
    return group_runs


def plot_group_runs(group_run_numbers: List[int], fig, ax):
    for run in group_run_numbers:
        ws = Load()
        ax.loglog(ws)

    ax.title()


def find_settings_json(web_settings_json: str,
                       output_rb_dir: str) -> Optional[str]:
    """
    Tries to find a settings.json that should be used for this reduction.

    If one is not found it defaults to using the one in the autoreduction directory on the Archive
    """
    # check if a specific file is provided from the web app
    if web_settings_json:
        return web_settings_json

    # if not - check if a settings.json exists in the experiment's CEPH folder
    settings_in_rb_dir = os.path.join(output_rb_dir, "settings.json")
    if os.path.exists(settings_in_rb_dir):
        return settings_in_rb_dir

    return None


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
