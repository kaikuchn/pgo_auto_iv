# PokemonGo AutoIV Script

This little script renames all Pokemon in possession of a player according to their IVs. E.g., `Charmander` with 13 attack, 12 defense and 15 stamina would be nicknamed `13-12-15`.

## Usage

Execute the `main.py` file passing your username. It will ask for your password to be able to authenticate against the Niantic API.
If you're not using a Pokemon Trainer Club account you also have to specify `google` as the authentication provider via the `--auth` flag.
E.g., `./main.py john.doe@gmail.com --auth google`.

Those of you who are using 2-Factor Authentication (absolutely recommended!!) will need to add an [Application Password](https://support.google.com/accounts/answer/185833) and then use that password.

## DISCLAIMER

This is unofficial, use at your own risk!

PS: I don't know any Python.. this is probably reflected in the code.. x)
