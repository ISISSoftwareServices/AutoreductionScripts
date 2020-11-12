# Set the standard parameters 
standard_vars = {
    'SampleTRANS': None,
    'CanSANS': None,
    'CanTRANS': None,
    'EmptyBeamTRANS': 16193,
    'UserFile': 'USER_ZOOM_Griffiths_4m_SampleChanger_202E_12mm_Large_BEAMSTOP_M5.txt',
    'RBNumber': 2010659
}
advanced_vars={
    'wl_ranges': [2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0, 16.0],
}
variable_help={
    'standard_vars' : {
    'SampleTRANS': 'Run number of the sample transmission to override any automatic setting',
    'CanSANS': 'Run number of the can scattering to override any automatic setting',
    'CanTRANS': 'Run number of the can transmission to override any automatic setting',
    'EmptyBeamTRANS': 'Run number of the empty beam transmission to override any automatic setting',
    'RBNumber': 'Current RB Number to allow the parsing of the current experiment',
    },
    'advanced_vars' : {
    'wl_ranges': 'Python of list wavelengths to produce the wavelength overlap plot for multiple scattering checks',
    },
}
