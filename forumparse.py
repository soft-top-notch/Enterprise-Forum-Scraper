import argparse
import os
from glob import glob
from oday_template import oday_parser
# from blackmarket_template import blackmarket_parser


class Parser:
    def __init__(self):
        self.counter = 1

    def get_args(self):
        parser = argparse.ArgumentParser(
            description='Parsing Forums Framework')
        parser.add_argument(
            '-t', '--template', help='Template forum to parse', required=True)
        parser.add_argument(
            '-p', '--path', help='input folder path', required=True)
        parser.add_argument(
            '-f', '--output_folder', help='output folder path', required=True)
        args = parser.parse_args()

        return args.template, args.path, args.output_folder

    def main(self):
        parser_name, folder_path, output_folder = self.get_args()

        # ------------make folder if not exist -----------------
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        # -----------filter files which user want to parse --------------
        files = []
        for filee in glob(folder_path+'/*'):
            if parser_name in filee:
                files.append(filee)

        if parser_name == '0day':
            oday_parser(parser_name, files, output_folder, folder_path)
        else:
            print('Message: your target name is wrong..!')


# -----run main ---
obj = Parser()
obj.main()