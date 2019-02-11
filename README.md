# smashrankingfi
The goal of the project is to create an easy-to-use and automatized Glicko/ELO(not done yet)/Trueskill(not done yet) ranking system and results database for the Finnish Super Smash Bros. Melee scene but can be used to rank any kind of competitive scene. Project is still in its early stages and there can be major modifications.

### Prerequisites
The project has been made with Python 3 and depends on the modules tkinter, numpy, dateutil, requests, sqlite3.

### How to use
You need to have a specifically prepared sql database with name "smashranking.db" in the directory. You can run the program with
```
python3 gui.py
```
You are presented with three options. 

Tournaments lets you inspect, modify (double-click a tournament), delete and add tournaments and their results. To add H2H set results to a tournament, the player needs to be added to the results list first. Tournament addition can be hastened by providing a suitable Challonge or smash.gg identifier.

Players lists all the players in the database and allows you to add and modify (but not skill values!) player data.

H2H sets lets you inspect H2H set results during recent sets.

##License
This project has been licensed under the MIT license.
