import configparser

class ConfigParse:
    def __init__(self, filename):
        self.config = configparser.ConfigParser()
        self.config.optionxform = str
        self.config.read(filename)
        self.configs = self._load_all_settings()


    def get_setting(self, key, default=None, value_type=str):
        return self._get_value('Setting', key, default, value_type)

    def get_filter(self, key, default=None, value_type=str):
        return self._get_value('Filters', key, default, value_type)

    def _get_value(self, section, key, default, value_type):
        try:
            if value_type == int:
                return self.config.getint(section, key)
            elif value_type == float:
                return self.config.getfloat(section, key)
            elif value_type == bool:
                return self.config.getboolean(section, key)
            else:
                return self.config.get(section, key)
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError) as e:
            print(f"Warning: {e}. Using default value: {default}")
            return default

    def _load_all_settings(self):
        configs = {}
        for section in self.config.sections():
            configs[section] = {}
            for key, value in self.config.items(section):
                # Attempt to convert values to int, float, or bool if applicable
                try:
                    configs[section][key] = int(value)
                except ValueError:
                    try:
                        configs[section][key] = float(value)
                    except ValueError:
                        if value.lower() in ['true', 'false']:
                            configs[section][key] = value.lower() == 'true'
                        else:
                            configs[section][key] = value
        return configs

    def print_all_settings(self):
        print("************CONFIG***********")
        for section, params in self.configs.items():
            print(f"[{section}]")
            for key, value in params.items():
                print(f"{key}={value}")
            print()  # Print a newline for better readability
        print("******************************")
        print()