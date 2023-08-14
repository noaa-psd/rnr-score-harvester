""" Collection of methods to faciliate retrieval of global mean surface         
    temperature (GMST) and global surface air temperature (GSAT). GMST is   
    defined as the average temperature of the upper few meters of the ocean, 
    aka sea surface temperature (SST), and 2 m air temperature
    over land and sea ice. GMST is defined as the global mean 2 m air   
    temperautre (Arias et al., 2021).

    References
    
    Arias, P.A., N. Bellouin, E. Coppola, R.G. Jones, G. Krinner, J. Marotzke, 
    V. Naik, M.D. Palmer, G.-K. Plattner, J. Rogelj, M. Rojas, J. Sillmann, T. 
    Storelvmo, P.W. Thorne, B. Trewin, K. Achuta Rao, B. Adhikary, R.P. Allan, 
    K. Armour, G. Bala, R. Barimalala, S. Berger, J.G. Canadell, C. Cassou, A. 
    Cherchi, W. Collins, W.D. Collins, S.L. Connors, S. Corti, F. Cruz, F.J. 
    Dentener, C. Dereczynski, A. Di Luca, A. Diongue Niang, F.J. Doblas-Reyes, 
    A. Dosio, H. Douville, F. Engelbrecht, V. Eyring, E. Fischer, P. Forster, 
    B. Fox-Kemper, J.S. Fuglestvedt, J.C. Fyfe, N.P. Gillett, L. Goldfarb, I. 
    Gorodetskaya, J.M. Gutierrez, R. Hamdi, E. Hawkins, H.T. Hewitt, P. Hope, 
    A.S. Islam, C. Jones, D.S. Kaufman, R.E. Kopp, Y. Kosaka, J. Kossin, S. 
    Krakovska, J.-Y. Lee, J. Li, T. Mauritsen, T.K. Maycock, M. Meinshausen, 
    S.-K. Min, P.M.S. Monteiro, T. Ngo-Duc, F. Otto, I. Pinto, A. Pirani, K. 
    Raghavan, R. Ranasinghe, A.C. Ruane, L. Ruiz, J.-B. Sallée, B.H. Samset, S. 
    Sathyendranath, S.I. Seneviratne, A.A. Sörensson, S. Szopa, I. Takayabu, 
    A.-M. Tréguier, B. van den Hurk, R. Vautard, K. von Schuckmann, S. Zaehle, 
    X. Zhang, and K. Zickfeld, 2021: Technical Summary. In Climate Change 2021: 
    The Physical Science Basis. Contribution of Working Group I to the Sixth 
    Assessment Report of the Intergovernmental Panel on Climate Change 
    [Masson-Delmotte, V., P. Zhai, A. Pirani, S.L. Connors, C. Péan, S. Berger, 
    N. Caud, Y. Chen, L. Goldfarb, M.I. Gomis, M. Huang, K. Leitzell, E. 
    Lonnoy, J.B.R. Matthews, T.K. Maycock, T. Waterfield, O. Yelekçi, R. Yu, 
    and B. Zhou (eds.)]. Cambridge University Press, Cambridge, United Kingdom 
    and New York, NY, USA, pp. 33−144, doi:10.1017/9781009157896.002.
"""

import os

from collections import namedtuple
from dataclasses import dataclass
from dataclasses import field
import numpy as np

from score_hv.config_base import ConfigInterface

HARVESTER_NAME = 'global_surface_temperature'
VALID_STATISTICS = ('mean')
VALID_VARIABLES = ['gsat', 'gmst']

HarvestedData = namedtuple('HarvestedData', ['datafile',
                                             'statistic',
                                             'variable',
                                             'value',
                                             'units'])
                                             
@dataclass
class GlobalSurfaceTemperatureConfig(ConfigInterface):
    """ Dataclass to hold and provide configuration information pertaining to
        how the harvester should calculate global surface temperature
    
        Parameters:
        -----------
        config_data: dict - contains configuration data parsed from either an
                            input yaml file or input dict
        
    """
    config_data: dict = field(default_factory=dict)
    
    def __post_init__(self):
        self.set_config()
    
    def set_config(self):
        """ function to set configuration variables from given dictionary
        """ 
        self.harvest_filenames = self.config_data.get('filenames')
        self.set_stats()
        self.set_variables()
    
    def set_variables(self):
        """
        set the variables specified by the config dict
        """
        
        self.variables = self.config_data.get('variable')
        for var in self.variables:
            if var not in VALID_VARIABLES:
                msg = ("'%s' is not a supported global surface temperature "
                       "variable to harvest from the background forecast data. "
                       "Please reconfigure the input dictionary using only the "
                       "following variables: %r" % (var, VALID_VARIABLES))
                raise KeyError(msg)

    def set_stats(self):
        """
        set the statistics specified by the config dict
        """
        self.stats = self.config_data.get('statistic')
        for stat in self.stats:
            if stat not in VALID_STATISTICS:
                msg = ("'%s' is not a supported statistic to harvest for global "
                       " surface temperature. "
                       "Please reconfigure the input dictionary using only the "
                       "following statistics: %r" % (stat, VALID_STATISTICS))
                raise KeyError(msg)
    
    def get_stats(self):
        ''' return list of all stat types based on harvest_config '''
        return self.stats
        
    def get_variables(self):
        ''' return list of all variable types based on harvest_config'''
        return self.variables
        
@dataclass
class GlobalSurfaceTemperatureHv(object):
    """ Harvester dataclass used to parse global surface temperature stored in 
        background forecast data
    
        Parameters:
        -----------
        config: TemperatureConfig object containing information used to determine
                which variable to parse the log file
        Methods:
        --------
        get_data: parse descriptive statistics from log files based on input
                  config file
    
                  returns a list of tuples containing specific data
    """
    config: GlobalSurfaceTemperatureConfig = field(
                                default_factory=GlobalSurfaceTemperatureConfig)
    
    def get_data(self):
        """ Harvests GMST and GSAT from background forecast data
        
            returns harvested_data, a list of HarvestData tuples
        """
        harvested_data = list()
        
        for i, variable in enumerate(self.config.get_variables()):
            """ The first nested loop iterates through each requested variable
            """
            for j, statistic in enumerate(self.config.get_stats()):
                """ The second nested loop iterates through each requested 
                    statistic
                """
                harvested_data.append(HarvestedData(None, statistic, variable,
                                                    np.nan, None))
                                                    
        return harvested_data
        