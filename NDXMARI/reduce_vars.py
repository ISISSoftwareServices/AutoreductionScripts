standard_vars = {
    'incident_energy': "Auto",
    'energy_bins': [-1.5, 0.01, 0.9],
    'sum_runs': False,
    'monovan_run': None,
    'white_beam_run': 'mar27292.raw',
    'sample_mass': 0,
    'sample_rmm': 0,
    'plot_type': 'slice'
}
advanced_vars={
    'normalise_method': 'current',
    'map_file': 'mari_res2013.map',
    'monovan_mapfile': 'mari_res2013.map',
    'hard_mask_file': 'mari_mask2020_2.xml',
    'save_format': 'nxspe',
    'data_file_ext':'.nxs', 
    'load_monitors_with_workspace': False,
    'check_background': False,
    'bkgd-range-min': 18000,
    'bkgd-range-max': 19000,
}
variable_help={
    'standard_vars' : {
        'incident_energy':'Provide incident energy or range of incident energies to be processed.\n\n Set it up to list of values (even with single value i.e. prop_man.incident_energy=[10]),\n if the energy_bins property value to be treated as relative energy ranges.\n\n Set it up to single value (e.g. prop_man.incident_energy=10) to treat energy_bins\n as absolute energy values.\n ',
        'energy_bins':'Energy binning, expected in final converted to energy transfer workspace.\n\n Provide it in the form:\n propman.energy_bins = [min_energy,step,max_energy]\n if energy to process (incident_energy property) has a single value,\n or\n propman.energy_bins = [min_rel_enrgy,rel_step,max_rel_energy]\n where all values are relative to the incident energy,\n if energy(ies) to process (incident_energy(ies)) are list of energies.\n The list of energies can contain only single value.\n (e.g. prop_man.incident_energy=[100])/\n ',
        'sum_runs':'Boolean property specifies if list of files provided as input for sample_run property\n should be summed.\n ',
        'monovan_run':'Run number, workspace or symbolic presentation of such run\n containing results of monochromatic neutron beam scattering from vanadium sample\n used in absolute units normalization.\n None disables absolute units calculations.',
        'wb_run':'Run number, workspace or symbolic presentation of such run\n containing results of white beam neutron scattering from vanadium used in detectors calibration.',
        'plotting_type': 'The type of plot you want to be produced. Currently for MARI plotting options are: \'slice\'',
         },
     'advanced_vars' : {
        'motor_offset':'Initial value used to identify crystal rotation angle according to the formula:\n psi=motor_offset+wccr.timeAverageValue() where wccr is the log describing\n crystal rotation. See motor_log_name property for its description.\n ',
        'save_format':'The format to save reduced results using internal save procedure.\n\n Can be one name or list of supported format names. Currently supported formats\n are: spe, nxspe and nxs data formats.\n See Mantid documentation for detailed description of the formats.\n If set to None, internal saving procedure is not used.\n ',
        'det_cal_file':'Provide a source of the detector calibration information.\n\n A source can be a file, present on a data search path, a workspace\n or a run number, corresponding to a file to be loaded as a\n workspace.\n ',
        'monovan_mapfile':'Mapping file for the monovanadium integrals calculation.\n\n The file used to group various monochromatic vanadium spectra together to provide\n reasonable statistics for these groups when calculating monovanadium integrals.',
        'hard_mask_file':'Hard mask file.\n\n The file containing list of spectra to be excluded from analysis (spectra with failing detectors).',
        'map_file':'Mapping file for the sample run.\n\n The file used to group various spectra together to obtain appropriate instrument configuration \n and improve statistics.',
         },
}
