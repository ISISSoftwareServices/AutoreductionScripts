standard_vars = {
    "path_to_json_settings_file": ""
    # "analysis_mode": "MultiDetectorAnalysis",
    # "first_transmission_run_list" : "INTER00061705",
    # "second_transmission_run_list" : "INTER00061669",
    # "transmission_processing_instructions": "76-85",
    # "processing_instructions": "80-84",
    # "start_overlap" : 10.0,
    # "end_overlap" : 12.0
}
advanced_vars = {
    "flood_workspace":
    "/isis/NDXINTER/User/INTER/FloodFiles/Flood_cycle_21_1.nxs"
    # "monitor_integration_wavelength_min" : 4.0,
    # "monitor_integration_wavelength_max" : 10.0,
    # "monitor_background_wavelength_min": 17.0,
    # "monitor_background_wavelength_max": 18.0,
    # "wavelength_min" : 1.5,
    # "wavelength_max" : 17.0,
    # "i_zero_monitor_index" : 2,
    # "detector_correction_type": "VerticalShift"
}

variable_help = {
    "standard_vars": {
        "path_to_json_settings_file":
        "Path to a settings.json saved on CEPH from the Mantid Reflectometry GUI, such as /instrument/INTER/RBNumber/RB1234567/settings.json",
    },
    "advanced_vars": {
        "flood_workspace":
        "Path to a flood workspace that will be used for Flood corrections"
    },
}
