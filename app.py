import os
import pkgutil
import traceback
from collections import OrderedDict

from flask import Flask, request, jsonify, Response
from flask_cors import CORS

import compilers

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024
CORS(app)


def augment_conf_file(compiler, config):
    if not os.path.exists('.temp'):
        os.mkdir('.temp')

    schema_file_path = os.path.join(os.getcwd(), '.temp/schema.yaml')
    with open('.temp/augmented_conf.yaml', 'w') as output_file:
        compiler.execute_compiler(config, output_file, schema_file_path)

    with open('.temp/augmented_conf.yaml', 'r') as output_file, open(schema_file_path, 'r') as schema_file:
        return output_file.read(), schema_file.read()


@app.route('/', methods=['GET'])
def health():
    return "I'm alive."


@app.route('/versions', methods=['GET'])
def versions():
    v = []
    for importer, modname, ispkg in pkgutil.iter_modules(compilers.__path__):
        if ispkg:
            v.append(modname.replace('_', '.'))

    return jsonify(v)


@app.route('/compile', methods=['POST'])
def compile():
    if request.method == 'POST':
        tempdir = os.path.join(os.getcwd(), '.temp')
        if 'version' not in request.form:
            return Response('No version provided\n', status=400)
        else:
            pkg_version_name = request.form['version'].replace('.', '_')
            compiler = __import__('compilers.{}.simple_grid_yaml_compiler.yaml_compiler'.format(pkg_version_name),
                                  fromlist="yaml_compiler")

            print 'Imported', compiler

        if 'site_conf' not in request.files:
            return Response('No file provided\n', status=400)
        try:
            [augmented_conf, schema] = augment_conf_file(compiler, request.files['site_conf'])
            return jsonify({'augmented_conf': augmented_conf, 'schema': schema})
        except Exception as ex:
            response = OrderedDict()

            request.files['site_conf'].stream.seek(0)
            response['Input File'] = request.files['site_conf'].stream.read()

            response['error'] = traceback.format_exc()

            for filename in os.listdir(tempdir):
                with open(os.path.join(tempdir, filename), 'r') as f:
                    response[filename] = f.read()
            return jsonify(response)
        finally:
            for filename in os.listdir(tempdir):
                os.remove(os.path.join(tempdir, filename))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
