standard_vars = {
    'energy_bins': [-0.2, 0.002, 0.9],
    'incident_energy': 'AUTO',
    'sum_runs': False,
    'monovan_run': None,
    'wb_run': 37520,
	'sample_mass': 0,
    'sample_rmm': 0,
    'plot_type': None,
}
advanced_vars={
    'wb_integr_range': [20, 100],
    'bkgd_range': [15000, 19000],
    'van_mass': 30.1,
    'save_format': 'nxspe',
    'data_file_ext': '.nxs',
    'monovan_mapfile': '4to1_mid_lowang.map',
    'diag_remove_zero': False,
	'check_background': False,
    'monovan_lo_frac': -0.5,
    'hardmaskOnly': '4to1_193_msk.xml',
    'map_file': 'MAPS_rings.map',
}
variable_help={
    'standard_vars' : {
    'energy_bins': 'Energy binning, expected in final converted to energy transfer workspace.\n\n Provide it in the form:\n propman.energy_bins = [min_energy,step,max_energy]\n if energy to process (incident_energy property) has a single value,\n or\n propman.energy_bins = [min_rel_enrgy,rel_step,max_rel_energy]\n where all values are relative to the incident energy,\n if energy(ies) to process (incident_energy(ies)) are list of energies.\n The list of energies can contain only single value.\n (e.g. prop_man.incident_energy=[100])/\n ',
    'incident_energy': 'Provide incident energy or range of incident energies to be processed.\n\n Set it up to list of values (even with single value i.e. prop_man.incident_energy=[10]),\n if the energy_bins property value to be treated as relative energy ranges.\n\n Set it up to single value (e.g. prop_man.incident_energy=10) to treat energy_bins\n as absolute energy values.\n ',
    'sum_runs': 'Boolean property specifies if list of files provided as input for sample_run property\n should be summed.\n ',
    'monovan_run': 'Run number, workspace or symbolic presentation of such run\n containing results of monochromatic neutron beam scattering from vanadium sample\n used in absolute units normalization.\n None disables absolute units calculations.',
    'wb_run': 'Run number, workspace or symbolic presentation of such run\n containing results of white beam neutron scattering from vanadium used in detectors calibration.',
    'sample_run': 'Run number, workspace or symbolic presentation of such run\n containing data of scattering from a sample to convert to energy transfer.\n Also accepts a list of the such run numbers',
    },
    'advanced_vars' : {
    'save_format': 'The format to save reduced results using internal save procedure.\n\n Can be one name or list of supported format names. Currently supported formats\n are: spe, nxspe and nxs data formats.\n See Mantid documentation for detailed description of the formats.\n If set to None, internal saving procedure is not used.\n ',
    'monovan_mapfile': 'Mapping file for the monovanadium integrals calculation.\n\n The file used to group various monochromatic vanadium spectra together to provide\n reasonable statistics for these groups when calculating monovanadium integrals.',
    'hard_mask_file': 'Hard mask file.\n\n The file containing list of spectra to be excluded from analysis (spectra with failing detectors).',
    'map_file': 'Mapping file for the sample run.\n\n The file used to group various spectra together to obtain appropriate instrument configuration \n and improve statistics.',
    },
}
