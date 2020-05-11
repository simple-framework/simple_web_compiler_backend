## Replace runtime variables with the tag simple-runtime-{varname} and put name in a dict of var,mapped val
## mapped val is determined by yaml search query.
## basically ce_host should be moved to pre-config.py. It can be marked as pre-config.py replacable and therefore it is runtime.
## process the YAML file,
def extract_runtime_variables(includes_made):
    filename = includes_made.name
    site_config_with_includes = open(filename, 'r')
    print("RUNTIME$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
    runtime_vars = ""
    config_file = ""
    variables = ""
    copy_variable_flag = False
    copy_runtime_vairable_flag = False
    for line in site_config_with_includes.readlines():
        if "runtime_variables" in line:
            runtime_vars += line
            space_offset = len(line) - len(line.lstrip())
            copy_runtime_vairable_flag = True
            copy_variable_flag = False
            continue
        elif "global_variables:" in line:
            variables += line
            space_offset = len(line) - len(line.lstrip())
            copy_variable_flag = True
            copy_runtime_vairable_flag = False
            continue

        if copy_variable_flag is True:
            current_space_offset = len(line) - len(line.lstrip())
            if line.strip().startswith('-') and current_space_offset >space_offset: # and not line == '\n':
                variables +=line
            else:
                copy_variable_flag = False
                continue
        elif copy_runtime_vairable_flag is True:
            current_space_offset = len(line) - len(line.lstrip())
            if line.strip().startswith('-') and current_space_offset > space_offset:
                runtime_vars += line
            else:
                copy_runtime_vairable_flag = False
                continue
        else:
            config_file += line


    return variables + runtime_vars, config_file


def add_runtime_variables(runtime_vars, config_file):
    output = open('./.temp/runtime.yaml', 'w')
    output.write(runtime_vars + config_file)
    output.close()
    return output

