def reader(gsifortfile, verbosity=0):
    """return a reader object which will iterate over lines in the given
    gsifortfile
    
    each row read from the gsifortfile is returned as a list of strings
    """
    with open(gsifortfile) as gsifortfile:
        if verbosity > 0:
            for row in gsifortfile:
                print(row)        
        
        return gsifortfile.readlines()
    
class DictReader(object):
    """create an object that operates like a regular reader but maps the
    information in each row to a dict"""
    def __init__(self, gsifortfile, fieldnames=('it', 'obs', 'use', 'typ', 
                                                'styp', 'ptop', 'pbot', 
                                                'count', 'bias', 'rms', 'cpen', 
                                                'qcpen'),
                 verbosity=0):
        
        true_option = None
        self.fit_psfc_rows = list()
        for row in reader(gsifortfile, verbosity=verbosity):
            if row.split('data')[0] == 'current fit of surface pressure ':
                true_option='fit_psfc'
            elif row.split('data')[0] == 'current vfit of wind ':
                true_option = 'fit_wind'
                fit_wind_data = True
            elif row.split('data')[0] == 'current fit of temperature ':
                true_option = 'fit_temp'
            elif row.split('data')[0] == 'current fit of q ':
                true_option = 'fit_rhum'
            elif row.split('data')[0] == 'current fit of gps ':
                true_option = 'fit_gps'
                
            row_parts = row.split()
            if true_option == 'fit_psfc' and row_parts[0] == 'o-g':
                """
                """
                if row_parts[1] == 'it':
                    # header row
                    row_fieldnames = list()
                    row_indicies = list()
                    for fieldname in fieldnames:
                        if fieldname in row_parts:
                            row_fieldnames.append(fieldname)
                            row_indicies.append(row_parts.index(fieldname))
                else:
                    # data rows
                    for fieldname_index, fieldname in enumerate(row_fieldnames):
                        self.fit_psfc_rows.append(
                            {fieldname: 
                                row_parts[row_indicies[fieldname_index]]})
                                
        print(row_fieldnames)
                       
if __name__=='__main__':
    import sys
    import argparse
    import ipdb
    
    parser = argparse.ArgumentParser()
    parser.add_argument("gsifortfile")
    parser.add_argument('--verbose', '-v', action='count', default=0)
    args = parser.parse_args()

    dict_reader = DictReader(args.gsifortfile, verbosity=args.verbose)