standard_vars = {
    'do_absorb_corrections' : False,
    'do_van_normalisation' : True,
    'input_mode' : "Individual",
    'mode' : ""
}

advanced_vars = {
    'multiple_scattering' : False,
    'number_density' : 0.0,
    'center' : [0,0,0],
    'height' : 1.0,
    'radius' : 1.0,
    'shape' : 'cylinder',
    'composition' : "",
}

variable_help = {
    'standard_vars' : {
        'do_absorb_corrections' : "Do you want absorb corrections on?",
        'vanadium_normalisation' : "Do you want vanadium normalisation on?",
        'input_mode' : "Choose an input mode, probably Summed",
        'mode' : "Either 'PDF' or 'Rietveld', if left blank then the script will attempt to automatically guess the correct mode by using chopper frequency.",
    },
        'advanced_vars' : {
        'multiple_scattering' : "Do you want multiple scattering on? This option is only required if do_absorbtion corrections is true.",
        'number_density': "The number density of your sample",
        'center' : "The center of the sample given by a list of [x,y,z]",
        'height' : "The height of the sample",
        'radius' : "The radius of the sample",
        'shape' : "The shape of the sample",
        'composition': "The chemical composition of your sample e.g. H-2O"
    },
}