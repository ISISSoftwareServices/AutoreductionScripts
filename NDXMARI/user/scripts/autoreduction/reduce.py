# For headless usage
import matplotlib
matplotlib.use('Agg')

import numpy  # Required due to Mantid4.0 import issue
from mantid import config
import time
import os
import datetime
import sys

AUTOREDUCTION_DIR = r"/isis/NDXMARI/user/scripts/autoreduction"
sys.path.append(AUTOREDUCTION_DIR)

import mantid.simpleapi
from mantid.api import ScriptRepositoryFactory as srf
repo = srf.Instance().create("ScriptRepositoryImpl")
repo.install('/tmp/repo')
# listFiles is required for any download call to be successful
repo.listFiles()
repo.download('direct_inelastic/MARI/MARIReduction_Sample.py')
import MARIReduction_Sample as mari_red

import reduce_vars as web_var
config['default.facility'] = 'ISIS'
config['datasearch.searcharchive'] = 'on'

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
    standard_params = web_var.standard_vars
    advanced_params = web_var.advanced_vars

    config['defaultsave.directory'] = output_dir

    kwargs = {}
    if advanced_params['hard_mask_file'] and advanced_params['hard_mask_file'] != 'None':
        kwargs['hard_mask_file'] = os.path.join(AUTOREDUCTION_DIR, advanced_params['hard_mask_file'])
    else:
        kwargs['hard_mask_file'] = None

    run_number = get_run_number(input_file)
    output_ws_list = mari_red.iliad_mari(runno=run_number,
                                         ei=standard_params['incident_energy'],
                                         wbvan=standard_params['white_beam_run'],
                                         monovan=standard_params['monovan_run'],
                                         sam_mass=standard_params['sample_mass'],
                                         sam_rmm=standard_params['sample_rmm'],
                                         sum_runs=standard_params['sum_runs'],
                                         check_background=advanced_params['check_background'],
                                         map_file=os.path.join(AUTOREDUCTION_DIR, advanced_params['map_file']),
                                         **kwargs)
    if standard_params['plot_type'] == 'slice':
        slice_plot(run_number, output_ws_list, output_dir)


def slice_plot(run_number, workspaces_to_plot, output_dir):
    """
    Autoreduction generate plot from slice viewer
    ---------------------------------------------

    The slice viewer provides the best first look at the data. As such, we will generate and
    save the slice images to CEPH and these will be picked up and displayed by the webapp
    :param workspaces_to_plot: A list of mantid workspaces to generate slices for.
                               Names for plots should be generated from workspace name.
    """
    #for workspace in workspaces_to_plot:
    #    ei_name = '{:<3.2f}'.format(workspace.run().getProperty('Ei').value)
    #    plot_name = f"MAR{run_number}_Ei{ei_name}meV"
    #    file_path = os.path.join(output_dir, f"{plot_name}.nxspe")
    for file in os.listdir(output_dir):
        if '.nxspe' not in file or f'MAR{run_number}' not in file:
            continue
        file_path = os.path.join(output_dir, file)
        plot_name = file.split('.nxspe')[0]
        fig = create_slice(file_path, plot_name)
        fig.savefig(os.path.join(output_dir, f"{plot_name}.png"), dpi=None)        
        
def create_slice(file_path, plot_name):
        import mslice.cli as mc
        import matplotlib.pyplot as plt
        import numpy as np
        ws_name = plot_name.replace('.', '_')
        ws = mc.Load(Filename=file_path, OutputWorkspace=ws_name)
        fig = plt.figure()
        # Using Mantid projection instead of MSlice to ensure it works headless
        ax = fig.add_subplot(111, projection="mantid")
        slice_ws = mc.Slice(ws)
        mantid_slice = mantid.simpleapi.Transpose(slice_ws.raw_ws)
        mesh = ax.pcolormesh(mantid_slice, cmap="viridis")
        # Restrict color range to be 1/5 of the max counts in the range between 0.1 and 0.9 Ei
        en = ws.get_coordinates()['Energy transfer']
        en_id = np.where((en > ws.e_fixed/10) * (en < ws.e_fixed*0.9))
        mesh.set_clim(0.0, np.max(ws.get_signal()[:,en_id]) / 5)
        cb = plt.colorbar(mesh, ax=ax)
        cb.set_label('Intensity (arb. units)', labelpad=20, rotation=270, picker=5)
        ax.set_title(plot_name)
        return fig

def get_run_number(path):
    """
    Autoreduction run number parser
    -------------------------------

    Autoreduction provides the full absolute path to the data file to reduce.
    In this case we only want the run number hence split the path in just run number
    """
    return path.split(os.sep)[-1][3:][:-4]


if __name__ == "__main__":
    main('', '')