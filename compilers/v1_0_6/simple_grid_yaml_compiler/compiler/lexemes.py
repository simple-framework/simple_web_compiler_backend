import re
from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedSeq, CommentedMap

def get_repo_list(site_level_configuration_file):
    all_urls = []
    find_revision = False
    pending_url = None
    revision_line = None
    for line in site_level_configuration_file.readlines():
        if find_revision:
            revision_line = re.search('repository_revision\w*:(.*)', line)
            revision_line_string = revision_line.group(1)
            all_urls.append({
                'url': pending_url,
                'revision': revision_line_string.strip().replace("\"", '').replace('\'', '')
            })
            pending_url = None
            find_revision = False
        else:
            url_line = re.search('repository_url\w*:\w*(.*)', line)
            if url_line is not None:
                url_line_string = url_line.group()
                url = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', url_line_string)
                pending_url = url[0]
                find_revision = True
    unique_urls = [dict(y) for y in set(tuple(x.items()) for x in all_urls)]
    return unique_urls

##########################################################################
# Warning: Badass recursive way to replace all __from__ keywords correctly
##########################################################################
def parse_for_variable_hierarchies(data, keyword):
    data_type = type(data)
    if data_type is not CommentedSeq and data_type is not CommentedMap:
        return data

    if keyword in data:
        data = data[keyword]
        return parse_for_variable_hierarchies(data, keyword)

    if data_type is CommentedSeq:
        data_updated = CommentedSeq()
        for sub_data in data:
            sub_data_updated = parse_for_variable_hierarchies(sub_data, keyword)
            data_updated.append(sub_data_updated)
        return  data_updated
    elif data_type is CommentedMap:
        data_updated = CommentedMap()
        for sub_data_key in data:
            sub_data_updated = parse_for_variable_hierarchies(data[sub_data_key], keyword)
            data_updated[sub_data_key] = sub_data_updated
        return data_updated