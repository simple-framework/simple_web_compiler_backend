import os

from compiler import lexemes
from compiler import semantics, yaml_augmentation, repo_processor, runtime_variables, processor_config_schemas, yamale_converter
import argparse
from ruamel.yaml import YAML
from shutil import copyfile
from simple_grid_yaml_compiler.compiler import constants


# fetch repos, add include statement for the downloaded default_values.yaml
# INPUT: raw site-level-config file filled by site admin
# PROCESS: extract repo_urls, download and save default files and meta info files for repositories
# OUTPUT: include statements for default files and meta-info files of repositories + raw site level-config file
def phase_1(site_level_configuration_file):
    # fetch repo and get default_values.yaml
    repo_processor.get_base_files(constants.BASE_REPO_URL, constants.BASE_REPO_REVISION)
    main_default_values_file = repo_processor.get_repo_file(constants.BASE_REPO_URL, "site_level_configuration_defaults.yaml", "site_level_defaults", branch=constants.BASE_REPO_REVISION)
    repo_urls = lexemes.get_repo_list(site_level_configuration_file)
    print(repo_urls)
    file_names_repository_default = [main_default_values_file]
    file_names_repository_meta = []
    for url in repo_urls:
        file_names_repository_default.append(
            repo_processor.get_repo_file(url['url'], 'default-data.yaml', "defaults", branch=url['revision']))
        file_names_repository_meta.append(
            repo_processor.get_repo_file(url['url'], "meta-info.yaml", "meta_info", branch=url['revision'], post_func=repo_processor.augment_meta_info))
    all_includes = file_names_repository_meta + file_names_repository_default
    includes_yaml_file = yaml_augmentation.add_include_statements(all_includes, site_level_configuration_file)
    return includes_yaml_file, repo_urls

# add data from all includes
# INPUT: include statements for default files of repositories + include statements for meta-info.yaml's +  raw site level-config file
# PROCESS: recursively replace include statements with contents of the files that are to be included.
# OUTPUT: include statements replaced by contents of referred files + raw site-level-config file
def phase_2(default_includes_yaml_file):
    return yaml_augmentation.add_included_files(default_includes_yaml_file)


def phase_3(include_made):
    runtime_vars, config_file = runtime_variables.extract_runtime_variables(include_made)
    return runtime_vars, runtime_variables.add_runtime_variables(runtime_vars, config_file)


# syntax_checking
def phase_4(final_yaml_file):
    return semantics.check_yaml_syntax(final_yaml_file)


def phase_5(phase_4_output, runtime_vars, yaml):
    phase_4_output_file = open(phase_4_output.name, 'r')
    phase_5_output_file = open("./.temp/phase_5_output.yaml", 'w')
    data = yaml.load(phase_4_output_file)

    base_repo_info = repo_processor.analyse_repo_url(constants.BASE_REPO_URL, constants.BASE_REPO_REVISION)

    base_repo_file = lambda x: repo_processor.get_file_location(base_repo_info, x)

    data = processor_config_schemas.process_complete_schema(
            config = data,
            config_schema_file = base_repo_file("config_schema"),
            defaults_file = base_repo_file("defaults"),
            meta_info_file = base_repo_file("meta_info")
            )

    phase_5_output = {}
    for data_section in data:
        if data_section == 'lightweight_components':
            updated_components = []
            for lightweight_component in data[data_section]:
                print "Component: " + lightweight_component['name']
                updated_component = {}
                for component_section in lightweight_component:
                    if component_section == 'config':
                        repo_url = lightweight_component['repository_url']
                        repo_version = lightweight_component['repository_revision']
                        repo_processor.get_repo_file(repo_url, "config-schema.yaml", "config_schema", branch=repo_version)
                        repo_processor.get_repo_file(repo_url, "meta-info.yaml", "meta_info", branch=repo_version, post_func=repo_processor.augment_meta_info)
                        repo_info = repo_processor.analyse_repo_url(repo_url, repo_version)
                        config_schema_file_name = repo_processor.get_file_location(repo_info, "config_schema")
                        config_schema_file = open(config_schema_file_name, 'r')
                        meta_info_file = repo_processor.get_file_location(repo_info, "meta_info")
                        meta_info_parent_name = repo_processor.generate_meta_info_parent_name(meta_info_file)
                        meta_info = data[meta_info_parent_name]
                        default_data_file_name = repo_processor.get_file_location(repo_info, "defaults")
                        default_data_runtime_file = open(default_data_file_name + ".runtime", 'w')
                        default_data_file = open(default_data_file_name, 'r')
                        default_data_runtime_file.write(runtime_vars)
                        for l in default_data_file.readlines():
                            default_data_runtime_file.write(l)
                        default_data_file.close()
                        default_data_runtime_file.close()
                        config_schema_file.close()
                        augmented_config = processor_config_schemas.process_config_schema(lightweight_component[component_section], config_schema_file, default_data_runtime_file, meta_info)
                        updated_component[component_section] = augmented_config
                    else:
                        updated_component[component_section] = lightweight_component[component_section]
                updated_components.append(updated_component)
            phase_5_output[data_section] = updated_components
        else:
            phase_5_output[data_section] = data[data_section]
    yaml.dump(phase_5_output, phase_5_output_file)
    phase_5_output_file.close()
    return phase_5_output_file


def phase_6(phase_5_output_file, yaml):
    phase_5_output = open(phase_5_output_file.name, 'r')
    input_data = yaml.load(phase_5_output)
    phase_6_output_file = open("./.temp/phase_6_output.yaml", 'w')
    #pass 1
    variable_hierarchies = lexemes.parse_for_variable_hierarchies(input_data, "__from__")
    #pass 2
    split_config = yaml_augmentation.split_component_config(variable_hierarchies)
    #pass 3
    container_split_config = yaml_augmentation.split_container_config(variable_hierarchies)
    #pass 4
    with_ids =  yaml_augmentation.add_execution_ids(container_split_config)
    print with_ids
    yaml.dump(with_ids, phase_6_output_file)
    return phase_6_output_file

def phase_7(yamale_flie, config_file):
    yaml = YAML()

    base_repo_info     = repo_processor.analyse_repo_url(constants.BASE_REPO_URL, constants.BASE_REPO_REVISION)
    config_schema_file = repo_processor.get_file_location(base_repo_info, "config_schema")

    lc_schemas = set()

    config_file = open(config_file, "r")
    config = yaml.load(config_file)

    for lc in config["lightweight_components"]:
        lc_url    = lc["repository_url"]
        lc_revision = lc["repository_revision"]
        lc_info   = repo_processor.analyse_repo_url(lc_url, lc_revision)
        lc_schema = repo_processor.get_file_location(lc_info, "config_schema")

        lc_schemas.add(lc_schema)

    yamale_converter.yamale_converter(config_schema_file, yamale_flie, lc_schemas)

def parse_args():

    parser = argparse.ArgumentParser()
    parser.add_argument('filename')
    parser.add_argument('-o', '--output')
    parser.add_argument('-s', '--schema')
    args = parser.parse_args()
    return {
        'site_level_configuration_file': args.filename,
        'output': args.output,
        'schema': args.schema
    }

def execute_compiler(site_level_configuration_file, output, schema):
    yaml = YAML()
    phase_1_output, repo_urls = phase_1(site_level_configuration_file)
    phase_2_output = phase_2(phase_1_output)
    runtime_vars, phase_3_output = phase_3(phase_2_output)
    phase_4_output = phase_4(phase_3_output)
    phase_5_output_file = phase_5(phase_4_output, runtime_vars, yaml)
    phase_6_output = phase_6(phase_5_output_file, yaml)
    copyfile(phase_6_output.name, output.name)
    output.close()

    # Yamale schema generation
    phase_7(schema, output.name)


def main():
    args = parse_args()
    site_level_configuration_file = open(args['site_level_configuration_file'], 'r')
    output = open(args['output'], 'w')
    schema = args['schema']
    cwd = os.getcwd()
    temp_dir = "{cwd}/.temp".format(cwd=cwd)
    if not os.path.exists(temp_dir):
        os.mkdir(temp_dir)
    execute_compiler(site_level_configuration_file, output, schema)


if __name__ == "__main__":
    main()
