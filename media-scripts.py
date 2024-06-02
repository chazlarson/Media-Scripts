# Import the necessary packages
from consolemenu import *
from consolemenu.items import *
import glob
import re

# Create the menu
menu = ConsoleMenu("Media Scripts", "Some Scripts for Plex and Kometa")

# Create some items
# A SelectionMenu constructs a menu from a list of strings

plex_submenu = ConsoleMenu("Plex Scripts", "Scripts targeting Plex")

with open('Plex/README.md', 'r') as file:
  data = file.read()
  scripts = re.findall(r'\d\. \[(.*\.py)', data)
  for script in scripts:
    plex_submenu.append_item(CommandItem(f"{script}", f"python Plex/{script}"))

kometa_submenu = ConsoleMenu("kometa Scripts", "Scripts targeting kometa")

with open('Kometa/README.md', 'r') as file:
  data = file.read()
  scripts = re.findall(r'\d\. \[(.*\.py)', data)
  for script in scripts:
    plex_submenu.append_item(CommandItem(f"{script}", f"python Kometa/{script}"))

tmdb_submenu = ConsoleMenu("TMDB Scripts", "Scripts targeting TheMovieDB")

with open('TMDB/README.md', 'r') as file:
  data = file.read()
  scripts = re.findall(r'\d\. \[(.*\.py)', data)
  for script in scripts:
    plex_submenu.append_item(CommandItem(f"{script}", f"python TMDB/{script}"))

# A SubmenuItem lets you add a menu (the selection_menu above, for example)
# as a submenu of another menu
plex_item = SubmenuItem("Plex scripts", plex_submenu, menu)

kometa_item = SubmenuItem("Kometa scripts", kometa_submenu, menu)

tmdb_item = SubmenuItem("TMDB scripts", tmdb_submenu, menu)

# Once we're done creating them, we just add the items to the menu
# menu.append_item(menu_item)
menu.append_item(plex_item)
menu.append_item(kometa_item)
menu.append_item(tmdb_item)

# Finally, we call show to show the menu and allow the user to interact
menu.show()
