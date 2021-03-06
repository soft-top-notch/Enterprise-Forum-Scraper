import json
import traceback
import argparse
import re
from copy import deepcopy

MAPPER = {
    "a": "address",
    "n": "name",
    "s": "salt",
    "h": "hash",
    "p": "password",
    "m": "mobile",
    "u": "username",
    "e": "email",
    "i": "ip",
    "de": "device",
    "lat": "latitude",
    "long": "longitude",
    "did": "device_id",
    "fb": "fb_user",
    "telegramid": "tgid",
    "d": "domain",
    "r": "breach",
    "t": "phone",
    "c": "company",
    "o": "other",
    "url1": "linkedin",
    "liid": "linkedin"
}

class Parser:
    def __init__(self):
        self.parser = argparse.ArgumentParser(
            description='Parsing Filter JSON Parameters')
        self.parser.add_argument(
            '-i', '--input', help='Input File', required=True)
        self.parser.add_argument(
            '-o', '--output', help='Output File', required=True)
        self.parser.add_argument(
            '-k', '--keep',
            help='list of fields to keep (comma separated). '
                 'Everything else will be removed.',
            required=False)
        self.parser.add_argument(
            '-r', '--remove_empty_fields',
            help='remove fields that are empty.',
            default=False,
            action='store_true',
            required=False)
        self.parser.add_argument(
            '-x', '--remove_x_fields',
            help='remove fields that start with x.',
            default=False,
            action='store_true',
            required=False)
        self.parser.add_argument(
            '-ea', '--expand_abbreviations',
            help='expand the abbreviations and replace them with their full forms present in MAPPER.',
            default=False,
            action='store_true',
            required=False)
        self.parser.add_argument(
            '-d', '--domain',
            help='add domain field from email',
            action='store_true')
        self.parser.add_argument(
            '-am', '--address_merge',
            help='merge addresses', action='store_true')
        self.parser.add_argument(
            '-nm', '--name_merge', help='merge names', action='store_true')
        self.parser.add_argument(
            '-f', '--format',
            help='Insert formatting for elasticsearch', action='store_true')
        self.parser.add_argument(
            '-importdate', '--importdate',
            help='Add importdate field')
        self.parser.add_argument(
            '-b', '--breach',
            help='Add breach field')
    def get_args(self,):
        return self.parser.parse_args()


def filter_json(data, parent_key, filter_fields):
    """
    Keep only specified property for nested json
    """
    if isinstance(data, list) or isinstance(data, dict):
        for key in list(data.keys()):
            path = str(parent_key + "/" + key)
            if path.strip("/") not in filter_fields and not len([s for s in filter_fields if s.startswith(path.strip("/") + "/")]):
                del data[key]
            else:
                if not data[key]:
                    del data[key]
                else:
                    if type(data[key]) == type(dict()):
                        filter_json(data[key], parent_key + "/" + key, filter_fields)
                    elif type(data[key]) == type(list()):
                        for val in data[key]:
                            if type(val) == type(str()):
                                pass
                            elif type(val) == type(list()):
                                pass
                            else:
                                filter_json(val, parent_key + "/" + key, filter_fields)


def expand_abbreviations(data_dict):
    temp_data = deepcopy(data_dict)
    for key, value in temp_data.items():
        if key in MAPPER:
            new_key = MAPPER.get(key)
            data_dict.pop(key)
            data_dict[new_key] = value


def remove_empty_fields(data_dict):
    temp_data = deepcopy(data_dict)
    for key, value in temp_data.items():
        if not value or (type(value) == str and len(value.strip()) == 0):
            del data_dict[key]


def remove_x_fields(data_dict):
    temp_data = deepcopy(data_dict)
    for key, value in temp_data.items():
        if key.startswith("x"):
            del data_dict[key]


def process_line(out_file, single_json, args):
    # while True:
    #     try:
    #         json_response = json.loads(single_json)
    #         break
    #     except Exception as e:
    #         unexp = int(re.findall(r'\(char (\d+)\)', str(e))[0])
    #         # position of unescaped '"' before that
    #         unesc = single_json.rfind(r'"', 0, unexp)
    #         single_json = single_json[:unesc] + r'\"' + single_json[unesc+1:]
    #         # position of correspondig closing '"' (+2 for inserted '\')
    #         closg = single_json.find(r'"', unesc + 2)
    #         single_json = single_json[:closg] + r'\"' + single_json[closg+1:]

    json_response = json.loads(single_json)
    if args.keep:
        out_fields = args.keep
        out_fields = [
            i.strip() for i in out_fields.split(',')] if out_fields else []
        filter_json(json_response, "", out_fields)

    address = 'address city state zip'
    name = 'fn ln'
    final_data = dict()
    if '_source' in json_response:
        data = json_response['_source'].items()
    else:
        data = json_response.items()
    for key, value in data:
        if key in ['email', 'e'] and args.domain:
            value = value.replace("@@", "@")
            email_parts = value.split('@')
            if len(email_parts) == 2:
                domain = email_parts[-1]
                if domain and domain.strip():
                    final_data.update({'domain': domain})
        if key in ['address', 'city', 'state', 'zip'] and args.address_merge:
            address = address.replace(key, value)
            final_data.update({'address': address})
            continue
        if key in ['fn', 'ln'] and args.name_merge:
            name = name.replace(key, value)
            final_data.update({'name': name})
            continue

        final_data.update({key: value})
    if final_data.get('a'):
        final_data['a'] = final_data['a'].replace('zip', '').strip()
    if args.importdate:
        final_data['importdate'] = args.importdate
    if args.breach:
        final_data['breach'] = args.breach
    if args.remove_empty_fields:
        remove_empty_fields(final_data)
    if args.remove_x_fields:
        remove_x_fields(final_data)
    if args.expand_abbreviations:
        expand_abbreviations(final_data)
    if args.format:
        filtered_json = {'_source': final_data}
    else:
        filtered_json = final_data
    out_file.write(json.dumps(filtered_json, ensure_ascii=False) + '\n')


def main():
    try:
        args = Parser().get_args()
    except SystemExit:
        help_message = """
            Usage: jproc.py [-h] -i INPUT -o OUTPUT [-k KEEP] [-d] [-am] [-nm] [-f]\n
            Arguments:
            -i  | --input  INPUT:         Input File
            -o  | --output OUTPUT:          Output File

            Optional:
            -s           | --keep KEEP_LIST:         List of fields to keep (comma separated).
            -d           | --domain:                 Add domain field from email
            -r           | --remove_empty_fields:    Remove fields that are empty
            -x           | --remove_x_fields:        Remove fields that start with x
            -ea          | --expand_abbreviations:   Expand the abbreviations and replace with full forms
            -am          | --address_merge:          Merge Addresses
            -nm          | --name_merge              Merge Names
            -f           | --format                  Insert formatting for elasticsearch
            -importdate  | --importdate              Add importdate field
            -b           | --breach                  Add breach field
            """
        print(help_message)
        raise

    input_file = args.input
    output_file = args.output
    with open(output_file, 'w') as out_file:
        with open(input_file, 'r') as fp:
            for line_number, single_json in enumerate(fp, 1):
                try:
                    process_line(out_file, single_json, args)
                    print('Writing line number:', line_number)
                except Exception:
                    print('Error in line number:', line_number)
                    traceback.print_exc()
                    break


if __name__ == '__main__':
    main()
