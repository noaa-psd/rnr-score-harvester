"""Collection of methods to facilitate retrieval of the replay analysis
increments (from the fv3_increment6.nc files)
"""

HARVESTER_NAME = 'replay_analysis_increments'
VALID_STATISTICS = ('mean', 'variance', 'minimum', 'maximum')

"""Variables of interest that come from the analysis increment data.
Commented out variables can be uncommented to generate gridcell weighted
statistics but are in development and are currently not fully supported.
"""
VALID_VARIABLES  = ()

HarvestedData = namedtuple('HarvestedData', [])

#TODO: move get_gridcell_area_data_path() to utils file
def get_gridcell_area_data_path():
    return os.path.join(Path(__file__).parent.parent.parent.parent.resolve(),
                        'data', 'gridcell-area' + 
                        '_noaa-ufs-gefsv13replay-pds' + 
                        '_bfg_control_1536x768_20231116.nc')
@dataclass
class IncrementsConfig(ConfigInterface):

    config_data: dict = field(default_factory=dict)

    def __post_init__(self):
        self.set_config()

    def set_config(self):
        """function to set configuration variables from given dictionary
        """
        self.harvest_filenames = self.config_data.get('filenames')
        self.set_stats()
        self.set_variables()

    def set_variables(self):
        """set the variables specified by the config dict
        """
        
        self.variables = self.config_data.get('variable')
        for var in self.variables:
            if var not in VALID_VARIABLES:
                msg = ("'%s' is not a supported "
                       "variable to harvest from the replay analysis " 
                       "increments (fv3_increment6.nc). "
                       "Please reconfigure the input dictionary using only the "
                       "following variables: %r" % (var, VALID_VARIABLES))
                raise KeyError(msg)
    
    def get_stats(self):
        '''return list of all stat types based on harvest_config '''
        return self.stats

    def set_stats(self):
        """set the statistics specified by the config dict
        """
        self.stats = self.config_data.get('statistic')
        for stat in self.stats:
            if stat not in VALID_STATISTICS:
                msg = ("'%s' is not a supported statistic to harvest from "
                       "the replay analysis increments (fv3_increment6.nc). "
                       "Please reconfigure the input dictionary using only the "
                       "following statistics: %r" % (stat, VALID_STATISTICS))
                raise KeyError(msg)

    def get_variables(self):
        '''return list of all variable types based on harvest_config'''
        return self.variables

@dataclass
class IncrementsHv(object):
    """Harvester dataclass used to parse daily mean statistics from the replay 
    analysis increments
    
    Parameters:
    -----------
    config: IncrementsConfig object containing information used to determine
            which variable to harvest
    Methods:
    --------
    get_data: calculate descriptive statistics from analysis increments 
              based on input config file
    
    returns a list of tuples containing specific data
    """
    config: IncrementsConfig = field(default_factory=IncrementsConfig)
    
    def get_data(self):
        """Harvests requested statistics and variables from replay analysis 
        increments and returns harvested_data, a list of HarvestData tuples
        """
        
        harvested_data = list()
        
        return harvested_data