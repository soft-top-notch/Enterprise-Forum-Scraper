import sys
import re
import csv
import json
import traceback
import argparse
from copy import deepcopy

POSH_FIELDS = [
    'first_name',
    'last_name',
    'email',
    'address',
    'city',
    'state',
    'country',
    'zip',
    'ip_address',
    'phone'
]

IG_FIELDS = [
    'username',
    'instagramId',
    'fullName',
    'id_external_profile',
    'email',
    'phoneNumber',
    'streetAddress',
    'cityName',
    'zipCode'
]

PDL_FIELDS = [
    'first_name',
    'last_name',
    'url_profile',
    'id_external_profile',
    'emails',
    'phone_numbers',
    'lip_location'
]

PIZAP_FIELDS = [
    'donor_name',
    'donor_dob',
    'donor_mobile_no',
    'donor_telephone_no',
    'donor_email_id',
    'bb_city',
    'bb_pincode',
    'bb_address',
    'bb_contact_no'
]
GYFCAT_FIELDS = [
    'phone',
    'city',
    'site_url',
    'state',
    'email',
    'user_ip',
    'firstname',
    'lastname',
    'zip',
    'company_name',
    'contact_name',
    'title',
    'address',
    'phone',
    'company_website',
    'firstname',
    'lastname',
    'ip',
    'url',
    'fname',
    'lname',
    'mobile',
    'dob',
]

PIPL_FIELDS = {
    'firstname': 'fn',
    'lastname': 'ln',
    'middlename': 'mn',
    'street': 'a1',
    'city': 'a2',
    'zip': 'a3',
    'dateOfBirth': 'dob',
    'phone': 't'
}
TO_REMOVE_PIPL = [
    '_id',
    'id',
    'title',
    'age',
    'dateUpdated',
    'gender',
    'politicalParty',
    'race',
    'religion',
    'aka'
]
SCRAPE_FIELDS = {
    'firstName',
    'lastName',
    'email',
    'address',
    'phone'
}

VEDANTU_FIELDS = {
    'fullName',
    'password',
    'gender',
    'email',
}

IRAN1_FIELDS = {
    'username',
    'pk',
    'full_name',
    'uuid',
    'addAccount'
}

IRAN2_FIELDS = {
    'first_name',
    'last_name',
    'phone',
    'id'
}

GEEKEDIN_FIELDS = {
    'name',
    'email',
    'url'
}

FIELD_MAPS = {
    'pizap': PIZAP_FIELDS,
    'gyfcat': GYFCAT_FIELDS,
    'pipl': PIPL_FIELDS,
    'pdl': PDL_FIELDS,
    'ig': IG_FIELDS,
    'posh': POSH_FIELDS,
    'scrape': SCRAPE_FIELDS,
    'vedantu': VEDANTU_FIELDS,
    'iran1': IRAN1_FIELDS,
    'iran2': IRAN2_FIELDS,
    'geekedin': GEEKEDIN_FIELDS,
    'exactis': ''
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
            '-t', '--type', help='JSON Type', required=True)

    def get_args(self,):
        return self.parser.parse_args()


def process_pipl(out_file, single_json):
    single_json = re.sub(r'ObjectId\((.*?)\)', '\\1', single_json)
    single_json = re.sub(r'NumberInt\((.*?)\)', '\\1', single_json)
    json_response = json.loads(single_json)
    filtered_json = dict()
    for key, value in json_response.items():
        if key in TO_REMOVE_PIPL:
            continue
        if not value:
            continue
        if key == 'emails':
            for index, email in enumerate(value, 1):
                filtered_json.update({'e{}'.format(index): email})
        elif key == 'socialUrls':
            for social in value:
                if social['domain'] == 'facebook.com' and\
                   '/people/' not in social['url']:
                    filtered_json.update({'fb': social['url']})

                elif social['domain'] == 'linkedin.com':
                    filtered_json.update({'linkedin': social['url']})

                elif social['domain'] == 'twitter.com':
                    filtered_json.update({'twitter': social['url']})

                elif social['domain'] == 'amazon.com':
                    filtered_json.update({'amazon': social['url']})

                elif social['domain'].lower() == '10digits.us':
                    filtered_json.update({'10digits': social['url']})
                elif social['domain'].lower() == 'pinterest.com':
                    filtered_json.update({'pinterest': social['url']})

        elif key in PIPL_FIELDS:
            filtered_json.update({PIPL_FIELDS[key]: value})
        else:
            filtered_json.update({key: value})
    process_address(filtered_json)
    process_name(filtered_json)
    out_file.write(json.dumps(filtered_json, ensure_ascii=False)+'\n')


def process_ig(out_file, single_json):
    json_response = json.loads(single_json)
    filtered_json = dict()
    for key, value in json_response.items():
        if not value:
            continue
        if key == 'business':
            if value['email']:
                filtered_json.update({'email': value['email']})
            if value['phoneNumber']:
                filtered_json.update({'phoneNumber': value['phoneNumber']})
            if value['address']['streetAddress']:
                filtered_json.update({'streetAddress': value['address']['streetAddress']})
            if value['address']['cityName']:
                filtered_json.update({'cityName': value['address']['cityName']})
            if value['address']['zipCode']:
                filtered_json.update({'zipCode': value['address']['zipCode']})

        elif key in IG_FIELDS:
            filtered_json.update({key: value})
    out_file.write(json.dumps(filtered_json, ensure_ascii=False)+'\n')


def process_pdl(out_file, single_json):
    json_response = json.loads(single_json)
    filtered_json = dict()
    for key, value in json_response.items():
        if not value:
            continue
        if key == 'emails':
            email_data = dict()
            for index, email in enumerate(value.split(','), 1):
                email_data.update({'e{}'.format(index): email})
            filtered_json.update({'e': email_data})
        elif key == 'phone_numbers':
            ph_data = dict()
            for index, ph in enumerate(value.split(','), 1):
                ph_data.update({'t{}'.format(index): ph})
            filtered_json.update({'t': ph_data})
        elif key in PDL_FIELDS:
            filtered_json.update({key: value})
    out_file.write(json.dumps(filtered_json, ensure_ascii=False)+'\n')


def process_iran1(out_file, single_json):
    json_response = json.loads(single_json)
    filtered_json = dict()
    for key, value in json_response.items():
        if not value:
            continue
        if key in IRAN1_FIELDS:
            filtered_json.update({key: value})
        elif key == 'user':
            filtered_json.update({
                'username': value['username'],
                'pk': value['pk'],
                'full_name': value['full_name']
            })
    if filtered_json:
        out_file.write(json.dumps(filtered_json, ensure_ascii=False)+'\n')


def process_iran2(out_file, single_json):
    single_json = single_json.replace(':"{"', ':{"').replace('}","', '},"')
    json_response = json.loads(single_json)
    filtered_json = dict()
    if not json_response.get('message'):
        return
    for key, value in json_response['message'].items():
        if not value:
            continue
        if key in IRAN2_FIELDS:
            filtered_json.update({key: value})
    if filtered_json:
        out_file.write(json.dumps(filtered_json, ensure_ascii=False)+'\n')


def process_posh(out_file, single_json):
    json_response = json.loads(single_json)
    filtered_json = dict()
    for key, value in json_response.items():
        if not value:
            continue
        if key == 'surl':
            filtered_json.update({'url': value})
        elif key == 'profile':
            if value.get('city'):
                filtered_json.update({
                    'city': value['city']
                })
            if value.get('state'):
                filtered_json.update({
                    'state': value['state']
                })
            if value.get('website'):
                filtered_json.update({
                    'website': value['website']
                })
        elif key == 'fb_info':
            if value.get('ext_user_id'):
                filtered_json.update({
                    'fbid': value['ext_user_id'],
                })
            if value.get('ext_username'):
                filtered_json.update({
                    'fbuser': value['ext_username']
                })
        elif key == 'pn_info':
            if value.get('ext_user_id'):
                filtered_json.update({
                    'pnid': value['ext_user_id'],
                })
            if value.get('ext_username'):
                filtered_json.update({
                    'pnuser': value['ext_username']
                })
        elif key == 'tw_info':
            if value.get('ext_user_id'):
                filtered_json.update({
                    'twid': value['ext_user_id'],
                })
            if value.get('ext_username'):
                filtered_json.update({
                    'twuser': value['ext_username']
                })

        elif key in POSH_FIELDS:
            filtered_json.update({key: value})
    process_posh_name(filtered_json)
    out_file.write(json.dumps(filtered_json, ensure_ascii=False)+'\n')


def process_address(filtered_json):
    address = ''
    if 'a1' in filtered_json:
        address = filtered_json.pop('a1')
    if 'a2' in filtered_json:
        address = f"{address} {filtered_json.pop('a2')}"
    if 'state' in filtered_json:
        address = f"{address} {filtered_json.pop('state')}"
    if 'a3' in filtered_json:
        address = f"{address} {filtered_json.pop('a3')}"
    if address:
        filtered_json.update({'a': address})


def process_posh_name(filtered_json):
    name = ''
    if 'first_name' in filtered_json:
        name = filtered_json.pop('first_name')
    if 'last_name' in filtered_json:
        name = f"{name} {filtered_json.pop('last_name')}"
    if name:
        filtered_json.update({'n': name})


def process_name(filtered_json):
    name = ''
    if 'fn' in filtered_json:
        name = filtered_json.pop('fn')
    if 'mn' in filtered_json:
        name = f"{name} {filtered_json.pop('mn')}"
    if 'ln' in filtered_json:
        name = f"{name} {filtered_json.pop('ln')}"
    if name:
        filtered_json.update({'n': name})


def process_line(out_file, single_json, _type):
    fields = FIELD_MAPS[_type]
    match = re.findall(r'.*?({.*})', single_json)
    if not match:
        print('Following line is not valid JSON')
        print(single_json)
        return
    try:
        json_response = json.loads(match[0])
    except Exception:
        print('Following line is not valid JSON')
        print(single_json)
        return
    filtered_json = dict()
    for key, value in json_response.items():
        if value is not None and key in fields:
            if isinstance(value, list):
                filtered_json.update({key: list(value.values())[0]})
            elif isinstance(value, str):
                filtered_json.update({key: value})
    out_file.write(json.dumps(filtered_json, ensure_ascii=False)+'\n')


def process_scrape(out_file, single_json):
    print(single_json)
    json_response = json.loads(single_json)
    filtered_json = dict()
    for key, value in json_response.items():
        if not value:
            continue
        if key == 'email':
            if value:
                if isinstance(value, list):
                    filtered_json.update({'email': value[0]})
                else:
                    filtered_json.update({'email': value})
            else:
                continue
        elif key == 'company':
            filtered_json.update(value['address'])
            filtered_json.update({'company': value['name']})
            if not value.get('phone'):
                continue
            phone = value['phone']
            if phone:
                filtered_json.update({'phone': phone[0]['phoneNumber']})
        elif key in SCRAPE_FIELDS:
            filtered_json.update({key: value})
    out_file.write(json.dumps(filtered_json, ensure_ascii=False)+'\n')


def process_vedantu(out_file, single_json):
    print(single_json)
    json_response = json.loads(single_json)
    filtered_json = dict()
    for key, value in json_response.items():
        if not value:
            continue
        if key == 'phones':
            if value and value[0]:
                phone = f'{value[0]["phoneCode"]}-{value[0]["number"]}'
                filtered_json.update({'phone': phone})
            else:
                continue
        elif key == 'studentInfo' and value['parentEmails']:
            filtered_json.update({'parentEmails': value['parentEmails'][0]})
        elif key == 'locationInfo':
            filtered_json.update(value)
        elif key in VEDANTU_FIELDS:
            filtered_json.update({key: value})
    out_file.write(json.dumps(filtered_json, ensure_ascii=False) + '\n')


def process_geekedin(out_file, single_json):
    filtered_json = dict()
    urls = set()
    json_response = json.loads(single_json)
    for data in iterate_all(json_response):
        key, value = data
        if key == 'url':
            urls.add(value)
        elif key in GEEKEDIN_FIELDS:
            filtered_json.update({key: value})
    if urls:
        filtered_json.update({'url': list(urls)})
    out_file.write(json.dumps(filtered_json, ensure_ascii=False) + '\n')


def process_exactis(out_file, single_json):
    json_response = json.loads(single_json)
    data = deepcopy(json_response['_source'])
    for key, value in data.items():
        if not value or value == 'U':
            json_response['_source'].pop(key)
    out_file.write(json.dumps(json_response, ensure_ascii=False) + '\n')


def iterate_all(iterable):
    if isinstance(iterable, dict):
        for key, value in iterable.items():
            if not (isinstance(value, dict) or isinstance(value, list)):
                yield key, value
            for ret in iterate_all(value):
                yield ret
    elif isinstance(iterable, list):
        for el in iterable:
            for ret in iterate_all(el):
                yield ret


def process_file(args):
    input_file = args.input
    output_file = args.output
    with open(output_file, 'w') as out_file:
        with open(input_file, 'r') as fp:
            for line_number, single_json in enumerate(fp, 1):
                pattern = re.compile(r': "(([^"]+)"([^"]*))",')
                single_json = pattern.sub(": \"\\2'\\3\",", single_json)
                try:
                    if args.type == 'pipl':
                        process_pipl(out_file, single_json)
                    elif args.type == 'ig':
                        process_ig(out_file, single_json)
                    elif args.type == 'posh':
                        process_posh(out_file, single_json)
                    elif args.type == 'pdl':
                        process_pdl(out_file, single_json)
                    elif args.type == 'scrape':
                        process_scrape(out_file, single_json)
                    elif args.type == 'vedantu':
                        process_vedantu(out_file, single_json)
                    elif args.type == 'iran1':
                        process_iran1(out_file, single_json)
                    elif args.type == 'iran2':
                        process_iran2(out_file, single_json)
                    elif args.type == 'geekedin':
                        process_geekedin(out_file, single_json)
                    elif args.type == 'exactis':
                        process_exactis(out_file, single_json)
                    else:
                        process_line(out_file, single_json, args.type)
                    print('Writing line number:', line_number)
                except Exception:
                    print('Error in line number:', line_number)
                    continue


def main():
    args = Parser().get_args()
    if args.type not in FIELD_MAPS:
        print('Invalid JSON type')
        return
    process_file(args)


if __name__ == '__main__':
    main()
