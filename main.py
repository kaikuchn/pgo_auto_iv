#!/usr/bin/python
# -*- coding: utf-8 -*-

from pgoapi import PGoApi
from time import sleep
from random import randint
import logging
import sys
import argparse
import pickle
import os
from getpass import getpass

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
log = logging.getLogger('AutoIV')
api = PGoApi()

def collect_login_info():
    parser = argparse.ArgumentParser(
        description='Rename pokemon according to their IVs')
    parser.add_argument(
        'username',
        help='Username of the account for which you want to rename the pokemon')
    parser.add_argument(
        '--auth',
        nargs='?',
        default='ptc',
        help='Authentication method, can be either ptc (default) or google')
    args = parser.parse_args()

    prompt = 'Enter the password for the {0} account {1}: '.format(
        args.auth, args.username)
    password = getpass(prompt)

    return args.auth, args.username, password

def retrieve_inventory(api, auth, username, password):
    if api.login(provider=auth,
                 username=username,
                 password=password,
                 lat=51.202957,
                 lng=6.782099,
                 alt=36.720):
        sleep(2) # wait a little to avoid throttling
        return api.get_inventory()
    else:
        log.debug('Failed to retrieve inventory.')
        return {}

def extract_items(response):
    inventory = response['responses']['GET_INVENTORY']['inventory_delta']
    return inventory['inventory_items']

def filter_for_pokemon(items):
    for item in items:
        maybe_pokemon = item['inventory_item_data'].get('pokemon_data', {})
        if 'pokemon_id' in maybe_pokemon:
            yield maybe_pokemon

def remove_rated(pokemon, rated_pokemon):
    for pkmn in pokemon:
        if pkmn['id'] in rated_pokemon:
            log.debug('Skipping {0}'.format(pkmn))
        else:
            yield pkmn

def load_rated_pkmn():
    if os.path.exists('.rated_pkmn_list.pkl'):
        return pickle.load(open('.rated_pkmn_list.pkl', 'rb'))
    else:
        return []

def store_rated_pkmn(list):
    pickle.dump(list, open('.rated_pkmn_list.pkl', 'wb'))

(auth, user, password) = collect_login_info()
response = retrieve_inventory(api, auth, user, password)
items = extract_items(response)
rated_pkmn = load_rated_pkmn()
pokemon = [pkmn for pkmn in remove_rated(filter_for_pokemon(items), rated_pkmn)]
amount = len(pokemon)
log.info("Looping through {0} pokemon..".format(amount))
i = 0
try:
    for pkmn in pokemon:
        attack = pkmn.get('individual_attack', 0)
        defense = pkmn.get('individual_defense', 0)
        stamina = pkmn.get('individual_stamina', 0)
        nick = "{0}-{1}-{2}".format(attack, defense, stamina)
        id = pkmn['id']
        i = i + 1
        api.nickname_pokemon(pokemon_id=id, nickname=nick)
        log.info("(%(i)s/%(amount)s) Renamed %(id)s to %(nick)s" % locals())
        rated_pkmn.append(id)
        sleep_time = randint(3, 10)
        log.info("Waiting for {0} seconds".format(sleep_time))
        sleep(sleep_time)
finally:
    store_rated_pkmn(rated_pkmn)
log.info("Finished renaming Pokemon according to IVs.")