# Set the standard parameters 
standard_vars = {
    'SampleTRANS': None,
    'CanSANS': None,
    'CanTRANS': None,
    'EmptyBeamTRANS': 56068,
    'UserFile': 'USER_Jones_203A_Changer_r56068.txt',
    'RBNumber': 2010389
}
advanced_vars={
    'wl_ranges': [1.0, 3.0, 5.0, 7.0, 9.0, 11.0, 13.0],
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
