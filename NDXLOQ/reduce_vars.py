# Set the standard parameters 
standard_vars = {
    'SampleTRANS': None,
    'CanSANS': None,
    'CanTRANS': None,
    'EmptyBeamTRANS': 108241,
    'UserFile': 'USER_LOQ_203A_M3_Lu_Xpress_12mm_Changer_MAIN_LIN.txt',
    'RBNumber': 2090073
}
advanced_vars={
    'wl_ranges': [2.2,4.0,6.0,8.0,10.0],
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
