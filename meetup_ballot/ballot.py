# coding=utf-8

from datetime import datetime
from datetime import timedelta
import random
import logging
import os

from meetup_ballot.meetup import MeetupClient

MEETUP_KEY_VAR = 'MEETUP_KEY'
MEETUP_URLNAME_VAR = 'MEETUP_URLNAME'
MAX_RSVPS_VAR = 'MAX_RSVPS'
RSVP_BEFORE_DAYS = 7


def setup_logging():
    """
    Setups logging for the ballot.
    :return: None
    """
    logging_format = '%(asctime)s %(levelname)9s %(lineno)4s %(module)s: %(message)s'
    logging.basicConfig(level=logging.INFO, format=logging_format)


def get_environment_variable(var):
    """
    Extracts environment variables
    :param var:
    :return: value of the environment variable.
    """
    try:
        return os.environ[var]
    except KeyError as excep:
        logging.error('Environment variable: %s not found', var)
        raise excep


def select_random(sample_list, sample_size):
    """
    Select a random sample of size sample_size
    :param sample_list:
    :param sample_size:
    :return:
    """
    sample = random.sample(sample_list, sample_size)
    return sample


def check_meetup_is_in_less_than_delta_time(meetup_key, meetup_urlname, days):
    """
    Checks if the meetup is less than delta days away. Useful
    for triggering cron.
    :param meetup_key: Meetup.com API Key
    :param meetup_urlname: Meetup's group API.
    :param days:
    :return: bool True if meetup is less than delta days away else False
    """
    today = datetime.utcnow()
    time_after_delta = today + timedelta(days=days)
    client = MeetupClient(key=meetup_key, urlname=meetup_urlname)
    next_event_time = client.get_next_event_time()/1000
    return next_event_time < time_after_delta


def run_ballot(meetup_key, meetup_urlname):
    """
    Run's the PyData London Meetups's RSVP Ballot.
    :param meetup_key: Meetup.com API Key
    :param meetup_urlname: Url name of the meetup group.
    :return: None
    """

    logging.info('Creating Meetup Client')
    client = MeetupClient(key=meetup_key, urlname=meetup_urlname)

    logging.info('Getting next event id')
    next_event_id = client.get_next_event_id()

    logging.info('Next event id: %s', next_event_id)
    event_rsvps = client.get_rsvps(next_event_id)

    logging.info('Next event RSVPS: %s', len(event_rsvps))
    member_ids = client.get_member_ids_from_rsvps(event_rsvps)
    max_rsvps = min(len(member_ids), int(get_environment_variable(MAX_RSVPS_VAR)))

    logging.info('Get event hosts and coorganizers')
    coorg_hosts_member_ids = client.get_coorganizers_and_hosts_from_rsvps(event_rsvps)

    logging.info('Selecting random: %s members', max_rsvps)
    random_members = select_random(member_ids, max_rsvps)

    logging.info('Marking RSVPs to Yes for random members')
    attending_members = coorg_hosts_member_ids + random_members
    client.mark_rsvps_to_yes(next_event_id, attending_members)


def main():
    """
    Main function which will be executed when this scripted is invoked directly.
    Setups logging, checks if its the right time to run the ballot and runs the
    ballot if its the right time.
    :return: None
    """
    setup_logging()
    meetup_key = get_environment_variable(MEETUP_KEY_VAR)
    meetup_urlname = get_environment_variable(MEETUP_URLNAME_VAR)
    if check_meetup_is_in_less_than_delta_time(meetup_key, meetup_urlname, days=RSVP_BEFORE_DAYS):
        logging.info('The next meetup is less than %s days ago.', RSVP_BEFORE_DAYS)
        logging.info('Running the PyData London Meetup"s RSVP Ballot')
        run_ballot(meetup_key, meetup_urlname)
    else:
        logging.info('The next meetup is more than %s days ago.', RSVP_BEFORE_DAYS)
        logging.info('It"s not the right time to run the ballot.')


if __name__ == '__main__':
    main()
