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
import json

# redirect log to stdout and make logger available for script
logging.basicConfig(stream=sys.stdout, level=logging.WARNING)
log = logging.getLogger('pgo_auto_iv')

# initialize PGOAPI
api = PGoApi()
pokemon_data = {}
with open('pokemon.json') as json_data:
    pokemon_data = json.load(json_data)

# collect login info via cmd-line arguments and user input
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
    parser.add_argument(
        '--password',
        nargs='?',
        default=None,
        help='Unsafe way to provide password'
    )
    args = parser.parse_args()

    password = args.password
    if password == None:
        prompt = 'Enter the password for the {0} account {1}: '.format(
            args.auth, args.username)
        password = getpass(prompt)

    return args.auth, args.username, password

# send request via PGOAPI to retrieve inventory
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

# we are only interested in the inventory_items of the response object
def extract_items(response):
    inventory = response['responses']['GET_INVENTORY']['inventory_delta']
    return inventory['inventory_items']

# of the inventory items we only care for actual pokemon
def filter_for_pokemon(items):
    for item in items:
        maybe_pokemon = item['inventory_item_data'].get('pokemon_data', {})
        # since eggs are also stored under the key 'pokemon_data' check for the
        # presence of pokemon_id
        if 'pokemon_id' in maybe_pokemon:
            yield maybe_pokemon

# avoid unnecessary nick-naming of pokemon that were rated in the past
def remove_rated(pokemon, rated_pokemon):
    for pkmn in pokemon:
        if pkmn['id'] in rated_pokemon:
            log.debug('Skipping {0}'.format(pkmn))
        else:
            yield pkmn

# load list of pokemon from disk that have been rated in the past 
def load_rated_pkmn():
    if os.path.exists('.rated_pkmn_list.pkl'):
        return pickle.load(open('.rated_pkmn_list.pkl', 'rb'))
    else:
        return []

# store list of pokemon that have been rated to disk
def store_rated_pkmn(list):
    pickle.dump(list, open('.rated_pkmn_list.pkl', 'wb'))

(auth, user, password) = collect_login_info()
response = retrieve_inventory(api, auth, user, password)
items = extract_items(response)
rated_pkmn = load_rated_pkmn()
pokemon = [pkmn for pkmn in remove_rated(filter_for_pokemon(items), rated_pkmn)]
amount = len(pokemon)
log.warning("Looping through {0} pokemon..".format(amount))
i = 0
try:
    for pkmn in pokemon:
        # build nickname in the format of ATK-DEF-STAMINA
        attack = pkmn.get('individual_attack', 0)
        defense = pkmn.get('individual_defense', 0)
        stamina = pkmn.get('individual_stamina', 0)
        cp = pkmn.get('cp')
        pkmn_name = pokemon_data[pkmn['pokemon_id'] - 1].get('Name', '???')
        nick = "{0}-{1}-{2}".format(attack, defense, stamina)
        id = pkmn['id']
        i = i + 1
        # nickname pokemon
        api.nickname_pokemon(pokemon_id=id, nickname=nick)

        print("(%(i)s/%(amount)s) Renamed %(pkmn_name)s with %(cp)s CP to %(nick)s" % locals())
        # add pkmn to list of rated pkmn
        rated_pkmn.append(id)
        # wait a little so we do not spam the API
        sleep_time = randint(3, 10)
        print("Waiting for {0} seconds".format(sleep_time))
        sleep(sleep_time)
finally:
    # make sure we store the new list of rated pokemon
    store_rated_pkmn(rated_pkmn)
print("Finished renaming Pokemon according to IVs.")
