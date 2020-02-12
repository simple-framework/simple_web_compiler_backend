from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from collections import OrderedDict
from simple_grid_yaml_compiler import yaml_compiler

app = Flask(__name__)
CORS(app)


def augment_conf_file(config):
    if not os.path.exists('.temp'):
        os.mkdir('.temp')

    schema_file_path = os.path.join(os.getcwd(), '.temp/schema.yaml')

    with open('.temp/augmented_conf.yaml', 'w') as output_file:
        yaml_compiler.execute_compiler(config, output_file, schema_file_path)

    with open('.temp/augmented_conf.yaml', 'r') as output_file, open(schema_file_path, 'r') as schema_file:
        return output_file.read(), schema_file.read()


@app.route('/compile', methods=['POST'])
def compile():
    if request.method == 'POST':
        if 'site_conf' not in request.files:
            return "No file provided\n"
        try:
            [augmented_conf, schema] = augment_conf_file(request.files['site_conf'])
            return jsonify({'augmented_conf': augmented_conf, 'schema': schema})
        except Exception as ex:
            tempdir = os.path.join(os.getcwd(), '.temp')
            response = OrderedDict()
            response['error'] = ex.message
            for filename in os.listdir(tempdir):
                with open(os.path.join(tempdir, filename), 'r') as f:
                    response[filename] = f.read()
            return jsonify(response)


if __name__ == '__main__':
    app.run(debug=True)
