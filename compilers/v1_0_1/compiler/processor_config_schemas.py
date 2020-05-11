from ruamel.yaml import YAML
from compiler.repo_processor import generate_meta_info_parent_name

import re

def find_component_data(data, meta_info):
    components = []
    for component in data['lightweight_components']:
        if component['name'] == meta_info['component']:
            components.append(component)

    return components


def lookup(data, parameter):
    value = None
    try:
        value = data[parameter]
    except Exception as ex:
        pass
    return value


def lookup_defaults(default_data, meta_info, parameter):
    default_value = None
    #try:
    default_value = default_data[meta_info['default_var_prefix'] + '_' + parameter]
    #except Exception as ex:
    #    print ex.message

    return default_value


def get_final_config_values_for_component(component, expected_params, defaults_for_expected_params, meta_info):
        final_component_data = {}
        print " No of expected params: " + str(len(expected_params))
        i=0
        for config_param in expected_params:
            value = None
            i=i+1
            print "  - Param " + str(i) + " :" +config_param
            if expected_params[config_param]['required']:
                print "     - required: True"
                value_defined_by_user = lookup(component, config_param)
                if value_defined_by_user != None:
                    print "     - specified: True"
                    value = value_defined_by_user
                    print "     - user-defined-value: " + str(value)
                else:
                    print "     - specified: False"
                    #check use_default
                    if expected_params[config_param]['use_default']:
                        print "     - use-default: True"
                        default_value = lookup_defaults(defaults_for_expected_params, meta_info, config_param)
                        print "     - default-value: " + str(default_value)
                        value = default_value
                    else:
                        print "     - use-default: False"
            else:
                print "     - required: False"
                value_defined_by_user = lookup(component, config_param)
                if value_defined_by_user != None:
                    print "     - specified: True"
                    value = value_defined_by_user
                    print "     - user-defined-value: " + str(value)
                else:
                    print "     - specified: False"
                    if expected_params[config_param]['use_default']:
                        print "     - use-default: True"
                        default_value = lookup_defaults(defaults_for_expected_params, meta_info, config_param)
                        print "     - default-value: " + str(default_value)
                        value = default_value
                    else:
                        print "     - use-default: False"
                        value = "Ignore"
            print "     - Final Value: " + str(value)
            if value is None:
                message = "A value needs to be specified for " + str(config_param) + " in your site level config file for correctly configuring component "
                raise Exception(message)
                sys.exit(message)
            if value is not "Ignore":
                final_component_data[str(config_param)] = value
        return final_component_data


def process_config_schema(component, config_schema_file, default_data_runtime_file, meta_info ):
    yaml = YAML()
    config_schema_file = open(config_schema_file.name, 'r')
    config_schema = yaml.load(config_schema_file)
    default_data_file = open(default_data_runtime_file.name, 'r')
    default_data = yaml.load(default_data_file)
    expected_key = str(meta_info['component']).lower() + '-expected-from-site-level-config'
    expected_params = config_schema['expected-from-site-level-config']
    defaults_for_expected_params = default_data[expected_key]
    final_config_for_component = get_final_config_values_for_component(component, expected_params, defaults_for_expected_params, meta_info)
    print final_config_for_component
    return final_config_for_component

def get_final_config(config, expected_params, defaults, meta_info, expandable_types, indent=0):
    for index, param in enumerate(expected_params, 1):
        print "     " * indent + "Param {}: {}".format(index, param)

        param_type = expected_params[param]['type']

        if param_type in expandable_types:
            config[param] = get_final_config(
                    config = config[param],
                    expected_params = expandable_types[param_type],
                    defaults = defaults,
                    meta_info = meta_info,
                    expandable_types = expandable_types,
                    indent = indent + 1)

            continue

        else:
            match = re.match("list\((.*)\)", param_type)

            if match and match.group(1) in expandable_types:
                final_values = []
                base_type    = match.group(1)

                for index, value in enumerate(config[param]):
                    if index:
                        print "     " * (indent + 1) + "-----------"

                    final_value = get_final_config(
                        config = value,
                        expected_params = expandable_types[base_type],
                        defaults = defaults,
                        meta_info = meta_info,
                        expandable_types = expandable_types,
                        indent = indent + 1)

                    final_values.append(final_value)

                config[param] = final_values
                continue

        is_required  = expected_params[param]["required"]
        use_default  = expected_params[param]["use_default"]
        is_specified = True if param in config else False

        default_value = None
        final_value   = None

        print "     " * (indent + 1) + "- required: {}".format(is_required)
        print "     " * (indent + 1) + "- use_default: {}".format(use_default)
        print "     " * (indent + 1) + "- specified: {}".format(is_specified)

        if use_default:
            default_value = lookup_defaults(defaults, meta_info, param)
            print "     " * (indent + 1) + "- default_value: {}".format(default_value)

        if is_specified:
            print "     " * (indent + 1) + "- user_defined_value: {}".format(config[param])

        if is_specified:
            final_value = config[param]
        elif use_default:
            final_value = default_value

        if final_value is None and is_required:
            message = "A value is required is required for parameter ({}) but is not specified in the config schema".format(param)
            raise Exception(message)

        if final_value is not None:
            print "     " * (indent + 1) + "- final_value: {}".format(final_value)
            config[param] = final_value

    return config

def process_complete_schema(config, config_schema_file, defaults_file, meta_info_file):
    yaml = YAML()

    config_schema_file = open(config_schema_file, "r")
    defaults_file      = open(defaults_file, "r")
    meta_info_file     = open(meta_info_file, "r")

    # Config schema has expected schema and all the expandable types
    config_schema = yaml.load_all(config_schema_file)
    defaults      = yaml.load(defaults_file)
    meta_info     = yaml.load(meta_info_file)

    expected_params  = None
    expandable_types = {}

    for yaml_doc in config_schema:
        for key in yaml_doc:
            if key == "expected":
                expected_params = yaml_doc[key]

            else:
                expandable_types[key] = yaml_doc[key]

    if expected_params is None:
        message = "Config schema needs to have an expected params section"
        raise Exception(message)

    return get_final_config(config, expected_params, defaults, meta_info, expandable_types)
