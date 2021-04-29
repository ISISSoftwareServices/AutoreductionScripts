import collections
standard_vars = collections.OrderedDict()

standard_vars['Minimum Extents'] = '-3,-5,-4,-5.0'
standard_vars['Maximum Extents'] = '5,2,4,30.0'
standard_vars['UB Matrix'] = [2.87, 2.87, 2.87] # a, b, c
standard_vars['Run Range Starts'] = [22413, 22450]
standard_vars['Run Range Ends'] = []
standard_vars['Psi Starts'] = [0, 7]
standard_vars['Psi Increments'] = [2, 0.5]
standard_vars['test var'] = 0

#  = {
#     'Minimum Extents' : '-3,-5,-4,-5.0',
#     'Maximum Extents' : '5,2,4,30.0',
#     'UB Matrix' : [2.87, 2.87, 2.87], # a, b, c
#     'Run Range Starts' : [22413, 22450],
#     'Run Range Ends' : [],
#     'Psi Starts' : [0, 7],
#     'Psi Increments' : [2, 0.5],
#     'test var': 0
# }


advanced_vars = collections.OrderedDict()

advanced_vars['Number of Runs to Merge'] = [5]
advanced_vars['Filenames'] = []


#  = {
#     'Number of Runs to Merge' : [5],
#     'Filenames' : []
# }


variable_help = {
    'standard_vars' : {
        'UB Matrix' : "The list of a, b, c"
    },
    'advanced_vars' : {
        'Number of Runs to Merge' : "The total number of runs that should be merged."
    },
}