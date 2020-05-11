from ruamel.yaml import YAML

def check_yaml_syntax(expanded_yaml_file):
    #try:
        yaml = YAML()
        expanded_yaml_file_temp = open(expanded_yaml_file.name, 'r')
        augmented_yaml = yaml.load(expanded_yaml_file_temp)
        augmented_site_level_configuration_file = open("./.temp/augmented_yaml_file_final.yaml", 'w')
        yaml.dump(augmented_yaml, augmented_site_level_configuration_file)
        augmented_site_level_configuration_file.close()
        return augmented_site_level_configuration_file
    # except yaml.YAMLError as exc:
    #     print(exc.message)
    #     return expanded_yaml_file
