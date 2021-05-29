import sys
from typing import List, Optional, Tuple
from numpy.core.numeric import full
import plotly.graph_objs as go
import plotly.express as px

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
    matplotlib_figure, (det_image_ax, spec_pixel_ax) = plt.subplots(figsize=(13, 4.8),
                                                                    ncols=2,
                                                                    subplot_kw={'projection': 'mantid'})
    matplotlib_figure.suptitle(input_workspace.getTitle())

    plot_detector_image(input_workspace, matplotlib_figure, det_image_ax)
    plotly_fig = plot_specular_pixel_check(input_workspace, flood_workspace, spec_pixel_ax)
    save_plotly_figure(plotly_fig, datafile_name, "peak", output_dir)
    matplotlib_figure.savefig(os.path.join(output_dir, f"{datafile_name}.png"))

    full_run_title = input_workspace.getTitle()
    run_rb = str(input_workspace.getRun().getLogData("rb_proposal").value)
    run_number = str(input_workspace.getRun().getLogData("run_number").value)

    print("Run title:", full_run_title, "RB:", run_rb)

    # only reduce if not a transmission run
    if "trans" in full_run_title.lower():
        print("Skipping reduction due to having 'trans' in the title: {full_run_title}")
    else:
        sample_name = get_sample_name(full_run_title)
        settings_file = find_settings_json(sample_name, standard_params['JSON Settings File'],
                                           f"/instrument/INTER/RBNumber/RB{run_rb}")

        output_workspace_binned = None
        if settings_file:
            output_workspace_binned = run_reduction(input_workspace, datafile_name, settings_file, output_dir)
        else:
            print("Skipping reduction due to missing settings file")
        group_run_numbers = find_group_runs(sample_name, run_rb, input_file)
        print("Found group_run_numbers:", group_run_numbers)

        if group_run_numbers:
            try:
                group_plot_fig = plot_group_runs(group_run_numbers, sample_name, run_rb, run_number,
                                                 output_workspace_binned)
                if group_plot_fig:
                    with open(os.path.join(output_dir, f"{datafile_name}_group.json"), 'w') as figfile:
                        figfile.write(group_plot_fig)
            except Exception as err:
                print("Encountered error while trying to plot group:", err)


def run_reduction(input_workspace: EventWorkspace, workspace_name: str, settings_file: str,
                  output_dir: str):  # Run reduction
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
        "MonitorBackgroundWavelengthMin": params.monitor_background_wavelength_min,
        "MonitorBackgroundWavelengthMax": params.monitor_background_wavelength_max,
        "MonitorIntegrationWavelengthMin": params.monitor_integration_wavelength_min,
        "MonitorIntegrationWavelengthMax": params.monitor_integration_wavelength_max,
        "WavelengthMin": params.wavelength_min,
        "WavelengthMax": params.wavelength_max,
        "I0MonitorIndex": params.i_zero_monitor_index,
        "AnalysisMode": params.analysis_mode,
        "StartOverlap": params.start_overlap,
        "EndOverlap": params.end_overlap,
        "ScaleRHSWorkspace": params.scale_rhs_workspace,
        "TransmissionProcessingInstructions": params.transmission_processing_instructions,
        "ProcessingInstructions": params.processing_instructions
    }
    alg.setProperties(properties)
    alg.execute()

    # Save reduced data as Nexus files
    OutputWorkspace = alg.getPropertyValue("OutputWorkspace")
    OutputWorkspaceBinned = alg.getPropertyValue("OutputWorkspaceBinned")

    SaveNexus(OutputWorkspace, os.path.join(output_dir, OutputWorkspace + ".nxs"))
    SaveNexus(OutputWorkspaceBinned, os.path.join(output_dir, OutputWorkspaceBinned + ".nxs"))

    # Save a copy of the .json settings file
    copy(settings_file, output_dir)

    return OutputWorkspaceBinned


def load_workspace(input_file) -> Tuple[EventWorkspace, str]:
    """
    Get the average angle from logs of motor position
    :param input_file: The input Nexus file
    :return: Average (mean) angle from motor position readback
    """
    filename = os.path.basename(input_file)
    run_str = filename.split("INTER")[1].split(".")[0]
    ws = LoadISISNexus(Filename=input_file, OutputWorkspace='TOF_' + run_str)
    return ws, filename


def get_sample_name(full_run_title):
    return full_run_title[:full_run_title.lower().index(" th=")]


def get_angle(workspace: EventWorkspace):
    # Filter the logs for all angles starting from time 0 and use the average of the returned angles
    (angle_list, average_angle) = FilterLogByTime(workspace, 'Theta', StartTime=0)
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
                angle_found, params = get_per_angle_defaults_params(row, params)
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


def plot_specular_pixel_check(input_workspace: EventWorkspace, flood_workspace: EventWorkspace, ax):
    flooded_ws = ApplyFloodWorkspace(input_workspace, flood_workspace)

    integrated = Integration(flooded_ws,
                             RangeLower=9000,
                             RangeUpper=88000,
                             StartWorkspaceIndex=70,
                             EndWorkspaceIndex=95)

    integrated_transposed = Transpose(integrated)

    def _1gaussian(x, ampl, cent, sigma):
        return ampl * (1 / sigma * (np.sqrt(2 * np.pi))) * (np.exp(-((x - cent)**2) / (2 * sigma)**2))

    xval = integrated_transposed.readX(0)
    yval = integrated_transposed.readY(0)
    popt_gauss, pcov_gauss = optimize.curve_fit(_1gaussian, xval, yval, p0=[56000, 86, 0.8])
    perr_gauss = np.sqrt(np.diag(pcov_gauss))

    fit_yvals = _1gaussian(xval, *popt_gauss)

    ax.plot(xval, yval, "rx")
    ax.plot(xval, fit_yvals, 'k--')
    ax.axvline(x=86.0, color='b', linestyle='--')
    ax.set_xlabel("Spectrum")
    ax.set_ylabel("Counts")
    max_pos = fit_yvals.argmax()
    annot_y = fit_yvals[max_pos]
    annot_x = xval[max_pos]
    ax.annotate(f"X:{annot_x}, Y:{annot_y}", xy=(annot_x, annot_y), xytext=(annot_x * 1.02, annot_y))
    ax.minorticks_on()
    ax.grid(True, which="both")
    ax.set_title("Specular pixel")

    # make interactive plotly figure
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=xval, y=yval, name="Data", mode="markers", marker_symbol=4))
    fig.add_trace(go.Scatter(x=xval, y=fit_yvals, mode="lines", name="Fit"))
    fig.add_vline(x=86, line_dash="dash", line_color="blue")
    fig.update_layout(xaxis_title="Spectrum", yaxis_title="Counts", width=600, title_text="Specular pixel", title_x=0.5)
    return fig


def save_plotly_figure(plotly_fig, datafile_name, plot_type_suffix, output_dir):
    with open(os.path.join(output_dir, f"{datafile_name}_{plot_type_suffix}.json"), 'w') as figfile:
        figfile.write(plotly_fig.to_json())

    # plotly_fig.write_image(os.path.join(output_dir, f"plotly_{plot_type_suffix}_{datafile_name}.png"))


def which_cycle(input_file):
    cycle_str_start_pos = input_file.rindex("cycle_") + len("cycle_")
    return input_file[cycle_str_start_pos:cycle_str_start_pos + 4]


def find_group_runs(sample_name, run_rb, input_file):
    """
    Queries the JournalViewer to find runs in the RB number that have the same title
    """
    group_runs = []
    cycle = which_cycle(input_file)
    try:
        journal_ws = ISISJournalGetExperimentRuns(cycle, run_rb, "INTER")

        for i in range(journal_ws.rowCount()):
            _, group_run_number, group_run_title = journal_ws.row(i).values()

            if sample_name in group_run_title:
                group_runs.append(group_run_number)
    except:
        print('Title not formatted for NR workspace so runs not grouped.')
    return group_runs


def find_pre_reduced_run(run_number, run_rb):
    """
    Find the file for a manually reduced run that has been saved to the RB folder inside single_angles
    """
    expected_location = web_var.standard_vars["Pre-reduced single angles"].format(run_rb)

    full_path = os.path.join(expected_location, f"IvsQ_binned_{run_number}.dat")
    if os.path.isfile(full_path):
        return full_path
    else:
        return None


def find_autoreduced_run(run_number, run_rb):
    """
    Find the file saved from a previous autoreduction
    """
    ## not loading the current run - the data should be on CEPH
    run_ceph_folder = f"/instrument/INTER/RBNumber/RB{run_rb}/autoreduced/{run_number}"
    ## use the newest version available for the run
    newest_run_version = sorted(os.listdir(run_ceph_folder))[-1]
    expected_location = f"{run_ceph_folder}/{newest_run_version}"
    full_path = os.path.join(expected_location, f"IvsQ_binned_{run_number}.nxs")
    if os.path.isfile(full_path):
        return full_path
    else:
        return None


def find_reduced_run(run_number, run_rb, current_run_number, output_workspace_binned):
    """
    Contains the logic to find the reduced run.

    First checks for a manually pre-reduced run inside RB/single_angles.

    If not found, then looks for an autoreduced run.
    """
    # try to find the file in a pre-reduced single_angles folder
    run_file_path = find_pre_reduced_run(run_number, run_rb)

    # did not find a pre-reduced run, try to load an autoreduced one
    if not run_file_path:
        if run_number == current_run_number:
            # if we are looking for the current run number, we have this calculated in a local variable
            return output_workspace_binned
        else:
            # only search for a file if the run is not the current one
            run_file_path = find_autoreduced_run(run_number, run_rb)

    # found a reduced run at some location, load it into a workspace and return it
    if run_file_path:
        ws = Load(run_file_path)
        return ws
    else:
        return None


def plot_group_runs(group_run_numbers: List[int], group_name, run_rb: str, current_run_number, output_workspace_binned):
    fig = go.Figure()
    fig.update_layout(yaxis={'exponentformat': 'power'},
                      margin=dict(l=100, r=20, t=20, b=20),
                      modebar={'orientation': 'v'},
                      width=1000,
                      height=500)
    anything_plotted = False
    for run_number in group_run_numbers:
        ws = find_reduced_run(run_number, run_rb, current_run_number, output_workspace_binned)
        if not ws:
            # did not find anything to plot for this run
            print("Did not find any reduced files for run", run_number)
            continue
        anything_plotted = True
        fig.add_trace(
            go.Scatter(
                x=ws.dataX(0),
                y=ws.dataY(0),
                error_y=dict(
                    type='data',  # value of error bar given in data coordinates
                    array=ws.dataE(0),
                    visible=True),
                name=run))

    fig.update_xaxes(type="log")
    fig.update_yaxes(type="log")
    # fig.update_layout(xaxis_title="q (r'$\AA$'^{-1})", yaxis_title="Reflectivity")
    if anything_plotted:
        return fig.to_json()  ## Add a to_image too?
    else:
        return None


def find_settings_json(sample_name, web_settings_json: str, output_rb_dir: str) -> Optional[str]:
    """
    Tries to find a settings.json that should be used for this reduction.

    If one is not found it defaults to using the one in the autoreduction directory on the Archive
    """
    # check if a specific file is provided from the web app
    if web_settings_json:
        return web_settings_json

    # If not - check if a {sample_name}.json exists in the experiment's CEPH folder.
    # This is a small workaround as the json files cannot describe angles for multiple samples
    settings_for_sample_name = os.path.join(output_rb_dir, f"{sample_name}.json")
    if os.path.exists(settings_for_sample_name):
        return settings_for_sample_name

    # if not - check if a general, experiment-wide settings.json exists in the CEPH folder
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
