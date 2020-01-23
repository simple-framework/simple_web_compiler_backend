# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os
from django.http import HttpResponse

from django.shortcuts import render

from forms.upload_conf_file_form import UploadSiteConfForm

from simple_grid_yaml_compiler import yaml_compiler


def augment_conf_file(file):
    os.mkdir('.temp')
    yaml_compiler.execute_compiler(file, '.temp/augmented_conf.yaml', '<add schema>') # TODO: add schema
    os.removedirs('.temp')
    return 'SUCCESS'


def compile_yaml(request):
    if request.method == 'POST':
        form = UploadSiteConfForm(request.POST, request.FILES)
        if form.is_valid():
            augment_conf_file(request.FILES['file'])
            return HttpResponse("UPLOADED!")
        else:
            print form.errors
    else:
        form = UploadSiteConfForm()
        return render(request, 'compile_yaml.html', {'form': form})