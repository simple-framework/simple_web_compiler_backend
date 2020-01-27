# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os
import sys
from ruamel.yaml import YAML

from django.shortcuts import render

from forms.upload_conf_file_form import UploadSiteConfForm

from simple_grid_yaml_compiler import yaml_compiler


def augment_conf_file(config):
    if not os.path.exists('.temp'):
        os.mkdir('.temp')

    schema_file_path = os.getcwd() + '/.temp/schema.yaml'

    with open('.temp/augmented_conf.yaml', 'w') as output_file:
        yaml_compiler.execute_compiler(config, output_file, schema_file_path)

    with open('.temp/augmented_conf.yaml', 'r') as output_file, open(schema_file_path, 'r') as schema_file:
        # yaml = YAML()
        # yaml.indent(mapping=2, sequence=4, offset=2)
        # augmented_conf = yaml.load(output_file)
        # schema = yaml.load(schema_file)
        # return yaml.dump(augmented_conf), 'yaml.dump(schema)'
        return output_file.read(), schema_file.read()


def compile_yaml(request):
    if request.method == 'POST':
        form = UploadSiteConfForm(request.POST, request.FILES)
        if form.is_valid():
            [augmented_conf, schema] = augment_conf_file(request.FILES['site_config'])
            return render(request, 'compile_yaml.html', {'form': form, 'augmented_conf': augmented_conf, 'schema': schema})
        else:
            print form.errors
    else:
        form = UploadSiteConfForm()
        return render(request, 'compile_yaml.html', {'form': form})