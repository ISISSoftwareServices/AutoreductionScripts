# Set the standard parameters 
standard_vars = {
    'SampleTRANS': None,
    'CanSANS': None,
    'CanTRANS': None,
    'EmptyBeamTRANS': 65054,
    'UserFile': 'USER_SANS2D_202I_2p4_4m_M4_Growney_12mm_Changer_MERGED.txt',
    'RBNumber': 2055010
}
advanced_vars={
    'wl_ranges': [2.0,4.0,6.0,8.0,10.0,12.0,14.0,16.0],
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
