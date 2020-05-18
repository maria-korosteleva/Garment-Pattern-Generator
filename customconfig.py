"""
    The module contain Porperties class to manage paramters & stats in various parts of the system
    The module might be used in Maya, so its Python 2.7 compatible
"""

from datetime import timedelta
import json
from numbers import Number


class Properties():
    """Keeps, loads, and saves cofiguration & statistic information
        Supports gets&sets as a dictionary
        Provides shortcuts for batch-init configurations

        One of the usages -- store system-dependent basic cofiguration
    """
    def __init__(self, filename="", clean_stats=False):
        self.properties = {}

        if filename:
            self.properties = self._from_file(filename)
            if clean_stats:  # only makes sense when initialized from file =) 
                self.clean_stats(self.properties)

    def has(self, key):
        """Used to quety if a top-level property/section is already defined"""
        return key in self.properties

    def merge(self, filename="", clean_stats=False):
        """Merge current set of properties with the one from file
            As with Python dicts, values from new props overrite 
            the one from old one if keys are the same
        """
        new_props = self._from_file(filename)
        if clean_stats:
            self.clean_stats(new_props)
        # merge
        self._recursive_dict_update(self.properties, new_props)

    def set_section_config(self, section, **kwconfig):
        """adds or modifies a (top level) section and updates its configuration info
        """
        # create new section
        if section not in self.properties:
            self.properties[section] = {
                'config': kwconfig,
                'stats': {}
            }
            return
        # section exists
        for key, value in kwconfig.items():
            self.properties[section]['config'][key] = value
        
    def set_section_stats(self, section, **kwstats):
        """adds or modifies a (top level) section and updates its statistical info
        """
        # create new section
        if section not in self.properties:
            self.properties[section] = {
                'config': {},
                'stats': kwstats
            }
            return
        # section exists
        for key, value in kwstats.items():
            self.properties[section]['stats'][key] = value

    def set_basic(self, **kwconfig):
        """Adds/updates info on the top level of properties
            Only to be used for basic information!
        """
        # section exists
        for key, value in kwconfig.items():
            self.properties[key] = value

    def clean_stats(self, properties):
        """ Remove info from all Stats sub sections """
        for key, value in properties.items():
            # detect section
            if isinstance(value, dict) and 'stats' in value:
                value['stats'] = {}

    def summarize_stats(self, key, log_sum=False, log_avg=False, as_time=False):
        """Make a summary of requested key with requested statistics in current props"""
        for section in self.properties.values():
            # check all stats sections
            if isinstance(section, dict) and 'stats' in section:
                if key in section['stats']:
                    stats_values = section['stats'][key]
                    if isinstance(stats_values, dict):
                        stats_values = stats_values.values()
                    # summarize all foundable statistics
                    if isinstance(stats_values, list) and len(stats_values) > 0 and isinstance(stats_values[0], Number):
                        if log_sum:
                            section['stats'][key + "_sum"] = str(timedelta(seconds=sum(stats_values))) if as_time else sum(stats_values)
                        if log_avg:
                            section['stats'][key + "_avg"] = sum(stats_values) / len(stats_values)
                            if as_time:
                                section['stats'][key + "_avg"] = str(timedelta(seconds=section['stats'][key + "_avg"]))

    def serialize(self, filename):
        """Log current props to file"""
        # gather stats first
        with open(filename, 'w') as f_json:
            json.dump(self.properties, f_json, indent=2, sort_keys=True)

    def _from_file(self, filename):
        """ Load properties from previously created file """
        with open(filename, 'r') as f_json:
            return json.load(f_json)

    def _recursive_dict_update(self, in_dict, new_dict):
        """updates input dictionary with the update_dict properly updating all the inner dictionaries"""
        if not isinstance(new_dict, dict):
            in_dict = new_dict  # just update with all values
            return

        for new_key in new_dict:
            if new_key in in_dict and isinstance(in_dict[new_key], dict):
                # update inner dict properly
                self._recursive_dict_update(in_dict[new_key], new_dict[new_key])
            else:  # at sertain depth there will be no more dicts -- recusrion stops
                in_dict[new_key] = new_dict[new_key]
        # if new_dict is empty -- no update happens

    def __getitem__(self, key):
        return self.properties[key]

    def __setitem__(self, key, value):
        self.properties[key] = value

    def __contains__(self, key):
        return key in self.properties

    def __str__(self):
        return str(self.properties)
