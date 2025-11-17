import os
import yaml

YAML_FILE = 'check_sensor_aswc_composition.yaml' 
OUTPUT_C_FILE = 'TestProcess_generated2.c'  

def load_yaml(path):
	with open(path, 'r', encoding='utf-8') as f:
		return yaml.safe_load(f)


def map_type(yaml_type):
	
	t = yaml_type.lower()
	if t in ('boolean', 'bool'):
		return 'Boolean'
	if t in ('double', 'float', 'real'):
		return 'Double'
	# Fallback: preserve and capitalize
	return yaml_type.capitalize()


def extract_interfaces_and_ports(yaml_doc):

	# YAML may have structure under top-level 'Component'
	top = yaml_doc.get('Component', yaml_doc)

	interfaces = {}
	for iface in top.get('Interfaces', []) or []:
		name = iface.get('name')
		data_elements = []
		for de in iface.get('dataElements', []) or []:
			de_name = de.get('name')
			de_type = de.get('type')
			initial = de.get('initialValue') if 'initialValue' in de else None
			data_elements.append({'name': de_name, 'type': de_type, 'initialValue': initial})
		interfaces[name] = {'dataElements': data_elements}

	ports = {}
	for port in top.get('Ports', []) or []:
		pname = port.get('name')
		ptype = port.get('type')
		interface = port.get('interface')
		ports[pname] = {'type': ptype, 'interface': interface}

	return interfaces, ports


def generate_header_and_buffers(component_name, interfaces, ports):

	lines = []
	lines.append('/* Auto-generated RTE file for component: %s */' % component_name)
	lines.append('#include "include/Rte.h"')
	lines.append('#include "Rte_%s.h"' % component_name)
	lines.append('')

	# Input buffers: extern
	lines.append('/* =============================================================================')
	lines.append(' * RTE INTERNAL BUFFERS (Global scope for macro access)')
	lines.append(' * =============================================================================*/')
	lines.append('')
	# For each RPort, declare extern buffer for each data element
	for port_name, port in ports.items():
		if port['type'] and port['type'].upper() == 'RPORT':
			iface = port.get('interface')
			iface_def = interfaces.get(iface, {})
			for de in iface_def.get('dataElements', []):
				ctype = map_type(de['type'])
				buf_name = f'Rte_Buffer_{port_name}_{de["name"]}'
				lines.append(f'extern {ctype} {buf_name};')
	lines.append('')

	# Output buffers definitions
	lines.append('/* Output buffers - written by this SWC */')
	for port_name, port in ports.items():
		if port['type'] and port['type'].upper() == 'PPORT':
			iface = port.get('interface')
			iface_def = interfaces.get(iface, {})
			for de in iface_def.get('dataElements', []):
				ctype = map_type(de['type'])
				buf_name = f'Rte_Buffer_{port_name}_{de["name"]}'
				# Choose an initial value
				init = de.get('initialValue')
				if init is None:
					if ctype == 'Boolean':
						init_val = '(Boolean)0'
					elif ctype == 'Double':
						init_val = '0.0'
					else:
						init_val = '0'
				else:
					# attempt to format booleans and numbers
					if ctype == 'Boolean':
						init_val = f'(Boolean){int(bool(init))}'
					else:
						init_val = str(init)
				lines.append(f'{ctype} {buf_name} = {init_val};')
	lines.append('')

	return '\n'.join(lines)


def generate_rte_read_write(interfaces, ports):
	lines = []
	lines.append('')
	lines.append('/* RTE API implementations */')
	lines.append('')

	for port_name, port in ports.items():
		iface = port.get('interface')
		iface_def = interfaces.get(iface, {})
		if not iface_def:
			continue
		for de in iface_def.get('dataElements', []):
			ctype = map_type(de['type'])
			fname_read = f'Rte_Read_{port_name}_{de["name"]}'
			buf_name = f'Rte_Buffer_{port_name}_{de["name"]}'

			if port['type'] and port['type'].upper() == 'RPORT':
				# Generate read function
				lines.append(f'Std_ReturnType {fname_read}({ctype}* data){{')
				lines.append('    if (data == NULL) {')
				lines.append('        return RTE_E_LIMIT;  // Invalid pointer')
				lines.append('    }')
				# Optional debug prints can be added conditionally; keep simple
				lines.append(f'    *data = {buf_name};')
				lines.append('    return RTE_E_OK;')
				lines.append('}')
				lines.append('')

			if port['type'] and port['type'].upper() == 'PPORT':
				# Generate write function
				fname_write = f'Rte_Write_{port_name}_{de["name"]}'
				lines.append(f'Std_ReturnType {fname_write}({ctype} data){{')
				lines.append(f'    {buf_name} = data;')
				# If boolean, print like example to aid debugging
				lines.append('    return RTE_E_OK;')
				lines.append('}')
				lines.append('')

	return '\n'.join(lines)


def generate_c_from_yaml(yaml_path, out_path):
	doc = load_yaml(yaml_path)
	interfaces, ports = extract_interfaces_and_ports(doc)

	# Component name
	top = doc.get('Component', doc)
	comp_name = top.get('name', os.path.splitext(os.path.basename(out_path))[0].replace('Rte_', ''))

	header_and_buffers = generate_header_and_buffers(comp_name, interfaces, ports)
	api_impl = generate_rte_read_write(interfaces, ports)

	full = header_and_buffers + '\n' + api_impl

	with open(out_path, 'w', encoding='utf-8') as f:
		f.write(full)

	print(f'Generated {out_path} from {yaml_path}')


def main():
	data = load_yaml(YAML_FILE)
	top = data.get('Component', data)
	comp = top.get('name', 'component')
	generate_c_from_yaml(YAML_FILE, OUTPUT_C_FILE)


if __name__ == '__main__':
	main()

