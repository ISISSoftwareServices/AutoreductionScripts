import os
import sys

AUTOREDUCTION_DIR = r"/isis/NDXMERLIN/user/scripts/autoreduction"
sys.path.append(AUTOREDUCTION_DIR)

import mantid.simpleapi
from mantid.api import ScriptRepositoryFactory as srf
from mantid import config
repo = srf.Instance().create("ScriptRepositoryImpl")
repo.install('/tmp/repo')
# listFiles is required for any download call to be successful
repo.listFiles()
repo.download('direct_inelastic/MERLIN/MERLINReduction_Sample.py')
import MERLINReduction_Sample as mer_red

import reduce_vars as web_var

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

#------------------------------------------------------------------------------------#
#------------------------------------------------------------------------------------#
#------------------------------------------------------------------------------------#
def main(input_file=None,output_dir=None):
    """ This method is used to run code from web service
        and should not be touched unless you change the name of the
        particular ReductionWrapper class (e.g. ReduceMAPS_MultiRep2015 here)

        exception to change the output folder to save data to
    """
    inst_dir = '/ceph/home/isis_direct_soft/InstrumentFiles/merlin/';
    data_dir1 = r'//isis/inst$/NDXMERLIN/Instrument/data/cycle_17_1'    
    data_dir2 = '/archive/NDXMERLIN/Instrument/data/cycle_16_5/;/archive/NDXMERLIN/Instrument/data/cycle_16_4/'
    config.appendDataSearchDir('{0};{1};{2}'.format(inst_dir,data_dir1,data_dir2))    

    web_var.advanced_vars['hardmaskPlus'] = os.path.join(AUTOREDUCTION_DIR, web_var.advanced_vars['hardmaskPlus'])
    web_var.advanced_vars['det_cal_file'] = os.path.join(AUTOREDUCTION_DIR, web_var.advanced_vars['det_cal_file'])
    web_var.advanced_vars['map_file'] = os.path.join(AUTOREDUCTION_DIR, web_var.advanced_vars['map_file'])

    # note web variables initialization
    rd = mer_red.MERLINReduction(web_var)

    file,ext = os.path.splitext(input_file)
    fext = rd.reducer.prop_man.data_file_ext

    input_file = file+fext

    rd.reduce(input_file,output_dir)
    
    # Define folder for web service to copy results to
    output_folder = ''
    return output_folder

if __name__ == "__main__":
#------------------------------------------------------------------------------------#
# TESTING OPTIONS                                                                    #
#------------------------------------------------------------------------------------#
##### Here one sets up folders where to find input data and where to save results ####
    # It can be done here or from Mantid GUI:
    #      File->Manage user directory ->Browse to directory
    # Folder where map and mask files are located:
    #map_mask_dir = 'c:/Users/wkc26243/Documents/work/Libisis/InstrumentFiles/let'
    # folder where input data can be found
    #data_dir = 'd:/Data/Mantid_Testing/15_01_27/LET/data'
    # auxiliary folder with results
    #rez_dir = 'd:/Data/Mantid_Testing/15_01_27/LET'
    # Set input search path to values, specified above
    #config.setDataSearchDirs('{0};{1};{2}'.format(data_dir,map_mask_dir,rez_dir))
    # use appendDataSearch directory to add more locations to existing Mantid 
    # data search path
    #config.appendDataSearchDir('d:/Data/Mantid_GIT/Test/AutoTestData')
    # folder to save resulting spe/nxspe files.
    #config['defaultsave.directory'] = rez_dir
    # Define input file and output directory
    #input_file='/isis/NDXMERLIN/Instrument/data/cycle_15_3/MER28083.raw'
    #output_dir='/autoreducetmp/instrument/MERLIN/RBNumber/RB1520329/autoreduced/'
    #input_file=r'/archive/NDXMERLIN/Instrument/data/cycle_15_3/MER28161.raw'
    #output_dir=r'/home/isisautoreduce/tt'
    input_file=r'd:\Data\Mantid_Testing\15_11\MER28161.raw'
    output_dir=r'd:\Data\Mantid_Testing\15_11'
    main(input_file,output_dir)

