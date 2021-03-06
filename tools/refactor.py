import re
import json
import traceback
import argparse
from copy import deepcopy

EMAILS = ['e', 'e1', 'e2', 'e3', 'e4', 'e5']
IPS = ['i', 'i1', 'i2', 'i3', 'i4', 'i5']
TELEPHONES = ['t', 't1', 't2', 't3', 't4', 't5']
ADDRESS = ['address', 'a1', 'a2', 'a3', 'a4']

KEYS_TO_CHECK = ['breach']


KEY_LENGTH = 5
KEYS_WITH_LESS_CHARS = set()


class Parser:
    def __init__(self):
        self.parser = argparse.ArgumentParser(
            description='Refactoring JSON Keys')
        self.parser.add_argument(
            '-m', '--mapper', help='Input mapper json', required=False)
        self.parser.add_argument(
            '-i', '--input', help='Input File', required=True)
        self.parser.add_argument(
            '-o', '--output', help='Output File', required=False)
        self.parser.add_argument(
            '-chk', '--check',
            help='Checkfor few parameters',
            action='store_true'
        )

    def get_args(self,):
        return self.parser.parse_args()


def check_line(err_file, single_json):
    global KEYS_WITH_LESS_CHARS
    json_response = json.loads(single_json)
    data = deepcopy(json_response['_source'])
    for key, value in data.items():
        if len(key) < KEY_LENGTH and key not in KEYS_WITH_LESS_CHARS:
            err_file.write(key + '\n')
            KEYS_WITH_LESS_CHARS.add(key)
    error = not all(k in data.keys() for k in KEYS_TO_CHECK)
    return error


def process_line(out_file, single_json, mapper):
    json_response = json.loads(single_json)
    data = deepcopy(json_response['_source'])
    email = list()
    ip = list()
    telephone = list()
    address = dict()
    for key, value in data.items():
        json_response['_source'].pop(key)
        if key in EMAILS:
            email.append(value)
        elif key in IPS:
            ip.append(value)
        elif key in TELEPHONES:
            telephone.append(value)
        elif key in ADDRESS:
            address.update({key: value})
        else:
            new_key = mapper.get(key, key)
            json_response['_source'][new_key] = value
    if email:
        json_response['_source']['email'] = email[0]\
            if len(email) == 1 else email
    if telephone:
        json_response['_source']['telephone'] = telephone[0]\
            if len(telephone) == 1 else telephone
    if ip:
        json_response['_source']['ip'] = ip[0] if len(ip) == 1 else ip
    if address:
        merged_addr = f"{address.get('address', '')} "\
                      f"{address.get('a1', '')} "\
                      f"{address.get('a2', '')} "\
                      f"{address.get('a3', '')} "\
                      f"{address.get('a4', '')}"
        merged_addr = re.sub(r'\s{2,}', ' ', merged_addr.strip())
        json_response['_source']['address'] = merged_addr
    out_file.write(json.dumps(json_response, ensure_ascii=False) + '\n')


def main():
    args = Parser().get_args()
    input_file = args.input
    output_file = args.output
    mapper_file = args.mapper
    if output_file:
        with open(mapper_file, 'r') as fp:
            mapper = json.load(fp)
        with open(output_file, 'w') as out_file:
            with open(input_file, 'r') as fp:
                for line_number, single_json in enumerate(fp, 1):
                    try:
                        process_line(out_file, single_json, mapper)
                        print('Writing line number:', line_number)
                    except Exception:
                        print('Error in line number:', line_number)
                        traceback.print_exc()
                        break
    if args.check:
        file_name_only = input_file.rsplit('.', 1)[0]
        error_file = f'{file_name_only}_error.txt'
        with open(error_file, 'w', 1) as err_file:
            with open(input_file, 'r') as fp:
                for line_number, single_json in enumerate(fp, 1):
                    print('Checking line number:', line_number)
                    error = check_line(err_file, single_json)
                    if error:
                        err_file.write(str(line_number) + '\n')


if __name__ == '__main__':
    main()
