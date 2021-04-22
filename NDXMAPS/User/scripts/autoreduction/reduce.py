# For headless usage
import matplotlib
matplotlib.use('Agg')

import numpy  # Required due to Mantid4.0 import issue 
from mantid import config
import os
import sys

AUTOREDUCTION_DIR = r"/isis/NDXMAPS/user/scripts/autoreduction"
sys.path.append(AUTOREDUCTION_DIR)

from mantid.simpleapi import Load, LoadNexusMonitors, ExtractSingleSpectrum, GetEi, Rebin, Max, Transpose
from mantid.api import ScriptRepositoryFactory as srf
repo = srf.Instance().create("ScriptRepositoryImpl")
repo.install('/tmp/repo')
# listFiles is required for any download call to be successful
repo.listFiles()
repo.download('direct_inelastic/MAPS/MAPSReduction_Sample.py')
import MAPSReduction_Sample as maps_red

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
    # ToDo: Put into function 
    if advanced_params['hardmaskOnly'] and advanced_params['hardmaskOnly'] != 'None':
        kwargs['hardmaskOnly'] = os.path.join(AUTOREDUCTION_DIR, advanced_params['hardmaskOnly'])
    else:
        kwargs['hardmaskOnly'] = None
    
    if advanced_params['monovan_mapfile'] and advanced_params['monovan_mapfile'] != 'None':
        kwargs['monovan_mapfile'] = os.path.join(AUTOREDUCTION_DIR, advanced_params['monovan_mapfile'])
    else:
        kwargs['monovan_mapfile'] = None
    
    if advanced_params['map_file'] and advanced_params['map_file'] != 'None':
        kwargs['map_file'] = os.path.join(AUTOREDUCTION_DIR, advanced_params['map_file'])
    else:
        kwargs['map_file'] = None
    
    if standard_params['incident_energy'].upper() == "AUTO":
        standard_params['incident_energy'] = calculate_ei(input_file)


    run_number = get_run_number(input_file)
    maps_red.iliad_maps_powder(runno=run_number,
                               ei=standard_params['incident_energy'],
                               wbvan=standard_params['wb_run'],
                               rebin_pars=standard_params['energy_bins'],
                               monovan=standard_params['monovan_run'],
                               sam_mass=standard_params['sample_mass'],
                               sam_rmm=standard_params['sample_rmm'],
                               sum_runs=standard_params['sum_runs'],
                               check_background=advanced_params['check_background'],
                               **kwargs)

    if standard_params['plot_type'] == 'slice':
        slice_plot(run_number, output_dir)
            
def calculate_ei(input_file):
    # Auto Find Eis by finding maximum data point in m2 (excluding end points)
    # and looking for neighbouring reps according to Fermi speed
    # Doesn't deal with cases where the peaks enter the 2nd frame (i.e 2 meV on MARI)
    print(input_file)
    w1 = Load(input_file)
    mon = LoadNexusMonitors(input_file)
    run = w1.getRun()

    # set up ==================================================
    monitor_spectra_2  = 41475
    monitor_spectra_3  = 41476
    monitor_index_2 = 2
    monitor_index_3 = 3
    log  = 'Fermi_Speed'

    # Get instrument parameters ===============================
    inst = w1.getInstrument()
    source = inst.getSource()
    L_m2 = mon.getDetector(monitor_index_2).getDistance(source)
    L_m3 = mon.getDetector(monitor_index_3).getDistance(source)
    L_Fermi = inst.getComponentByName("chopper-position").getDistance(source)
    freq = run.getLogData(log).value[-1]
    period = L_m2 / L_Fermi * 1.e6 / freq / 2. # include pi-pulses

    # Find maximum value and identify strongest rep ===========
    m2spec = ExtractSingleSpectrum(mon,monitor_index_2)
    m2spec = Rebin(m2spec,"200,2,18000")
    maxm2 = Max(m2spec)
    TOF = maxm2.readX(0)[0]

    # Generate list of possible reps in m2 ====================
    irep = -5
    while True:
        t = TOF + irep*period
        if t > 0:
            ireps = numpy.array(range(irep,irep+20))
            reps = TOF + period * ireps
            break
        else:
            irep += 1

    # exclude all reps that go past the frame in m3 ===========       
    reps_m3 = reps * L_m3 / L_m2
    reps_m3 = [x for x in reps_m3 if x < 19999.]
    reps = reps[0:len(reps_m3)]
    # exclude all reps at short times
    reps = [x for x in reps if x > 200.]

    # try GetEi for the reps ==================================
    Ei = []
    TOF = []
    for t in reps:
        v_i = L_m2 / t                    # m/mus
        Ei_guess = 5.227e6 * v_i**2       # meV
        try:
            (En,TOF2,dummy,tzero) = GetEi(mon, monitor_spectra_2, monitor_spectra_3, Ei_guess)
        except:
            continue
        if abs(t - TOF2) > 20. or abs(tzero) > 100.: continue
        Ei.append(Ei_guess)
        TOF.append(TOF2)

    #=========================================================
    for ii in range(len(Ei)):
        print("%f meV at TOF = %f mus" % (Ei[ii],TOF[ii]))
    return Ei

                               
def get_run_number(path):
    """
    Autoreduction run number parser
    -------------------------------
    
    Autoreduction provides the full absolute path to the data file to reduce.
    In this case we only want the run number hence split the path in just run number
    """
    return path.split(os.sep)[-1][3:][:-4]


def slice_plot(run_number, output_dir):
    """
    Autoreduction generate plot from slice viewer
    ---------------------------------------------

    The slice viewer provides the best first look at the data. As such, we will generate and
    save the slice images to CEPH and these will be picked up and displayed by the webapp
    :param run_number: The current run number
    """
    for file in os.listdir(output_dir):
        if '.nxspe' not in file or f'MAP{run_number}' not in file.upper():
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
        mantid_slice = Transpose(slice_ws.raw_ws)
        mesh = ax.pcolormesh(mantid_slice, cmap="viridis")
        # Restrict color range to be 1/5 of the max counts in the range between 0.1 and 0.9 Ei
        en = ws.get_coordinates()['Energy transfer']
        en_id = np.where((en > ws.e_fixed/10) * (en < ws.e_fixed*0.9))
        mesh.set_clim(0.0, np.max(ws.get_signal()[:,en_id]) / 3)
        cb = plt.colorbar(mesh, ax=ax)
        cb.set_label('Intensity (arb. units)', labelpad=20, rotation=270, picker=5)
        ax.set_title(plot_name)
        return fig


if __name__ == "__main__":
    main('/archive/NDXMAPS/Instrument/data/cycle_20_3/MAP40554.nxs', '/home/dl11170/autmp')
