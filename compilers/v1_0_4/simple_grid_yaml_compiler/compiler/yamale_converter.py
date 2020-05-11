from ruamel.yaml import YAML

def translate(schema, expandable_types):
	# Keys in the in basic (non-nested) attribute
	basic_keys = ["type", "required", "use_default"]

	is_basic_attr = all([key in schema for key in basic_keys])

	if is_basic_attr:
		schema_type = schema["type"]

		for key in expandable_types:
			if schema_type == key:
				schema_type = "include('{}')".format(key)

			elif schema_type == "list({})".format(key):
				schema_type = "list(include('{}'))".format(key)

		if not schema["required"]:
			if schema_type[-2:] == "()":
				schema_type = schema_type[:-2] + "(required=False)"

			else:
				schema_type = schema_type[:-1] + ", required=False)"

		return schema_type

	for key, value in schema.items():
		schema[key] = translate(value, expandable_types)

	return schema

def yamale_converter(config_schema_file, yamale_file, lc_schema_files):
	yaml = YAML()

	config_schema_file = open(config_schema_file, "r")
	config_schema      = yaml.load_all(config_schema_file)

	schema = None
	expandable_types = {}

	for yaml_doc in config_schema:
		for key, value in yaml_doc.items():
			if key == "expected":
				schema = value

			else:
				expandable_types[key] = value

	with open(yamale_file, "w") as yamale:
		schema = translate(schema, expandable_types)

		yaml.dump(schema, yamale)

		# Add types defined in schema file
		for key, value in expandable_types.items():
			final = translate({key: value}, expandable_types)

			if key == "lightweight_component":
				lc_schema_filenames = [lc_schema.split("/")[-1].replace(".yaml", "") for lc_schema in lc_schema_files]

				lc_schemas = ["include('{}')".format(lc_schema.replace(".yaml", "")) for lc_schema in lc_schema_filenames]

				any_schemas = "any({})".format(", ".join(lc_schemas))

				final[key]["config"] = any_schemas

			yamale.write("---\n")
			yaml.dump(final, yamale)


		# Add lc_schemas
		for lc_schema_file in lc_schema_files:
			lc_schema = yaml.load(open(lc_schema_file, "r"))

			lc_schema = lc_schema["expected-from-site-level-config"]

			lc_schema_name = lc_schema_file.split("/")[-1].replace(".yaml", "")

			final = translate({lc_schema_name: lc_schema}, expandable_types)

			yamale.write("---\n")
			yaml.dump(final, yamale)
