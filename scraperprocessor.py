
import arrow
import getopt
import json
import logging
import os
import requests
import sys

import post_processing
from forumparse import Parser
from helpers.err_messages import ERROR_MESSAGES, WARNING_MESSAGES
from run_scrapper import Scraper
from settings import (
    API_TOKEN,
    DV_BASE_URL,
    OUTPUT_DIR,
    PARSE_DIR,
)

headers = {
    'apiKey': API_TOKEN
}

# shell script to combine JSON and create archives
post_process_script = 'tools/post_process.sh'

logger = logging.getLogger(__name__)


def get_active_scrapers():
    """
    Retrieves the active scrapers from the Data Viper API.
    """
    response = requests.get('{}/api/scraper'.format(DV_BASE_URL), headers=headers)
    if response.status_code != 200:
        raise Exception('Failed to get scrapers from API (status={})'.format(response.status_code))
    return response.json()


def get_scraper(scraper_id):
    response = requests.get('{}/api/scraper/{}'.format(DV_BASE_URL, scraper_id), headers=headers)
    if response.status_code != 200:
        raise Exception('Failed to get scraper by ID from API (status={})'.format(response.status_code))
    return response.json()


def update_scraper(scraper, payload):
    """
    Updates the scraper in the Data Viper API.
    """
    scraper_url = '{}/api/scraper/{}'.format(DV_BASE_URL, scraper['id'])
    response = requests.patch(scraper_url, data=json.dumps(payload), headers=headers)
    if response.status_code != 200:
        logger.warning('Failed to update scraper (status={})'.format(response.status_code))


def process_scraper(scraper):
    """
    Processes the scraper by running the scraper template and then parsing the data.
    """
    start_date = None
    if scraper['nextStartDate']:
        start_date = arrow.get(scraper['nextStartDate']).format('YYYY-MM-DD')
    subfolder = scraper['name']
    template = scraper['template']
    sitename = scraper['name']

    process_date = arrow.now().format('YYYY-MM-DD')

    # the output dirs for the scraper and parser
    scraper_output_dir = os.path.join(OUTPUT_DIR, subfolder)
    parse_output_dir = os.path.join(PARSE_DIR, subfolder)

    try:
        ############################
        # Run scraper for template
        ############################
        logger.info('Scraping {} from {}...'.format(template, start_date))

        update_scraper(scraper, {'status': 'Scraping'})

        kwargs = {
            'start_date': start_date,
            'template': template,
            'output': scraper_output_dir,
            'sitename': sitename
        }

        result = Scraper(kwargs).do_scrape()

        # check if there was any error
        err_code = result.get('result/error')
        if err_code:
            raise RuntimeError('[%s] %s' % (err_code, ERROR_MESSAGES[err_code]))

        # check for "No new files"(W08) warning
        if 'W08' in result.get('result/warnings', []):
            raise RuntimeError(WARNING_MESSAGES['W08'])

        ############################
        # Run parser for template
        ############################
        logger.info('Processing {}...'.format(template))

        update_scraper(scraper, {'status': 'Processing'})

        kwargs = {
            'template': template,
            'output': parse_output_dir,
            'input_path': scraper_output_dir,
            'sitename': sitename
        }
        Parser(kwargs).start()

        ##############################
        # Post-process HTML & JSON
        ##############################
        logger.info('Post-processing {}...'.format(scraper['name']))

        kwargs = dict(
            site=scraper['name'],
            template=template,
            date=arrow.now().format('YYYY_MM_DD'),
            sync=False
        )
        post_processing.run(kwargs)

        ##############################
        # Update Scraper Status / Date
        ##############################

        # set the scraper's next start date to the current date and clear PID
        update_scraper(scraper, {'status': 'Idle', 'nextStartDate': process_date, 'pid': None})
        logger.info('Done')

    except Exception as e:
        logger.error('Failed to process scraper {}: {}'.format(scraper['name'], e))
        update_scraper(scraper, {'status': 'Error', 'pid': None, 'message': e})


def help():
    logger.info('scraperprocessor.py -s <scraper_id>')


def main(argv):
    ##############################
    # Parse CLI Args
    ##############################
    try:
        opts, args = getopt.getopt(argv, "hs:", ["scraperid="])
    except getopt.GetoptError:
        help()
        sys.exit(2)

    scraper_id = None

    for opt, arg in opts:
        if opt == '-h':
            help()
            sys.exit()
        elif opt in ("-s", "--scraperid"):
            scraper_id = arg

    if scraper_id is None:
        logger.error('Missing required option scraper ID')
        help()
        sys.exit(2)

    try:
        ##############################
        # Get / Process Scraper
        ##############################
        scraper = get_scraper(scraper_id)
        # scraper = dict(
            # nextStartDate=arrow.now().format('YYYY-MM-DD'),
            # name=scraper_id,
            # template=scraper_id
        # )
        process_scraper(scraper)
    except Exception as e:
        logger.error('Failed to process scraper: {}'.format(e))


if __name__ == "__main__":
    main(sys.argv[1:])
