import re
import urllib2
from urlparse import urlparse, urljoin
import constants as constants


def get_file_location(repo_info, file_type):
    base = "./.temp/" + repo_info["repo_name"]

    suffix = {
        "defaults": "_defaults.yaml",
        "config_schema": "_schema.yaml",
        "meta_info": "_info.yaml",
        "site_level_defaults": "_site_level_defaults.yaml"
    }

    return base + suffix[file_type]

def analyse_repo_url(repo_url, revision="master"):
    repo_analysis = re.search('//.*/(.*)/(.*)', repo_url)
    org_name = repo_analysis.group(1)
    repo_name = repo_analysis.group(2)
    return {
        'org_name':org_name,
        'repo_name': repo_name,
        'branch_name': revision
    }

def generate_meta_info_parent_name(meta_info_file):
    with open(meta_info_file, 'r') as meta_info:
        for line in meta_info:
            if "component" in line:
                parent_name = line.split(':')[1].strip().lower()
                return 'meta_info_' + ''.join(parent_name.split('"'))


def augment_meta_info(meta_info_file):
    augmented_meta_info = ""
    component_line = ""
    meta_info_parent_name = generate_meta_info_parent_name(meta_info_file)
    with open(meta_info_file, 'r') as meta_info:
        for line in meta_info:
            augmented_meta_info += "    " + line
    augmented_meta_info = meta_info_parent_name + ":\n" + augmented_meta_info
    with open(meta_info_file, 'w') as meta_info:
        meta_info.write(augmented_meta_info)
        return meta_info


def get_repo_file(repo_url, file_name, file_type, branch = "master", post_func=None):
    try:
        base_url  = urlparse("https://raw.githubusercontent.com/", branch)
        repo_info = analyse_repo_url(repo_url, branch)

        repo_info_list = [
            repo_info['org_name'],
            repo_info['repo_name'],
            repo_info['branch_name'],
            file_name
        ]

        relative_url = urlparse('/'.join(x.strip() for x in repo_info_list))

        file_url = urljoin(base_url.geturl(), relative_url.geturl())

        response = urllib2.urlopen(file_url)

        file_loc = get_file_location(repo_info, file_type)

        with open(file_loc, "w") as file:
            file.write(response.read())

        if post_func is not None:
           return post_func(file_loc).name

        return file_loc

    except Exception as ex:
        print(ex.message)

def get_base_files(repo_url, branch='master'):
    for file, file_type in constants.BASE_FILES:
        get_repo_file(repo_url, file, file_type, branch=branch)
