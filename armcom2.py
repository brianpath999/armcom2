# -*- coding: UTF-8 -*-                                                         
# Python 3.6.6 x64
# Libtcod 1.6.4 x64
##########################################################################################
#                                                                                        #
#                                Armoured Commander II                                   #
#                                                                                        #
##########################################################################################
#             Project Started February 23, 2016; Restarted July 25, 2016                 #
#          Restarted again January 11, 2018; Restarted again January 2, 2019             #
##########################################################################################
#
#    Copyright (c) 2016-2019 Gregory Adam Scott (sudasana@gmail.com)
#
#    This file is part of Armoured Commander II.
#
#    Armoured Commander II is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    Armoured Commander II is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.

#    You should have received a copy of the GNU General Public License
#    along with Armoured Commander II, in the form of a file named "gpl.txt".
#    If not, see <https://www.gnu.org/licenses/>.
#
#    xp_loader.py is covered under a MIT License (MIT) and is Copyright (c) 2015
#    Sean Hagar; see XpLoader_LICENSE.txt for more info.
#
##########################################################################################


##### Libraries #####
import os, sys						# OS-related stuff
		
import libtcodpy as libtcod			# The Doryen Library
os.environ['PYSDL2_DLL_PATH'] = os.getcwd() + '/lib'.replace('/', os.sep)	# set sdl2 dll path
	
from configparser import ConfigParser			# saving and loading configuration settings
from random import choice, shuffle, sample		# for the illusion of randomness
from math import floor, cos, sin, sqrt, degrees, atan2, ceil	# math and heading calculations
import xp_loader, gzip					# loading xp image files
import json						# for loading JSON data
import time
from textwrap import wrap				# breaking up strings
import shelve						# saving and loading games
import sdl2.sdlmixer as mixer				# sound effects



##########################################################################################
#                                        Constants                                       #
##########################################################################################

DEBUG = False						# debug flag - set to False in all distribution versions
NAME = 'Armoured Commander II'				# game name
VERSION = '0.4.0'					# game version
DATAPATH = 'data/'.replace('/', os.sep)			# path to data files
SOUNDPATH = 'sounds/'.replace('/', os.sep)		# path to sound samples
CAMPAIGNPATH = 'campaigns/'.replace('/', os.sep)	# path to campaign files

if os.name == 'posix':					# linux (and OS X?) has to use SDL for some reason
	RENDERER = libtcod.RENDERER_SDL
else:
	RENDERER = libtcod.RENDERER_GLSL

LIMIT_FPS = 50						# maximum screen refreshes per second
WINDOW_WIDTH, WINDOW_HEIGHT = 90, 60			# size of game window in character cells
WINDOW_XM, WINDOW_YM = int(WINDOW_WIDTH/2), int(WINDOW_HEIGHT/2)	# center of game window

KEYBOARDS = ['QWERTY', 'AZERTY', 'QWERTZ', 'Dvorak', 'Custom']	# list of possible keyboard layout settings

MAX_TANK_NAME_LENGTH = 20				# maximum length of tank names
MAX_NICKNAME_LENGTH = 10				# " for crew nicknames

##### Hex geometry definitions #####

# directional and positional constants
DESTHEX = [(0,-1), (1,-1), (1,0), (0,1), (-1,1), (-1,0)]	# change in hx, hy values for hexes in each direction
CD_DESTHEX = [(1,-1), (1,0), (0,1), (-1,1), (-1,0), (0,-1)]	# same for pointy-top
PLOT_DIR = [(0,-1), (1,-1), (1,1), (0,1), (-1,1), (-1,-1)]	# position of direction indicator
TURRET_CHAR = [254, 47, 92, 254, 47, 92]			# characters to use for turret display

# relative locations of edge cells in a given direction for a map hex
HEX_EDGE_CELLS = {
	0: [(-1,-2),(0,-2),(1,-2)],
	1: [(1,-2),(2,-1),(3,0)],
	2: [(3,0),(2,1),(1,2)],
	3: [(1,2),(0,2),(-1,2)],
	4: [(-1,2),(-2,1),(-3,0)],
	5: [(-3,0),(-2,-1),(-1,-2)]
}

# same for campaign day hexes (pointy-topped)
CD_HEX_EDGE_CELLS = {
	0: [(0,-4),(1,-3),(2,-2),(3,-1)],
	1: [(3,-1),(3,0),(3,1)],
	2: [(3,1),(2,2),(1,3),(0,4)],
	3: [(0,4),(-1,3),(-2,2),(-3,1)],
	4: [(-3,1),(-3,0),(-3,-1)],
	5: [(-3,-1),(-2,-2),(-1,-3),(0,-4)]
}

# list of hexes on campaign day map
CAMPAIGN_DAY_HEXES = [
	(0,0),(1,0),(2,0),(3,0),(4,0),
	(0,1),(1,1),(2,1),(3,1),
	(-1,2),(0,2),(1,2),(2,2),(3,2),
	(-1,3),(0,3),(1,3),(2,3),
	(-2,4),(-1,4),(0,4),(1,4),(2,4),
	(-2,5),(-1,5),(0,5),(1,5),
	(-3,6),(-2,6),(-1,6),(0,6),(1,6),
	(-3,7),(-2,7),(-1,7),(0,7),
	(-4,8),(-3,8),(-2,8),(-1,8),(0,8)
]


##### Colour Definitions #####
KEY_COLOR = libtcod.Color(255, 0, 255)			# key color for transparency
ACTION_KEY_COL = libtcod.Color(51, 153, 255)		# colour for key commands
HIGHLIGHT_MENU_COL = libtcod.Color(30, 70, 130)		# background highlight colour for selected menu option
PORTRAIT_BG_COL = libtcod.Color(217, 108, 0)		# background color for unit portraits
UNKNOWN_UNIT_COL = libtcod.grey				# unknown enemy unit display colour
ENEMY_UNIT_COL = libtcod.Color(255, 20, 20)		# known "
ALLIED_UNIT_COL = libtcod.Color(120, 120, 255)		# allied unit display colour
GOLD_COL = libtcod.Color(255, 255, 100)			# golden colour for awards

# text names for months
MONTH_NAMES = [
	'', 'January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September',
	'October', 'November', 'December'
]

# order of turn phases
PHASE_COMMAND = 0
PHASE_SPOTTING = 1
PHASE_CREW_ACTION = 2
PHASE_MOVEMENT = 3
PHASE_SHOOTING = 4
PHASE_CC = 5
PHASE_ALLIED_ACTION = 6
PHASE_ENEMY_ACTION = 7

# text names for scenario turn phases
SCEN_PHASE_NAMES = [
	'Command', 'Spotting', 'Crew Action', 'Movement', 'Shooting', 'Close Combat', 'Allied Action', 'Enemy Action'
]

# colour associated with phases
SCEN_PHASE_COL = [
	libtcod.yellow, libtcod.purple, libtcod.light_blue, libtcod.green, libtcod.red, libtcod.white, ALLIED_UNIT_COL, ENEMY_UNIT_COL 
]

# list of campaign day menus and their highlight colours
CD_MENU_LIST = [
	('Support', 1, libtcod.Color(128, 128, 128)),
	('Crew', 2, libtcod.Color(140, 140, 0)),
	('Travel', 3, libtcod.Color(70, 140, 0)),
	('Group', 4, libtcod.Color(180, 0, 45)),
	('Supply', 5, libtcod.Color(128, 100, 64))
]

# directional arrows for directions on the campaign day map
CD_DIR_ARROW = [
	228,26,229,230,27,231
]

# list of commands for travel in campaign day
CD_TRAVEL_CMDS = [
	('e',2,-2,228), ('d',2,0,26), ('c',2,2,229), ('z',-2,2,230), ('a',-2,0,27), ('q',-2,-2,231)
]

# order to display ammo types
AMMO_TYPES = ['HE', 'AP']

# list of MG-type weapons
MG_WEAPONS = ['Co-ax MG', 'Turret MG', 'Hull MG', 'AA MG']

# text names for months
MONTH_NAMES = [
	'', 'January', 'February', 'March', 'April', 'May', 'June', 'July', 'August',
	'September', 'October', 'November', 'December'
]


##########################################################################################
#                                    Engine Constants                                    #
##########################################################################################

# FUTURE: move these to a JSON file

# length of scenario turn in minutes
TURN_LENGTH = 2

# maximum visible distance when buttoned up
MAX_BU_LOS = 1

# base chance to spot unit at distance 0,1,2,3
SPOT_BASE_CHANCE = [95.0, 85.0, 70.0, 50.0]

# each point of Perception increases chance to spot enemy unit by this much
PERCEPTION_SPOTTING_MOD = 5.0

# base chance of moving forward/backward into next hex
BASE_FORWARD_MOVE_CHANCE = 50.0
BASE_REVERSE_MOVE_CHANCE = 20.0

# bonus per unsuccessful move attempt
BASE_MOVE_BONUS = 15.0

# critical hit and miss thresholds
CRITICAL_HIT = 3.0
CRITICAL_MISS = 97.0

# maximum range at which MG attacks have a chance to penetrate armour
MG_AP_RANGE = 1

# base success chances for point fire attacks
# first column is for vehicle targets, second is everything else
PF_BASE_CHANCE = [
	[98.0, 88.0],			# same hex
	[83.0, 78.0],			# 1 hex range
	[72.0, 58.0],			# 2 "
	[58.0, 35.0]			# 3 hex range
]

# bonus for level 1 and level 2 acquired target
AC_BONUS = [10.0, 25.0]

# modifier for target size if target is known
PF_SIZE_MOD = {
	'Very Small' : -28.0,
	'Small' : -12.0,
	'Large' : 12.0,
	'Very Large' : 28.0
}

# base chances of partial effect for area fire attacks: infantry/gun and vehicle targets
INF_FP_BASE_CHANCE = 30.0
VEH_FP_BASE_CHANCE = 20.0

FP_CHANCE_STEP = 5.0		# each additional firepower beyond 1 adds this additional chance
FP_CHANCE_STEP_MOD = 0.95	# additional firepower modifier reduced by this much beyond 1
FP_FULL_EFFECT = 0.75		# multiplier for full effect
FP_CRIT_EFFECT = 0.1		# multipler for critical effect


RESOLVE_FP_BASE_CHANCE = 5.0	# base chance of a 1 firepower attack destroying a unit
RESOLVE_FP_CHANCE_STEP = 5.0	# each additional firepower beyond 1 adds this additional chance
RESOLVE_FP_CHANCE_MOD = 1.05	# additional firepower modifier increased by this much beyond 1

ARTY_BASE_SPOT_CHANCE = 50.0	# base chance of ranging in with an artillery support attack

MORALE_CHECK_BASE_CHANCE = 70.0	# base chance of passing a morale check


# base success chances for armour penetration
AP_BASE_CHANCE = {
	'MG' : 16.7,
	'AT Rifle' : 28.0,
	'20L' : 28.0,
	'37S' : 58.4,
	'37' : 72.0,
	'37L' : 83.0,
	'47S' : 72.0,
	'45L' : 91.7,
	'75S' : 91.7,
	'75' : 120.0,		# not sure if this and below are accurate, FUTURE: check balance
	'75L' : 160.0,
	'76S' : 83.0,
	'88L' : 200.0
}

# effective FP of an HE hit from different weapon calibres
HE_FP_EFFECT = [
	(200, 36),(183, 34),(170, 32),(160, 31),(150, 30),(140, 28),(128, 26),(120, 24),
	(107, 22),(105, 22),(100, 20),(95, 19),(88, 18),(85, 17),(80, 16),(75, 14),
	(70, 12),(65, 10),(60, 8),(57, 7),(50, 6),(45, 5),(37, 4),(30, 2),(25, 2),(20, 1)
]

# penetration chance on armour of HE hits
HE_AP_CHANCE = [
	(150, 110.0),
	(120, 100.0),
	(100, 91.7),
	(80, 72.2),
	(70, 58.4),
	(50, 41.7),
	(40, 27.8),
	(30, 16.7),
]

# odds of unarmoured vehicle destruction when resolving FP
VEH_FP_TK = [
	(36, 110.0),
	(30, 100.0),
	(24, 97.0),
	(20, 92.0),
	(16, 83.0),
	(12, 72.0),
	(8, 58.0),
	(6, 42.0),
	(4, 28.0),
	(2, 17.0),
	(1, 8.0)
]

# amount within an AFV armour save will result in Stun tests for crew/unit
AP_STUN_MARGIN = 10.0

# terrain type odds for campaign day hexes
# FUTURE: can have different sets for different areas of the world
CD_TERRAIN_ODDS = {
	'Flat' : 50.0,
	'Forest' : 10.0,
	'Hills' : 15.0,
	'Fields' : 10.0,
	'Marsh' : 5.0,
	'Villages' : 10.0
}

# for each campaign day hex terrain type, odds that a unit on the scenario map will be in
# a given type of terrain in its scenario hex
SCENARIO_TERRAIN_ODDS = {
	'Flat' : {
		'Open Ground' : 60.0,
		'Broken Ground' : 20.0,
		'Brush' : 10.0,
		'Woods' : 5.0,
		'Wooden Buildings' : 5.0
	},
	'Forest' : {
		'Open Ground' : 10.0,
		'Broken Ground' : 15.0,
		'Brush' : 25.0,
		'Woods' : 45.0,
		'Wooden Buildings' : 5.0
	},
	'Hills' : {
		'Open Ground' : 15.0,
		'Broken Ground' : 10.0,
		'Brush' : 5.0,
		'Woods' : 5.0,
		'Hills' : 50.0,
		'Wooden Buildings' : 5.0
	},
	'Fields' : {
		'Open Ground' : 20.0,
		'Broken Ground' : 5.0,
		'Brush' : 5.0,
		'Woods' : 5.0,
		'Fields' : 50.0,
		'Wooden Buildings' : 5.0
	},
	'Marsh' : {
		'Open Ground' : 10.0,
		'Broken Ground' : 5.0,
		'Brush' : 5.0,
		'Woods' : 5.0,
		'Marsh' : 60.0,
		'Wooden Buildings' : 5.0
	},
	'Villages' : {
		'Open Ground' : 10.0,
		'Broken Ground' : 10.0,
		'Brush' : 10.0,
		'Woods' : 5.0,
		'Fields' : 15.0,
		'Wooden Buildings' : 50.0
	}
}

# TODO: modifiers and effects for different types of terrain on the scenario layer
SCENARIO_TERRAIN_EFFECTS = {
	'Open Ground' : {
		'HD Chance' : 5.0
	},
	'Broken Ground' : {
		'TEM' : {
			'Infantry' : -15.0,
			'Deployed Gun' : -15.0
		},
		'HD Chance' : 10.0,
		'Movement Mod' : -5.0,
		'Bog Mod' : 5.0
	},
	'Brush': {
		'TEM' : {
			'All' : -15.0
		},
		'HD Chance' : 10.0,
		'Movement Mod' : -15.0,
		'Bog Mod' : 15.0,
		'Air Burst' : 10.0,
		'Burnable' : True
	},
	'Woods': {
		'TEM' : {
			'All' : -25.0
		},
		'HD Chance' : 20.0,
		'Movement Mod' : -30.0,
		'Bog Mod' : 30.0,
		'Air Burst' : 20.0,
		'Burnable' : True
	},
	'Fields': {
		'TEM' : {
			'All' : -10.0
		},
		'HD Chance' : 5.0,
		'Burnable' : True
	},
	'Hills': {
		'TEM' : {
			'All' : -20.0
		},
		'HD Chance' : 40.0,
		'Hidden Mod' : 30.0
	},
	'Wooden Buildings': {
		'TEM' : {
			'Infantry' : -30.0,
			'Deployed Gun' : -30.0
		},
		'HD Chance' : 30.0,
		'Hidden Mod' : 20.0,
		'Burnable' : True
	}
}

# Road: no effects but allows road movement; -TEM for units using road movement
# Entrenchments: ++TEM for infantry if not moving and deployed guns
# Hills: ++Hidden Chance -move chance, +bog chance
# Orchard: +TEM; -move chance; can Burn
# Marsh: -TEM; --move chance, ++bog chance
# Riverbank: -TEM
# Stone Building: ++Hidden chance; +++TEM for infantry and guns
# Fortifications: ++Hidden chance; ++++TEM for infantry and guns
# Railroad: -TEM; +bog chance for non Train/Tracked vehicles

# relative locations to draw greebles for terrain on scenario map
GREEBLE_LOCATIONS = [
	(-1,-1), (0,-1), (1,-1), (-1,0), (1,0), (-1,1), (0,1), (1,1)
]


# modifier for base HD chance
HD_SIZE_MOD = {
	'Very Small' : 12.0,
	'Small' : 6.0,
	'Normal' : 0.0,
	'Large' : -6.0,
	'Very Large' : -12.0
}

# base chance of a random event in the campaign day interface
BASE_CD_RANDOM_EVENT_CHANCE = 5.0



##########################################################################################
#                                         Classes                                        #
##########################################################################################

# Campaign: stores data about a campaign and calendar currently in progress
class Campaign:
	def __init__(self):
		
		self.player_vp = 0		# total player victory points
		
		# placeholder for player unit
		self.player_unit = None
		
		self.stats = {}			# campaign stats
		self.today = None		# pointer to current day in calendar
		
		# holder for active enemy units
		self.enemy_units = []
	
	
	# award VP to the player
	def AwardVP(self, vp_to_add):
		self.player_vp += vp_to_add
	
	
	# menu to select a campaign
	def CampaignSelectionMenu(self):
		
		# update screen with info about the currently selected campaign
		def UpdateCampaignSelectionScreen(selected_campaign):
			libtcod.console_clear(con)
			DrawFrame(con, 26, 1, 37, 58)
			libtcod.console_set_default_foreground(con, ACTION_KEY_COL)
			libtcod.console_print_ex(con, 45, 3, libtcod.BKGND_NONE, libtcod.CENTER,
				'Campaign Selection')
			libtcod.console_set_default_background(con, libtcod.dark_blue)
			libtcod.console_rect(con, 27, 5, 35, 4, True, libtcod.BKGND_SET)
			libtcod.console_set_default_background(con, libtcod.black)
			libtcod.console_set_default_foreground(con, libtcod.white)
			lines = wrap(selected_campaign['name'], 33)
			y = 6
			for line in lines:
				libtcod.console_print_ex(con, 45, y, libtcod.BKGND_NONE, libtcod.CENTER, line)
				y += 1
			
			# player nation flag
			if selected_campaign['player_nation'] in session.flags:
				libtcod.console_blit(session.flags[selected_campaign['player_nation']],
					0, 0, 0, 0, con, 30, 10)
			
			# player and enemy forces
			libtcod.console_print_ex(con, 45, 26, libtcod.BKGND_NONE, libtcod.CENTER,
				'PLAYER FORCE')
			libtcod.console_print_ex(con, 45, 30, libtcod.BKGND_NONE, libtcod.CENTER,
				'ENEMY FORCES')
			
			libtcod.console_set_default_foreground(con, libtcod.light_grey)
			libtcod.console_print_ex(con, 45, 27, libtcod.BKGND_NONE, libtcod.CENTER,
				selected_campaign['player_nation'])
			text = ''
			for nation_name in selected_campaign['enemy_nations']:
				if selected_campaign['enemy_nations'].index(nation_name) != 0:
					text += ', '
				text += nation_name
			libtcod.console_print_ex(con, 45, 31, libtcod.BKGND_NONE, libtcod.CENTER, text)
			
			# calendar range and total combat days
			libtcod.console_set_default_foreground(con, libtcod.white)
			text = GetDateText(selected_campaign['start_date']) + ' to'
			libtcod.console_print_ex(con, 45, 33, libtcod.BKGND_NONE, libtcod.CENTER, text)
			text = GetDateText(selected_campaign['end_date'])
			libtcod.console_print_ex(con, 45, 34, libtcod.BKGND_NONE, libtcod.CENTER, text)
			
			text = 'Combat Days: ' + selected_campaign['action_days']
			libtcod.console_print_ex(con, 45, 36, libtcod.BKGND_NONE, libtcod.CENTER, text)
			
			# wrapped description text
			libtcod.console_set_default_foreground(con, libtcod.light_grey)
			y = 39
			lines = wrap(selected_campaign['desc'], 33)
			for line in lines[:10]:
				libtcod.console_print(con, 28, y, line)
				y+=1
				
			libtcod.console_set_default_foreground(con, ACTION_KEY_COL)
			libtcod.console_print(con, 32, 53, EnKey('a').upper() + '/' + EnKey('d').upper())
			libtcod.console_print(con, 32, 55, 'Enter')
			libtcod.console_print(con, 32, 56, 'Esc')
			libtcod.console_set_default_foreground(con, libtcod.white)
			libtcod.console_print(con, 38, 53, 'Change Campaign')
			libtcod.console_print(con, 38, 55, 'Proceed')
			libtcod.console_print(con, 38, 56, 'Return to Main Menu')
			
			libtcod.console_blit(con, 0, 0, 0, 0, 0, 0, 0)
		
		# load basic information of campaigns into a list of dictionaries
		BASIC_INFO = [
			'name', 'start_date', 'end_date', 'action_days', 'player_nation',
			'enemy_nations', 'desc'
		]
		
		campaign_list = []
		
		for filename in os.listdir(CAMPAIGNPATH):
			if not filename.endswith('.json'): continue
			with open(CAMPAIGNPATH + filename, encoding='utf8') as data_file:
				campaign_data = json.load(data_file)
			new_campaign = {}
			new_campaign['filename'] = filename
			for k in BASIC_INFO:
				new_campaign[k] = campaign_data[k]
			campaign_list.append(new_campaign)
			del campaign_data
		
		# sort campaigns by start date
		campaign_list = sorted(campaign_list, key = lambda x : (x['start_date']['year'],
			x['start_date']['month'], x['start_date']['day']))
		
		# select first campaign by default
		selected_campaign = campaign_list[0]
		
		# draw menu screen for first time
		UpdateCampaignSelectionScreen(selected_campaign)
		
		exit_menu = False
		while not exit_menu:
			if libtcod.console_is_window_closed(): sys.exit()
			libtcod.console_flush()
			if not GetInputEvent(): continue
			
			# exit without starting a new campaign if escape is pressed
			if key.vk == libtcod.KEY_ESCAPE:
				return False
			
			# proceed with selected campaign
			elif key.vk == libtcod.KEY_ENTER:
				exit_menu = True
			
			key_char = DeKey(chr(key.c).lower())
			
			# change selected campaign
			if key_char in ['a', 'd']:
				
				i = campaign_list.index(selected_campaign)
				
				if key_char == 'd':
					if i == len(campaign_list) - 1:
						selected_campaign = campaign_list[0]
					else:
						selected_campaign = campaign_list[i+1]
				else:
					if i == 0:
						selected_campaign = campaign_list[-1]
					else:
						selected_campaign = campaign_list[i-1]
				UpdateCampaignSelectionScreen(selected_campaign)
		
		# create a local copy of selected scenario stats
		with open(CAMPAIGNPATH + selected_campaign['filename'], encoding='utf8') as data_file:
			self.stats = json.load(data_file)
		
		# set current day to first day in calendar
		self.today = self.stats['calendar'][0]
		
		return True
		
		
	# menu to select player tank
	# also allows input/generation of tank name, and return both
	# FUTURE: can be used when replacing a tank mid-campaign as well
	def TankSelectionMenu(self):
		
		def UpdateTankSelectionScreen(selected_unit, player_tank_name):
			libtcod.console_clear(con)
			DrawFrame(con, 26, 1, 37, 58)
			
			libtcod.console_set_default_background(con, libtcod.darker_blue)
			libtcod.console_rect(con, 27, 2, 35, 3, False, libtcod.BKGND_SET)
			libtcod.console_set_default_background(con, libtcod.black)
			
			libtcod.console_set_default_foreground(con, ACTION_KEY_COL)
			libtcod.console_print_ex(con, 45, 3, libtcod.BKGND_NONE, libtcod.CENTER,
				'Player Unit Selection')
			libtcod.console_set_default_foreground(con, libtcod.white)
			
			libtcod.console_print_ex(con, 45, 6, libtcod.BKGND_NONE, libtcod.CENTER,
				'Select a unit to command')
			libtcod.console_print_ex(con, 45, 7, libtcod.BKGND_NONE, libtcod.CENTER,
				'to start the campaign')
			
			DrawFrame(con, 32, 10, 27, 18)
			selected_unit.DisplayMyInfo(con, 33, 11, status=False)
			libtcod.console_set_default_foreground(con, libtcod.white)
			libtcod.console_print(con, 33, 26, 'Crew: ' + str(len(selected_unit.GetStat('crew_positions'))))
			
			libtcod.console_print(con, 33, 13, player_tank_name)
			
			text = ''
			for t in selected_unit.GetStat('description'):
				text += t
			
			lines = wrap(text, 33)
			y = 32
			libtcod.console_set_default_foreground(con, libtcod.light_grey)
			for line in lines[:20]:
				libtcod.console_print(con, 28, y, line)
				y+=1
			
			libtcod.console_set_default_foreground(con, ACTION_KEY_COL)
			libtcod.console_print(con, 32, 53, EnKey('a').upper() + '/' + EnKey('d').upper())
			libtcod.console_print(con, 32, 54, 'N')
			libtcod.console_print(con, 32, 55, 'Enter')
			libtcod.console_set_default_foreground(con, libtcod.white)
			libtcod.console_print(con, 38, 53, 'Select Unit Type')
			libtcod.console_print(con, 38, 54, 'Set/Generate Tank Name')
			libtcod.console_print(con, 38, 55, 'Proceed')
			
			libtcod.console_blit(con, 0, 0, 0, 0, 0, 0, 0)
		
		# generate tempoary list of units, one per possible unit type
		unit_list = []
		
		for unit_id in self.stats['player_unit_list']:
			new_unit = Unit(unit_id)
			unit_list.append(new_unit)
		
		# select first tank by default
		selected_unit = unit_list[0]
		
		# placeholder for tank name if any
		player_tank_name = ''
		
		# draw menu screen for first time
		UpdateTankSelectionScreen(selected_unit, player_tank_name)
		
		exit_loop = False
		while not exit_loop:
			
			# emergency exit in case of endless loop
			if libtcod.console_is_window_closed(): sys.exit()
			
			libtcod.console_flush()
			if not GetInputEvent(): continue
			
			# proceed with selected tank
			if key.vk == libtcod.KEY_ENTER:
				exit_loop = True
			
			# unmapped keys
			key_char = chr(key.c).lower()
			
			# change/generate player tank name
			if key_char == 'n':
				
				player_tank_name = ShowTextInputMenu('Enter a name for your tank', player_tank_name, MAX_TANK_NAME_LENGTH, [])
				UpdateTankSelectionScreen(selected_unit, player_tank_name)
			
			# mapped keys
			key_char = DeKey(chr(key.c).lower())
			
			# change selected tank
			if key_char in ['a', 'd']:
				
				i = unit_list.index(selected_unit)
				
				if key_char == 'd':
					if i == len(unit_list) - 1:
						selected_unit = unit_list[0]
					else:
						selected_unit = unit_list[i+1]
				else:
					if i == 0:
						selected_unit = unit_list[-1]
					else:
						selected_unit = unit_list[i-1]
				UpdateTankSelectionScreen(selected_unit, player_tank_name)
			
		return (selected_unit.unit_id, player_tank_name)
	
	# display a briefing for the start of a new campaign day
	def ShowCDBriefing(self):
		
		# generate the briefing screen
		libtcod.console_clear(con)
		
		for y in range(WINDOW_HEIGHT):
			col = libtcod.Color(int(255 * (y / WINDOW_HEIGHT)), int(170 * (y / WINDOW_HEIGHT)), 0)
			libtcod.console_set_default_background(con, col)
			libtcod.console_rect(con, 0, y, WINDOW_WIDTH, 1, True, libtcod.BKGND_SET)
		libtcod.console_set_default_background(con, libtcod.black)
		
		# display briefing outline, 29x54
		libtcod.console_blit(LoadXP('CD_briefing.xp'), 0, 0, 0, 0, con, 31, 3)
		libtcod.console_set_default_foreground(con, libtcod.white)
		
		# current date, time, and location
		libtcod.console_print_ex(con, 45, 4, libtcod.BKGND_NONE, libtcod.CENTER, GetDateText(campaign.today))
		text = campaign.today['start_hour'].zfill(2) + ':' + campaign.today['start_minute'].zfill(2)
		libtcod.console_print_ex(con, 45, 5, libtcod.BKGND_NONE, libtcod.CENTER, text)
		text = campaign.today['location']
		libtcod.console_print_ex(con, 45, 6, libtcod.BKGND_NONE, libtcod.CENTER, text)
		
		# day description
		libtcod.console_set_default_foreground(con, libtcod.light_grey)
		lines = wrap(campaign.today['desc'], 25)
		y = 8
		for line in lines:
			libtcod.console_print(con, 33, y, line)
			y+=1
			if y == 19: break
		
		# placeholder for mission details
		libtcod.console_set_default_foreground(con, libtcod.white)
		libtcod.console_print_ex(con, 45, 23, libtcod.BKGND_NONE, libtcod.CENTER,
			'Advance')
		
		libtcod.console_set_default_foreground(con, libtcod.light_grey)
		text = 'Capture enemy-held territory and destroy enemy units.'
		lines = wrap(text, 25)
		y = 25
		for line in lines:
			libtcod.console_print(con, 32, y, line)
			y+=1
			if y == 29: break
		
		# player support
		text = 'Air Support: '
		if 'air_support_level' not in campaign.today:
			text += 'None'
		else:
			text += str(campaign.today['air_support_level'])
		libtcod.console_print(con, 33, 33, text)
		
		text = 'Artillery Support: '
		if 'arty_support_level' not in campaign.today:
			text += 'None'
		else:
			text += str(campaign.today['arty_support_level'])
		libtcod.console_print(con, 33, 34, text)
		
		# expected enemy forces
		text = session.nations[campaign.stats['enemy_nations'][0]]['adjective']
		text += ' infantry, guns, and AFVs'
		lines = wrap(text, 25)
		y = 39
		for line in lines:
			libtcod.console_print(con, 33, y, line)
			y+=1
			if y == 42: break
		
		# FUTURE: weather forecast
		
		# end of day
		text = 'End of Day: ' + campaign.today['end_hour'].zfill(2) + ':' + campaign.today['end_minute'].zfill(2)
		libtcod.console_print_ex(con, 45, 49, libtcod.BKGND_NONE, libtcod.CENTER, text)
		
		libtcod.console_blit(con, 0, 0, 0, 0, 0, 0, 0)
		libtcod.console_flush()
		
		# wait for player input
		exit_loop = False
		cont = False
		while not exit_loop:
			if libtcod.console_is_window_closed(): sys.exit()
			libtcod.console_flush()
			if not GetInputEvent(): continue
			
			if key.vk in [libtcod.KEY_ENTER, libtcod.KEY_ESCAPE]:
				if key.vk == libtcod.KEY_ENTER:
					cont = True
				exit_loop = True
		return cont



# Campaign Day: represents one calendar day in a campaign with a 5x7 map of terrain hexes, each of
# which may spawn a Scenario
class CampaignDay:
	def __init__(self):
		
		# current weather conditions, will be set by GenerateWeather
		self.weather = {
			'Cloud Cover': '',
			'Precipitation': '',
			'Fog': 0,
			'Ground': ''
		}
		self.weather_update_clock = 0		# number of minutes until next weather update
		self.GenerateWeather()
		
		self.fate_points = libtcod.random_get_int(0, 1, 3)	# fate points protecting the player
		
		# victory point rewards for this campaign day
		self.capture_zone_vp = 2
		self.unit_destruction_vp = {
			'Infantry': 1,
			'Gun' : 2,
			'Vehicle': 4 
		}
		
		# records for end-of-day summary
		self.records = {
			'Map Areas Captured' : 0,
			'Gun Hits' : 0,
			'Vehicles Destroyed' : 0,
			'Guns Destroyed' : 0,
			'Infantry Destroyed' : 0
		}
		
		# current hour, and minute: set initial time from campaign info
		self.day_clock = {}
		self.day_clock['hour'] = int(campaign.today['start_hour'])
		self.day_clock['minute'] = int(campaign.today['start_minute'])
		
		# end of day
		self.end_of_day = {}
		self.end_of_day['hour'] = int(campaign.today['end_hour'])
		self.end_of_day['minute'] = int(campaign.today['end_minute'])
		
		# combat day length in minutes
		hours = self.end_of_day['hour'] - self.day_clock['hour']
		minutes = self.end_of_day['minute'] - self.day_clock['minute']
		if minutes < 0:
			hours -= 1
			minutes += 60
		self.day_length = minutes + (hours * 60)
		
		# current odds of a random event being triggered
		self.random_event_chance = BASE_CD_RANDOM_EVENT_CHANCE
		
		# flag set when end of day has been reached
		self.ended = False
		
		# log of important events during the day
		self.day_log = []
		
		# generate campaign day map
		self.map_hexes = {}
		for (hx, hy) in CAMPAIGN_DAY_HEXES:
			self.map_hexes[(hx,hy)] = CDMapHex(hx, hy)
		
			# set zone terrain type too
			self.map_hexes[(hx,hy)].GenerateTerrainType()
		
		# dictionary of screen display locations on the display console
		self.cd_map_index = {}
		
		# FUTURE: generate dirt roads on campaign day map
		#self.GenerateRoads()
		
		self.active_menu = 3				# number of currently active command menu
		self.selected_direction = None			# select direction for support, travel, etc.
		self.abandoned_tank = False			# set to true if player abandoned their tank that day
		self.scenario = None				# currently active scenario in progress
		
		self.air_support_level = 0.0
		if 'air_support_level' in campaign.today:
			self.air_support_level = campaign.today['air_support_level']
			self.air_support_step = campaign.today['air_support_step']
		
		self.arty_support_level = 0.0
		if 'arty_support_level' in campaign.today:
			self.arty_support_level = campaign.today['arty_support_level']
			self.arty_support_step = campaign.today['arty_support_step']
		
		self.encounter_mod = 0.0			# increases every time player caputures an area without resistance
		
		# set up player
		self.player_unit_location = (-2, 8)		# set initial player unit location
		self.map_hexes[(-2, 8)].controlled_by = 0	# set player location to player control
	
	
	# generate a new random set of initial weather conditions, should only be called when day is created
	def GenerateWeather(self):
		
		# cloud cover
		roll = GetPercentileRoll()
		
		if roll <= 50.0:
			self.weather['Cloud Cover'] = 'Clear'
		elif roll <= 65.0:
			self.weather['Cloud Cover'] = 'Scattered'
		elif roll <= 85.0:
			self.weather['Cloud Cover'] = 'Heavy'
		else:
			self.weather['Cloud Cover'] = 'Overcast'
		
		# precipitation
		if self.weather['Cloud Cover'] == 'Clear':
			self.weather['Precipitation'] = 'None'
		else:
			roll = GetPercentileRoll()
			
			if roll <= 40.0:
				self.weather['Precipitation'] = 'None'
			elif roll <= 50.0:
				self.weather['Precipitation'] = 'Mist'
			elif roll <= 80.0:
				self.weather['Precipitation'] = 'Rain'
			else:
				self.weather['Precipitation'] = 'Heavy Rain'
		
		# FUTURE fog level: 0-3
		
		# Ground conditions
		roll = GetPercentileRoll()
		
		if self.weather['Cloud Cover'] == 'Clear':
			roll -= 40.0
		elif self.weather['Cloud Cover'] == 'Overcast':
			roll += 10.0
		
		if self.weather['Precipitation'] == 'None':
			roll -= 20.0
		elif self.weather['Precipitation'] == 'Rain':
			roll += 30.0
		elif self.weather['Precipitation'] == 'Heavy Rain':
			roll += 70.0
		
		if roll <= 75.0:
			self.weather['Ground'] = 'Dry'
		elif roll <= 85.0:
			self.weather['Ground'] = 'Wet'
		else:
			self.weather['Ground'] = 'Muddy'
		
		# set first weather update countdown
		self.weather_update_clock = 14 + (libtcod.random_get_int(0, 1, 16))
	
	
	# update weather conditions, possibly changing them
	def UpdateWeather(self):
		
		# reset update clock
		self.weather_update_clock = 14 + (libtcod.random_get_int(0, 1, 16))
		
		# always apply ground condition update
		
		roll = GetPercentileRoll()
			
		if self.weather['Ground'] == 'Muddy':
			if self.weather['Precipitation'] == 'None':
				if roll <= 20.0:
					self.weather['Ground'] = 'Wet'
					ShowMessage('The ground has become less muddy.')
		
		elif self.weather['Ground'] == 'Wet':
			if self.weather['Precipitation'] == 'None':
				if roll <= 20.0:
					self.weather['Ground'] = 'Dry'
					ShowMessage('The ground has dried out.')
			else:
				
				if self.weather['Precipitation'] == 'Heavy Rain':
					roll -= 10.0
				
				if roll <= 30.0:
					self.weather['Ground'] = 'Muddy'
					ShowMessage('The ground has become muddy.')
		# dry ground
		else:
			if self.weather['Precipitation'] != 'None':
				
				if self.weather['Precipitation'] == 'Heavy Rain':
					roll -= 10.0
				
				if roll <= 25.0:
					self.weather['Ground'] = 'Wet'
					ShowMessage('The ground has become wet.')
		
		
		# roll for possible type of change
		roll = GetPercentileRoll()
			
		# change in precipitation level
		if roll <= 50.0:
			
			if self.weather['Cloud Cover'] == 'Clear':
				return False
			
			roll = GetPercentileRoll()
			
			if self.weather['Precipitation'] == 'None':
				if roll <= 20.0:
					self.weather['Precipitation'] = 'Mist'
					ShowMessage('A light mist begins to fall.')
				elif roll <= 40.0:
					self.weather['Precipitation'] = 'Rain'
					ShowMessage('Rain begins to fall.')
				elif roll <= 50.0:
					self.weather['Precipitation'] = 'Heavy Rain'
					ShowMessage('A heavy downpour suddenly begins to fall.')
				else:
					return False
			
			elif self.weather['Precipitation'] == 'Mist':
				if roll <= 20.0:
					self.weather['Precipitation'] = 'None'
					ShowMessage('The light mist has cleared up.')
				elif roll <= 40.0:
					self.weather['Precipitation'] = 'Rain'
					ShowMessage('The light mist thickens into a steady rain.')
				elif roll <= 50.0:
					self.weather['Precipitation'] = 'Heavy Rain'
					ShowMessage('The light mist suddenly turns into a heavy downpour.')
				else:
					return False
			
			elif self.weather['Precipitation'] == 'Rain':
				if roll <= 15.0:
					self.weather['Precipitation'] = 'None'
					ShowMessage('The rain has cleared up.')
				elif roll <= 35.0:
					self.weather['Precipitation'] = 'Mist'
					ShowMessage('The rain turns into a light mist.')
				elif roll <= 50.0:
					self.weather['Precipitation'] = 'Heavy Rain'
					ShowMessage('The rain gets heavier.')
				else:
					return False
			
			elif self.weather['Precipitation'] == 'Heavy Rain':
				if roll <= 35.0:
					self.weather['Precipitation'] = 'Rain'
					ShowMessage('The rain lightens a little.')
				else:
					return False
			
			return True
		
		# FUTURE: change in fog level
		#elif roll <= 75.0:
		#	return False
		
		# change in cloud level
		else:
			
			roll = GetPercentileRoll()
			
			if self.weather['Cloud Cover'] == 'Clear':
				if roll <= 25.0:
					self.weather['Cloud Cover'] = 'Scattered'
					ShowMessage('Scattered clouds begin to form.')
				elif roll <= 30.0:
					self.weather['Cloud Cover'] = 'Heavy'
					ShowMessage('A heavy cloud front rolls in.')
				else:
					return False
			
			elif self.weather['Cloud Cover'] == 'Scattered':
				if roll <= 35.0:
					# clouds won't disappear if precip is falling
					if self.weather['Precipitation'] == 'None':
						return
					self.weather['Cloud Cover'] = 'Clear'
					ShowMessage('The clouds part and the sky is clear.')
				elif roll <= 50.0:
					self.weather['Cloud Cover'] = 'Heavy'
					ShowMessage('The cloud cover gets thicker.')
				elif roll <= 55.0:
					self.weather['Cloud Cover'] = 'Overcast'
					ShowMessage('A storm front has rolled in.')
				else:
					return False
			
			elif self.weather['Cloud Cover'] == 'Heavy':
				if roll <= 25.0:
					self.weather['Cloud Cover'] = 'Scattered'
					ShowMessage('The clouds begin to thin out.')
				elif roll <= 40.0:
					self.weather['Cloud Cover'] = 'Overcast'
					ShowMessage('The cloud cover thickens.')
				else:
					return False
			
			# overcast
			else:
				if roll <= 25.0:
					self.weather['Cloud Cover'] = 'Heavy'
					ShowMessage('The cloud cover begins to part but remains heavy.')
				else:
					return False
			
			# stop rain if clouds have cleared up
			if self.weather['Cloud Cover'] == 'Clear' and self.weather['Precipitation'] != 'None':
				self.weather['Precipitation'] = 'None'
				ShowMessage('The rain has stopped.')
			
			return True

	
	# advance the current campaign day time, check for end of day, and also weather conditions update
	def AdvanceClock(self, hours, minutes):
		self.day_clock['hour'] += hours
		self.day_clock['minute'] += minutes
		while self.day_clock['minute'] >= 60:
			self.day_clock['hour'] += 1
			self.day_clock['minute'] -= 60
		self.CheckForEndOfDay()
		# check for weather update
		self.weather_update_clock -= hours * 60
		self.weather_update_clock -= minutes
		if self.weather_update_clock <= 0:
			# if weather conditions change, update relevant consoles
			if self.UpdateWeather():
				self.UpdateCDCommandCon()
				DisplayWeatherInfo(cd_weather_con)
				if scenario is not None:
					scenario.UpdateScenarioInfoCon()
	
	
	# sets flag if we've met or exceeded the set length of the combat day
	def CheckForEndOfDay(self):
		if self.day_clock['hour'] > self.end_of_day['hour']:
			self.ended = True
		if self.day_clock['hour'] == self.end_of_day['hour']:
			if self.day_clock['minute'] >= self.end_of_day['minute']:
				self.ended = True
	
	
	# roll for trigger of random Campaign Day event
	def CheckForRandomEvent(self):
		
		# don't trigger an event if day has already ended
		if self.ended: return
		
		roll = GetPercentileRoll()
		
		if DEBUG:
			if session.debug['Always CD Random Event']:
				roll = 1.0
		
		if roll > self.random_event_chance:
			self.random_event_chance += 2.0
			return
		
		# reset random event chance
		self.random_event_chance = BASE_CD_RANDOM_EVENT_CHANCE
		
		# roll for event
		roll = GetPercentileRoll()
		
		# friendly forces capture an enemy zone
		if roll <= 35.0:
			
			# find a possible zone to capture
			hex_list = []
			for (hx, hy) in self.map_hexes:
				map_hex = self.map_hexes[(hx,hy)]
				if map_hex.controlled_by == 0: continue
				
				# make sure there is at least one adjacent friendly hex
				for direction in range(5):
					(hx2, hy2) = self.GetAdjacentCDHex(hx, hy, direction)
					if (hx2, hy2) not in self.map_hexes: continue
					if self.map_hexes[(hx2,hy2)].controlled_by == 0:
						hex_list.append((hx,hy))
						break
			
			# no possible hexes to capture
			if len(hex_list) == 0:
				return
			
			ShowMessage('Allied forces have captured an enemy-held zone!') 
			(hx, hy) = choice(hex_list)
			self.map_hexes[(hx,hy)].CaptureMe(0, no_vp=True)
		
		# enemy strength increases
		elif roll <= 45.0:
			
			hex_list = []
			for (hx, hy) in self.map_hexes:
				if self.map_hexes[(hx,hy)].controlled_by == 0: continue
				hex_list.append((hx, hy))
			
			if len(hex_list) == 0:
				return
			
			(hx, hy) = choice(hex_list)
			map_hex = self.map_hexes[(hx,hy)]
			
			map_hex.enemy_strength += libtcod.random_get_int(0, 1, 3)
			if map_hex.enemy_strength > 10:
				map_hex.enemy_strength = 10
			
			# don't show anything if zone not known to player
			if not map_hex.known_to_player: return
			
			ShowMessage('We have reports of an increase of enemy strength in a zone!')
			# FUTURE: highlight hex momentarily
		
		# reveal enemy strength
		elif roll <= 55.0:
			
			hex_list = []
			for (hx, hy) in self.map_hexes:
				if self.map_hexes[(hx,hy)].controlled_by == 0: continue
				if self.map_hexes[(hx,hy)].known_to_player: continue
				hex_list.append((hx, hy))
			
			if len(hex_list) == 0:
				return
			
			(hx, hy) = choice(hex_list)
			self.map_hexes[(hx,hy)].known_to_player = True
			
			ShowMessage('We have received information about expected enemy strength in an area.')
			# FUTURE: highlight hex momentarily
		
		# friendly zone lost
		elif roll <= 60.0:
			
			hex_list = []
			for (hx, hy) in self.map_hexes:
				map_hex = self.map_hexes[(hx,hy)]
				if map_hex.controlled_by == 1: continue
				# don't capture player location!
				if (hx, hy) == self.player_unit_location: continue
				
				# make sure there is at least one adjacent enemy hex
				for direction in range(5):
					(hx2, hy2) = self.GetAdjacentCDHex(hx, hy, direction)
					if (hx2, hy2) not in self.map_hexes: continue
					if self.map_hexes[(hx2,hy2)].controlled_by == 1:
						hex_list.append((hx,hy))
						break
			
			# no possible hexes to capture
			if len(hex_list) == 0:
				return
			
			ShowMessage('Enemy forces have captured an allied-held zone!') 
			(hx, hy) = choice(hex_list)
			self.map_hexes[(hx,hy)].CaptureMe(1)
		
		# free resupply
		elif roll <= 65.0:
			ShowMessage('You happen to encounter a supply truck, and can restock your gun ammo.')
			self.AmmoReloadMenu()
		
		# loss of recon knowledge and possible change in strength
		elif roll <= 80.0:
			
			hex_list = []
			for (hx, hy) in self.map_hexes:
				if self.map_hexes[(hx,hy)].controlled_by == 0: continue
				if not self.map_hexes[(hx,hy)].known_to_player: continue
				hex_list.append((hx, hy))
			
			if len(hex_list) == 0:
				return
			
			ShowMessage('Enemy movement reported in a map zone, estimated strength no longer certain.')
			
			(hx, hy) = choice(hex_list)
			map_hex = self.map_hexes[(hx,hy)]
			
			map_hex.known_to_player = False
			map_hex.enemy_strength -= 3
			map_hex.enemy_strength += libtcod.random_get_int(0, 0, 6)
			
			if map_hex.enemy_strength < 1:
				map_hex.enemy_strength = 1
			if map_hex.enemy_strength > 10:
				map_hex.enemy_strength = 10
		
		# increase current support level
		elif roll <= 90.0:
			
			text = 'Additional '
			
			if 'air_support_level' in campaign.today:
				text += 'air'
				self.air_support_level += (self.air_support_step * float(libtcod.random_get_int(0, 1, 3)))
			elif 'arty_support_level' in campaign.today:
				text += 'artillery'
				self.arty_support_level += (self.arty_support_step * float(libtcod.random_get_int(0, 1, 3)))
			else:
				return
			
			text += ' support has made available to you from Command.'
			ShowMessage(text)
		
		# no other random events for now
		else:
			pass
		
		# random event finished, update consoles and screen
		self.UpdateCDUnitCon()
		self.UpdateCDControlCon()
		self.UpdateCDGUICon()
		self.UpdateCDCommandCon()
		self.UpdateCDHexInfoCon()
		self.UpdateCDDisplay()
	
	
	# menu for restocking ammo for main guns on the player tank
	def AmmoReloadMenu(self):
		
		weapon = None
		ammo_num = 0
		add_num = 1
		
		# update the menu console and draw to screen
		def UpdateMenuCon():
			
			libtcod.console_clear(con)
			
			# window title
			libtcod.console_set_default_background(con, libtcod.dark_blue)
			libtcod.console_rect(con, 0, 2, WINDOW_WIDTH, 5, True, libtcod.BKGND_SET)
			libtcod.console_set_default_foreground(con, libtcod.white)
			libtcod.console_print_ex(con, WINDOW_XM, 4, libtcod.BKGND_NONE,
				libtcod.CENTER, 'Ammo Load')
			
			# player unit portrait
			x = 33
			y = 9
			libtcod.console_set_default_background(con, PORTRAIT_BG_COL)
			libtcod.console_rect(con, x, y, 25, 8, True, libtcod.BKGND_SET)
			portrait = campaign.player_unit.GetStat('portrait')
			if portrait is not None:
				libtcod.console_blit(LoadXP(portrait), 0, 0, 0, 0, con, x, y)
			libtcod.console_set_default_foreground(con, libtcod.white)
			if campaign.player_unit.unit_name != '':
				libtcod.console_print(con, x, y, self.player_unit.unit_name)
			libtcod.console_set_default_background(con, libtcod.black)
			
			# command menu
			x = 58
			y = 43
			libtcod.console_set_default_foreground(con, ACTION_KEY_COL)
			libtcod.console_print(con, x, y, EnKey('q').upper())
			libtcod.console_print(con, x, y+1, EnKey('e').upper())
			libtcod.console_print(con, x, y+3, EnKey('d').upper())
			libtcod.console_print(con, x, y+4, EnKey('a').upper())
			libtcod.console_print(con, x, y+6, EnKey('z').upper())
			
			libtcod.console_print(con, x, y+8, EnKey('x').upper())
			
			libtcod.console_print(con, x, y+10, 'Enter')
			
			
			libtcod.console_set_default_foreground(con, libtcod.white)
			libtcod.console_print(con, x+2, y, 'Cycle Selected Gun')
			libtcod.console_print(con, x+2, y+1, 'Cycle Selected Ammo Type')
			libtcod.console_print(con, x+2, y+3, 'Load ' + str(add_num))
			libtcod.console_print(con, x+2, y+4, 'Unload ' + str(add_num))
			libtcod.console_print(con, x+2, y+6, 'Toggle 1/10')
			
			libtcod.console_print(con, x+2, y+8, 'Default Load')
			
			libtcod.console_print(con, x+6, y+10, 'Accept and Continue')
			
			
			# possible but not likely
			if weapon is None:
				libtcod.console_blit(con, 0, 0, 0, 0, 0, 0, 0)
				return
			
			libtcod.console_print_ex(con, WINDOW_XM, 18, libtcod.BKGND_NONE,
				libtcod.CENTER, weapon.GetStat('name'))
			
			# description of ammo types available to current gun
			x = 62
			y = 9
			for ammo_type in weapon.stats['ammo_type_list']:
				
				libtcod.console_set_default_foreground(con, libtcod.white)
				
				if ammo_type == 'HE':
					libtcod.console_print(con, x, y, 'High Explosive (HE)')
					libtcod.console_set_default_foreground(con, libtcod.light_grey)
					libtcod.console_print(con, x, y+2, 'Used against guns,')
					libtcod.console_print(con, x, y+3, 'infantry, and unarmoured')
					libtcod.console_print(con, x, y+4, 'vehicles.')
					
					y += 7
				
				elif ammo_type == 'AP':
					libtcod.console_print(con, x, y, 'Armour Penetrating (AP)')
					libtcod.console_set_default_foreground(con, libtcod.light_grey)
					libtcod.console_print(con, x, y+2, 'Used against armoured')
					libtcod.console_print(con, x, y+3, 'targets.')
					
					y += 6
			
			# TODO: visual depicition of ready rack
			
			# visual depicition of main stores
			x = 41
			y = 26
			libtcod.console_set_default_foreground(con, libtcod.white)
			libtcod.console_print(con, x-8, y+1, 'Stores')
			
			ammo_count = weapon.ammo_stores.copy()
			
			libtcod.console_set_default_foreground(con, libtcod.darker_grey)
			xm = 0
			ym = 0
			total = 0
			for ammo_type in AMMO_TYPES:
				if ammo_type in ammo_count:
					for i in range(ammo_count[ammo_type]):
						
						# determine colour to use
						if ammo_type == 'HE':
							col = libtcod.grey
						elif ammo_type == 'AP':
							col = libtcod.yellow
						
						libtcod.console_put_char_ex(con, x+xm, y+ym, 7, col, libtcod.black)
						
						if xm == 8:
							xm = 0
							ym += 1
						else:
							xm += 1
						
						total += 1
			
			# fill out empty slots up to max ammo
			if total < int(weapon.stats['max_ammo']):
				for i in range(int(weapon.stats['max_ammo']) - total):
					libtcod.console_put_char(con, x+xm, y+ym, 9)
					if xm == 8:
						xm = 0
						ym += 1
					else:
						xm += 1
			
			# show current numerical values for each ammo type
			# also which type is currently selected
			x = 52
			y = 26
			for ammo_type in AMMO_TYPES:
				if ammo_type in weapon.ammo_stores:
					
					if selected_ammo_type == ammo_type:
						libtcod.console_set_default_background(con, libtcod.dark_blue)
						libtcod.console_rect(con, x, y, 10, 1, True, libtcod.BKGND_SET)
						libtcod.console_set_default_background(con, libtcod.black)
					
					if ammo_type == 'HE':
						col = libtcod.grey
					elif ammo_type == 'AP':
						col = libtcod.yellow
					libtcod.console_put_char_ex(con, x, y, 7, col, libtcod.black)
					
					libtcod.console_set_default_foreground(con, libtcod.white)
					libtcod.console_print(con, x+2, y, ammo_type)
					libtcod.console_set_default_foreground(con, libtcod.light_grey)
					libtcod.console_print_ex(con, x+8, y, libtcod.BKGND_NONE,
						libtcod.RIGHT, str(weapon.ammo_stores[ammo_type]))
					y += 1
			y += 1
			libtcod.console_set_default_foreground(con, libtcod.white)
			libtcod.console_print(con, x+2, y, 'Max:')
			libtcod.console_set_default_foreground(con, libtcod.light_grey)
			libtcod.console_print_ex(con, x+8, y, libtcod.BKGND_NONE,
				libtcod.RIGHT, weapon.stats['max_ammo'])
			
			libtcod.console_set_default_foreground(con, libtcod.light_grey)
			
			
			# TODO: visual depicition of extra ammo
			
			libtcod.console_blit(con, 0, 0, 0, 0, 0, 0, 0)
			
			
		# select first weapon by default, and first ammo type
		weapon = campaign.player_unit.weapon_list[0]
		selected_ammo_type = weapon.stats['ammo_type_list'][0]
		
		# record initial total number of ammo
		ammo_num = 0
		for ammo_type in AMMO_TYPES:
			if ammo_type in weapon.ammo_stores:
				ammo_num += weapon.ammo_stores[ammo_type]
		
		# draw screen for first time
		UpdateMenuCon()
		
		# menu input loop
		exit_menu = False
		while not exit_menu:
			
			if libtcod.console_is_window_closed(): sys.exit()
			libtcod.console_flush()
			keypress = GetInputEvent()
			if not keypress: continue
			
			if key.vk == libtcod.KEY_ENTER:
				exit_menu = True
				continue
			
			# mapped key commands
			key_char = DeKey(chr(key.c).lower())
			
			# cycle selected ammo type
			if key_char == 'e':
				i = weapon.stats['ammo_type_list'].index(selected_ammo_type)
				
				if i == len(weapon.stats['ammo_type_list']) - 1:
					i = 0
				else:
					i += 1
					
				selected_ammo_type = weapon.stats['ammo_type_list'][i]
				UpdateMenuCon()
				continue
			
			# load one shell of selected type
			elif key_char == 'd':
				
				# make sure room remains
				if ammo_num + add_num > int(weapon.stats['max_ammo']):
					continue
				
				weapon.ammo_stores[selected_ammo_type] += add_num
				ammo_num += add_num
				UpdateMenuCon()
				continue
			
			# unload one shell of selected type
			elif key_char == 'a':
				
				# make sure shell(s) are available
				if weapon.ammo_stores[selected_ammo_type] - add_num < 0:
					continue
				
				weapon.ammo_stores[selected_ammo_type] -= add_num
				ammo_num -= add_num
				UpdateMenuCon()
				continue
			
			# toggle adding/removing 1/10
			elif key_char == 'z':
				
				if add_num == 1:
					add_num = 10
				else:
					add_num = 1
				UpdateMenuCon()
				continue
			
			# replace current load with default
			elif key_char == 'x':
				
				# clear current load
				for ammo_type in AMMO_TYPES:
					if ammo_type in weapon.ammo_stores:
						weapon.ammo_stores[ammo_type] = 0
				
				# replace with default load
				
				# HE only
				if 'HE' in weapon.ammo_stores and 'AP' not in weapon.ammo_stores:
					weapon.ammo_stores['HE'] = int(weapon.stats['max_ammo'])
					
				# AP only
				elif 'AP' in weapon.ammo_stores and 'HE' not in weapon.ammo_stores:
					weapon.ammo_stores['AP'] = int(weapon.stats['max_ammo'])
		
				# HE and AP
				else:
					weapon.ammo_stores['HE'] = int(float(weapon.stats['max_ammo']) * 0.75)
					weapon.ammo_stores['AP'] = int(weapon.stats['max_ammo']) - weapon.ammo_stores['HE']
							
				UpdateMenuCon()
				continue
				
		
	
	# check to see whether we need to replace crew after a scenario
	def DoCrewCheck(self, unit):
		
		# Stunned, Unconscious, and Critical crew automatically recover
		# FUTURE: Do a final recovery roll for Critical crew
		replacement_needed = False
		for position in unit.positions_list:
			if position.crewman is None: continue
			if position.crewman != '':
				if position.crewman.status == 'Dead':
					replacement_needed = True
					continue
				position.crewman.status = ''
		
		# replace dead crewmen if needed
		if not replacement_needed: return
		
		if unit == campaign.player_unit:
			self.AdvanceClock(0, 30)
			ShowMessage('You await a transport to recover bodies and provide new crew, which takes 30 mins.')
			
		for position in unit.positions_list:
			if position.crewman is None: continue
			if position.crewman.status == 'Dead':
				unit.personnel_list.remove(position.crewman)
				unit.personnel_list.append(Personnel(unit, unit.nation, position))
				position.crewman = unit.personnel_list[-1]
				if unit == campaign.player_unit:
					text = position.crewman.GetFullName() + ' joins your crew in the ' + position.name + ' position.'
					ShowMessage(text)
				
	
	# generate roads linking zones; only dirt roads for now
	def GenerateRoads(self):
		
		# generate one road from the bottom to the top of the map
		hx = choice([-4,-3,-2,-1,0])
		for hy in range(8, -1, -1):
			direction = choice([5,0])
			(hx2,hy2) = self.GetAdjacentCDHex(hx, hy, direction)
			if (hx2,hy2) not in self.map_hexes:
				if direction == 0:
					direction = 5
				else:
					direction = 0
				(hx2,hy2) = self.GetAdjacentCDHex(hx, hy, direction)
			self.map_hexes[(hx,hy)].dirt_roads.append(direction)
			# avoid looking for final hex off-map
			if (hx2,hy2) in self.map_hexes:
				self.map_hexes[(hx2,hy2)].dirt_roads.append(ConstrainDir(direction + 3))
			hx = hx2
		
		# 1-2 branch roads
		target_hy_list = sample(range(0, 9), libtcod.random_get_int(0, 1, 3))
		for target_hy in target_hy_list:
			for (hx, hy) in CAMPAIGN_DAY_HEXES:
				if hy != target_hy: continue
				if len(self.map_hexes[(hx,hy)].dirt_roads) == 0: continue
				
				direction = choice([1,4])
				# make sure can take at least one step in this direction
				if self.GetAdjacentCDHex(hx, hy, direction) not in self.map_hexes:
					if direction == 1:
						direction = 4
					else:
						direction = 1
				
				# create road
				while (hx,hy) in self.map_hexes:
					self.map_hexes[(hx,hy)].dirt_roads.append(direction)
					(hx,hy) = self.GetAdjacentCDHex(hx, hy, direction)
					if (hx,hy) in self.map_hexes:
						self.map_hexes[(hx,hy)].dirt_roads.append(ConstrainDir(direction + 3))
		
		
	# plot the centre of a day map hex location onto the map console
	# top left of hex 0,0 will appear at cell 2,2
	def PlotCDHex(self, hx, hy):
		x = (hx*6) + (hy*3)
		y = (hy*5)
		return (x+5,y+6)
	
	
	# returns the hx, hy location of the adjacent hex in direction
	def GetAdjacentCDHex(self, hx1, hy1, direction):
		(hx_m, hy_m) = CD_DESTHEX[direction]
		return (hx1+hx_m, hy1+hy_m)
	
	
	# display a summary of a completed campaign day
	def DisplayCampaignDaySummary(self):
	
		RECORD_ORDER = [
			'Map Areas Captured',
			'Gun Hits',
			'Vehicles Destroyed',
			'Guns Destroyed',
			'Infantry Destroyed'
		]
		
		# create a local copy of the current screen to re-draw when we're done
		temp_con = libtcod.console_new(WINDOW_WIDTH, WINDOW_HEIGHT)
		libtcod.console_blit(0, 0, 0, 0, 0, temp_con, 0, 0)
		
		# darken screen background
		libtcod.console_blit(darken_con, 0, 0, 0, 0, 0, 0, 0, 0.0, 0.7)
		
		# build info window
		temp_con = libtcod.console_new(29, 54)
		libtcod.console_set_default_background(temp_con, libtcod.black)
		libtcod.console_set_default_foreground(temp_con, libtcod.light_grey)
		libtcod.console_clear(temp_con)
		DrawFrame(temp_con, 0, 0, 29, 54)
		libtcod.console_set_default_foreground(temp_con, libtcod.white)
		
		# campaign and calendar day info
		libtcod.console_print_ex(temp_con, 14, 2, libtcod.BKGND_NONE, libtcod.CENTER,
			campaign.stats['name'])
		libtcod.console_print_ex(temp_con, 14, 4, libtcod.BKGND_NONE, libtcod.CENTER,
			GetDateText(campaign.today))
		
		# day result: survived or destroyed
		libtcod.console_print_ex(temp_con, 14, 7, libtcod.BKGND_NONE, libtcod.CENTER,
			'Outcome of Day:')
		
		#if campaign_day.abandoned_tank:
		#	col = libtcod.light_grey
		#	text = 'ABANDONED TANK'
		if campaign.player_unit.alive:
			col = GOLD_COL
			text = 'SURVIVED'
		else:
			col = ENEMY_UNIT_COL
			text = 'TANK LOST'
		libtcod.console_set_default_foreground(temp_con, col)
		libtcod.console_print_ex(temp_con, 14, 8, libtcod.BKGND_NONE, libtcod.CENTER,
			text)
		
		# total VP
		libtcod.console_set_default_foreground(temp_con, libtcod.white)
		libtcod.console_print_ex(temp_con, 14, 11, libtcod.BKGND_NONE, libtcod.CENTER,
			'Total VP Earned:')
		libtcod.console_print_ex(temp_con, 14, 13, libtcod.BKGND_NONE, libtcod.CENTER,
			str(campaign.player_vp))
		
		# day stats
		y = 17
		for text in RECORD_ORDER:
			libtcod.console_print(temp_con, 2, y, text + ':')
			libtcod.console_print_ex(temp_con, 26, y, libtcod.BKGND_NONE, libtcod.RIGHT,
				str(campaign_day.records[text]))
			y += 1
			if y == 49:
				break
		
		libtcod.console_set_default_foreground(temp_con, ACTION_KEY_COL)
		libtcod.console_print(temp_con, 7, 51, 'Enter')
		libtcod.console_set_default_foreground(temp_con, libtcod.light_grey)
		libtcod.console_print(temp_con, 14, 51, 'Continue')
		
		# display console to screen
		libtcod.console_blit(temp_con, 0, 0, 0, 0, 0, 31, 3)
		
		# get input from player
		exit_menu = False
		while not exit_menu:
			if libtcod.console_is_window_closed(): sys.exit()
			libtcod.console_flush()
			if not GetInputEvent(): continue
			
			# end menu
			if key.vk in [libtcod.KEY_ESCAPE, libtcod.KEY_ENTER]:
				exit_menu = True
	
	
	# resupply the player unit
	# (not used at the moment)
	def ResupplyPlayer(self):
		for weapon in campaign.player_unit.weapon_list:
			if weapon.ammo_stores is not None:
				weapon.LoadGunAmmo()
				text = weapon.stats['name'] + ' has been fully restocked with ammo.'
				ShowMessage(text)

	
	##### Campaign Day Console Functions #####
	
	# generate/update the campaign day map console
	def UpdateCDMapCon(self):
		
		CHAR_LOCATIONS = [
				(3,1), (2,2), (3,2), (4,2), (1,3), (2,3), (3,3), (4,3), (5,3),
				(1,4), (2,4), (4,4), (5,4), (1,5), (2,5), (3,5), (4,5), (5,5),
				(2,6), (3,6), (4,6), (3,7)
		]
		
		def GetRandomLocation(gen):
			return CHAR_LOCATIONS[libtcod.random_get_int(generator, 0, 21)]
		
		libtcod.console_clear(cd_map_con)
		self.cd_map_index = {}
		
		# draw map hexes to console
		
		# load base zone image
		dayhex_openground = LoadXP('dayhex_openground.xp')
		temp_con = libtcod.console_new(7, 9)
		libtcod.console_set_key_color(temp_con, KEY_COLOR)
		bg_col = libtcod.Color(0,64,0)
		
		for (hx, hy), cd_hex in self.map_hexes.items():
			
			# generate console image for this zone's terrain type
			libtcod.console_blit(dayhex_openground, 0, 0, 0, 0, temp_con, 0, 0)
			
			generator = libtcod.random_new_from_seed(cd_hex.console_seed)
			
			if cd_hex.terrain_type == 'Forest':
				
				for (x,y) in CHAR_LOCATIONS:
					if libtcod.random_get_int(generator, 1, 10) <= 4: continue
					col = libtcod.Color(0,libtcod.random_get_int(generator, 100, 170),0)
					libtcod.console_put_char_ex(temp_con, x, y, 6, col, bg_col)
				
			elif cd_hex.terrain_type == 'Hills':
				
				col = libtcod.Color(70,libtcod.random_get_int(generator, 110, 150),0)
				x = libtcod.random_get_int(generator, 2, 3)
				libtcod.console_put_char_ex(temp_con, x, 2, 236, col, bg_col)
				libtcod.console_put_char_ex(temp_con, x+1, 2, 237, col, bg_col)
				
				if libtcod.random_get_int(generator, 0, 1) == 0:
					x = 1
				else:
					x = 4
				libtcod.console_put_char_ex(temp_con, x, 4, 236, col, bg_col)
				libtcod.console_put_char_ex(temp_con, x+1, 4, 237, col, bg_col)
				
				x = libtcod.random_get_int(generator, 2, 3)
				libtcod.console_put_char_ex(temp_con, x, 6, 236, col, bg_col)
				libtcod.console_put_char_ex(temp_con, x+1, 6, 237, col, bg_col)
				
			elif cd_hex.terrain_type == 'Fields':
				
				for (x,y) in CHAR_LOCATIONS:
					c = libtcod.random_get_int(generator, 120, 190)
					libtcod.console_put_char_ex(temp_con, x, y, 176,
						libtcod.Color(c,c,0), bg_col)
				
			elif cd_hex.terrain_type == 'Marsh':
				
				elements = libtcod.random_get_int(generator, 7, 13)
				while elements > 0:
					(x,y) = GetRandomLocation(generator)
					if libtcod.console_get_char(temp_con, x, y) == 176: continue
					libtcod.console_put_char_ex(temp_con, x, y, 176,
						libtcod.Color(45,0,180), bg_col)
					elements -= 1
				
			elif cd_hex.terrain_type == 'Villages':
				
				elements = libtcod.random_get_int(generator, 5, 9)
				while elements > 0:
					(x,y) = GetRandomLocation(generator)
					if libtcod.console_get_char(temp_con, x, y) == 249: continue
					libtcod.console_put_char_ex(temp_con, x, y, 249,
						libtcod.Color(77,77,77), bg_col)
					elements -= 1
			
			# draw the final image to the map console
			(x,y) = self.PlotCDHex(hx, hy)
			libtcod.console_blit(temp_con, 0, 0, 0, 0, cd_map_con, x-3, y-4)
			
			# record screen locations of hex
			# strictly speaking this only needs to be done once ever, but in
			# the future it might be possible to scroll the campaign day map
			# so we'd need to update this anyway
			self.cd_map_index[(x, y-3)] = (hx, hy)
			for x1 in range(x-1, x+2):
				self.cd_map_index[(x1, y-2)] = (hx, hy)
				self.cd_map_index[(x1, y+2)] = (hx, hy)
			for x1 in range(x-2, x+3):
				self.cd_map_index[(x1, y-1)] = (hx, hy)
				self.cd_map_index[(x1, y)] = (hx, hy)
				self.cd_map_index[(x1, y+1)] = (hx, hy)
			self.cd_map_index[(x, y+3)] = (hx, hy)
			
		del temp_con, dayhex_openground
		
		# draw dirt roads overtop
		for (hx, hy), map_hex in self.map_hexes.items():
			if len(map_hex.dirt_roads) == 0: continue
			for direction in map_hex.dirt_roads:
				# only draw if in direction 0-2
				if direction > 2: continue
				# get the other zone linked by road
				(hx2, hy2) = self.GetAdjacentCDHex(hx, hy, direction)
				if (hx2, hy2) not in self.map_hexes: continue
				
				# paint road
				(x1, y1) = self.PlotCDHex(hx, hy)
				(x2, y2) = self.PlotCDHex(hx2, hy2)
				line = GetLine(x1, y1, x2, y2)
				for (x, y) in line:
				
					# don't paint over outside of map area
					if libtcod.console_get_char_background(cd_map_con, x, y) == libtcod.black:
						continue
					
					libtcod.console_set_char_background(cd_map_con, x, y,
						DIRT_ROAD_COL, libtcod.BKGND_SET)
					
					# if character is not blank or hex edge, remove it
					if libtcod.console_get_char(cd_map_con, x, y) not in [0, 249, 250]:
						libtcod.console_set_char(cd_map_con, x, y, 0)
				
		# draw hex row guides
		for i in range(0, 9):
			libtcod.console_put_char_ex(cd_map_con, 0, 6+(i*5), chr(i+65),
				libtcod.light_green, libtcod.black)
		
		# draw hex column guides
		for i in range(0, 5):
			libtcod.console_put_char_ex(cd_map_con, 7+(i*6), 50, chr(i+49),
				libtcod.light_green, libtcod.black)
		for i in range(5, 9):
			libtcod.console_put_char_ex(cd_map_con, 32, 39-((i-5)*10), chr(i+49),
				libtcod.light_green, libtcod.black)
	
	
	# generate/update the campaign day unit layer console
	def UpdateCDUnitCon(self):
		libtcod.console_clear(cd_unit_con)
		libtcod.console_set_default_foreground(cd_unit_con, libtcod.white)
		
		# enemy strength level, player arty/air support
		libtcod.console_set_default_foreground(cd_unit_con, libtcod.red)
		for (hx, hy) in CAMPAIGN_DAY_HEXES:
			map_hex = self.map_hexes[(hx,hy)]
			
			(x,y) = self.PlotCDHex(hx, hy)
			
			if map_hex.air_support:
				libtcod.console_put_char_ex(cd_unit_con, x-1, y, 'A', ALLIED_UNIT_COL, libtcod.black)
			if map_hex.arty_support:
				libtcod.console_put_char_ex(cd_unit_con, x+1, y, 'R', ALLIED_UNIT_COL, libtcod.black)
			
			if map_hex.controlled_by == 0: continue
			if not map_hex.known_to_player: continue
			libtcod.console_print(cd_unit_con, x, y-1, str(map_hex.enemy_strength))
			
		
		# draw player unit group
		(hx, hy) = self.player_unit_location
		(x,y) = self.PlotCDHex(hx, hy)
		libtcod.console_put_char_ex(cd_unit_con, x, y, '@', libtcod.white, libtcod.black)
	
	
	# generate/update the zone control console, showing the battlefront between two sides
	def UpdateCDControlCon(self):
		libtcod.console_clear(cd_control_con)
		
		# run through every hex, if it's under player control, see if there an adjacent
		# enemy-controlled hex and if so, draw a border there
		for (hx, hy) in CAMPAIGN_DAY_HEXES:
			if self.map_hexes[(hx,hy)].controlled_by != 0: continue
			
			for direction in range(6):
				(hx_m, hy_m) = CD_DESTHEX[direction]
				hx2 = hx+hx_m
				hy2 = hy+hy_m
				
				# hex is off map
				if (hx2, hy2) not in self.map_hexes: continue
				# hex is friendly controlled
				if self.map_hexes[(hx2,hy2)].controlled_by == 0: continue
				
				# draw a border
				(x,y) = self.PlotCDHex(hx, hy)
				for (xm,ym) in CD_HEX_EDGE_CELLS[direction]:
					libtcod.console_put_char_ex(cd_control_con, x+xm,
						y+ym, chr(249), libtcod.red, libtcod.black)
	
	
	# generate/update the GUI console
	def UpdateCDGUICon(self):
		libtcod.console_clear(cd_gui_con)
		
		# support menu, direction currently selected
		if self.active_menu == 1 and self.selected_direction is not None:
			# draw target on hex if any
			(hx, hy) = self.player_unit_location
			(hx, hy) = self.GetAdjacentCDHex(hx, hy, self.selected_direction)
			if (hx, hy) in self.map_hexes:
				(x,y) = self.PlotCDHex(hx, hy)
				libtcod.console_put_char_ex(cd_gui_con, x-1, y-1, 92, libtcod.red, libtcod.black)
				libtcod.console_put_char_ex(cd_gui_con, x+1, y+1, 92, libtcod.red, libtcod.black)
				libtcod.console_put_char_ex(cd_gui_con, x+1, y-1, 47, libtcod.red, libtcod.black)
				libtcod.console_put_char_ex(cd_gui_con, x-1, y+1, 47, libtcod.red, libtcod.black)
		
		# movement menu, direction currently selected
		elif self.active_menu == 3 and self.selected_direction is not None:
			
			# draw directional line
			(hx, hy) = self.player_unit_location
			(x1,y1) = self.PlotCDHex(hx, hy)
			(hx, hy) = self.GetAdjacentCDHex(hx, hy, self.selected_direction)
			if (hx, hy) in self.map_hexes:
				(x2,y2) = self.PlotCDHex(hx, hy)
				line = GetLine(x1,y1,x2,y2)
				for (x,y) in line[1:-1]:
					libtcod.console_put_char_ex(cd_gui_con, x, y, 250, libtcod.green,
						libtcod.black)
				(x,y) = line[-1]
				libtcod.console_put_char_ex(cd_gui_con, x, y, CD_DIR_ARROW[self.selected_direction],
					libtcod.green, libtcod.black)
	
	
	# generate/update the player unit console
	def UpdateCDPlayerUnitCon(self):
		libtcod.console_clear(cd_player_unit_con)
		campaign.player_unit.DisplayMyInfo(cd_player_unit_con, 0, 0, status=False)
	
	
	# generate/update the directional console
	def UpdateCDDirectionCon(self):
		libtcod.console_clear(cd_direction_con)
		
		x1 = 12
		y1 = 6
		
		# display possible support/move/recon directions
		libtcod.console_set_default_foreground(cd_direction_con, libtcod.white)
		libtcod.console_print_ex(cd_direction_con, 12, 1, libtcod.BKGND_NONE, libtcod.CENTER,
			'Directional Control')
		libtcod.console_put_char(cd_direction_con, x1, y1, '@')
		for direction in range(6):
			libtcod.console_set_default_foreground(cd_direction_con, ACTION_KEY_COL)
			
			if self.selected_direction is not None:
				if self.selected_direction == direction:
					libtcod.console_set_default_foreground(cd_direction_con, libtcod.light_green)
					
			(k, x, y, char) = CD_TRAVEL_CMDS[direction]
			libtcod.console_put_char(cd_direction_con, x1+x, y1+y, EnKey(k).upper())
			if direction <= 2:
				x+=1
			else:
				x-=1
			libtcod.console_set_default_foreground(cd_direction_con, libtcod.dark_green)
			libtcod.console_put_char(cd_direction_con, x1+x, y1+y, chr(char))
		
		if self.selected_direction is None:
			libtcod.console_set_default_foreground(cd_direction_con, libtcod.light_grey)
			libtcod.console_print_ex(cd_direction_con, 12, y1+5, libtcod.BKGND_NONE, libtcod.CENTER,
				'Select Direction')
	
	
	# generate/update the command menu console
	def UpdateCDCommandCon(self):
		libtcod.console_set_default_foreground(cd_command_con, libtcod.white)
		libtcod.console_clear(cd_command_con)
		
		x = 0
		for (text, num, col) in CD_MENU_LIST:
			libtcod.console_set_default_background(cd_command_con, col)
			libtcod.console_rect(cd_command_con, x, 0, 2, 1, True, libtcod.BKGND_SET)
			
			# only support, travel, and supply menus active for now
			# display menu number
			libtcod.console_set_default_foreground(cd_command_con, ACTION_KEY_COL)
			if num not in [1, 3, 5]:
				libtcod.console_set_default_foreground(cd_command_con, libtcod.dark_grey)
			libtcod.console_print(cd_command_con, x, 0, str(num))
			libtcod.console_set_default_foreground(cd_command_con, libtcod.white)
			
			x += 2
			
			# display menu text if active
			if self.active_menu == num:
				libtcod.console_rect(cd_command_con, x, 0, len(text)+2, 1,
					True, libtcod.BKGND_SET)
				libtcod.console_print(cd_command_con, x, 0, text)
				x += len(text) + 2
		
		# fill in rest of menu line with final colour
		libtcod.console_rect(cd_command_con, x, 0, 25-x, 1, True, libtcod.BKGND_SET)
		libtcod.console_set_default_background(cd_command_con, libtcod.black)
		
		# support
		if self.active_menu == 1:
			
			# overcast sky, no support possible
			no_air_support = False
			if self.weather['Cloud Cover'] == 'Overcast':
				no_air_support = True
			
			# display current support levels
			if no_air_support:
				text = 'Overcast: Air Supp. N/A'
			else:
				text = 'Air Support: '
				if self.air_support_level == 0.0:
					text += 'None'
				else:
					text += str(self.air_support_level)
			libtcod.console_print(cd_command_con, 1, 3, text)
			
			text = 'Artillery Support: '
			if self.arty_support_level == 0.0:
				text += 'None'
			else:
				text += str(self.arty_support_level)
			libtcod.console_print(cd_command_con, 1, 5, text)
			
			# no direction selected yet
			if self.selected_direction is None:
				libtcod.console_print(cd_command_con, 3, 12, 'Select a direction')
				return
			
			# get the target hex
			(hx, hy) = self.player_unit_location
			(hx, hy) = self.GetAdjacentCDHex(hx, hy, self.selected_direction)
			
			# hex is off map
			if (hx, hy) not in self.map_hexes: return
			
			map_hex = self.map_hexes[(hx,hy)]
			
			# display call support options
			if map_hex.air_support:
				libtcod.console_set_default_foreground(cd_command_con, ALLIED_UNIT_COL)
				libtcod.console_print(cd_command_con, 1, 13, 'Air Support inbound')
			elif not no_air_support and map_hex.controlled_by == 1 and self.air_support_level > 0.0:
				libtcod.console_set_default_foreground(cd_command_con, libtcod.white)
				libtcod.console_print_ex(cd_command_con, 12, 16, libtcod.BKGND_NONE, libtcod.CENTER,
					'15 mins to attempt call')
				libtcod.console_set_default_foreground(cd_command_con, ACTION_KEY_COL)
				libtcod.console_print(cd_command_con, 3, 21, EnKey('r').upper())
				libtcod.console_set_default_foreground(cd_command_con, libtcod.lighter_grey)
				libtcod.console_print(cd_command_con, 5, 21, 'Call Air Support')
			
			if map_hex.arty_support:
				libtcod.console_set_default_foreground(cd_command_con, ALLIED_UNIT_COL)
				libtcod.console_print(cd_command_con, 1, 14, 'Arty Support inbound')
			elif map_hex.controlled_by == 1 and self.arty_support_level > 0.0:
				libtcod.console_set_default_foreground(cd_command_con, libtcod.white)
				libtcod.console_print_ex(cd_command_con, 12, 16, libtcod.BKGND_NONE, libtcod.CENTER,
					'15 mins to attempt call')
				libtcod.console_set_default_foreground(cd_command_con, ACTION_KEY_COL)
				libtcod.console_print(cd_command_con, 3, 22, EnKey('f').upper())
				libtcod.console_set_default_foreground(cd_command_con, libtcod.lighter_grey)
				libtcod.console_print(cd_command_con, 5, 22, 'Call Arty Support')
		
		# travel
		elif self.active_menu == 3:
			
			# check to see whether travel in selected direction is not possible
			if self.selected_direction is None:
				libtcod.console_set_default_foreground(cd_command_con, libtcod.white)
				libtcod.console_print(cd_command_con, 3, 12, 'Select a direction')
				return
			(hx, hy) = self.player_unit_location
			(hx, hy) = self.GetAdjacentCDHex(hx, hy, self.selected_direction)
			if (hx, hy) not in self.map_hexes: return
				
			# display enemy strength/organization if any and chance of encounter
			map_hex = self.map_hexes[(hx,hy)]
			if map_hex.controlled_by == 1:
				
				libtcod.console_set_default_foreground(cd_command_con, libtcod.red)
				libtcod.console_print(cd_command_con, 1, 2, 'Enemy Controlled')
				
				if not map_hex.known_to_player:
					libtcod.console_set_default_foreground(cd_command_con, libtcod.white)
					libtcod.console_print(cd_command_con, 1, 3, 'Recon: 15 mins.')
					libtcod.console_set_default_foreground(cd_command_con, ACTION_KEY_COL)
					libtcod.console_print(cd_command_con, 5, 21, EnKey('r').upper())
					libtcod.console_set_default_foreground(cd_command_con, libtcod.lighter_grey)
					libtcod.console_print(cd_command_con, 12, 21, 'Recon')
				else:
					libtcod.console_print(cd_command_con, 1, 3, 'Strength: ' + str(map_hex.enemy_strength))
					libtcod.console_set_default_foreground(cd_command_con, libtcod.white)
			
			libtcod.console_set_default_foreground(cd_command_con, libtcod.white)
			text = 'Travel Time: '
			if self.selected_direction in map_hex.dirt_roads:
				mins = 10
			else:
				mins = 15
			if self.weather['Ground'] == 'Muddy':
				mins = mins * 2
			text += str(mins) + ' mins.'
			libtcod.console_print(cd_command_con, 1, 5, text)
		
			libtcod.console_set_default_foreground(cd_command_con, ACTION_KEY_COL)
			libtcod.console_print(cd_command_con, 5, 22, 'Enter')
			libtcod.console_set_default_foreground(cd_command_con, libtcod.lighter_grey)
			libtcod.console_print(cd_command_con, 12, 22, 'Proceed')
		
		# resupply menu
		elif self.active_menu == 5:
			
			libtcod.console_print_ex(cd_command_con, 12, 10, libtcod.BKGND_NONE, libtcod.CENTER,
				'Request resupply:')
			libtcod.console_print_ex(cd_command_con, 12, 11, libtcod.BKGND_NONE, libtcod.CENTER,
				'30 mins.')
			libtcod.console_set_default_foreground(cd_command_con, ACTION_KEY_COL)
			libtcod.console_print(cd_command_con, 8, 22, EnKey('r').upper())
			libtcod.console_set_default_foreground(cd_command_con, libtcod.lighter_grey)
			libtcod.console_print(cd_command_con, 10, 22, 'Resupply')
	
	
	# generate/update the campaign info console
	def UpdateCDCampaignCon(self):
		libtcod.console_clear(cd_campaign_con)
		
		# current VP total
		libtcod.console_set_default_foreground(cd_campaign_con, libtcod.blue)
		libtcod.console_print(cd_campaign_con, 0, 0, 'Campaign Info')
		libtcod.console_set_default_foreground(cd_campaign_con, libtcod.white)
		libtcod.console_print(cd_campaign_con, 1, 2, 'VP: ' + str(campaign.player_vp))
	
	
	# generate/update the zone info console
	def UpdateCDHexInfoCon(self):
		libtcod.console_clear(cd_hex_info_con)
		
		libtcod.console_set_default_foreground(cd_hex_info_con, libtcod.blue)
		libtcod.console_print(cd_hex_info_con, 0, 0, 'Area Info')
		
		# mouse cursor outside of map area
		if mouse.cx < 31 or mouse.cx > 59:
			libtcod.console_set_default_foreground(cd_hex_info_con, libtcod.light_grey)
			libtcod.console_print(cd_hex_info_con, 0, 2, 'Mouseover an area')
			libtcod.console_print(cd_hex_info_con, 0, 3, 'for info')
			return
		x = mouse.cx - 29
		y = mouse.cy - 6
		
		# no zone here
		if (x,y) not in self.cd_map_index: return
		
		(hx, hy) = self.cd_map_index[(x,y)]
		cd_hex = self.map_hexes[(hx, hy)]
		
		# display hex zone coordinates
		libtcod.console_set_default_foreground(cd_hex_info_con, libtcod.light_green)
		libtcod.console_print(cd_hex_info_con, 11, 0, cd_hex.coordinate)
		
		# terrain
		libtcod.console_set_default_foreground(cd_hex_info_con, libtcod.light_grey)
		libtcod.console_print(cd_hex_info_con, 0, 1, cd_hex.terrain_type)
		
		# control
		if cd_hex.controlled_by == 0:
			libtcod.console_set_default_foreground(cd_hex_info_con, ALLIED_UNIT_COL)
			libtcod.console_print(cd_hex_info_con, 0, 2, 'Friendly controlled')
		else:
			libtcod.console_set_default_foreground(cd_hex_info_con, ENEMY_UNIT_COL)
			libtcod.console_print(cd_hex_info_con, 0, 2, 'Enemy controlled')
			libtcod.console_print(cd_hex_info_con, 0, 3, 'Strength: ')
			if cd_hex.known_to_player:
				text = str(cd_hex.enemy_strength)
			else:
				text = 'Unknown'
			libtcod.console_print(cd_hex_info_con, 10, 3, text)
		
		# support
		libtcod.console_set_default_foreground(cd_hex_info_con, ALLIED_UNIT_COL)
		if cd_hex.air_support:
			libtcod.console_print(cd_hex_info_con, 0, 5, 'Air Support inbound')
		if cd_hex.arty_support:
			libtcod.console_print(cd_hex_info_con, 0, 5, 'Arty Support inbound')
		libtcod.console_set_default_foreground(cd_hex_info_con, libtcod.light_grey)
		
		# roads
		if len(cd_hex.dirt_roads) > 0:
			libtcod.console_print(cd_hex_info_con, 0, 8, 'Dirt roads')
	
	
	# draw all campaign day consoles to screen
	def UpdateCDDisplay(self):
		libtcod.console_clear(con)
		
		libtcod.console_blit(daymap_bkg, 0, 0, 0, 0, con, 0, 0)			# background frame
		libtcod.console_blit(cd_map_con, 0, 0, 0, 0, con, 29, 6)		# terrain map
		libtcod.console_blit(cd_control_con, 0, 0, 0, 0, con, 29, 6, 1.0, 0.0)	# zone control layer
		libtcod.console_blit(cd_unit_con, 0, 0, 0, 0, con, 29, 6, 1.0, 0.0)	# unit group layer
		libtcod.console_blit(cd_gui_con, 0, 0, 0, 0, con, 29, 6, 1.0, 0.0)	# GUI layer
		
		libtcod.console_blit(time_con, 0, 0, 0, 0, con, 36, 1)			# date and time
		
		libtcod.console_blit(cd_player_unit_con, 0, 0, 0, 0, con, 1, 1)		# player unit info
		libtcod.console_blit(cd_direction_con, 0, 0, 0, 0, con, 1, 18)		# directional info		
		libtcod.console_blit(cd_command_con, 0, 0, 0, 0, con, 1, 35)		# command menu
		
		libtcod.console_blit(cd_weather_con, 0, 0, 0, 0, con, 66, 1)		# weather info
		libtcod.console_blit(cd_campaign_con, 0, 0, 0, 0, con, 66, 18)		# campaign info
		libtcod.console_blit(cd_hex_info_con, 0, 0, 0, 0, con, 66, 50)		# zone info
		
		libtcod.console_blit(con, 0, 0, 0, 0, 0, 0, 0)
	
	
	# main campaign day input loop
	def DoCampaignDayLoop(self):
		
		global daymap_bkg, cd_map_con, cd_unit_con, cd_control_con, cd_command_con
		global cd_player_unit_con, cd_direction_con, cd_gui_con, time_con
		global cd_campaign_con, cd_weather_con, cd_hex_info_con
		global scenario
		
		# create consoles
		daymap_bkg = LoadXP('daymap_bkg.xp')
		cd_map_con = NewConsole(35, 53, libtcod.black, libtcod.white)
		cd_unit_con = NewConsole(35, 53, KEY_COLOR, libtcod.white)
		cd_control_con = NewConsole(35, 53, KEY_COLOR, libtcod.red)
		cd_gui_con = NewConsole(35, 53, KEY_COLOR, libtcod.red)
		time_con = NewConsole(21, 6, libtcod.darkest_grey, libtcod.white)
		cd_player_unit_con = NewConsole(25, 16, libtcod.black, libtcod.white)
		cd_direction_con = NewConsole(25, 16, libtcod.black, libtcod.white)
		cd_command_con = NewConsole(25, 24, libtcod.black, libtcod.white)
		cd_weather_con = NewConsole(23, 12, libtcod.black, libtcod.white)
		cd_campaign_con = NewConsole(23, 16, libtcod.black, libtcod.white)
		cd_hex_info_con = NewConsole(23, 9, libtcod.black, libtcod.white)
		
		# generate consoles for the first time
		self.UpdateCDMapCon()
		self.UpdateCDUnitCon()
		self.UpdateCDControlCon()
		self.UpdateCDGUICon()
		self.UpdateCDPlayerUnitCon()
		self.UpdateCDDirectionCon()
		self.UpdateCDCommandCon()
		self.UpdateCDCampaignCon()
		self.UpdateCDHexInfoCon()
		DisplayWeatherInfo(cd_weather_con)
		DisplayTimeInfo(time_con)
		if self.scenario is not None:
			self.UpdateCDDisplay()
		
		# record mouse cursor position to check when it has moved
		mouse_x = -1
		mouse_y = -1
		
		SaveGame()
		
		exit_loop = False
		while not exit_loop:
			
			# if we've initiated a scenario or are resuming a saved game with a scenario
			# running, go into the scenario loop now
			if self.scenario is not None:
				
				scenario.DoScenarioLoop()
				
				if session.exiting:
					exit_loop = True
					continue
				
				# scenario is finished
				if scenario.finished:
					
					self.scenario = None
					scenario = None
					
					# capture area if player is still alive
					if campaign.player_unit.alive:
						(hx, hy) = self.player_unit_location
						self.map_hexes[(hx,hy)].CaptureMe(0)
						self.DoCrewCheck(campaign.player_unit)
						self.CheckForEndOfDay()
						self.UpdateCDDisplay()
						libtcod.console_flush()
						self.CheckForRandomEvent()
						SaveGame()
					
					# player was destroyed
					else:
						EraseGame()
						self.DisplayCampaignDaySummary()
						exit_loop = True
						continue
				
				DisplayTimeInfo(time_con)
				self.UpdateCDCampaignCon()
				self.UpdateCDControlCon()
				self.UpdateCDUnitCon()
				self.UpdateCDCommandCon()
				self.UpdateCDHexInfoCon()
				self.UpdateCDDisplay()
			
			# check for end of campaign day
			if self.ended:
				ShowMessage('Your combat day has ended.') 
				EraseGame()
				self.DisplayCampaignDaySummary()
				exit_loop = True
				continue
			
			if libtcod.console_is_window_closed(): sys.exit()
			libtcod.console_flush()
			keypress = GetInputEvent()
			
			# check to see if mouse cursor has moved
			if mouse.cx != mouse_x or mouse.cy != mouse_y:
				mouse_x = mouse.cx
				mouse_y = mouse.cy
				self.UpdateCDHexInfoCon()
				self.UpdateCDDisplay()
			
			if not keypress: continue
			
			# game menu
			if key.vk == libtcod.KEY_ESCAPE:
				ShowGameMenu()
				if session.exiting:
					exit_loop = True
					continue
			
			# debug menu
			elif key.vk == libtcod.KEY_F2:
				if not DEBUG: continue
				ShowDebugMenu()
				continue
			
			# mapped key commands
			key_char = DeKey(chr(key.c).lower())
			
			# switch active menu
			if key_char in ['1', '3', '5']:
				if self.active_menu != int(key_char):
					self.active_menu = int(key_char)
					self.UpdateCDGUICon()
					self.UpdateCDCommandCon()
					self.UpdateCDDisplay()
				continue
			
			# select direction
			DIRECTION_KEYS = ['e', 'd', 'c', 'z', 'a', 'q'] 
			if key_char in DIRECTION_KEYS:
				direction = DIRECTION_KEYS.index(key_char)
				if self.selected_direction is None:
					self.selected_direction = direction
				else:
					# cancel direction
					if self.selected_direction == direction:
						self.selected_direction = None
					else:
						self.selected_direction = direction
				self.UpdateCDDirectionCon()
				self.UpdateCDGUICon()
				self.UpdateCDCommandCon()
				self.UpdateCDDisplay()
				continue
			
			# support menu active
			if self.active_menu == 1:
			
				# call support
				if key_char in ['r', 'f']:
					if self.selected_direction is None: continue
					(hx, hy) = self.player_unit_location
					(hx, hy) = self.GetAdjacentCDHex(hx, hy, self.selected_direction)
					if (hx, hy) not in self.map_hexes: continue
					map_hex = self.map_hexes[(hx,hy)]
					
					# support not possible or already called
					if map_hex.controlled_by == 0: continue
					if key_char == 'r':
						if self.air_support_level == 0.0: continue
						if map_hex.air_support: continue
					if key_char == 'f':
						if self.arty_support_level == 0.0: continue
						if map_hex.arty_support: continue
					
					# do roll
					roll = GetPercentileRoll()
					
					if DEBUG:
						if session.debug['Support Requests Always Granted']:
							roll = 1.0
					
					if key_char == 'r':
						
						# Overcast, air support not allowed
						if self.weather['Cloud Cover'] == 'Overcast':
							continue
						
						if roll > self.air_support_level:
							ShowMessage('Request for air support was not successful.')
						else:
							ShowMessage('Request successful! Air support inbound.')
							map_hex.air_support = True
							self.air_support_level -= self.air_support_step
							if self.air_support_level < 0.0: self.air_support_level = 0.0 
						
					elif key_char == 'f':
						if roll > self.arty_support_level:
							ShowMessage('Request for artillery support was not successful.')
						else:
							ShowMessage('Request successful! Artillery support inbound.')
							map_hex.arty_support = True
							self.arty_support_level -= self.arty_support_step
							if self.arty_support_level < 0.0: self.arty_support_level = 0.0
					
					# spend time
					campaign_day.AdvanceClock(0, 15)
					DisplayTimeInfo(time_con)
					self.UpdateCDGUICon()
					self.UpdateCDCommandCon()
					self.UpdateCDUnitCon()
					self.UpdateCDDisplay()
					
					self.CheckForRandomEvent()
					
					continue
			
			# travel menu active
			elif self.active_menu == 3:
				
				# recon or proceed with travel
				if key_char == 'r' or key.vk == libtcod.KEY_ENTER:
					
					# no direction set
					if self.selected_direction is None: continue
					
					# ensure that travel/recon is possible
					(hx, hy) = self.player_unit_location
					map_hex1 = self.map_hexes[(hx,hy)]
					(hx, hy) = self.GetAdjacentCDHex(hx, hy, self.selected_direction)
					if (hx, hy) not in self.map_hexes:
						continue
					map_hex2 = self.map_hexes[(hx,hy)]
					
					# recon
					if key_char == 'r':
						# already reconned
						if map_hex2.known_to_player: continue
						# not enemy-controlled
						if map_hex2.controlled_by == 0: continue
						map_hex2.known_to_player = True
						text = 'Estimated enemy strength in zone: ' + str(map_hex2.enemy_strength)
						ShowMessage(text)
						campaign_day.AdvanceClock(0, 15)
						DisplayTimeInfo(time_con)
						self.UpdateCDUnitCon()
						self.UpdateCDCommandCon()
						self.UpdateCDHexInfoCon()
						self.UpdateCDDisplay()
						
						self.CheckForRandomEvent()
						
					# proceed with travel
					else:
						
						# do sound effect
						PlaySoundFor(campaign.player_unit, 'movement')
					
						# advance clock
						if self.selected_direction in map_hex1.dirt_roads:
							mins = 10
						else:
							mins = 15
						if campaign_day.weather['Ground'] == 'Muddy':
							mins = mins * 2
						campaign_day.AdvanceClock(0, mins)
						
						# set new player location and clear travel direction
						# save direction from which player entered zone
						self.player_unit_location = (hx, hy)
						#source_direction = ConstrainDir(self.selected_direction + 3)
						self.selected_direction = None
						self.UpdateCDGUICon()
						
						# roll to trigger battle encounter if enemy-controlled
						if map_hex2.controlled_by == 1:
							ShowMessage('You enter the enemy-held zone.')
							
							# roll for scenario trigger
							roll = GetPercentileRoll()
							roll -= campaign_day.encounter_mod
							
							if DEBUG:
								if session.debug['Always Scenario']:
									roll = 1.0
							
							if roll <= (float(map_hex2.enemy_strength) * 9.5):
								ShowMessage('You encounter enemy resistance!')
								campaign_day.AdvanceClock(0, 15)
								scenario = Scenario(map_hex2)
								self.scenario = scenario
								campaign_day.encounter_mod = 0.0
								continue
							
							ShowMessage('You find no resistance and gain control of the area.')
							self.map_hexes[(hx,hy)].CaptureMe(0)
							campaign_day.encounter_mod += 30.0
						
						# entering a friendly zone
						else:
							ShowMessage('You enter the allied-held zone.')
						
						# no battle triggered, update consoles
						DisplayTimeInfo(time_con)
						self.UpdateCDCampaignCon()
						self.UpdateCDControlCon()
						self.UpdateCDUnitCon()
						self.UpdateCDDirectionCon()
						self.UpdateCDCommandCon()
						self.UpdateCDHexInfoCon()
						self.UpdateCDDisplay()
						
						self.CheckForRandomEvent()
					
					SaveGame()
				
			# supply menu active
			elif self.active_menu == 5:
				
				# request resupply
				if key_char == 'r':
					ShowMessage('You contact HQ for resupply, which arrives 30 minutes later.')
					self.AmmoReloadMenu()
					self.AdvanceClock(0, 30)
					DisplayTimeInfo(time_con)
					self.UpdateCDDisplay()
					self.CheckForRandomEvent()
					SaveGame()


# Zone Hex: a hex on the campaign day map, each representing a map of scenario hexes
class CDMapHex:
	def __init__(self, hx, hy):
		self.hx = hx
		self.hy = hy
		
		self.coordinate = (chr(hy+65) + str(5 + int(hx - (hy - hy&1) / 2)))
		
		self.terrain_type = ''		# placeholder for terrain type in this zone
		self.console_seed = libtcod.random_get_int(0, 1, 128)	# seed for console image generation
		
		self.dirt_roads = []		# directions linked by a dirt road
		self.stone_roads = []		# " stone road
		
		self.controlled_by = 1		# which player side currently controls this zone
		self.known_to_player = False	# player knows enemy strength and organization in this zone
		self.air_support = False	# player has air support called in
		self.arty_support = False	# " arty "
		
		self.objective_type = None	# player objective for this zone
		
		# set enemy strength level
		self.enemy_strength = libtcod.random_get_int(0, 1, 5) + libtcod.random_get_int(0, 0, 5)
		
	
	# generate a random terrain type for this hex
	# FUTURE: can pull data from the campaign day to determine set of possible terrain types
	def GenerateTerrainType(self):
		
		roll = GetPercentileRoll()
		
		for terrain_type, odds in CD_TERRAIN_ODDS.items():
			if roll <= odds:
				self.terrain_type = terrain_type
				return
			roll -= odds
	
	
	# set control of this hex by the given player
	# if no_vp is True, player doesn't receive VP or credit for this capture
	def CaptureMe(self, player_num, no_vp=False):
		self.controlled_by = player_num
		self.air_support = False
		self.arty_support = False
		
		# captured by player
		if player_num == 0 and not no_vp:
			campaign.AwardVP(campaign_day.capture_zone_vp)
			campaign_day.records['Map Areas Captured'] += 1
		



# Session: stores data that is generated for each game session and not stored in the saved game
class Session:
	def __init__(self):
		
		# flag for when player is exiting from game
		self.exiting = False
		
		# pointer to player unit
		self.player_unit = None
		
		# flag: the last time the keyboard was polled, a key was pressed
		self.key_down = False
		
		# load debug flags if in debug mode
		self.debug = {}
		if DEBUG:
			with open(DATAPATH + 'debug.json', encoding='utf8') as data_file:
				self.debug = json.load(data_file)
		
		# store player crew command defintions
		with open(DATAPATH + 'crew_command_defs.json', encoding='utf8') as data_file:
			self.crew_commands = json.load(data_file)
		
		# store nation definition info
		with open(DATAPATH + 'nation_defs.json', encoding='utf8') as data_file:
			self.nations = json.load(data_file)
		
		# load national flag images
		self.flags = {}
		for name, data in self.nations.items():
			self.flags[name] = LoadXP(data['flag_image'])
		
		# background for attack console
		self.attack_bkg = LoadXP('attack_bkg.xp')
		
		# game menu background console
		self.game_menu_bkg = LoadXP('game_menu.xp')
		
		# field of view highlight on scenario hex map
		self.scen_hex_fov = LoadXP('scen_hex_fov.xp')
		libtcod.console_set_key_color(self.scen_hex_fov, KEY_COLOR)
	
	
	# try to initialize SDL2 mixer
	def InitMixer(self):
		mixer.Mix_Init(mixer.MIX_INIT_OGG)
		if mixer.Mix_OpenAudio(48000, mixer.MIX_DEFAULT_FORMAT,	2, 1024) == -1:
			print('ERROR in Mix_OpenAudio: ' + mixer.Mix_GetError())
			return False
		mixer.Mix_AllocateChannels(16)
		return True


# Personnel Class: represents an individual person within a unit 
class Personnel:
	def __init__(self, unit, nation, position):
		self.unit = unit				# pointer to which unit they belong
		self.nation = nation				# nationality of person
		self.current_position = position		# pointer to current position in a unit
		
		self.first_name = ''				# placeholders for first and last name
		self.last_name = ''				#   set by GenerateName()
		self.GenerateName()				# generate random first and last name
		self.nickname = ''				# player-set nickname
		
		self.stats = {					# default values for modification
			'Perception' : 3,
			'Grit' : 3,
			'Knowledge' : 3,
			'Morale' : 3
		}
		self.SetStats()
		
		self.ce = False					# crewman is exposed in a vehicle
		self.SetCEStatus()				# set CE status
		
		self.cmd_list = []				# list of possible commands
		self.current_cmd = 'Spot'			# currently assigned command in scenario
		
		self.status = ''				# current status: Stunned, Unconscious, or Dead
		self.wound = ''					# current wound: Light, Serious, or Critical
		
		self.bailed_out = False				# has bailed out of an AFV
	
	
	# generate a random first and last name for this person
	def GenerateName(self):
		
		# TEMP: have to normalize extended characters so they can be displayed on screen
		# FUTURE: will have their own glyphs as part of font
		def FixName(text):
			CODE = {
				u'Ś' : 'S', u'Ż' : 'Z', u'Ł' : 'L',
				u'ą' : 'a', u'ć' : 'c', u'ę' : 'e', u'ł' : 'l', u'ń' : 'n', u'ó' : 'o',
				u'ś' : 's', u'ź' : 'z', u'ż' : 'z'
			}
			
			fixed_name = ''
			for i in range(len(text)):
				if text[i] in CODE:
					fixed_name += CODE[text[i]]
				else:
					fixed_name += text[i]
			return fixed_name
		
		first_name = choice(session.nations[self.nation]['first_names'])
		self.first_name = FixName(first_name)
		last_name = choice(session.nations[self.nation]['surnames'])
		self.last_name = FixName(last_name)
	
	
	# return the person's full name
	def GetFullName(self):
		return (self.first_name + ' ' + self.last_name)
	
	
	# randomly modify initial stat values
	def SetStats(self):		
		for i in range(5):
			key = choice(list(self.stats))
			self.stats[key] += 1 
			key = choice(list(self.stats))
			self.stats[key] -= 1
		
		for key in self.stats:
			if self.stats[key] < 1:
				self.stats[key] = 1
			elif self.stats[key] > 5:
				self.stats[key] = 5
	
	
	# return the effective modifier for a given action, based on relavent stat and current status
	def GetActionMod(self, action_type):
		
		modifier = 0.0
		
		if self.status in ['Dead', 'Unconscious']: return modifier
		
		if action_type == 'Spotting':
			modifier = float(self.stats['Perception']) * PERCEPTION_SPOTTING_MOD
			if not self.ce:
				modifier = modifier * 0.25
		elif action_type == 'Attempt HD':
			modifier = float(self.stats['Knowledge']) * 3.0
			if not self.ce:
				modifier = modifier * 0.5
		elif action_type == 'Direct Movement':
			modifier = float(self.stats['Knowledge']) * 2.0
			if not self.ce:
				modifier = modifier * 0.5
		
		# modify by current status
		if self.status == 'Stunned':
			modifier = modifer * 0.5
		
		modifier = round(modifier, 1)
		
		#print('DEBUG: action modifier for ' + self.GetFullName() + ' doing ' + action_type +
		#	' is: ' + str(modifier))
		
		return modifier 
	
	# given an attack profile, check to see whether this personnel is wounded/KIA
	# return result if any
	def DoWoundCheck(self, fp=0, roll_modifier=0.0, show_messages=True):
		
		# can't get worse
		if self.status == 'Dead': return None
		
		# only show messages if this is the player unit
		if self.unit != scenario.player_unit: show_messages = False
		
		# final wound roll modifier
		modifier = 0
		
		# exposed to an fp attack
		if fp > 0:
			
			# currently in an armoured vehicle
			if self.unit.GetStat('armour') is not None:
				
				# not exposed
				if not self.ce: return None
				
				# Unconcious crew are assumed to be slumped down and are protected
				if self.status == 'Unconscious': return None
				
				if fp <= 4:
					modifier -= 10.0
				elif fp <= 6:
					modifier -= 5.0
				elif 8 < fp <= 10:
					modifier += 5.0
				elif fp <= 12:
					modifier += 10.0
				elif fp <= 16:
					modifier += 15.0
				else:
					modifier += 20.0
		
		# apply additional modifier if any
		modifier += roll_modifier
				
		# roll for wound
		roll = GetPercentileRoll()
		
		if DEBUG:
			if session.debug['Player Crew Hapless']:
				roll = 100.0
		
		# unmodified 99.0-100.0 always counts as KIA, otherwise modifier is applied
		if roll < 99.0:
			roll += modifier

		#print('DEBUG: final modified wound roll was: ' + str(roll))

		if roll <= 45.0:
			
			# near miss - no wound or other effect
			return None
		
		elif roll <= 55.0:
			
			if self.status in ['Stunned', 'Unconscious']:
				return None
				
			self.DoStunCheck(0)
			if self.status == 'Stunned':
				if show_messages:
					ShowMessage(self.GetFullName() + ' has been Stunned.')
				return 'Stunned'
			return None
		
		elif roll <= 70.0:
			
			if self.wound in ['Serious', 'Critical']: return None
			
			# light wound and possible stun
			self.wound = 'Light'
			if self.status not in ['Stunned', 'Unconscious']:
				self.DoStunCheck(15)
				if self.status == 'Stunned':
					if show_messages:
						ShowMessage(self.GetFullName() + ' has received a Light Wound and has been Stunned')
					return 'Light Wound, Stunned'
			
			if show_messages:
				ShowMessage(self.GetFullName() + ' has received a Light Wound.')
			return 'Light Wound'
				
			
		elif roll <= 85.0:
			
			if self.wound == 'Critical': return None
			
			# serious wound, possibly knocked unconscious, otherwise stunned
			self.wound = 'Serious'
			
			if self.status != 'Unconscious':
				self.DoKOCheck(0)
				if self.status == 'Unconscious':
					if show_messages:
						Message(self.GetFullName() + ' has received a Serious Wound ' +
							'and has been knocked Unconscious')
					return 'Serious Wound, Unconscious'
			
			if show_messages:
				ShowMessage(self.GetFullName() + ' has received a Serious Wound and is Stunned')
			return 'Serious Wound, Stunned'
			
			
		elif roll <= 97.0:
			
			# critical wound, possibly knocked unconscious, otherwise stunned, may die next recovery check
			self.wound = 'Critical'
			
			if self.status != 'Unconscious':
				self.DoKOCheck(15)
				if self.status == 'Unconscious':
					if show_messages:
						Message(self.GetFullName() + ' has received a Critical Wound ' +
							'and has been knocked Unconscious')
					return 'Critical Wound, Unconscious'
				
				if show_messages:
					ShowMessage(self.GetFullName() + ' has received a Critical Wound and is Stunned')
				return 'Critical Wound, Stunned'
		
		else:
			
			# killed
			self.status = 'Dead'
			self.wound = ''
			
			if show_messages:
				ShowMessage(self.GetFullName() + ' has been killed.')
			
			return 'Dead'
				
	
	# check to see if this personnel is Stunned
	def DoStunCheck(self, modifier):
		
		# can't make it worse
		if self.status in ['Stunned', 'Unconscious', 'Dead']: return
		
		roll = GetPercentileRoll() + modifier
		
		# roll passed
		if roll <= self.stats['Grit'] * 15.0: return
		
		self.status = 'Stunned'


	# check to see if this personnel is knocked unconscious
	def DoKOCheck(self, modifier):
		
		if self.status in ['Unconscious', 'Dead']: return False
		roll = GetPercentileRoll() + modifier
		if roll <= self.stats['Grit'] * 10.0:
			# not knocked out, but Stunned
			self.status = 'Stunned'
			return
		self.status = 'Unconscious'


	# check for recovery from any current status
	def DoRecoveryCheck(self):
		if self.status == '': return
		if self.status == 'Dead': return
		
		print('DEBUG: doing recovery roll for ' + self.GetFullName())
		
		roll = GetPercentileRoll()
		if self.status == 'Unconscious': roll += 15.0
		
		if self.status == 'Critical':
			if roll > 97.0:
				self.status = 'Dead'
				self.wound = ''
				if self.unit == scenario.player_unit:
					ShowMessage(self.GetFullName() + ' has died from his wounds.')
			return
		
		if roll <= self.stats['Grit'] * 15.0:
			
			if self.status == 'Stunned':
				self.status = ''
				if self.unit == scenario.player_unit:
					ShowMessage(self.GetFullName() + ' recovers from being Stunned.')
			
			# unconscious
			else:
				self.status = 'Stunned'
				if self.unit == scenario.player_unit:
					ShowMessage(self.GetFullName() + ' regains consciousness and is now Stunned.')

	
	# (re)build a list of possible commands for this turn
	def BuildCommandList(self):
		self.cmd_list = []
		
		# unconscious and dead crewmen cannot act
		if self.status in ['Unconscious', 'Dead']:
			self.cmd_list.append('None')
			return
		
		for (k, d) in session.crew_commands.items():
			
			# don't add "None" automatically
			if k == 'None': continue
			
			if 'position_list' in d:
				if self.current_position.name not in d['position_list']:
					continue
			
			if k == 'Abandon Tank':
				crew_injured = False
				for position in self.unit.positions_list:
					if position.crewman is None: continue
					if position.crewman.status == 'Dead' or position.crewman.wound in ['Critical']:
						crew_injured = True
						break
				if not crew_injured:
					continue
			
			self.cmd_list.append(k)
	
	# select a new command from command list
	def SelectCommand(self, reverse):
		
		c = 1
		if reverse:
			c = -1
		
		# find current command in list
		i = self.cmd_list.index(self.current_cmd)
		
		# find new command
		if i+c > len(self.cmd_list) - 1:
			i = 0
		elif i+c < 0:
			i = len(self.cmd_list) - 1
		else:
			i += c
		
		self.current_cmd = self.cmd_list[i]
	
	
	# attempt to toggle current hatch status
	def ToggleHatch(self):
		
		# no hatch in position
		if not self.current_position.hatch: return False
		if self.current_position.open_top: return False
		if self.current_position.crew_always_ce: return False
		
		# crewman unable to act
		if self.status in ['Dead', 'Unconscious']: return False
		
		self.current_position.hatch_open = not self.current_position.hatch_open
		
		# FUTURE: change other hatches in this group if any
		
		# set CE status based on new hatch status
		self.SetCEStatus()
		
		return True
	
	
	# set crewman BU/CE status based on position status
	def SetCEStatus(self):
		
		if not self.current_position.hatch:
			self.ce = False
			return
		
		if self.current_position.open_top or self.current_position.crew_always_ce:
			self.ce = True
			return
		
		if self.current_position.hatch_open:
			self.ce = True
		else:
			self.ce = False

		
	

# Position class: represents a personnel position within a unit
class Position:
	def __init__(self, unit, position_dict):
		
		self.unit = unit
		self.name = position_dict['name']
		
		self.location = None
		if 'location' in position_dict:
			self.location = position_dict['location']
		
		self.hatch = False
		if 'hatch' in position_dict:
			self.hatch = True
		
		self.hatch_group = None
		if 'hatch_group' in position_dict:
			self.hatch_group = int(position_dict['hatch_group'])
		
		self.open_top = False
		if 'open_top' in position_dict:
			self.open_top = True
		
		self.crew_always_ce = False
		if 'crew_always_exposed' in position_dict:
			self.crew_always_ce = True
		
		self.ce_visible = []
		if 'ce_visible' in position_dict:
			for direction in position_dict['ce_visible']:
				self.ce_visible.append(int(direction))
		
		self.bu_visible = []
		if 'bu_visible' in position_dict:
			for direction in position_dict['bu_visible']:
				self.bu_visible.append(int(direction))
		
		# person currently in this position
		self.crewman = None
		
		# current hatch open/closed status
		self.hatch_open = False
		
		# list of map hexes visible to this position
		self.visible_hexes = []
	
	
	# update the list of hexes currently visible from this position
	def UpdateVisibleHexes(self):
		
		self.visible_hexes = []
		
		if self.crewman is None: return
		
		# can always spot in own hex
		self.visible_hexes.append((self.unit.hx, self.unit.hy))
		
		# current crew command does not allow spotting
		if not session.crew_commands[self.crewman.current_cmd]['spotting_allowed']:
			return
		
		if self.hatch_open:
			direction_list = self.ce_visible
		else:
			direction_list = self.bu_visible
		
		for direction in direction_list:
			hextant_hex_list = GetCoveredHexes(self.unit.hx, self.unit.hy, direction)
			for (hx, hy) in hextant_hex_list:
				# hex is off map
				if (hx, hy) not in scenario.hex_dict: continue
				# already in list
				if (hx, hy) in self.visible_hexes: continue
				# too far away for BU crew
				if not self.hatch_open:
					if GetHexDistance(self.unit.hx, self.unit.hy, hx, hy) > MAX_BU_LOS:
						continue
				self.visible_hexes.append((hx, hy))



# Weapon Class: represents a weapon mounted on or carried by a unit
class Weapon:
	def __init__(self, unit, stats):
		self.unit = unit			# unit that owns this weapon
		self.stats = stats			# dictionary of weapon stats
		
		# some weapons need a descriptive name generated
		if 'name' not in self.stats:
			if self.GetStat('type') == 'Gun':
				text = self.GetStat('calibre') + 'mm'
				if self.GetStat('long_range') is not None:
					text += '(' + self.GetStat('long_range') + ')'
				self.stats['name'] = text
			else:
				self.stats['name'] = self.GetStat('type')
		
		# save maximum range as an local int
		self.max_range = 3
		if 'max_range' in self.stats:
			self.max_range = int(self.stats['max_range'])
			del self.stats['max_range']
		else:
			if self.stats['type'] in ['Turret MG', 'Co-ax MG']:
				self.max_range = 2
			elif self.stats['type'] in ['Hull MG', 'AA MG']:
				self.max_range = 1
		
		self.ammo_type = None
		
		# if weapon is a gun, set up ammo stores
		self.ammo_stores = None
		if self.GetStat('type') == 'Gun' and 'ammo_type_list' in self.stats:
			self.ammo_stores = {}
			self.LoadGunAmmo()
		
		# weapon statuses
		self.covered_hexes = []			# map hexes that could be targeted by this weapon
		self.fired = False
		self.maintained_rof = False
	
	
	# check for the value of a stat, return None if stat not present
	def GetStat(self, stat_name):
		if stat_name not in self.stats:
			return None
		return self.stats[stat_name]
	
	
	# calculate the map hexes covered by this weapon
	def UpdateCoveredHexes(self):
		
		self.covered_hexes = []
		
		# can always fire in own hex
		self.covered_hexes.append((self.unit.hx, self.unit.hy))
		
		# infantry can fire all around
		if self.unit.GetStat('category') == 'Infantry':
			for r in range(1, self.max_range + 1):
				ring_list = GetHexRing(self.unit.hx, self.unit.hy, r)
				for (hx, hy) in ring_list:
					# make sure hex is on map
					if (hx, hy) in scenario.hex_dict:
						self.covered_hexes.append((hx, hy))
			return
		
		# hull-mounted weapons fire in hull facing direction
		if self.GetStat('mount') == 'Hull':
			hextant_hex_list = GetCoveredHexes(self.unit.hx, self.unit.hy, self.unit.facing)
			
		# turret-mounted weapons fire in turret direction
		elif self.GetStat('mount') == 'Turret':
			hextant_hex_list = GetCoveredHexes(self.unit.hx, self.unit.hy, self.unit.turret_facing)
		
		else:
			print('ERROR: Could not set covered hexes for weapon: ' + self.stats['name'])
			return
		
		for (hx, hy) in hextant_hex_list:
			if (hx, hy) not in scenario.hex_dict: continue		# hex is off map
			# out of range
			if GetHexDistance(self.unit.hx, self.unit.hy, hx, hy) > self.max_range:
				continue
			self.covered_hexes.append((hx, hy))
		
		
	# load this gun full of ammo
	def LoadGunAmmo(self):
		
		if not self.GetStat('type') == 'Gun': return
		
		# set up empty categories first
		for ammo_type in self.stats['ammo_type_list']:
			self.ammo_stores[ammo_type] = 0
		
		# now determine loadout
		max_ammo = int(self.stats['max_ammo'])
		
		# only one type, fill it up
		if len(self.stats['ammo_type_list']) == 1:
			ammo_type = self.stats['ammo_type_list'][0]
			self.ammo_stores[ammo_type] = max_ammo
			self.ammo_type = ammo_type
		
		# HE and AP: 70% and 30%
		else:
			if self.stats['ammo_type_list'] == ['HE', 'AP']:
				self.ammo_stores['HE'] = int(max_ammo * 0.7)
				self.ammo_stores['AP'] = max_ammo - self.ammo_stores['HE']
				self.ammo_type = 'AP'
	
	
	# set/reset all scenario statuses for a new turn
	def ResetMe(self):
		self.fired = False
		self.moving = False
		self.maintained_rof = False
		self.UpdateCoveredHexes()
	
	
	# cycle to use next available ammo type
	def CycleAmmo(self):
		
		# no other types possible
		if len(self.stats['ammo_type_list']) == 1:
			return False
		
		i = self.stats['ammo_type_list'].index(self.ammo_type)
		if i == len(self.stats['ammo_type_list']) - 1:
			i = 0
		else:
			i += 1
		
		self.ammo_type = self.stats['ammo_type_list'][i]
		
		return True
	
	
	# return the effective FP of an HE hit from this gun
	def GetEffectiveFP(self):
		if self.GetStat('type') != 'Gun':
			print('ERROR: ' + self.stats['name'] + ' is not a gun, cannot generate effective FP')
			return 1
		
		for (calibre, fp) in HE_FP_EFFECT:
			if calibre <= int(self.GetStat('calibre')):
				return fp
		
		print('ERROR: Could not find effective FP for: ' + self.stats['name'])
		return 1
	
	
	# return the base penetration chance of an HE hit from this gun
	def GetBaseHEPenetrationChance(self):
		if self.GetStat('type') != 'Gun':
			print('ERROR: ' + self.stats['name'] + ' is not a gun, cannot generate HE AP chance')
			return 0.0
		
		for (calibre, chance) in HE_AP_CHANCE:
			if calibre <= int(self.GetStat('calibre')):
				return chance
		
		print('ERROR: Could not find HE AP chance for: ' + self.stats['name'])
		return 0.0



# AI: controller for enemy and player-allied units
class AI:
	def __init__(self, owner):
		self.owner = owner			# pointer to owning Unit
		self.disposition = None			# records type of action for this activation

	# do activation for this unit
	def DoActivation(self):
		
		# check for debug flag
		if DEBUG:
			if session.debug['No AI Actions']:
				return
		
		# no action if it's not alive
		if not self.owner.alive: return
		
		#print('AI DEBUG: ' + self.owner.unit_id + ' now acting')
		
		# FUTURE: check for automatic action here
					
		roll = GetPercentileRoll()
		
		# modify roll if player has this unit as an acquired target and vice-versa
		if scenario.player_unit.acquired_target is not None:
			(ac_target, level) = scenario.player_unit.acquired_target
			if ac_target == self.owner:
				roll -= 10.0
		if self.owner.acquired_target is not None:
			(ac_target, level) = self.owner.acquired_target
			if ac_target == scenario.player_unit:
				roll -= 10.0
		
		if DEBUG:
			if session.debug['AI Hates Player']:
				roll = 0.0
		
		# check for player crew vulnerability
		player_crew_vulnerable = False
		for position in scenario.player_unit.positions_list:
			if position.crewman is None: continue
			if not position.crewman.ce: continue
			if position.crewman.status in ['Dead', 'Unconscious']: continue
			player_crew_vulnerable = True
			break
		
		# Step 1: roll for unit action
		if self.owner.GetStat('category') == 'Infantry':
			
			if roll <= 25.0:
				if player_crew_vulnerable and roll <= 20.0:
					self.disposition = 'Harass Player'
				else:
					self.disposition = 'Attack Player'
			elif roll <= 40.0:
				self.disposition = 'Combat'
			elif roll <= 60.0:
				if self.owner.pinned:
					self.disposition = 'Combat'
				else:
					self.disposition = 'Movement'
			else:
				self.disposition = None
		
		elif self.owner.GetStat('category') == 'Gun':
			
			if not self.owner.deployed:
				self.disposition = None
			else:
				if roll <= 10.0:
					self.disposition = 'Attack Player'
				elif roll <= 65.0:
					self.disposition = 'Combat'
				else:
					self.disposition = None
		
		# non-combat unit
		elif self.owner.GetStat('class') == 'Truck':
			if roll <= 60.0:
				self.disposition = None
			else:
				self.disposition = 'Movement'
		
		# combat vehicle
		else:
			if roll <= 15.0:
				if player_crew_vulnerable and roll <= 10.0:
					self.disposition = 'Harass Player'
				else:
					self.disposition = 'Attack Player'
			elif roll <= 40.0:
				self.disposition = 'Combat'
			elif roll <= 65.0:
				self.disposition = 'Movement'
			else:
				self.disposition = None
		
		current_range = GetHexDistance(0, 0, self.owner.hx, self.owner.hy)
		
		# no combat if unit is off-map
		if current_range > 3:
			if self.disposition == 'Combat':
				self.disposition = None
		
		# player squad doesn't move on its own and doesn't harass or attack the player
		if self.owner in scenario.player_unit.squad:
			if self.disposition in ['Harass Player', 'Attack Player', 'Movement']:
				self.disposition = 'Combat'
		
		# chance that movement action will be cancelled if we have an acquired target
		if self.owner.acquired_target is not None and self.disposition == 'Movement':
			if GetPercentileRoll() <= 80.0:
				self.disposition = 'Combat'
		
		#if self.disposition is not None:
		#	print('AI DEBUG: ' + self.owner.unit_id + ' set disposition to: ' + self.disposition)
		
		# Step 2: Determine action to take
		if self.disposition == 'Movement':
			
			# build a list of adjacent hexes
			hex_list = GetHexRing(self.owner.hx, self.owner.hy, 1)
			
			for (hx, hy) in reversed(hex_list):
				
				# don't move into player's hex
				if hx == 0 and hy == 0:
					hex_list.remove((hx, hy))
					continue
				
				# if destination is on map, check if 1+ enemy units present
				if (hx, hy) in scenario.hex_dict:
					for unit in scenario.hex_dict[(hx,hy)].unit_stack:
						if unit.owning_player != self.owner.owning_player:
							hex_list.remove((hx, hy))
							continue
				
				# if move would take them off map, large chance that this hex gets thrown out
				dist = GetHexDistance(0, 0, hx, hy)
				if dist == 4:
					if GetPercentileRoll() <= 75.0:
						hex_list.remove((hx, hy))
						continue
				
				# otherwise, if range would change, smaller chance that this hex gets thrown out
				elif dist != current_range:
					if GetPercentileRoll() <= 40.0:
						hex_list.remove((hx, hy))
						continue
			
			# no possible moves
			if len(hex_list) == 0:
				return
			
			(hx, hy) = choice(hex_list)
			
			# if destination is off-map, remove from game
			if (hx, hy) not in scenario.hex_dict:
				self.owner.RemoveFromPlay()
				return
			
			# turn to face destination
			if self.owner.facing is not None:
				direction = GetDirectionToAdjacent(self.owner.hx, self.owner.hy, hx, hy)
				self.owner.facing = direction
				if self.owner.turret_facing is not None:
					self.owner.turret_facing = direction
			
			# set statuses
			self.owner.moving = True
			self.owner.ClearAcquiredTargets()
			
			# do movement roll
			chance = self.owner.forward_move_chance
			roll = GetPercentileRoll()
			
			# move was not successful
			if roll > chance:
				self.owner.forward_move_chance += BASE_MOVE_BONUS
			
			# move was successful, clear any bonus and move into new hex
			else:
				self.owner.forward_move_chance = 0.0
				scenario.hex_dict[(self.owner.hx, self.owner.hy)].unit_stack.remove(self.owner)
				self.owner.hx = hx
				self.owner.hy = hy
				scenario.hex_dict[(hx, hy)].unit_stack.append(self.owner)
				for weapon in self.owner.weapon_list:
					weapon.UpdateCoveredHexes()
			
			self.owner.GenerateTerrain()
			self.owner.CheckForHD()
			scenario.UpdateUnitCon()
			scenario.UpdateScenarioDisplay()
			
			# if new location is in ring 4, remove from game
			if GetHexDistance(0, 0, hx, hy) == 4:
				self.owner.RemoveFromPlay()
				
		
		elif self.disposition in ['Combat', 'Attack Player', 'Harass Player']:
			
			# determine target
			target_list = []
			
			if self.disposition in ['Attack Player', 'Harass Player']:
				target_list.append(scenario.player_unit)
			else:
				for unit in scenario.units:
					if unit == scenario.player_unit: continue
					if unit.owning_player == self.owner.owning_player: continue
					if GetHexDistance(0, 0, unit.hx, unit.hy) > 3: continue
					target_list.append(unit)
			
			# no possible targets
			if len(target_list) == 0:
				#print ('AI DEBUG: No possible targets for ' + self.owner.unit_id)
				return
			
			# score possible weapon-target combinations
			attack_list = []
			
			for target in target_list:
				for weapon in self.owner.weapon_list:
					
					# since we're ignoring our current hull/turret facing, make sure that target is in range
					if GetHexDistance(self.owner.hx, self.owner.hy, target.hx, target.hy) > weapon.max_range:
						continue
					
					# if Harassing player, only use MGs and small arms
					if self.disposition == 'Harass Player' and weapon.GetStat('type') == 'Gun': continue
					
					# gun weapons need to check multiple ammo type combinations
					if weapon.GetStat('type') == 'Gun':
						ammo_list = weapon.stats['ammo_type_list']
						for ammo_type in ammo_list:
							
							weapon.ammo_type = ammo_type
							result = scenario.CheckAttack(self.owner, weapon, target, ignore_facing=True)
							# attack not possible
							if result != '':
								continue
							attack_list.append((weapon, target, ammo_type))
						continue
					
					result = scenario.CheckAttack(self.owner, weapon, target, ignore_facing=True)
					if result != '':
						continue
					attack_list.append((weapon, target, ''))
			
			# no possible attacks
			if len(attack_list) == 0:
				#print ('AI DEBUG: No possible attacks for ' + self.owner.unit_id)
				return
			
			# score each possible weapon-ammo-target combination
			scored_list = []
			for (weapon, target, ammo_type) in attack_list:
				
				# skip small arms attacks on targets that have no chance of effect
				if self.disposition != 'Harass Player' and target.GetStat('category') == 'Vehicle':
					if weapon.GetStat('type') != 'Gun' and weapon.GetStat('type') not in MG_WEAPONS:
						continue
				
				# determine if a pivot or turret rotation would be required
				pivot_req = False
				turret_rotate_req = False
				mount = weapon.GetStat('mount')
				if mount is not None:
					if mount == 'Turret' and self.owner.turret_facing is not None:
						if (target.hx, target.hy) not in weapon.covered_hexes:
							turret_rotate_req = True
					else:
						if (target.hx, target.hy) not in weapon.covered_hexes:
							pivot_req = True
				
				# special: player squad cannot pivot
				if pivot_req and self.owner in scenario.player_unit.squad:
					#print ('DEBUG: discarded an attack because player squad member would have to pivot')
					continue
				
				# set ammo type if required
				if ammo_type != '':
					weapon.ammo_type = ammo_type
				
				# calculate odds of attack, taking into account if the attack
				# would require a pivot or turret rotation
				profile = scenario.CalcAttack(self.owner, weapon, target,
					pivot=pivot_req, turret_rotate=turret_rotate_req)
				
				# attack not possible
				if profile is None: continue
				
				score = profile['final_chance']
				
				# apply score modifiers
				
				# FUTURE: can factor armour penetration chance into score
				
				# try to avoid using HE on infantry in case MG is available too
				if target.GetStat('category') == 'Infantry' and ammo_type == 'HE':
					score -= 20.0
				
				# avoid small arms on armoured targets and MG attacks unless within AP range
				if self.disposition != 'Harass Player':
					if weapon.GetStat('type') != 'Gun' and target.GetStat('armour') is not None:
						if weapon.GetStat('type') not in MG_WEAPONS:
							score -= 40.0
						elif GetHexDistance(self.owner.hx, self.owner.hy, target.hx, target.hy) > MG_AP_RANGE:
							score -= 40.0
				
				if target.GetStat('category') == 'Vehicle':
				
					# avoid HE attacks on armoured targets
					if weapon.GetStat('type') == 'Gun' and target.GetStat('armour') is not None:
						if ammo_type == 'HE':
							score -= 20.0
					
					# avoid AP attacks on unarmoured vehicles
					if weapon.GetStat('type') == 'Gun' and target.GetStat('armour') is None:
						if ammo_type == 'AP':
							score -= 20.0
				
				# not sure if this is required, but seems to work
				score = round(score, 2)
				
				# add to list
				scored_list.append((score, weapon, target, ammo_type))
			
			# no possible attacks
			if len(scored_list) == 0:
				#print('AI DEBUG: ' + self.owner.unit_id + ': no possible scored attacks on targets')
				return
			
			# sort list by score
			scored_list.sort(key=lambda x:x[0], reverse=True)
			
			# DEBUG: list scored attacks
			#print ('AI DEBUG: ' + str(len(scored_list)) + ' possible attacks for ' + self.owner.unit_id + ':')
			#n = 1
			#for (score, weapon, target, ammo_type) in scored_list:
			#	text = '#' + str(n) + ' (' + str(score) + '): ' + weapon.stats['name']
			#	if ammo_type != '':
			#		text += '(' + ammo_type + ')'
			#	text += ' against ' + target.unit_id + ' in ' + str(target.hx) + ',' + str(target.hy)
			#	print (text)
			#	n += 1
			
			# select best attack
			(score, weapon, target, ammo_type) = scored_list[0]
			
			# no good attacks
			if score <= 3.0:
				#print('AI DEBUG: ' + self.owner.unit_id + ': no good scored attacks on target list')
				return
			
			# proceed with best attack
			
			# set ammo type if any
			if ammo_type != '': weapon.current_ammo = ammo_type
			
			# pivot or rotate turret if required
			mount = weapon.GetStat('mount')
			if mount is not None and (target.hx, target.hy) not in weapon.covered_hexes:
				
				direction = GetDirectionToward(self.owner.hx, self.owner.hy, target.hx, target.hy)
				
				if mount == 'Turret' and self.owner.turret_facing is not None:
					self.owner.turret_facing = direction
					#print('AI DEBUG: AI unit rotated turret to fire')
				
				elif mount == 'Hull' and self.owner.facing is not None:
					self.owner.facing = direction
					if self.owner.turret_facing is not None:
						self.owner.turret_facing = direction
					#print('AI DEBUG: AI unit pivoted hull to fire')
				
				scenario.UpdateUnitCon()
				scenario.UpdateScenarioDisplay()
				for weapon in self.owner.weapon_list:
					weapon.UpdateCoveredHexes()
			
			#text = 'AI DEBUG: ' + self.owner.unit_id + ' attacking with ' + weapon.stats['name']
			#if ammo_type != '':
			#	text += '(' + ammo_type + ')'
			#text += ' against ' + target.unit_id + ' in ' + str(target.hx) + ',' + str(target.hy)
			#print(text)
			
			# move target to top of hex stack
			target.MoveToTopOfStack()
			scenario.UpdateUnitCon()
			scenario.UpdateScenarioDisplay()
			libtcod.console_flush()
			
			result = self.owner.Attack(weapon, target)



# Unit Class: represents a single vehicle or gun, or a squad or small team of infantry
class Unit:
	def __init__(self, unit_id):
		
		self.unit_id = unit_id			# unique ID for unit type
		self.unit_name = ''			# name of tank, etc.
		self.alive = True			# unit is alive
		self.owning_player = 0			# unit is allied to 0:player 1:enemy
		self.nation = None			# nationality of unit and personnel
		self.ai = None				# AI controller if any
		
		self.squad = None			# list of units in player squad
		
		self.positions_list = []		# list of crew/personnel positions
		self.personnel_list = []		# list of crew/personnel
		
		# load unit stats from JSON file
		with open(DATAPATH + 'unit_type_defs.json', encoding='utf8') as data_file:
			unit_types = json.load(data_file)
		if unit_id not in unit_types:
			print('ERROR: Could not find unit id: ' + unit_id)
			self.unit_id = None
			return
		self.stats = unit_types[unit_id].copy()
		
		if 'crew_positions' in self.stats:
			for position_dict in self.stats['crew_positions']:
				self.positions_list.append(Position(self, position_dict))
		
		# set up weapons
		self.weapon_list = []			# list of unit weapons
		if 'weapon_list' in self.stats:
			weapon_list = self.stats['weapon_list']
			for weapon_dict in weapon_list:
				self.weapon_list.append(Weapon(self, weapon_dict))
			
			# clear this stat since we don't need it any more
			self.stats['weapon_list'] = None
		
		# set up initial scenario statuses
		self.ResetMe()
	
	
	# set/reset all scenario statuses
	def ResetMe(self):
		
		self.hx = 0				# location in scenario hex map
		self.hy = 0
		self.terrain = None			# surrounding terrain
		self.terrain_seed = 0			# seed for terrain depiction greebles
		self.dest_hex = None			# destination hex for move
		self.animation_cells = []		# list of x,y unit console locations for animation
		
		self.spotted = False			# unit has been spotted by opposing side
		
		self.hull_down = []			# list of directions unit in which Hull Down
		self.moving = False
		self.fired = False
		self.hit_by_fp = False			# was hit by an effective fp attack
		
		self.facing = None
		self.previous_facing = None
		self.turret_facing = None
		self.previous_turret_facing = None
		
		self.pinned = False
		self.deployed = False
		
		self.acquired_target = None		# tuple: unit has acquired this unit to this level (1/2)
		
		self.forward_move_chance = 0.0		# set by CalculateMoveChances()
		self.reverse_move_chance = 0.0
		
		self.forward_move_bonus = 0.0
		self.reverse_move_bonus = 0.0
		
		self.fp_to_resolve = 0			# fp from attacks to be resolved
		self.ap_hits_to_resolve = []		# list of unresolved AP hits
	
	
	# reset this unit for new turn
	def ResetForNewTurn(self):
		
		self.moving = False
		self.previous_facing = self.facing
		self.previous_turret_facing = self.turret_facing
		
		self.fired = False
		for weapon in self.weapon_list:
			weapon.ResetMe()
		
		# select first player weapon if none selected so far
		if self == scenario.player_unit:
			if scenario.selected_weapon is None:
				scenario.selected_weapon = self.weapon_list[0]
		
		# update crew positions
		for position in self.positions_list:
			# update visible hexes
			position.UpdateVisibleHexes()
			if position.crewman is None: continue
			# check for crew status recovery
			position.crewman.DoRecoveryCheck()

	
	# check for the value of a stat, return None if stat not present
	def GetStat(self, stat_name):
		if stat_name not in self.stats:
			return None
		return self.stats[stat_name]
	
	
	# return a to-hit modifier given current terrain
	def GetTEM(self):
		
		if self.terrain not in SCENARIO_TERRAIN_EFFECTS: return 0.0
		terrain_dict = SCENARIO_TERRAIN_EFFECTS[self.terrain]
		if 'TEM' not in terrain_dict: return 0.0
		tem_dict = terrain_dict['TEM']
		
		if 'All' in tem_dict: return tem_dict['All']
		
		if self.GetStat('category') == 'Infantry':
			if 'Infantry' in tem_dict:
				return tem_dict['Infantry']
		
		if self.GetStat('category') == 'Gun':
			if self.deployed:
				if 'Deployed Gun' in tem_dict:
					return tem_dict['Deployed Gun']
		
		return 0.0
	
	
	# get a descriptive name of this unit
	def GetName(self):
		if self.owning_player == 1 and not self.spotted:
			return 'Unspotted Unit'
		return self.unit_id
	
	
	# return the person in the given position
	def GetPersonnelByPosition(self, position_name):
		for position in self.positions_list:
			if position.crewman is None: continue
			if position.name == position_name:
				return position.crewman
		return None
	
	
	# clear any acquired target from this unit, and clear it from any enemy unit
	def ClearAcquiredTargets(self):
		self.acquired_target = None
		for unit in scenario.units:
			if unit.owning_player == self.owning_player: continue
			if unit.acquired_target is None: continue
			(target, level) = unit.acquired_target
			if target == self:
				unit.acquired_target = None
	
	
	# set a newly acquired target, or add a level
	def AddAcquiredTarget(self, target):
		
		# no previous acquired target
		if self.acquired_target is None:
			self.acquired_target = (target, False)
			return
		
		(old_target, level) = self.acquired_target
		
		# had an old target but now have a new one
		if old_target != target:
			self.acquired_target = (target, False)
			return
		
		# possible to add one level
		if not level:
			self.acquired_target = (target, True)
			return
		
		# otherwise, already acquired target to 2 levels, no further effect
	
	
	# calcualte chances of a successful forward/reverse move action for this unit
	def CalculateMoveChances(self):
		
		# set values to base values
		self.forward_move_chance = BASE_FORWARD_MOVE_CHANCE
		self.reverse_move_chance = BASE_REVERSE_MOVE_CHANCE
		
		# apply modifier from unit movement type
		movement_class = scenario.player_unit.GetStat('movement_class')
		if movement_class == 'Slow Tank':
			self.forward_move_chance -= 15.0
		elif movement_class == 'Fast Tank':
			self.forward_move_chance += 10.0
		elif movement_class == 'Wheeled':
			# FUTURE: additional modifier here if using road movement
			self.forward_move_chance += 5.0
		
		# apply modifier from current terrain type
		if self.terrain is not None:
			if 'Movement Mod' in SCENARIO_TERRAIN_EFFECTS[self.terrain]:
				mod = SCENARIO_TERRAIN_EFFECTS[self.terrain]['Movement Mod']
				self.forward_move_chance += mod
				self.reverse_move_chance += mod
		
		# apply modifier for ground conditions
		if campaign_day.weather['Ground'] == 'Muddy':
			if movement_class == 'Wheeled':
				mod = -45.0
			else:
				mod = -30.0
			self.forward_move_chance += mod
			self.reverse_move_chance += mod
		
		# add bonuses from previous moves
		self.forward_move_chance += self.forward_move_bonus
		self.reverse_move_chance += self.reverse_move_bonus
		
		# add bonuses from commander direction
		for position in ['Commander', 'Commander/Gunner']:
			crewman = self.GetPersonnelByPosition(position)
			if crewman is not None:
				if crewman.current_cmd == 'Direct Movement':
					self.forward_move_chance += 15.0
					self.reverse_move_chance += 10.0
				break
		
		# limit chances
		self.forward_move_chance = RestrictChance(self.forward_move_chance)
		self.reverse_move_chance = RestrictChance(self.reverse_move_chance)
	
	
	# upon spawning into a scenario map hex, or after moving or repositioning, roll to
	# see if this unit gains HD status
	# if driver_attempt is True, then the driver is actively trying to get HD
	def CheckForHD(self, driver_attempt=False):
		
		# unit not eligible for HD
		if self.GetStat('category') in ['Sniper', 'Infantry', 'Gun']: return False
		
		# clear any previous HD status
		self.hull_down = []
		
		# calculate base chance of HD
		if self.terrain not in SCENARIO_TERRAIN_EFFECTS: return False
		chance = SCENARIO_TERRAIN_EFFECTS[self.terrain]['HD Chance']
		
		# apply size modifier
		size_class = self.GetStat('size_class')
		if size_class is not None:
			chance += HD_SIZE_MOD[size_class]
		
		# bonus for driver action and commander direction if any
		if driver_attempt:
			crewman = self.GetPersonnelByPosition('Driver')
			if crewman is not None:
				crewman.GetActionMod('Attempt HD')
			for position in ['Commander', 'Commander/Gunner']:
				crewman = self.GetPersonnelByPosition(position)
				if crewman is None: continue
				if crewman.current_cmd == 'Direct Movement':
					chance += crewman.GetActionMod('Direct Movement')
					break
		
		chance = RestrictChance(chance)
		
		roll = GetPercentileRoll()
		
		# check for debug flag
		if self == scenario.player_unit and DEBUG:
			if session.debug['Player Always HD']:
				roll = 1.0
		
		if roll > chance: return False
		
		if driver_attempt:
			direction = self.facing
		else:
			direction = choice(range(6))
		self.hull_down = [direction]
		self.hull_down.append(ConstrainDir(direction + 1))
		self.hull_down.append(ConstrainDir(direction - 1))
		return True
	
	
	# build lists of possible commands for each personnel in this unit
	def BuildCmdLists(self):
		for position in self.positions_list:
			if position.crewman is None: continue
			position.crewman.BuildCommandList()
			
			# cancel current command if no longer possible
			if position.crewman.current_cmd not in position.crewman.cmd_list:
				position.crewman.current_cmd = position.crewman.cmd_list[0]
	
	
	# do a round of spotting from this unit
	# for now, only the player unit does these
	def DoSpotChecks(self):
				
		# unit out of play range
		if GetHexDistance(0, 0, self.hx, self.hy) > 3:
			return
		
		# create a local list of crew positions in a random order
		position_list = sample(self.positions_list, len(self.positions_list))
		
		for position in position_list:
			
			# no crewman in position
			if position.crewman is None:
				continue
			
			# build list of units it's possible to spot
			
			spot_list = []
			for unit in scenario.units:
				if unit.owning_player == self.owning_player:
					continue
				if not unit.alive:
					continue
				if unit.spotted:
					continue
				if (unit.hx, unit.hy) not in position.visible_hexes:
					continue
				
				spot_list.append(unit)
			
			# no units possible to spot from this position
			if len(spot_list) == 0:
				continue
			
			# roll once for each unit
			for unit in spot_list:
			
				distance = GetHexDistance(self.hx, self.hy, unit.hx, unit.hy)
				
				chance = SPOT_BASE_CHANCE[distance]
				
				# target size
				size_class = unit.GetStat('size_class')
				if size_class is not None:
					if size_class == 'Small':
						chance -= 7.0
					elif size_class == 'Very Small':
						chance -= 18.0
					elif size_class == 'Large':
						chance += 7.0
					elif size_class == 'Very Large':
						chance += 18.0
				
				# precipitation
				if campaign_day.weather['Precipitation'] == 'Rain':
					chance -= 5.0 * float(distance)
				elif campaign_day.weather['Precipitation'] == 'Heavy Rain':
					chance -= 10.0 * float(distance)
				
				# target moving
				if unit.moving:
					chance = chance * 1.5
				
				# target fired
				if unit.fired:
					chance = chance * 2.0
				
				# infantry are not as good at spotting from their lower position
				if self.GetStat('category') == 'Infantry':
					chance = chance * 0.5
				
				# snipers are hard to spot
				if unit.unit_id == 'Sniper':
					chance = chance * 0.25
				
				# spotting crew modifier
				chance += position.crewman.GetActionMod('Spotting')
				
				# target is HD to spotter
				if len(unit.hull_down) > 0:
					if GetDirectionToward(unit.hx, unit.hy, self.hx, self.hy) in unit.hull_down:
						chance = chance * 0.5
				
				chance = RestrictChance(chance)
				
				# special: target has been hit by effective fp
				if unit.hit_by_fp:
					chance = 100.0
				
				roll = GetPercentileRoll()
				
				if roll <= chance:
					
					unit.SpotMe()
					scenario.UpdateUnitCon()
					scenario.UpdateScenarioDisplay()
					
					# display message
					if self.owning_player == 0:
						text = unit.GetName() + ' ' + unit.GetStat('class')
						text += ' spotted!'
						portrait = unit.GetStat('portrait')
						ShowMessage(text, portrait=portrait)
						
					elif unit == scenario.player_unit:
						ShowMessage('You have been spotted!')
	
	
	# reveal this unit after being spotted
	def SpotMe(self):
		self.spotted = True
	
	
	# generate new personnel sufficent to fill all personnel positions
	def GenerateNewPersonnel(self):
		self.personnel_list = []
		for position in self.positions_list:
			self.personnel_list.append(Personnel(self, self.nation, position))
			position.crewman = self.personnel_list[-1]
	
	
	# spawn this unit into the given scenario map hex
	def SpawnAt(self, hx, hy):
		self.hx = hx
		self.hy = hy
		
		scenario.units.append(self)
		for map_hex in scenario.map_hexes:
			if map_hex.hx == hx and map_hex.hy == hy:
				map_hex.unit_stack.append(self)
				break
		
		# generate terrain for this unit
		self.GenerateTerrain()
		# check for HD status
		self.CheckForHD()
	
	
	# randomly determine what kind of terrain this unit is in
	def GenerateTerrain(self):
		
		self.terrain = None
		self.terrain_seed = 0
		
		if scenario is None: return
		
		self.terrain_seed = libtcod.random_get_int(0, 1, 128)
		odds_dict = SCENARIO_TERRAIN_ODDS[scenario.cd_map_hex.terrain_type]
		roll = GetPercentileRoll()
		for terrain, odds in odds_dict.items():
			if roll <= odds:
				self.terrain = terrain
				return
			roll -= odds
		
		# if we get here, something has gone wrong, so hopefully the first terrain type is always ok
		for terrain, odds in odds_dict.items():
			self.terrain = terrain
			return
	
	
	# move this unit to the top of its current hex stack
	def MoveToTopOfStack(self):
		map_hex = scenario.hex_dict[(self.hx, self.hy)]
		
		# only unit in stack
		if len(map_hex.unit_stack) == 1:
			return
		
		# not actually in stack
		if self not in map_hex.unit_stack:
			return
		
		map_hex.unit_stack.remove(self)
		map_hex.unit_stack.insert(0, self)
	
	
	# remove this unit from the scenario
	def RemoveFromPlay(self):
		# remove from hex stack
		scenario.hex_dict[(self.hx, self.hy)].unit_stack.remove(self)
		# remove from scenario unit list
		scenario.units.remove(self)
		#print ('DEBUG: removed a ' + self.unit_id + ' from play')
	
	
	# return the display character to use on the map viewport
	def GetDisplayChar(self):
		# player unit
		if scenario.player_unit == self: return '@'
		
		# unknown enemy unit
		if self.owning_player == 1 and not self.spotted: return '?'
		
		unit_category = self.GetStat('category')
		
		# sniper
		if self.unit_id == 'Sniper': return 248
		
		# infantry
		if unit_category == 'Infantry': return 176
		
		# gun, set according to deployed status / hull facing
		if unit_category == 'Gun':
			if self.facing is None:		# facing not yet set
				return '!'
			if not self.deployed:
				return 124
			elif self.facing in [5, 0, 1]:
				return 232
			elif self.facing in [2, 3, 4]:
				return 233
			else:
				return '!'		# should not happen
		
		# vehicle
		if unit_category == 'Vehicle':
			
			# turretless vehicle
			if self.turret_facing is None:
				return 249
			return 9

		# default
		return '!'
	
	
	# draw this unit to the scenario unit layer console
	def DrawMe(self):
		
		# don't display if not alive any more
		if not self.alive: return
		
		# determine draw location
		if len(self.animation_cells) > 0:
			(x,y) = self.animation_cells[0]
		else:
			(x,y) = scenario.PlotHex(self.hx, self.hy)
		
		# draw terrain greebles
		if self.terrain is not None and not (self.owning_player == 1 and not self.spotted):
			generator = libtcod.random_new_from_seed(self.terrain_seed)
			
			if self.terrain == 'Open Ground':
				for (xmod, ymod) in GREEBLE_LOCATIONS:
					if libtcod.random_get_int(generator, 1, 9) <= 2: continue
					c_mod = libtcod.random_get_int(generator, 0, 20)
					col = libtcod.Color(30+c_mod, 90+c_mod, 20+c_mod)
					libtcod.console_put_char_ex(unit_con, x+xmod, y+ymod, 46, col, libtcod.black)
				
			elif self.terrain == 'Broken Ground':
				for (xmod, ymod) in GREEBLE_LOCATIONS:
					if libtcod.random_get_int(generator, 1, 9) <= 2: continue
					c_mod = libtcod.random_get_int(generator, 10, 40)
					col = libtcod.Color(70+c_mod, 60+c_mod, 40+c_mod)
					if libtcod.random_get_int(generator, 1, 10) <= 4:
						char = 247
					else:
						char = 240
					libtcod.console_put_char_ex(unit_con, x+xmod, y+ymod, char, col, libtcod.black)

			elif self.terrain == 'Brush':
				for (xmod, ymod) in GREEBLE_LOCATIONS:
					if libtcod.random_get_int(generator, 1, 9) <= 3: continue
					col = libtcod.Color(0,libtcod.random_get_int(generator, 80, 120),0)
					if libtcod.random_get_int(generator, 1, 10) <= 6:
						char = 15
					else:
						char = 42
					libtcod.console_put_char_ex(unit_con, x+xmod, y+ymod, char, col, libtcod.black)
				
			elif self.terrain == 'Woods':
				for (xmod, ymod) in GREEBLE_LOCATIONS:
					if libtcod.random_get_int(generator, 1, 9) == 1: continue
					col = libtcod.Color(0,libtcod.random_get_int(generator, 100, 170),0)
					libtcod.console_put_char_ex(unit_con, x+xmod, y+ymod, 6, col, libtcod.black)
					
			elif self.terrain == 'Wooden Buildings':
				for (xmod, ymod) in GREEBLE_LOCATIONS:
					c_mod = libtcod.random_get_int(generator, 10, 40)
					col = libtcod.Color(70+c_mod, 60+c_mod, 40+c_mod)
					libtcod.console_put_char_ex(unit_con, x+xmod, y+ymod, 249, col, libtcod.black)
			
			elif self.terrain == 'Hills':
				for (xmod, ymod) in GREEBLE_LOCATIONS:
					if libtcod.random_get_int(generator, 1, 9) <= 3: continue
					c_mod = libtcod.random_get_int(generator, 10, 40)
					col = libtcod.Color(20+c_mod, 110+c_mod, 20+c_mod)
					libtcod.console_put_char_ex(unit_con, x+xmod, y+ymod, 220, col, libtcod.black)
				
			elif self.terrain == 'Fields':
				for (xmod, ymod) in GREEBLE_LOCATIONS:
					if libtcod.random_get_int(generator, 1, 9) == 1: continue
					c = libtcod.random_get_int(generator, 120, 190)
					col = libtcod.Color(c, c, 0)
					libtcod.console_put_char_ex(unit_con, x+xmod, y+ymod,
						176, col, libtcod.black)
			
			elif self.terrain == 'Marsh':
				for (xmod, ymod) in GREEBLE_LOCATIONS:
					if libtcod.random_get_int(generator, 1, 9) == 1: continue
					libtcod.console_put_char_ex(unit_con, x+xmod, y+ymod, 176,
						libtcod.Color(45,0,180), libtcod.black)
					
			
		
		# determine foreground color to use
		if self.owning_player == 1:
			col = ENEMY_UNIT_COL
		else:	
			if self == scenario.player_unit:
				col = libtcod.white
			else:
				col = ALLIED_UNIT_COL
		
		# draw main display character
		libtcod.console_put_char_ex(unit_con, x, y, self.GetDisplayChar(), col, libtcod.black)
		
		# determine if we need to display a turret / gun depiction
		draw_turret = True
		
		if self.GetStat('category') == 'Infantry': draw_turret = False
		if self.owning_player == 1 and not self.spotted: draw_turret = False
		if self.GetStat('category') == 'Gun' and not self.deployed: draw_turret = False
		if len(self.weapon_list) == 0: draw_turret = False
		
		if draw_turret:
			# use turret facing if present, otherwise hull facing
			if self.turret_facing is not None:
				facing = self.turret_facing
			else:
				facing = self.facing
			
			# determine location to draw turret/gun character
			x_mod, y_mod = PLOT_DIR[facing]
			char = TURRET_CHAR[facing]
			libtcod.console_put_char_ex(unit_con, x+x_mod, y+y_mod, char, col, libtcod.black)

		
	
	# display info on this unit to a given console starting at x,y
	# if status is False, don't display current status flags
	def DisplayMyInfo(self, console, x, y, status=True):
		
		libtcod.console_set_default_background(console, libtcod.black)
		libtcod.console_set_default_foreground(console, libtcod.lighter_blue)
		
		libtcod.console_print(console, x, y, self.unit_id)
		libtcod.console_set_default_foreground(console, libtcod.light_grey)
		libtcod.console_print(console, x, y+1, self.GetStat('class'))
		
		# draw empty portrait background
		libtcod.console_set_default_background(console, PORTRAIT_BG_COL)
		libtcod.console_rect(console, x, y+2, 25, 8, True, libtcod.BKGND_SET)
		
		# draw portrait if any
		portrait = self.GetStat('portrait')
		if portrait is not None:
			libtcod.console_blit(LoadXP(portrait), 0, 0, 0, 0, console, x, y+2)
		
		# display name if any overtop portrait
		libtcod.console_set_default_foreground(console, libtcod.white)
		if self.unit_name != '':
			libtcod.console_print(console, x, y+2, self.unit_name)
		
		# weapons
		libtcod.console_set_default_background(console, libtcod.darkest_red)
		libtcod.console_rect(console, x, y+10, 25, 2, True, libtcod.BKGND_SET)
		
		text1 = ''
		text2 = ''
		for weapon in self.weapon_list:
			if weapon.GetStat('type') == 'Gun':
				if text1 != '': text1 += ', '
				text1 += weapon.stats['name']
			else:
				if text2 != '': text2 += ', '
				text2 += weapon.stats['name']
		libtcod.console_print(console, x, y+10, text1)
		libtcod.console_print(console, x, y+11, text2)
		
		# armour
		armour = self.GetStat('armour')
		if armour is None:
			libtcod.console_print(console, x, y+12, 'Unarmoured')
		else:
			libtcod.console_print(console, x, y+12, 'Armoured')
			libtcod.console_set_default_foreground(console, libtcod.light_grey)
			if self.GetStat('turret'):
				text = 'T'
			else:
				text = 'U'
			text += ' ' + armour['turret_front'] + '/' + armour['turret_side']
			libtcod.console_print(console, x+1, y+13, text)
			text = 'H ' + armour['hull_front'] + '/' + armour['hull_side']
			libtcod.console_print(console, x+1, y+14, text)
		
		# movement
		libtcod.console_set_default_foreground(console, libtcod.light_green)
		libtcod.console_print_ex(console, x+24, y+12, libtcod.BKGND_NONE, libtcod.RIGHT,
			self.GetStat('movement_class'))
		
		# recce and/or off road
		libtcod.console_set_default_foreground(console, libtcod.dark_green)
		text = ''
		if self.GetStat('recce') is not None:
			text += 'Recce'
		if self.GetStat('off_road') is not None:
			if text != '':
				text += ' '
			text += 'ATV'
		libtcod.console_print_ex(console, x+24, y+13, libtcod.BKGND_NONE, libtcod.RIGHT,
			text)
		
		# size class
		libtcod.console_set_default_foreground(console, libtcod.white)
		size_class = self.GetStat('size_class')
		if size_class is not None:
			if size_class != 'Normal':
				libtcod.console_print_ex(console, x+24, y+14, libtcod.BKGND_NONE,
					libtcod.RIGHT, size_class)
			
		# mark place in case we skip unit status display
		ys = 15
		if status:
			
			# Hull Down status if any
			if len(self.hull_down) > 0:
				libtcod.console_set_default_foreground(console, libtcod.sepia)
				libtcod.console_print(console, x+8, ys-1, 'HD')
				char = GetDirectionalArrow(self.hull_down[0])
				libtcod.console_put_char_ex(console, x+10, ys-1, char, libtcod.sepia, libtcod.black)
		
			# reset of unit status
			libtcod.console_set_default_foreground(console, libtcod.light_grey)
			libtcod.console_set_default_background(console, libtcod.darkest_blue)
			libtcod.console_rect(console, x, y+ys, 25, 2, True, libtcod.BKGND_SET)
			
			text = ''
			if self.moving:
				text += 'Moving '
			if self.fired:
				text += 'Fired '
			libtcod.console_print(console, x, y+ys+1, text)
			
			ys = 17

		libtcod.console_set_default_background(console, libtcod.black)
	
	
	# initiate an attack from this unit with the specified weapon against the specified target
	def Attack(self, weapon, target):
		
		# make sure correct information has been supplied
		if weapon is None or target is None: return False
		
		# make sure attack is possible
		if scenario.CheckAttack(self, weapon, target) != '': return False
		
		# display message if player is the target
		if target == scenario.player_unit:
			text = self.GetName() + ' fires at you with ' + weapon.stats['name']
			ShowMessage(text)
		
		# attack loop, possible to maintain RoF and do multiple attacks within this loop
		attack_finished = False
		while not attack_finished:
			
			# calculate attack profile
			profile = scenario.CalcAttack(self, weapon, target)
			
			# attack not possible for some reason
			if profile is None:
				attack_finished = True
				continue
			
			# display attack profile on screen if is player involved
			if self == scenario.player_unit or target == scenario.player_unit:
				scenario.DisplayAttack(profile)
				# activate the attack console and display to screen
				scenario.attack_con_active = True
				scenario.UpdateScenarioDisplay()
			
				# allow player to cancel attack if not the target
				if not weapon.maintained_rof:
					if WaitForContinue(allow_cancel = (target != scenario.player_unit)):
						scenario.attack_con_active = False
						return True
			
			# set weapon and unit fired flags
			weapon.fired = True
			self.fired = True
			
			# expend a shell if gun weapon is firing
			if weapon.GetStat('type') == 'Gun' and weapon.ammo_type is not None:
				weapon.ammo_stores[weapon.ammo_type] -= 1
				scenario.UpdateContextCon()
			
			
			##### Attack Animation and Sound Effects #####
			
			if weapon.GetStat('type') == 'Gun':
				
				(x1, y1) = scenario.PlotHex(self.hx, self.hy)
				(x2, y2) = scenario.PlotHex(target.hx, target.hy)
				line = GetLine(x1,y1,x2,y2)
				
				PlaySoundFor(weapon, 'fire')
						
				for (x,y) in line[2:-1]:
					libtcod.console_clear(animation_con)
					libtcod.console_put_char_ex(animation_con, x, y, 250, libtcod.white,
						libtcod.black)
					scenario.UpdateScenarioDisplay()
					Wait(6)
				libtcod.console_clear(animation_con)
				
				# add explosion effect if HE ammo
				if weapon.ammo_type == 'HE':
					
					PlaySoundFor(weapon, 'he_explosion')
					
					for i in range(12):
						col = choice([libtcod.red, libtcod.yellow, libtcod.black])
						libtcod.console_put_char_ex(animation_con, x2, y2, 42, col,
							libtcod.black)
						scenario.UpdateScenarioDisplay()
						Wait(4)
					libtcod.console_clear(animation_con)
			
			elif weapon.GetStat('type') == 'Small Arms' or weapon.GetStat('type') in MG_WEAPONS:
				
				(x1, y1) = scenario.PlotHex(self.hx, self.hy)
				(x2, y2) = scenario.PlotHex(target.hx, target.hy)
				line = GetLine(x1,y1,x2,y2)
				
				PlaySoundFor(weapon, 'fire')
				
				for i in range(25):
					libtcod.console_clear(animation_con)
					(x,y) = choice(line[2:-1])
					libtcod.console_put_char_ex(animation_con, x, y, 250, libtcod.yellow,
						libtcod.black)
					scenario.UpdateScenarioDisplay()
					Wait(3)
				libtcod.console_clear(animation_con)
			
			
			# do the roll, display results to the screen, and modify the attack profile
			profile = scenario.DoAttackRoll(profile)
			
			# add one level of acquired target if firing gun
			if weapon.GetStat('type') == 'Gun':
				self.AddAcquiredTarget(target)
			
			# wait for the player if they are involved
			# if RoF is maintained, may choose to attack again
			attack_finished = True
			if self == scenario.player_unit or target == scenario.player_unit:
				scenario.UpdateScenarioDisplay()
				
				end_pause = False
				while not end_pause:
					if libtcod.console_is_window_closed(): sys.exit()
					libtcod.console_flush()
					if not GetInputEvent(): continue
					
					key_char = DeKey(chr(key.c).lower())
					
					if key.vk == libtcod.KEY_TAB:
						end_pause = True
					
					if self == scenario.player_unit:
						if key_char == 'f' and weapon.maintained_rof:
							attack_finished = False
							end_pause = True
			
			# apply results of this attack if any
			
			# area fire attack
			if profile['type'] == 'Area Fire':
					
				if profile['result'] in ['CRITICAL EFFECT', 'FULL EFFECT', 'PARTIAL EFFECT']:
					
					target.fp_to_resolve += profile['effective_fp']
					
					# target will automatically be spotted next turn if possible
					if not target.spotted:
						target.hit_by_fp = True
				
				# possible it was converted into an AP MG hit
				elif profile['result'] in ['HIT', 'CRITICAL HIT']:	
					target.ap_hits_to_resolve.append(profile)
					
					# also applies fp
					target.fp_to_resolve += profile['effective_fp']
			
			# point fire attack hit
			elif profile['result'] in ['CRITICAL HIT', 'HIT']:
				
				# record if player hit
				if self == scenario.player_unit:
					campaign_day.records['Gun Hits'] += 1
				
				# infantry or gun target
				if target.GetStat('category') in ['Infantry', 'Gun']:
					
					# if HE hit, apply effective FP
					if profile['ammo_type'] == 'HE':
						
						effective_fp = profile['weapon'].GetEffectiveFP()
						
						# apply critical hit multiplier
						if profile['result'] == 'CRITICAL HIT':
							effective_fp = effective_fp * 2
						
						# apply ground conditions modifier
						if campaign_day.weather['Ground'] == 'Muddy':
							effective_fp = int(float(effective_fp) * 0.5)
						
						target.fp_to_resolve += effective_fp
						
						if not target.spotted:
							target.hit_by_fp = True
					
					# AP hits are very ineffective against infantry/guns, and
					# have no spotting effect
					elif profile['ammo_type'] == 'AP':
						target.fp_to_resolve += 1
				
				# vehicle target
				elif target.GetStat('category') == 'Vehicle':
					target.ap_hits_to_resolve.append(profile)
					
					
		
		
		# turn off attack console display if any
		scenario.attack_con_active = False
		scenario.UpdateScenarioDisplay()
		
		# reset weapon RoF
		weapon.maintained_rof = False
		
		# attack is finished
		return True
	
	
	# resolve all unresolved AP hits on this unit
	def ResolveAPHits(self):
		
		# no hits to resolve! doing fine!
		if len(self.ap_hits_to_resolve) == 0: return
		
		#print('Resolving AP hits on ' + self.unit_id)
		
		# no effect if unit is not a vehicle
		if self.GetStat('category') != 'Vehicle':
			self.ap_hits_to_resolve = []
			return
		
		# move to top of hex stack
		self.MoveToTopOfStack()
		scenario.UpdateUnitCon()
		
		# handle AP hits
		for profile in self.ap_hits_to_resolve:
			
			# unit is vehicle
			if self.GetStat('category') == 'Vehicle':
				
				profile = scenario.CalcAP(profile)
				
				# display and wait if player is involved
				if profile['attacker'] == scenario.player_unit or self == scenario.player_unit:
					scenario.DisplayAttack(profile)
					scenario.attack_con_active = True
					scenario.UpdateScenarioDisplay()
					WaitForContinue()
				
				# do the attack roll; modifies the attack profile
				profile = scenario.DoAttackRoll(profile)
				
				if profile['result'] == 'NO PENETRATION':
					PlaySoundFor(self, 'armour_save')
				
				# wait if player is involved
				if profile['attacker'] == scenario.player_unit or self == scenario.player_unit:
					scenario.UpdateScenarioDisplay()
					WaitForContinue()
				
				# turn off attack console display if any
				scenario.attack_con_active = False
				scenario.UpdateScenarioDisplay()
				
				# apply result if any
				if profile['result'] == 'NO PENETRATION':
					
					# check for stun test
					difference = profile['final_chance'] - profile['roll']
					
					if 0.0 < difference <= AP_STUN_MARGIN:
						
						# player was target
						if self == scenario.player_unit:
							
							print('DEBUG: doing stun tests')
							
							for position in self.positions_list:
								if position.crewman is None: continue
								position.crewman.DoStunCheck(AP_STUN_MARGIN - difference)
						
						# FUTURE: target was AI unit
						else:
							
							pass
							
				elif profile['result'] == 'PENETRATED':
					
					# TODO: roll for penetration result here, use the
					# final 'roll' difference vs. 'final_chance' as modifier
					
					self.DestroyMe()
					
					# display message
					if self == scenario.player_unit:
						text = 'You were'
					else:
						text = self.GetName() + ' was'
					text += ' destroyed by '
					if profile['attacker'] == scenario.player_unit:
						text += 'you.'
					else:
						text += profile['attacker'].GetName() + '.'
					ShowMessage(text)
					return

		# clear unresolved hits
		self.ap_hits_to_resolve = []
	
	
	# resolve FP on this unit if any
	def ResolveFP(self):
		if self.fp_to_resolve == 0: return
		
		#print('DEBUG: resolving ' + str(self.fp_to_resolve) + ' fp on ' + self.unit_id)
		
		# move to top of hex stack
		self.MoveToTopOfStack()
		scenario.UpdateUnitCon()
		
		# fp has a different type of effect on vehicles
		if self.GetStat('category') == 'Vehicle':
			
			# FUTURE: if vehicle has any unarmoured area, possible that it will be destroyed
			if self.GetStat('armour') is None:
				for (fp, score) in VEH_FP_TK:
					if fp <= self.fp_to_resolve:
						break
				
				if GetPercentileRoll() <= score:
					text = self.GetName() + ' was destroyed.'
					ShowMessage(text)
					self.DestroyMe()
				
				return
			
			# FUTURE: chance of minor damage to vehicle
			
			# check for crew wound - Player unit only
			# FUTURE: also apply to AI units?
			if self == scenario.player_unit:
				
				for position in self.positions_list:
					if position.crewman is None: continue
					position.crewman.DoWoundCheck(fp=self.fp_to_resolve)
				
			self.fp_to_resolve = 0
			return
		
		# calculate base chance of destruction
		base_chance = RESOLVE_FP_BASE_CHANCE
		for i in range(2, self.fp_to_resolve + 1):
			base_chance += RESOLVE_FP_CHANCE_STEP * (RESOLVE_FP_CHANCE_MOD ** (i-1)) 
		
		# TODO: calculate modifiers
		
		# restrict final chances
		base_chance = RestrictChance(base_chance)
		
		#print('DEBUG: chance to destroy: ' + str(base_chance) + '%')
		
		# roll for effect
		roll = GetPercentileRoll()
		
		if roll <= base_chance:
			text = self.GetName() + ' was destroyed.'
			ShowMessage(text)
			self.DestroyMe()
		else:
			# pin test
			self.PinTest(self.fp_to_resolve)
		
		self.fp_to_resolve = 0
	
	
	# do a morale check for this unit to recover from Broken or Pinned status
	def MoraleCheck(self, modifier):
		
		chance = MORALE_CHECK_BASE_CHANCE + modifier
		
		# TODO: apply terrain modifiers
		
		# TODO: check for leader skill
		
		chance = RestrictChance(chance)
		
		roll = GetPercentileRoll()
		if roll <= chance:
			return True
		return False
	
	
	# do a pin test on this unit
	def PinTest(self, fp):
		
		# already pinned, no further effect
		if self.pinned: return
		
		chance = float(fp) * 5.0
		chance = RestrictChance(chance)
		roll = GetPercentileRoll()
		if roll <= chance:
			self.PinMe()
	
	
	# pin this unit
	def PinMe(self):
		self.pinned = True
		self.acquired_target = None
		scenario.UpdateUnitCon()
		scenario.UpdateScenarioDisplay()
		ShowMessage(self.GetName() + ' is now Pinned.')
	
	
	# destroy this unit and remove it from the game
	def DestroyMe(self):
		
		# check for debug flag
		if self == scenario.player_unit and DEBUG:
			if session.debug['Player Immortality']:
				ShowMessage('Debug powers will save you from death!')
				self.ap_hits_to_resolve = []
				return
		
		if self.GetStat('category') == 'Vehicle':
			PlaySoundFor(self, 'vehicle_explosion')
		
		# set flag
		self.alive = False
		
		# remove from hex stack
		map_hex = scenario.hex_dict[(self.hx, self.hy)]
		if self in map_hex.unit_stack:
			map_hex.unit_stack.remove(self)
			
		# remove from scenario unit list
		if self in scenario.units:
			scenario.units.remove(self)
		
		# remove from active target and target list
		if scenario.selected_target == self:
			scenario.selected_target = None
		if self in scenario.target_list:
			scenario.target_list.remove(self)
		
		# award VP to player for unit destruction
		if self.owning_player == 1:
			campaign.AwardVP(campaign_day.unit_destruction_vp[self.GetStat('category')])
			
			# add to day records
			category = self.GetStat('category')
			if category == 'Vehicle':
				campaign_day.records['Vehicles Destroyed'] += 1
			elif category == 'Gun':
				campaign_day.records['Guns Destroyed'] += 1
			elif category == 'Infantry':
				campaign_day.records['Infantry Destroyed'] += 1
		
		# if player unit has been destroyed
		if self == scenario.player_unit:
			# set end-scenario flag
			scenario.finished = True
		
			# do bail-out procedure
			scenario.PlayerBailOut()
		
		scenario.UpdateUnitCon()
		scenario.UpdateScenarioDisplay()
	
	
	# attempt to recover from pinned status at the end of an activation
	def DoRecoveryRoll(self):
		if not self.pinned: return
		if not self.MoraleCheck(0):
			return
		self.pinned = False
		scenario.UpdateUnitCon()
		scenario.UpdateScenarioDisplay()
		ShowMessage(self.GetName() + ' is no longer Pinned.')



# MapHex: a single hex on the scenario map
class MapHex:
	def __init__(self, hx, hy):
		self.hx = hx
		self.hy = hy
		self.unit_stack = []					# list of units present in this map hex



# Scenario: represents a single battle encounter
class Scenario:
	def __init__(self, cd_map_hex):
		
		self.init_complete = False			# flag to say that scenario has already been set up
		self.cd_map_hex = cd_map_hex			# Campaign Day map hex where this scenario is taking place
		self.finished = False				# Scenario has ended, returning to Campaign Day map
		
		# generate hex map: single hex surrounded by 4 hex rings. Final ring is not normally
		# part of play and stores units that are coming on or going off of the map proper
		# also store pointers to hexes in a dictionary for quick access
		self.map_hexes = []
		self.hex_dict = {}
		for r in range(0, 5):
			for (hx, hy) in GetHexRing(0, 0, r):
				self.map_hexes.append(MapHex(hx,hy))
				self.hex_dict[(hx,hy)] = self.map_hexes[-1]
		
		# dictionary of console cells covered by map hexes
		self.hex_map_index = {}
		self.BuildHexmapDict()
		
		# attack console display is active
		self.attack_con_active = False
		
		self.units = []						# list of units in play
		
		# turn and phase information
		self.current_turn = 1					# current scenario turn
		self.active_player = 0					# currently active player (0 is human player)
		self.phase = PHASE_COMMAND				# current phase
		self.advance_phase = False				# flag for input loop to automatically advance to next phase/turn
		
		self.player_pivot = 0					# keeps track of player unit pivoting
		
		# player targeting
		self.target_list = []					# list of possible player targets
		self.selected_weapon = None				# player's currently selected weapon
		self.selected_target = None				# player's current selected target
		
		self.selected_position = 0				# index of selected position in player unit
	
	
	# check for end of scenario and set flag if it has ended
	def CheckForEnd(self):
		all_enemies_dead = True
		for unit in self.units:
			if unit.owning_player == 1 and unit.alive:
				if GetHexDistance(0, 0, unit.hx, unit.hy) > 3: continue
				all_enemies_dead = False
				break
		if all_enemies_dead:
			ShowMessage('Victory! No enemy units remain in this area.')
			self.finished = True
			return
		
		# check for loss of player crew
		all_crew_dead = True
		for position in self.player_unit.positions_list:
			if position.crewman is None: continue
			if position.crewman.status != 'Dead':
				all_crew_dead = False
				break
		
		if all_crew_dead:
			ShowMessage('Your crew is all dead.')
			scenario.player_unit.DestroyMe()
			return
		
		# check for end of campaign day
		campaign_day.CheckForEndOfDay()
		if campaign_day.ended:
			ShowMessage('The campaign day is over.')
			self.finished = True
			return
	
	
	# go through procedure for player crew bailing out of tank
	def PlayerBailOut(self):
		
		# (re)draw the bail-out console and display on screen
		def UpdateBailOutConsole(skip_ko=False):
			
			libtcod.console_clear(con)
			
			# window title
			libtcod.console_set_default_background(con, libtcod.light_red)
			libtcod.console_rect(con, 0, 2, WINDOW_WIDTH, 5, True, libtcod.BKGND_SET)
			libtcod.console_set_default_foreground(con, libtcod.black)
			libtcod.console_print_ex(con, WINDOW_XM, 4, libtcod.BKGND_NONE,
				libtcod.CENTER, 'BAILING OUT')
			
			libtcod.console_set_default_foreground(con, libtcod.white)
			libtcod.console_set_default_background(con, libtcod.black)
			
			
			# display player unit
			libtcod.console_set_default_foreground(con, libtcod.lighter_blue)
			libtcod.console_print(con, 33, 9, self.player_unit.unit_id)
			libtcod.console_set_default_foreground(con, libtcod.light_grey)
			libtcod.console_print(con, 33, 10, self.player_unit.GetStat('class'))
			libtcod.console_set_default_background(con, PORTRAIT_BG_COL)
			libtcod.console_rect(con, 33, 11, 25, 8, True, libtcod.BKGND_SET)
			portrait = self.player_unit.GetStat('portrait')
			if portrait is not None:
				libtcod.console_blit(LoadXP(portrait), 0, 0, 0, 0, con, 33, 11)
			libtcod.console_set_default_foreground(con, libtcod.white)
			if self.player_unit.unit_name != '':
				libtcod.console_print(con, 33, 11, self.player_unit.unit_name)
			
			# roll column headers
			libtcod.console_print(con, 34, 21, 'KO Wound')
			libtcod.console_print(con, 49, 21, 'Bail Out')
			libtcod.console_print(con, 74, 21, 'Rescue')
			
			# list of crew
			x = 2
			y = 24
			
			for position in self.player_unit.positions_list:
				
				libtcod.console_set_default_foreground(con, libtcod.light_blue)
				libtcod.console_print(con, x, y, position.name)
				libtcod.console_set_default_foreground(con, libtcod.white)
				libtcod.console_print_ex(con, x+24, y, libtcod.BKGND_NONE, 
					libtcod.RIGHT, position.location)
				
				if position.crewman is None:
					libtcod.console_print(con, x, y+1, 'Empty')
				else:
					text = position.crewman.first_name[0] + '. ' + position.crewman.last_name
					libtcod.console_print(con, x, y+1, text.encode('IBM850'))
					
					if position.crewman.wound != '':
						libtcod.console_put_char_ex(con, x+21, y+1,
							position.crewman.wound[0], libtcod.black,
							libtcod.red)
					
					if position.crewman.ce:
						text = 'CE'
					else:
						text = 'BU'
					libtcod.console_print_ex(con, x+24, y+1, libtcod.BKGND_NONE, libtcod.RIGHT, text)
				
					# display current status
					if position.crewman.status != '':
						if position.crewman.status == 'Dead':
							libtcod.console_set_default_foreground(crew_con, libtcod.dark_grey)
						elif position.crewman.status == 'Unconscious':
							libtcod.console_set_default_foreground(crew_con, libtcod.grey)
						elif position.crewman.status == 'Stunned':
							libtcod.console_set_default_foreground(crew_con, libtcod.light_grey)
						libtcod.console_print_ex(con, x+24, y+2, libtcod.BKGND_NONE, libtcod.RIGHT, 
							position.crewman.status)
				
				y += 4
			
			# vertical dividing line
			libtcod.console_set_default_foreground(con, libtcod.light_grey)
			for y in range(23, 54):
				libtcod.console_put_char(con, 29, y, 250)
			
			libtcod.console_set_default_foreground(con, libtcod.white)
			libtcod.console_set_default_background(con, libtcod.black)
			
			libtcod.console_blit(con, 0, 0, 0, 0, 0, 0, 0)
			
		
		# draw screen for first time and pause
		UpdateBailOutConsole()
		
		Wait(120)
		
		# do roll procedures
		
		if not skip_ko:
		
			# initial tank KO wound
			libtcod.console_set_default_foreground(con, libtcod.light_grey)
			y = 20
			for position in self.player_unit.positions_list:
				
				y += 4
				
				if position.crewman is None: continue
				if position.crewman.status == 'Dead': continue
				
				# FUTURE: modify by location on tank penetrated
				result = position.crewman.DoWoundCheck(show_messages=False)
				
				if result is None:
					text = 'OK'
				else:
					text = result
				
				lines = wrap(text, 14)
				y1 = y
				for line in lines:
					libtcod.console_print(con, 32, y1, line)
					y1 += 1
				
				libtcod.console_blit(con, 0, 0, 0, 0, 0, 0, 0)
				libtcod.console_flush()
				Wait(100)
			
			Wait(100)
		
		# bail out roll
		y = 20
		for position in self.player_unit.positions_list:
			
			y += 4
			
			if position.crewman is None: continue
			
			if position.crewman.status in ['Unconscious', 'Dead']:
				text = 'N/A'
			else:
			
				modifier = 0.0
				if position.crewman.status == 'Stunned':
					modifier += 5.0
				
				if position.crewman.wound == 'Critical':
					modifier += 15.0
				elif position.crewman.wound == 'Serious':
					modifier += 10.0
				
				if not position.hatch:
					modifier += 15.0
				elif position.crewman.ce:
					modifier -= 20.0
				
				roll = GetPercentileRoll()
				
				# unmodified 97.0-100.0 always fail, otherwise modifier is applied
				if roll < 97.0:
					roll += modifier
				
				if roll <= 97.0:
					position.crewman.bailed_out = True
					text = 'Bailed'
				else:
					text = 'Failed'
			
			libtcod.console_print(con, 49, y, text)
			libtcod.console_blit(con, 0, 0, 0, 0, 0, 0, 0)
			libtcod.console_flush()
			Wait(100)
		
		# tank burn up roll
		# FUTURE: apply modifiers
		chance = 80.0
		burns = False
		
		roll = GetPercentileRoll()
		
		if roll <= chance:
			libtcod.console_set_default_foreground(con, libtcod.light_red)
			libtcod.console_print(con, 60, 21, 'Tank Burns')
			burns = True
		else:
			libtcod.console_set_default_foreground(con, libtcod.light_grey)
			libtcod.console_print(con, 60, 21, 'No Burn-up')
		
		if burns:
			y = 20
			for position in self.player_unit.positions_list:
				y += 4
				if position.crewman is None: continue
				if position.crewman.bailed_out: continue
				
				libtcod.console_print(con, 60, y, 'Vulnerable')
		
		libtcod.console_blit(con, 0, 0, 0, 0, 0, 0, 0)
		libtcod.console_flush()
		Wait(100)
		
		libtcod.console_set_default_foreground(con, libtcod.light_grey)
		
		# rescue rolls and final injuries
		y = 20
		for position in self.player_unit.positions_list:
			
			y += 4
			
			if position.crewman is None: continue
			
			if position.crewman.bailed_out: continue
			
			text = 'Rescued'
			
			if burns:
			
				# check for wound from burn-up before rescue
				result = position.crewman.DoWoundCheck(roll_modifier=20.0, show_messages=False)
				
				if result:
					text = result
			
			lines = wrap(text, 14)
			y1 = y
			for line in lines:
				libtcod.console_print(con, 74, y1, line)
				y1 += 1
			
			libtcod.console_blit(con, 0, 0, 0, 0, 0, 0, 0)
			libtcod.console_flush()
			Wait(100)
		
		libtcod.console_set_default_foreground(con, ACTION_KEY_COL)
		libtcod.console_print(con, 41, 56, 'Enter')
		libtcod.console_set_default_foreground(con, libtcod.white)
		libtcod.console_print(con, 47, 56, 'Continue')
		
		libtcod.console_blit(con, 0, 0, 0, 0, 0, 0, 0)
		libtcod.console_flush()
		
		exit_menu = False
		while not exit_menu:
			
			if libtcod.console_is_window_closed(): sys.exit()
			libtcod.console_flush()
			keypress = GetInputEvent()
			if not keypress: continue
			
			if key.vk == libtcod.KEY_ENTER:
				exit_menu = True
				continue
		
	
	# spawn enemy units on the hex map
	# FUTURE: will pull more data from the campaign day and campaign objects
	def SpawnEnemyUnits(self):
		
		# pointers to data for class odds and unit type list from campaign object
		
		class_odds = campaign.today['enemy_unit_class_odds']
		unit_type_list = campaign.stats['enemy_unit_list']
		
		# load unit stats for reference from JSON file
		with open(DATAPATH + 'unit_type_defs.json', encoding='utf8') as data_file:
			unit_types = json.load(data_file)
		
		# determine initial number of enemy units to spawn: 1-4
		num_units = 4
		for i in range(3):
			if libtcod.random_get_int(0, 0, 10) >= self.cd_map_hex.enemy_strength:
				num_units -= 1
		
		enemy_unit_list = []
		while len(enemy_unit_list) < num_units:
			
			if libtcod.console_is_window_closed(): sys.exit()
		
			# choose a random unit class, rolling against its ubiquity factor
			unit_class = None
			while unit_class is None:
				k, value = choice(list(class_odds.items()))
				if GetPercentileRoll() <= float(value):
					unit_class = k
			
			# FUTURE: if class unit type has already been set, use that one instead
			
			# choose a random unit type
			type_list = []
			for unit_id in unit_type_list:
				# unrecognized unit id
				if unit_id not in unit_types: continue
				# not the right class
				if unit_types[unit_id]['class'] != unit_class: continue
				type_list.append(unit_id)
			
			# no units of the correct class found
			if len(type_list) == 0: continue
			
			# select unit type
			selected_unit_id = None
			
			while selected_unit_id is None:
				
				# only one choice in class
				if len(type_list) == 1:
					selected_unit_id = type_list[0]
					continue
				
				unit_id = choice(type_list)
				# no ubiquity rating, select automatically
				if 'ubiquity' not in unit_types[unit_id]:
					selected_unit_id = unit_id
					continue
				
				# roll for ubiquity rating
				if GetPercentileRoll() <= float(unit_types[unit_id]['ubiquity']):
					selected_unit_id = unit_id
					continue
			
			# add the final selected unit id to list to spawn
			enemy_unit_list.append(selected_unit_id)
		
		# spawn one unit per unit id in the list
		for unit_id in enemy_unit_list:
	
			# determine spawn location
			distance = libtcod.random_get_int(0, 1, 3)
			
			if distance == 1:
				if GetPercentileRoll() <= 65.0:
					distance += 1
			if unit_types[unit_id]['category'] == 'Infantry':
				if GetPercentileRoll() <= 75.0:
					distance -= 1
			elif unit_types[unit_id]['category'] == 'Vehicle':
				if GetPercentileRoll() <= 60.0:
					distance += 1
			
			if distance < 1:
				distance = 1
			elif distance > 3:
				distance = 3
			
			hex_list = GetHexRing(0, 0, distance)
			shuffle(hex_list)
			
			# choose a random hex in which to spawn
			for (hx, hy) in hex_list:
				# make it less likely that enemy units will spawni behind the player
				if GetDirectionToward(hx, hy, 0, 0) in [5, 0, 1]:
					if GetPercentileRoll() <= 75.0: continue
				break
			
			# create the unit
			unit = Unit(unit_id)
			unit.owning_player = 1
			unit.nation = campaign.today['enemy_nation']
			unit.ai = AI(unit)
			unit.GenerateNewPersonnel()
			unit.SpawnAt(hx, hy)
			if unit.GetStat('category') == 'Gun':
				unit.deployed = True
			campaign.enemy_units.append(unit)
			
			# set facing if any toward player
			direction = GetDirectionToward(unit.hx, unit.hy, 0, 0)
			if unit.GetStat('category') != 'Infantry':
				unit.facing = direction
			
			# turreted vehicle
			if 'turret' in unit.stats:
				unit.turret_facing = direction
	
	
	# do an artillery bombardment against enemy units
	def ArtilleryAttack(self):
		
		# display bombardment animation (TEMP)
		for i in range(7):
			map_hex = choice(self.map_hexes)
			if GetHexDistance(0, 0, map_hex.hx, map_hex.hy) > 3: continue
			if map_hex.hx == 0 and map_hex.hy == 0: continue
			(x, y) = self.PlotHex(map_hex.hx, map_hex.hy)
			
			PlaySoundFor(None, 'he_explosion')
			# show animation
			# FUTURE: use animation console
			for i in range(18):
				col = choice([libtcod.red, libtcod.yellow, libtcod.black])
				libtcod.console_set_default_foreground(0, col)
				libtcod.console_put_char(0, x+32, y+9, 42)
				libtcod.console_flush()
				Wait(4)
			libtcod.console_blit(con, 0, 0, 0, 0, 0, 0, 0)
			libtcod.console_flush()
		
		# spawn gun unit and determine effective FP
		unit_id = choice(campaign.stats['player_arty_support'])
		gun_unit = Unit(unit_id)
		gun_calibre = int(gun_unit.weapon_list[0].GetStat('calibre'))
		
		# determine effective fp and base AP chance for gun
		for (calibre, effective_fp) in HE_FP_EFFECT:
			if calibre <= gun_calibre:
				break
		for (calibre, ap_chance) in HE_AP_CHANCE:
			if calibre <= gun_calibre:
				break
		
		# roll for possible hit against each enemy unit
		results = False
		for target in self.units:
			
			if target.owning_player == 0: continue
			if not target.alive: continue
			
			# calculate base effect chance
			if target.GetStat('category') == 'Vehicle':
				chance = VEH_FP_BASE_CHANCE
			else:
				chance = INF_FP_BASE_CHANCE
			for i in range(2, effective_fp + 1):
				chance += FP_CHANCE_STEP * (FP_CHANCE_STEP_MOD ** (i-1)) 
			
			# FUTURE: apply modifiers here
			
			chance = round(chance, 2)
			roll = GetPercentileRoll()
			
			# no effect
			if roll > chance:
				continue
			
			results = True
			
			# infantry or gun target hit
			if target.GetStat('category') in ['Infantry', 'Gun']:
				
				# critical hit modifier
				if roll <= 3.0:
					target.fp_to_resolve += (effective_fp * 2)
				else:
					target.fp_to_resolve += effective_fp
				
				if not target.spotted:
					target.hit_by_fp = True
				
				ShowMessage(target.GetName() + ' was hit by artillery attack')
			
			# vehicle hit
			elif target.GetStat('category') == 'Vehicle':
				
				# determine location hit - use side locations and modify later
				# for aerial attack
				if GetPercentileRoll() <= 50.0:
					hit_location = 'hull_side'
				else:
					hit_location = 'turret_side'
				
				# TODO: direct hit vs. near miss
				
				# start with base AP chance
				chance = ap_chance
				
				# apply target armour modifier
				armour = target.GetStat('armour')
				if armour is not None:
					if armour[hit_location] != '-':
						target_armour = int(armour[hit_location])
						if target_armour >= 0:
						
							modifier = -9.0
							for i in range(target_armour - 1):
								modifier = modifier * 1.8
							
							chance += modifier
							
							# apply critical hit modifier if any
							if roll <= 3.0:
								modifier = round(abs(modifier) * 0.8, 2)
								chance += modifier
				
				# calculate final chance of AP and do roll
				chance = RestrictChance(chance)
				roll = GetPercentileRoll()
				
				# no penetration
				if roll > chance:
					ShowMessage(target.GetName() + ' was hit by artillery attack but is unharmed.')
					if not target.spotted:
						target.hit_by_fp = True
					continue
				
				# penetrated
				target.DestroyMe()
				ShowMessage(target.GetName() + ' was destroyed by artillery attack')
		
		if not results:
			ShowMessage('Artillery attack had no effect.')
	
	
	# attempt an air attack against the support attack target hex
	def AirAttack(self):
		
		# roll for number of planes
		roll = libtcod.random_get_int(0, 1, 10)
		if roll <= 5:
			num_planes = 1
		elif roll <= 8:
			num_planes = 2
		else:
			num_planes = 3
		
		# determine type of plane
		plane_id = choice(campaign.stats['player_air_support'])
		
		# display message
		text = str(num_planes) + ' ' + plane_id + ' arrive'
		if num_planes == 1: text += 's'
		text += ' for an attack.'
		ShowMessage(text)
		
		# create plane units
		plane_unit_list = []
		for i in range(num_planes):
			plane_unit_list.append(Unit(plane_id))
		
		# determine calibre for bomb attack
		for weapon in plane_unit_list[0].weapon_list:
			if weapon.stats['name'] == 'Bombs':
				bomb_calibre = int(weapon.stats['calibre'])
				break
		
		# determine effective fp
		for (calibre, effective_fp) in HE_FP_EFFECT:
			if calibre <= bomb_calibre:
				break
		
		# build target list
		target_list = []
		for unit in self.units:
			if not unit.alive: continue
			if unit.owning_player == 0: continue
			target_list.append(unit)
		
		# do one attack per plane
		results = False
		for unit in plane_unit_list:
			
			if len(target_list) == 0:
				ShowMessage('No possible targets, calling off atttack.')
				return
			
			# select target
			target = choice(target_list)
		
			# determine attack direction and starting position
			(x, y) = self.PlotHex(target.hx, target.hy)
			(x2, y2) = (x, y)
		
			#x = x2
			if y2 <= 30:
				y1 = y2 + 20
				if y1 > 51: y1 = 51
				y2 += 1
				direction = -1
			else:
				y1 = y2 - 20
				if y1 < 9: y1 = 9
				y2 -= 3
				direction = 1
			
			# create and draw plane console
			temp_con = libtcod.console_new(3, 3)
			libtcod.console_set_default_background(temp_con, libtcod.black)
			libtcod.console_set_default_foreground(temp_con, libtcod.light_grey)
			libtcod.console_clear(temp_con)
			
			libtcod.console_put_char(temp_con, 0, 1, chr(196))
			libtcod.console_put_char(temp_con, 1, 1, chr(197))
			libtcod.console_put_char(temp_con, 2, 1, chr(196))
			if direction == -1:
				libtcod.console_put_char(temp_con, 1, 2, chr(193))
			else:
				libtcod.console_put_char(temp_con, 1, 0, chr(194))
			
			PlaySoundFor(None, 'plane_incoming')
			
			# animate plane movement toward target hex
			for yi in range(y1, y2, direction):
				if libtcod.console_is_window_closed(): sys.exit()
				libtcod.console_blit(con, 0, 0, 0, 0, 0, 0, 0)
				libtcod.console_blit(temp_con, 0, 0, 0, 0, 0, x+31, yi+8, 1.0, 0.0)
				libtcod.console_flush()
				Wait(8)
			
			PlaySoundFor(None, 'stuka_divebomb')
			
			# wait for sound effect to finish
			if config['ArmCom2'].getboolean('sounds_enabled'):
				Wait(100)
			
			# bomb animation
			for i in range(24):
				col = choice([libtcod.red, libtcod.yellow, libtcod.black])
				libtcod.console_set_default_foreground(0, col)
				libtcod.console_put_char(0, x+32, y+9, 42)
				libtcod.console_flush()
				Wait(4)
			libtcod.console_set_default_foreground(0, libtcod.white)
			libtcod.console_blit(con, 0, 0, 0, 0, 0, 0, 0)
			libtcod.console_flush()
		
			# calculate basic to-effect score required
			if not target.spotted:
				chance = PF_BASE_CHANCE[0][1]
			else:
				if target.GetStat('category') == 'Vehicle':
					chance = PF_BASE_CHANCE[0][0]
				else:
					chance = PF_BASE_CHANCE[0][1]
		
			# target size modifier
			size_class = target.GetStat('size_class')
			if size_class is not None:
				if size_class != 'Normal':
					chance += PF_SIZE_MOD[size_class]
			
			chance = RestrictChance(chance)
			roll = GetPercentileRoll()
			
			if roll > chance: continue
			
			# hit
			results = True
			
			# infantry or gun target
			if target.GetStat('category') in ['Infantry', 'Gun']:
				
				# critical hit modifier
				if roll <= 3.0:
					target.fp_to_resolve += (effective_fp * 2)
				else:
					target.fp_to_resolve += effective_fp
				
				if not target.spotted:
					target.hit_by_fp = True
				
				ShowMessage(target.GetName() + ' was hit by air attack')
			
			# vehicle hit
			elif target.GetStat('category') == 'Vehicle':
				
				# determine location hit - use side locations and modify later
				# for aerial attack
				if GetPercentileRoll() <= 50.0:
					hit_location = 'hull_side'
				else:
					hit_location = 'turret_side'
				
				# determine base penetration chance
				for (calibre, chance) in HE_AP_CHANCE:
					if calibre <= bomb_calibre:
						break
				
				# TODO: direct hit vs. near miss
				
				# target armour modifier
				armour = target.GetStat('armour')
				if armour is not None:
					if armour[hit_location] != '-':
						target_armour = int(armour[hit_location])
						if target_armour >= 0:
						
							modifier = -9.0
							for i in range(target_armour - 1):
								modifier = modifier * 1.8
							
							chance += modifier
							
							# apply critical hit modifier if any
							if roll <= 3.0:
								modifier = round(abs(modifier) * 0.8, 2)
								chance += modifier
				
				# calculate final chance
				chance = RestrictChance(chance)
				
				# do AP roll
				roll = GetPercentileRoll()
				
				# no penetration
				if roll > chance:
					ShowMessage(target.GetName() + ' was unaffected by air attack')
					continue
				
				# penetrated
				target.DestroyMe()
				ShowMessage(target.GetName() + ' was destroyed by air attack')
				
				target_list.remove(target)
				
		if not results:
			ShowMessage('Air attack had no effect.')
		
		# clean up
		libtcod.console_blit(con, 0, 0, 0, 0, 0, 0, 0)
		libtcod.console_flush()
		del temp_con
	
	
	# given a combination of an attacker, weapon, and target, see if this would be a
	# valid attack; if not, return a text description of why not
	# if ignore_facing is true, we don't check whether weapon is facing correct direction
	def CheckAttack(self, attacker, weapon, target, ignore_facing=False):
		
		# check that proper crew command has been set if player is attacking
		if attacker == self.player_unit:
			
			# FUTURE: move this check to weapon object and use in
			# advance phase to skip shooting phase automatically
			position_list = weapon.GetStat('fired_by')
			if position_list is None:
				return 'No positions to fire this weapon'
			
			if weapon.GetStat('type') == 'Gun':
				command_req = 'Operate Gun'
			elif weapon.GetStat('type') in MG_WEAPONS:
				command_req = 'Operate MG'
			else:
				return 'Unknown weapon type!'
				
			crewman_found = False
			for position in position_list:
				crewman = attacker.GetPersonnelByPosition(position)
				if crewman is None: continue
				if crewman.current_cmd != command_req: continue
				crewman_found = True
				break
			
			if not crewman_found:
				return 'No crewman operating this weapon'
		
		# check that weapon hasn't already fired
		if weapon.fired:
			return 'Weapon has already fired this turn'
		
		# if we're not ignoring facing,
		# check that target is in covered hexes and range
		if not ignore_facing:
			if (target.hx, target.hy) not in weapon.covered_hexes:
				return "Target not in weapon's covered arc"
		
		# check that current ammo is available and this ammo would affect the target
		if weapon.GetStat('type') == 'Gun':
			
			if weapon.ammo_type is None:
				return 'No ammo loaded'
			if weapon.ammo_stores[weapon.ammo_type] == 0:
				return 'No more ammo of the selected type'
			if weapon.ammo_type == 'AP' and target.GetStat('category') != 'Vehicle':
				return 'AP has no effect on target'
		
		# check firing group restrictions
		for weapon2 in attacker.weapon_list:
			if weapon2 == weapon: continue
			if not weapon2.fired: continue
			if weapon2.GetStat('firing_group') == weapon.GetStat('firing_group'):
				return 'A weapon on this mount has already fired'
		
		# check for hull-mounted weapons blocked by HD status
		if len(attacker.hull_down) > 0:
			mount = weapon.GetStat('mount')
			if mount is not None:
				if mount == 'Hull':
					if GetDirectionToward(attacker.hx, attacker.hy, target.hx, target.hy) in attacker.hull_down:
						return 'Weapon blocked by HD status'
			
		# attack can proceed
		return ''
	
	
	# generate a profile for a given attack
	# if pivot or turret_rotate are set to True or False, will override actual attacker status
	def CalcAttack(self, attacker, weapon, target, pivot=False, turret_rotate=False):
		
		profile = {}
		profile['attacker'] = attacker
		profile['weapon'] = weapon
		profile['ammo_type'] = weapon.ammo_type
		profile['target'] = target
		profile['result'] = ''		# placeholder for text rescription of result
		
		
		# determine attack type
		weapon_type = weapon.GetStat('type')
		if weapon_type == 'Gun':
			profile['type'] = 'Point Fire'
		elif weapon_type == 'Small Arms' or weapon_type in MG_WEAPONS:
			profile['type'] = 'Area Fire'
			profile['effective_fp'] = 0		# placeholder for effective fp
		else:
			print('ERROR: Weapon type not recognized: ' + weapon.stats['name'])
			return None
		
		# calculate distance to target
		distance = GetHexDistance(attacker.hx, attacker.hy, target.hx, target.hy)
		
		# list of modifiers
		# [maximum displayable modifier description length is 18 characters]
		
		modifier_list = []
		
		# point fire attacks (eg. large guns)
		if profile['type'] == 'Point Fire':
			
			# calculate base success chance
			
			# possible to fire HE at unspotted targets
			if not target.spotted:
				# use infantry chance as base chance
				profile['base_chance'] = PF_BASE_CHANCE[distance][1]
			else:
				if target.GetStat('category') == 'Vehicle':
					profile['base_chance'] = PF_BASE_CHANCE[distance][0]
				else:
					profile['base_chance'] = PF_BASE_CHANCE[distance][1]
		
			# calculate modifiers and build list of descriptions
			
			# description max length is 19 chars
			
			# attacker is moving
			if attacker.moving:
				modifier_list.append(('Attacker Moving', -60.0))
			
			# attacker pivoted
			elif pivot or attacker.facing != attacker.previous_facing:
				modifier_list.append(('Attacker Pivoted', -35.0))
			
			# player or player squad member attacker pivoted
			elif self.player_pivot != 0 and (attacker == scenario.player_unit or attacker in scenario.player_unit.squad):
				modifier_list.append(('Attacker Pivoted', -35.0))

			# weapon has turret rotated
			elif weapon.GetStat('mount') == 'Turret':
				if turret_rotate or attacker.turret_facing != attacker.previous_turret_facing:
					modifier_list.append(('Turret Rotated', -20.0))
			
			# attacker pinned
			if attacker.pinned:
				modifier_list.append(('Attacker Pinned', -60.0))
			
			# precipitation
			if campaign_day.weather['Precipitation'] == 'Rain':
				modifier_list.append(('Rain', -10.0 * float(distance)))
			elif campaign_day.weather['Precipitation'] == 'Heavy Rain':
				modifier_list.append(('Heavy Rain', -20.0 * float(distance)))
			
			
			# unspotted target
			if not target.spotted:
				modifier_list.append(('Unspotted Target', -20.0))
			
			# spotted target
			else:
			
				# acquired target
				if attacker.acquired_target is not None:
					(ac_target, level) = attacker.acquired_target
					if ac_target == target:
						if not level:
							mod = AC_BONUS[0]
						else:
							mod = AC_BONUS[1]
						modifier_list.append(('Acquired Target', mod))
				
				# target vehicle moving
				if target.moving and target.GetStat('category') == 'Vehicle':
					modifier_list.append(('Target Moving', -30.0))
				
				# target size
				size_class = target.GetStat('size_class')
				if size_class is not None:
					if size_class != 'Normal':
						text = size_class + ' Target'
						mod = PF_SIZE_MOD[size_class]
						modifier_list.append((text, mod))
				
				# target terrain
				tem = target.GetTEM()
				if tem != 0.0:
					modifier_list.append((target.terrain, tem))
			
			# long / short-barreled gun
			long_range = weapon.GetStat('long_range')
			if long_range is not None:
				if long_range == 'S' and distance > 1:
					modifier_list.append(('Short Gun', -12.0))
				
				elif long_range == 'L' and distance > 1:
					modifier_list.append(('Long Gun', 12.0))
				
				elif long_range == 'LL':
					if distance == 1:
						modifier_list.append(('Long Gun', 12.0))
					elif distance >= 2:
						modifier_list.append(('Long Gun', 24.0))
			
			# smaller-calibre gun at longer range
			if weapon_type == 'Gun':
				calibre_mod = 0
				
				if weapon.stats['name'] == 'AT Rifle':
					calibre = 20
				else:
					calibre = int(weapon.stats['calibre'])
				
				if calibre <= 40 and distance >= 2:
					calibre_mod -= 1	
				
				if calibre <= 57:
					if distance == 2:
						calibre_mod -= 1
					elif distance == 3:
						calibre_mod -= 2
				if calibre_mod < 0:
					modifier_list.append(('Small Calibre', (8.0 * calibre_mod)))
		
		# area fire
		elif profile['type'] == 'Area Fire':
			
			# calculate base FP
			fp = int(weapon.GetStat('fp'))
			
			# point blank range multiplier
			if distance == 0:
				fp = fp * 2
			
			profile['base_fp'] = fp
			
			# calculate base effect chance
			if target.GetStat('category') == 'Vehicle':
				base_chance = VEH_FP_BASE_CHANCE
			else:
				base_chance = INF_FP_BASE_CHANCE
			for i in range(2, fp + 1):
				base_chance += FP_CHANCE_STEP * (FP_CHANCE_STEP_MOD ** (i-1)) 
			profile['base_chance'] = round(base_chance, 2)
			
			# store the rounded base chance so we can use it later for modifiers
			base_chance = profile['base_chance']
			
			# calculate modifiers
			
			# attacker moving
			if attacker.moving:
				mod = round(base_chance / 2.0, 2)
				modifier_list.append(('Attacker Moving', 0.0 - mod))
			
			# attacker pivoted
			elif attacker.facing != attacker.previous_facing:
				mod = round(base_chance / 3.0, 2)
				modifier_list.append(('Attacker Pivoted', 0.0 - mod))

			# player attacker pivoted
			elif attacker == scenario.player_unit and self.player_pivot != 0:
				mod = round(base_chance / 3.0, 2)
				modifier_list.append(('Attacker Pivoted', 0.0 - mod))

			# weapon turret rotated
			elif weapon.GetStat('mount') == 'Turret':
				if attacker.turret_facing != attacker.previous_turret_facing:
					mod = round(base_chance / 4.0, 2)
					modifier_list.append(('Turret Rotated', 0.0 - mod))
			
			# attacker pinned
			if attacker.pinned:
				mod = round(base_chance / 2.0, 2)
				modifier_list.append(('Attacker Pinned', 0.0 - mod))
			
			if not target.spotted:
				modifier_list.append(('Unspotted Target', -10.0))
			else:
			
				# target is infantry and moving
				if target.moving and target.GetStat('category') == 'Infantry':
					mod = round(base_chance / 2.0, 2)
					modifier_list.append(('Infantry Moving', mod))
				else:
					if target.GetStat('class') == 'Team':
						modifier_list.append(('Small Team', -20.0))
				
				# target size
				size_class = target.GetStat('size_class')
				if size_class is not None:
					if size_class != 'Normal':
						text = size_class + ' Target'
						mod = PF_SIZE_MOD[size_class]
						modifier_list.append((text, mod))
				
		# FUTURE: Commander directing fire
		
		# save the list of modifiers
		profile['modifier_list'] = modifier_list[:]
		
		# calculate total modifier
		total_modifier = 0.0
		for (desc, mod) in modifier_list:
			total_modifier += mod
		
		# calculate final chance of success
		profile['final_chance'] = RestrictChance(profile['base_chance'] + total_modifier)
		
		# calculate additional outcomes for Area Fire
		if profile['type'] == 'Area Fire':
			profile['full_effect'] = RestrictChance((profile['base_chance'] + 
				total_modifier) * FP_FULL_EFFECT)
			profile['critical_effect'] = RestrictChance((profile['base_chance'] + 
				total_modifier) * FP_CRIT_EFFECT)
		
		return profile
	
	
	# takes an attack profile and generates a profile for an armour penetration attempt
	def CalcAP(self, profile):
		
		profile['type'] = 'ap'
		modifier_list = []
		
		# create local pointers for convenience
		attacker = profile['attacker']
		weapon = profile['weapon']
		target = profile['target']
		
		# get location hit on target
		location = profile['location']
		# hull hit or target does not have rotatable turret
		if location == 'Hull' or target.turret_facing is None:
			turret_facing = False
		else:
			turret_facing = True
		
		facing = GetFacing(attacker, target, turret_facing=turret_facing)
		hit_location = (location + '_' + facing).lower()
		
		# generate a text description of location hit
		if location == 'Turret' and target.turret_facing is None:
			location = 'Upper Hull'
		profile['location_desc'] = location + ' ' + facing
		
		# calculate base chance of penetration
		if weapon.GetStat('name') == 'AT Rifle':
			base_chance = AP_BASE_CHANCE['AT Rifle']
		elif weapon.GetStat('type') in MG_WEAPONS:
			base_chance = AP_BASE_CHANCE['MG']
		else:
			gun_rating = weapon.GetStat('calibre')
			
			# HE hits have a much lower base chance
			if profile['ammo_type'] == 'HE':
				base_chance = weapon.GetBaseHEPenetrationChance()
			else:
				if weapon.GetStat('long_range') is not None:
					gun_rating += weapon.GetStat('long_range')
				if gun_rating not in AP_BASE_CHANCE:
					print('ERROR: No AP base chance found for: ' + gun_rating)
					return None
				base_chance = AP_BASE_CHANCE[gun_rating]
		
		profile['base_chance'] = base_chance
		
		# calculate modifiers
		
		# unarmoured targets use flat modifiers
		
		# FUTURE: check for unarmoured locations on otherwise armoured targets
		
		armour = target.GetStat('armour')
		if armour is None:
			
			if profile['result'] == 'CRITICAL HIT':
				modifier_list.append(('Critical Hit', 75.0))
			
			elif profile['ammo_type'] == 'HE':
				modifier_list.append(('Unarmoured Target', 25.0))
			
			# AP hits have a chance to punch right through
			else:
				modifier_list.append(('Unarmoured Target', -18.0))
			
		else:
		
			# calibre/range modifier - not applicable to HE and MG attacks
			if profile['ammo_type'] == 'AP' and weapon.GetStat('calibre') is not None:
				calibre = int(weapon.GetStat('calibre'))
				distance = GetHexDistance(attacker.hx, attacker.hy, target.hx, target.hy)
				
				if calibre <= 25:
					if distance == 0:
						modifier_list.append(('Close Range', 18.0))
					elif distance == 2:
						modifier_list.append(('Medium Range', -7.0))
					else:
						modifier_list.append(('Long Range', -18.0))
				elif calibre <= 57:
					if distance == 0:
						modifier_list.append(('Close Range', 7.0))
					elif distance == 2:
						modifier_list.append(('Medium Range', -7.0))
					else:
						modifier_list.append(('Long Range', -12.0))
				else:
					if distance == 0:
						modifier_list.append(('Close Range', 7.0))
					elif 2 <= distance <= 3:
						modifier_list.append(('Long Range', -7.0))
		
			# hit location is armoured
			if armour[hit_location] != '-':
				target_armour = int(armour[hit_location])
				if target_armour >= 0:
					modifier = -9.0
					for i in range(target_armour - 1):
						modifier = modifier * 1.8
					
					modifier_list.append(('Target Armour', modifier))
					
					# apply critical hit modifier if any
					if profile['result'] == 'CRITICAL HIT':
						modifier = round(abs(modifier) * 0.8, 2)
						modifier_list.append(('Critical Hit', modifier))
		
		# save the list of modifiers
		profile['modifier_list'] = modifier_list[:]
		
		# calculate total modifer
		total_modifier = 0.0
		for (desc, mod) in modifier_list:
			total_modifier += mod
		
		# calculate final chance of success
		profile['final_chance'] = RestrictChance(profile['base_chance'] + total_modifier)
		
		return profile
	
	
	# generate an attack console to display an attack or AP profile to the screen and prompt to proceed
	# does not alter the profile
	def DisplayAttack(self, profile):
		
		# don't display if player is not involved
		#if profile['attacker'] != self.player_unit and profile['target'] != self.player_unit:
		#	return
		
		libtcod.console_clear(attack_con)
		
		# display the background outline
		libtcod.console_blit(session.attack_bkg, 0, 0, 0, 0, attack_con, 0, 0)
		
		# window title
		libtcod.console_set_default_background(attack_con, libtcod.darker_blue)
		libtcod.console_rect(attack_con, 1, 1, 25, 1, False, libtcod.BKGND_SET)
		libtcod.console_set_default_background(attack_con, libtcod.black)
		
		# set flags on whether attacker/target is spotted
		
		attacker_spotted = True
		if profile['attacker'].owning_player == 1 and not profile['attacker'].spotted:
			attacker_spotted = False
		target_spotted = True
		if profile['target'].owning_player == 1 and not profile['target'].spotted:
			target_spotted = False
		
		if profile['type'] == 'ap':
			text = 'Armour Penetration'
		else:
			text = 'Ranged Attack'
		libtcod.console_print_ex(attack_con, 13, 1, libtcod.BKGND_NONE, libtcod.CENTER, text)
		
		# attacker portrait if any
		if profile['type'] in ['Point Fire', 'Area Fire']:
			
			libtcod.console_set_default_background(attack_con, PORTRAIT_BG_COL)
			libtcod.console_rect(attack_con, 1, 2, 25, 8, False, libtcod.BKGND_SET)
		
			# FUTURE: store portraits for every active unit type in session object
			if attacker_spotted:
				portrait = profile['attacker'].GetStat('portrait')
				if portrait is not None:
					libtcod.console_blit(LoadXP(portrait), 0, 0, 0, 0, attack_con, 1, 2)
		
		# attack description
		if profile['type'] == 'ap':
			text1 = profile['target'].GetName()
			if attacker_spotted:
				text2 = 'hit by ' + profile['weapon'].GetStat('name')
			else:
				text2 = 'hit'
			if profile['ammo_type'] is not None:
				text2 += ' (' + profile['ammo_type'] + ')'
			text3 = 'in ' + profile['location_desc']
		else:
			text1 = profile['attacker'].GetName()
			if attacker_spotted:
				text2 = 'firing ' + profile['weapon'].GetStat('name')
				if profile['weapon'].ammo_type is not None:
					text2 += ' ' + profile['weapon'].ammo_type
				text2 += ' at'
			else:
				text2 = 'firing at'
			text3 = profile['target'].GetName()
			
		libtcod.console_print_ex(attack_con, 13, 10, libtcod.BKGND_NONE, libtcod.CENTER, text1)
		libtcod.console_print_ex(attack_con, 13, 11, libtcod.BKGND_NONE, libtcod.CENTER, text2)
		libtcod.console_print_ex(attack_con, 13, 12, libtcod.BKGND_NONE, libtcod.CENTER, text3)
		
		# display target portrait if any
		libtcod.console_set_default_background(attack_con, PORTRAIT_BG_COL)
		libtcod.console_rect(attack_con, 1, 13, 25, 8, False, libtcod.BKGND_SET)
		
		# FUTURE: store portraits for every active unit type in session object
		if target_spotted:
			portrait = profile['target'].GetStat('portrait')
			if portrait is not None:
				libtcod.console_blit(LoadXP(portrait), 0, 0, 0, 0, attack_con, 1, 13)
		
		# base chance
		text = 'Base Chance '
		if profile['type'] == 'ap':
			text += 'to Penetrate'
		elif profile['type'] == 'Area Fire':
			text += 'of Effect'
		else:
			text += 'to Hit'
		libtcod.console_print_ex(attack_con, 13, 23, libtcod.BKGND_NONE, libtcod.CENTER, text)
		text = str(profile['base_chance']) + '%%'
		libtcod.console_print_ex(attack_con, 13, 24, libtcod.BKGND_NONE, libtcod.CENTER, text)
		
		# list of modifiers
		libtcod.console_set_default_background(attack_con, libtcod.darker_blue)
		libtcod.console_rect(attack_con, 1, 27, 25, 1, False, libtcod.BKGND_SET)
		libtcod.console_set_default_background(attack_con, libtcod.black)
		libtcod.console_print_ex(attack_con, 13, 27, libtcod.BKGND_NONE, libtcod.CENTER,
			'Modifiers')
		
		y = 29
		if len(profile['modifier_list']) == 0:
			libtcod.console_print_ex(attack_con, 13, y, libtcod.BKGND_NONE, libtcod.CENTER,
				'None')
		else:
			for (desc, mod) in profile['modifier_list']:
				# max displayable length is 17 chars
				libtcod.console_print(attack_con, 2, y, desc[:17])
				
				if mod > 0.0:
					col = libtcod.green
					text = '+'
				else:
					col = libtcod.red
					text = ''
				
				text += str(mod)
				
				libtcod.console_set_default_foreground(attack_con, col)
				libtcod.console_print_ex(attack_con, 24, y, libtcod.BKGND_NONE,
					libtcod.RIGHT, text)
				libtcod.console_set_default_foreground(attack_con, libtcod.white)
				
				y += 1
		
		# display final chance
		libtcod.console_set_default_background(attack_con, libtcod.darker_blue)
		libtcod.console_rect(attack_con, 1, 43, 25, 1, False, libtcod.BKGND_SET)
		libtcod.console_set_default_background(attack_con, libtcod.black)
		libtcod.console_print_ex(attack_con, 14, 43, libtcod.BKGND_NONE, libtcod.CENTER,
			'Final Chance')
		
		# display chance graph
		if profile['type'] == 'Area Fire':
			# area fire has partial, full, and critical outcomes possible
			
			# no effect
			libtcod.console_set_default_background(attack_con, libtcod.red)
			libtcod.console_rect(attack_con, 1, 46, 25, 3, False, libtcod.BKGND_SET)
			
			# partial effect
			libtcod.console_set_default_background(attack_con, libtcod.darker_green)
			x = int(ceil(25.0 * profile['final_chance'] / 100.0))
			libtcod.console_rect(attack_con, 1, 46, x, 3, False, libtcod.BKGND_SET)
			
			if profile['final_chance'] > profile['full_effect']:
				libtcod.console_print_ex(attack_con, 24, 46, libtcod.BKGND_NONE,
					libtcod.RIGHT, 'PART')
				text = str(profile['final_chance']) + '%%'
				libtcod.console_print_ex(attack_con, 24, 47, libtcod.BKGND_NONE,
					libtcod.RIGHT, text)
			
			# full effect
			libtcod.console_set_default_background(attack_con, libtcod.green)
			x = int(ceil(25.0 * profile['full_effect'] / 100.0))
			libtcod.console_rect(attack_con, 1, 46, x, 3, False, libtcod.BKGND_SET)
			
			if profile['full_effect'] > profile['critical_effect']:
				libtcod.console_print_ex(attack_con, 13, 46, libtcod.BKGND_NONE,
					libtcod.CENTER, 'FULL')
				text = str(profile['full_effect']) + '%%'
				libtcod.console_print_ex(attack_con, 13, 47, libtcod.BKGND_NONE,
					libtcod.CENTER, text)
			
			# critical effect
			libtcod.console_set_default_background(attack_con, libtcod.blue)
			x = int(ceil(25.0 * profile['critical_effect'] / 100.0))
			libtcod.console_rect(attack_con, 1, 46, x, 3, False, libtcod.BKGND_SET)
			libtcod.console_print(attack_con, 2, 46, 'CRIT')
			text = str(profile['critical_effect']) + '%%'
			libtcod.console_print(attack_con, 2, 47, text)
			
		else:
			
			# miss
			libtcod.console_set_default_background(attack_con, libtcod.red)
			libtcod.console_rect(attack_con, 1, 46, 25, 3, False, libtcod.BKGND_SET)
			
			# hit
			x = int(ceil(25.0 * profile['final_chance'] / 100.0))
			libtcod.console_set_default_background(attack_con, libtcod.green)
			libtcod.console_rect(attack_con, 1, 46, x, 3, False, libtcod.BKGND_SET)
			
			# critical hit band
			libtcod.console_set_default_foreground(attack_con, libtcod.blue)
			for y in range(46, 49):
				libtcod.console_put_char(attack_con, 1, y, 221)
			
			# critical miss band
			libtcod.console_set_default_foreground(attack_con, libtcod.dark_grey)
			for y in range(46, 49):
				libtcod.console_put_char(attack_con, 25, y, 222)
		
			libtcod.console_set_default_foreground(attack_con, libtcod.white)
			libtcod.console_set_default_background(attack_con, libtcod.black)
		
			text = str(profile['final_chance']) + '%%'
			libtcod.console_print_ex(attack_con, 13, 47, libtcod.BKGND_NONE,
				libtcod.CENTER, text)
		
		# display prompts
		libtcod.console_set_default_foreground(attack_con, ACTION_KEY_COL)
		if profile['attacker'] == self.player_unit:
			libtcod.console_print(attack_con, 6, 56, 'Bksp')
		libtcod.console_print(attack_con, 6, 57, 'Tab')
		libtcod.console_set_default_foreground(attack_con, libtcod.white)
		if profile['attacker'] == self.player_unit:
			libtcod.console_print(attack_con, 12, 56, 'Cancel')
		libtcod.console_print(attack_con, 12, 57, 'Continue')
		
		
	
	# do a roll, animate the attack console, and display the results
	# returns an modified attack profile
	def DoAttackRoll(self, profile):
		
		# check to see if this weapon maintains Rate of Fire
		def CheckRoF(profile):
			
			if profile['weapon'].GetStat('type') == 'Gun':
			
				# guns must have a Loader on proper order to get RoF
				position_list = profile['weapon'].GetStat('reloaded_by')
				if position_list is None:
					return False
				
				crewman_found = False
				for position in position_list:
					crewman = profile['attacker'].GetPersonnelByPosition(position)
					if crewman is None: continue
					if crewman.current_cmd != 'Reload': continue
					crewman_found = True
					break
				
				if not crewman_found:
					return False
			
				# guns must have at least one shell of the current type available
				if profile['weapon'].ammo_type is not None:
					if profile['weapon'].ammo_stores[profile['weapon'].ammo_type] == 0:
						return False
			
			base_chance = float(profile['weapon'].GetStat('rof'))
			roll = GetPercentileRoll()
			
			if roll <= base_chance:
				return True
			return False
		
		# clear prompts from attack console
		libtcod.console_print(attack_con, 6, 56, '                  ')
		libtcod.console_print(attack_con, 6, 57, '                  ')
		
		# don't animate percentage rolls if player is not involved
		if profile['attacker'] != scenario.player_unit and profile['target'] != scenario.player_unit:
			roll = GetPercentileRoll()
		else:
			for i in range(6):
				roll = GetPercentileRoll()
				
				# modifiers applied to the final roll, the one that counts
				if i == 5:
				
					# check for player fate point usage
					if profile['target'] == scenario.player_unit and campaign_day.fate_points > 0:
						
						# hit or penetration
						if roll <= profile['final_chance'] or roll <= CRITICAL_HIT:
							
							# point fire hit
							if profile['type'] == 'Point Fire':
								
								# hit with large calibre weapon
								if profile['weapon'].GetStat('calibre') is not None:
									if int(profile['weapon'].GetStat('calibre')) > 25:
										
										# apply fate point
										campaign_day.fate_points -= 1
										roll = profile['final_chance'] + float(libtcod.random_get_int(0, 10, 500)) / 10.0
										if roll > 100.0:
											roll = 100.0
							
							# AP penetration
							elif profile['type'] == 'ap':
								
								# apply fate point
								campaign_day.fate_points -= 1
								roll = profile['final_chance'] + float(libtcod.random_get_int(0, 10, 500)) / 10.0
								if roll > 100.0:
									roll = 100.0
				
					# check for debug flag
					if DEBUG:
						if profile['attacker'] == scenario.player_unit and session.debug['Player Always Hits']:
							roll = 3.0
						elif profile['target'] == scenario.player_unit and profile['type'] == 'ap' and session.debug['Player Always Penetrated']:
							roll = 3.0
				
				# clear any previous text
				libtcod.console_print_ex(attack_con, 13, 49, libtcod.BKGND_NONE,
					libtcod.CENTER, '      ')
				
				text = str(roll) + '%%'
				libtcod.console_print_ex(attack_con, 13, 49, libtcod.BKGND_NONE,
					libtcod.CENTER, text)
				
				scenario.UpdateScenarioDisplay()
				Wait(15)
		
		# record the final roll in the attack profile
		profile['roll'] = roll
			
		# determine location hit on target (not always used)
		location_roll = GetPercentileRoll()
		
		if location_roll <= 75.0:
			profile['location'] = 'Hull'
		else:
			profile['location'] = 'Turret'
		
		# armour penetration roll
		if profile['type'] == 'ap':
			
			if roll >= CRITICAL_MISS:
				result_text = 'NO PENETRATION'
			elif roll <= CRITICAL_HIT:
				result_text = 'PENETRATED'
			elif roll <= profile['final_chance']:
				result_text = 'PENETRATED'
			else:
				result_text = 'NO PENETRATION'
		
		# area fire attack
		elif profile['type'] == 'Area Fire':
			
			if roll <= profile['critical_effect']:
				result_text = 'CRITICAL EFFECT'
				profile['effective_fp'] = profile['base_fp'] * 2
			elif roll <= profile['full_effect']:
				result_text = 'FULL EFFECT'
				profile['effective_fp'] = profile['base_fp']
			elif roll <= profile['final_chance']:
				result_text = 'PARTIAL EFFECT'
				profile['effective_fp'] = int(floor(profile['base_fp'] / 2))
			else:
				result_text = 'NO EFFECT'
			
			# might be converted into an AP MG hit
			if result_text in ['FULL EFFECT', 'CRITICAL EFFECT']:
				if profile['weapon'].GetStat('type') in MG_WEAPONS and profile['target'].GetStat('armour') is not None:
					distance = GetHexDistance(profile['attacker'].hx,
						profile['attacker'].hy, profile['target'].hx,
						profile['target'].hy)
					if distance <= MG_AP_RANGE:
						if result_text == 'FULL EFFECT':
							result_text = 'HIT'
						else:
							result_text = 'CRITICAL HIT'

		# point fire attack
		else:
			
			if roll >= CRITICAL_MISS:
				result_text = 'MISS'
			elif roll <= CRITICAL_HIT:
				result_text = 'CRITICAL HIT'
			elif roll <= profile['final_chance']:
				result_text = 'HIT'
			else:
				result_text = 'MISS'
		
		# if point fire hit or AP MG hit, may be saved by HD status
		if result_text in ['HIT', 'CRITICAL HIT'] and len(profile['target'].hull_down) > 0:
			
			if profile['location'] == 'Hull':
				direction = GetDirectionToward(profile['target'].hx,
					profile['target'].hy, profile['attacker'].hx,
					profile['attacker'].hy)
				if direction in profile['target'].hull_down:
					result_text = 'MISS - HULL DOWN'
		
		profile['result'] = result_text
		
		# if player is not involved, we can return here
		if profile['attacker'] != scenario.player_unit and profile['target'] != scenario.player_unit:
			return profile
		
		libtcod.console_print_ex(attack_con, 13, 51, libtcod.BKGND_NONE,
			libtcod.CENTER, result_text)
		
		# display effective FP if it was successful area fire attack
		if profile['type'] == 'Area Fire' and result_text != 'NO EFFECT':
			libtcod.console_print_ex(attack_con, 13, 52, libtcod.BKGND_NONE,
				libtcod.CENTER, str(profile['effective_fp']) + ' FP')
		
		# check for RoF for gun / MG attacks
		if profile['type'] != 'ap' and profile['weapon'].GetStat('rof') is not None:
			
			# FUTURE: possibly allow AI units to maintain RoF?
			if profile['attacker'] == scenario.player_unit:
				profile['weapon'].maintained_rof = CheckRoF(profile) 
				if profile['weapon'].maintained_rof:
					libtcod.console_print_ex(attack_con, 13, 53, libtcod.BKGND_NONE,
						libtcod.CENTER, 'Maintained Rate of Fire')
					libtcod.console_set_default_foreground(attack_con, ACTION_KEY_COL)
					libtcod.console_print(attack_con, 6, 56, EnKey('f').upper())
					libtcod.console_set_default_foreground(attack_con, libtcod.white)
					libtcod.console_print(attack_con, 12, 56, 'Fire Again')
		
		# display prompt
		libtcod.console_set_default_foreground(attack_con, ACTION_KEY_COL)
		libtcod.console_print(attack_con, 6, 57, 'Tab')
		libtcod.console_set_default_foreground(attack_con, libtcod.white)
		libtcod.console_print(attack_con, 12, 57, 'Continue')
		
		return profile
	
	
	# selecte a different weapon on the player unit
	def SelectWeapon(self, forward):
		
		if self.selected_weapon is None:
			self.selected_weapon = scenario.player_unit.weapon_list[0]
			return
		
		if forward:
			m = 1
		else:
			m = -1
		
		i = scenario.player_unit.weapon_list.index(self.selected_weapon)
		i += m
		
		if i < 0:
			self.selected_weapon = scenario.player_unit.weapon_list[-1]
		elif i > len(scenario.player_unit.weapon_list) - 1:
			self.selected_weapon = scenario.player_unit.weapon_list[0]
		else:
			self.selected_weapon = scenario.player_unit.weapon_list[i]
	
	
	# (re)build a sorted list of possible player targets
	def BuildTargetList(self):
		
		self.target_list = []
		
		for unit in self.units:
			# allied unit
			if unit.owning_player == 0: continue
			# beyond active part of map
			if GetHexDistance(0, 0, unit.hx, unit.hy) > 3: continue
			self.target_list.append(unit)
		
		# old target no longer on list
		if self.selected_target not in self.target_list:
			self.selected_target = None
	
	
	# cycle selected player target
	# FUTURE: combine into general "next in list, previous in list, wrap around" function
	def CycleTarget(self, forward):
		
		# no targets to select from
		if len(self.target_list) == 0: return
		
		# no target selected yet
		if self.selected_target is None:
			self.selected_target = self.target_list[0]
			return
		
		if forward:
			m = 1
		else:
			m = -1
		
		i = self.target_list.index(self.selected_target)
		i += m
		
		if i < 0:
			self.selected_target = self.target_list[-1]
		elif i > len(self.target_list) - 1:
			self.selected_target = self.target_list[0]
		else:
			self.selected_target = self.target_list[i]
		
		self.selected_target.MoveToTopOfStack()
		self.UpdateUnitCon()
		self.UpdateUnitInfoCon()
	
	
	# execute a player move forward/backward, repositioning units on the hex map as needed
	def MovePlayer(self, forward):
		
		# do sound effect
		PlaySoundFor(self.player_unit, 'movement')
		
		# set statuses
		self.player_unit.moving = True
		self.player_unit.ClearAcquiredTargets()
		for unit in scenario.player_unit.squad:
			unit.moving = True
			unit.ClearAcquiredTargets()
		
		# do move success roll
		if forward:
			chance = scenario.player_unit.forward_move_chance
		else:
			chance = scenario.player_unit.reverse_move_chance
		roll = GetPercentileRoll()
		
		# check for debug flag
		if DEBUG:
			if session.debug['Player Always Moves']:
				roll = 1.0
		
		# move was not successful
		if roll > chance:
			
			# clear any alternative bonus and apply bonus for future moves
			if forward:
				scenario.player_unit.reverse_move_bonus = 0.0
				scenario.player_unit.forward_move_bonus += BASE_MOVE_BONUS
			else:
				scenario.player_unit.forward_move_bonus = 0.0
				scenario.player_unit.reverse_move_bonus += BASE_MOVE_BONUS
			
			# show pop-up message to player
			ShowMessage('You move but not far enough to enter a new map hex')
			
			# set new terrain for player and squad
			for unit in self.units:
				if unit != scenario.player_unit and unit not in scenario.player_unit.squad: continue
				unit.GenerateTerrain()
				unit.CheckForHD()
			
			# end movement phase
			self.advance_phase = True
			
			return
		
		# move was successful, clear all bonuses
		scenario.player_unit.forward_move_bonus = 0.0
		scenario.player_unit.reverse_move_bonus = 0.0
		
		# calculate new hex positions for each unit in play
		if forward:
			direction = 3
		else:
			direction = 0
		
		# run through list of units and move them
		# player movement will never move an enemy unit into ring 4 nor off board
		for unit in self.units:
			
			if unit == scenario.player_unit: continue
			if unit in scenario.player_unit.squad: continue
			
			(new_hx, new_hy) = GetAdjacentHex(unit.hx, unit.hy, direction)
			
			# skip if unit would end up in ring 4 or off board
			if GetHexDistance(0, 0, new_hx, new_hy) > 3:
				continue
				
			# special case: jump over player hex 0,0
			jump = False
			if new_hx == 0 and new_hy == 0:
				(new_hx, new_hy) = GetAdjacentHex(0, 0, direction)
				jump = True
			
			# set destination hex
			unit.dest_hex = (new_hx, new_hy)
			
			# calculate animation locations
			(x1, y1) = scenario.PlotHex(unit.hx, unit.hy)
			(x2, y2) = scenario.PlotHex(new_hx, new_hy)
			unit.animation_cells = GetLine(x1, y1, x2, y2)
			# special case: unit is jumping over 0,0
			if jump:
				for i in range(12, 0, -2):
					unit.animation_cells.pop(i)
		
		# animate movement
		for i in range(6):
			for unit in self.units:
				if unit == scenario.player_unit: continue
				if unit in scenario.player_unit.squad: continue
				if len(unit.animation_cells) > 0:
					unit.animation_cells.pop(0)
			self.UpdateUnitCon()
			self.UpdateScenarioDisplay()
			Wait(15)
		
		# set new hex location for each moving unit and move into new hex stack
		for unit in self.units:
			if unit.dest_hex is None: continue
			scenario.hex_dict[(unit.hx, unit.hy)].unit_stack.remove(unit)
			(unit.hx, unit.hy) = unit.dest_hex
			scenario.hex_dict[(unit.hx, unit.hy)].unit_stack.append(unit)
			# clear destination hex and animation data
			unit.dest_hex = None
			unit.animation_cells = []
		
		# set new terrain for player and squad
		for unit in self.units:
			if unit != scenario.player_unit and unit not in scenario.player_unit.squad: continue
			unit.GenerateTerrain()
			unit.CheckForHD()
		
		self.UpdateUnitCon()
		
		# end movement phase
		self.advance_phase = True
	
	
	# pivot the hull of the player unit
	def PivotPlayer(self, clockwise):
		
		if clockwise:
			r = 5
			f = -1
		else:
			r = 1
			f = 1
		
		# calculate new hex positions of units
		for unit in self.units:
			if unit == self.player_unit: continue
			if unit in self.player_unit.squad: continue
			
			(new_hx, new_hy) = RotateHex(unit.hx, unit.hy, r)
			# set destination hex
			unit.dest_hex = (new_hx, new_hy)
		
		# TODO: animate movement
		
		# set new hex location for each unit and move into new hex stack
		for unit in self.units:
			if unit == self.player_unit: continue
			if unit in self.player_unit.squad: continue
			self.hex_dict[(unit.hx, unit.hy)].unit_stack.remove(unit)
			(unit.hx, unit.hy) = unit.dest_hex
			self.hex_dict[(unit.hx, unit.hy)].unit_stack.append(unit)
			# clear destination hex
			unit.dest_hex = None
			
			# pivot unit facings if any
			if unit.facing is not None:
				unit.facing = ConstrainDir(unit.facing + f)
			if unit.turret_facing is not None:
				unit.turret_facing = ConstrainDir(unit.turret_facing + f)
			
			# pivot unit HD if any
			if len(unit.hull_down) > 0:
				for i in range(3):
					unit.hull_down[i] = ConstrainDir(unit.hull_down[i] + f)
		
		self.UpdateUnitCon()
		
		# NEW pivot player HD if any
		if len(self.player_unit.hull_down) > 0:
			for i in range(3):
				self.player_unit.hull_down[i] = ConstrainDir(self.player_unit.hull_down[i] + f)
		
		# record player pivot
		self.player_pivot = ConstrainDir(self.player_pivot + f)
	
	
	# rotate turret of player unit
	def RotatePlayerTurret(self, clockwise):
		
		if scenario.player_unit.turret_facing is None: return
		
		if clockwise:
			f = 1
		else:
			f = -1
		scenario.player_unit.turret_facing = ConstrainDir(scenario.player_unit.turret_facing + f)
		
		# update covered hexes for any turret-mounted weapons
		for weapon in scenario.player_unit.weapon_list:
			if weapon.GetStat('mount') != 'Turret': continue
			weapon.UpdateCoveredHexes()
		
		self.UpdateUnitCon()
		self.UpdateGuiCon()
	
	
	# display a pop-up window with info on a particular unit
	def ShowUnitInfoWindow(self, unit):
		
		# create a local copy of the current screen to re-draw when we're done
		temp_con = libtcod.console_new(WINDOW_WIDTH, WINDOW_HEIGHT)
		libtcod.console_blit(0, 0, 0, 0, 0, temp_con, 0, 0)
	
		# darken screen background
		libtcod.console_blit(darken_con, 0, 0, 0, 0, 0, 0, 0, 0.0, 0.7)
		
		# create window and draw frame
		window_con = libtcod.console_new(27, 26)
		libtcod.console_set_default_background(window_con, libtcod.black)
		libtcod.console_set_default_foreground(window_con, libtcod.white)
		DrawFrame(window_con, 0, 0, 27, 26)
		
		# draw unit info and command instructions
		unit.DisplayMyInfo(window_con, 1, 1)
		libtcod.console_set_default_foreground(window_con, ACTION_KEY_COL)
		libtcod.console_print(window_con, 7, 24, 'ESC')
		libtcod.console_set_default_foreground(window_con, libtcod.lighter_grey)
		libtcod.console_print(window_con, 12, 24, 'Return')
		
		# blit window to screen and then delete
		libtcod.console_blit(window_con, 0, 0, 0, 0, 0, WINDOW_XM-13, WINDOW_YM-13)
		del window_con
		
		# wait for player to exit view
		exit = False
		while not exit:
			if libtcod.console_is_window_closed(): sys.exit()
			libtcod.console_flush()
			
			# get keyboard and/or mouse event
			if not GetInputEvent(): continue
			
			if key.vk == libtcod.KEY_ESCAPE:
				exit = True
		
		# re-draw original view
		libtcod.console_blit(temp_con, 0, 0, 0, 0, 0, 0, 0)
		del temp_con
	
	
	# advance to next phase/turn and do automatic events
	def AdvanceToNextPhase(self):
		
		# do end of phase actions for player
		
		# end of player turn, switching to enemy turn
		if self.phase == PHASE_ALLIED_ACTION:
			
			# resolve fp on enemy units first
			for unit in reversed(self.units):
				if not unit.alive: continue
				if unit.owning_player == self.active_player: continue
				unit.ResolveFP()
			
			self.phase = PHASE_ENEMY_ACTION
			self.active_player = 1
		
		# end of enemy activation, player's turn
		elif self.phase == PHASE_ENEMY_ACTION:
		
			# resolve fp on player units first
			for unit in reversed(self.units):
				if not unit.alive: continue
				if unit.owning_player == self.active_player: continue
				unit.ResolveFP()
			
			# advance clock
			campaign_day.AdvanceClock(0, TURN_LENGTH)
			
			# check for end of scenario
			self.CheckForEnd()
			if self.finished: return
			
			self.active_player = 0
			self.phase = PHASE_COMMAND
			
			self.player_unit.ResetForNewTurn()
			for unit in scenario.player_unit.squad:
				unit.ResetForNewTurn()
			
			self.player_unit.MoveToTopOfStack()
			self.UpdateUnitCon()
			self.UpdateScenarioDisplay()
			libtcod.console_flush()
		
		# still player turn, advance phase
		else:
		
			# end of movement phase
			if self.phase == PHASE_MOVEMENT:
				
				# player pivoted during movement phase
				if self.player_pivot != 0:
					self.player_unit.acquired_target = None
			
			# end of shooting phase
			elif self.phase == PHASE_SHOOTING:
				
				# clear GUI console and refresh screen
				libtcod.console_clear(gui_con)
				self.UpdateScenarioDisplay()
				libtcod.console_flush()
				
				# resolve AP hits on enemy units
				for unit in reversed(self.units):
					if not unit.alive: continue
					if unit.owning_player == self.active_player: continue
					unit.ResolveAPHits()
			
			self.phase += 1
		
		# do automatic actions at start of phase
		
		# command phase: rebuild lists of commands
		if self.phase == PHASE_COMMAND:
			self.player_unit.BuildCmdLists()
		
		# spotting phase: do spotting then automatically advance
		elif self.phase == PHASE_SPOTTING:
			
			# check for abandoning tank
			for position in self.player_unit.positions_list:
				if position.crewman is None: continue
				if position.crewman.current_cmd == 'Abandon Tank':
					campaign.player_unit.alive = False
					ShowMessage('You abandon your tank, ending the combat day.')
					campaign_day.ended = True
					self.finished = True
					continue
			
			self.player_unit.DoSpotChecks()
			self.advance_phase = True
		
		# crew action phase: FUTURE: check to see if any crew are on action commands
		elif self.phase == PHASE_CREW_ACTION:
			
			skip_phase = True
			for position in self.player_unit.positions_list:
				if position.crewman is None: continue
				#if position.crewman.current_cmd == 'Request Support':
				#	skip_phase = False
				#	break
			
			if skip_phase:
				self.advance_phase = True
		
		# movement phase: 
		elif self.phase == PHASE_MOVEMENT:
			
			self.player_pivot = 0
			
			# skip phase if driver not on move command
			crewman = scenario.player_unit.GetPersonnelByPosition('Driver')
			if crewman is None:
				self.advance_phase = True
			else:
				# driver not on Drive command
				if crewman.current_cmd != 'Drive':
					self.advance_phase = True
			
			# if we're doing the phase, calculate move chances for player unit
			if not self.advance_phase:
				scenario.player_unit.CalculateMoveChances()
		
		# shooting phase
		elif self.phase == PHASE_SHOOTING:
			
			# check that 1+ crew are on correct order
			skip_phase = True
			for position in self.player_unit.positions_list:
				if position.crewman is None: continue
				if position.crewman.current_cmd in ['Operate Gun', 'Operate MG']:
					skip_phase = False
					break
			
			if skip_phase:
				self.advance_phase = True
			else:
				self.BuildTargetList()
				self.UpdateGuiCon()
		
		# close combat phase
		elif self.phase == PHASE_CC:
			
			# TEMP - advance automatically past this phase
			self.advance_phase = True
		
		# allied action
		elif self.phase == PHASE_ALLIED_ACTION:
			
			DisplayTimeInfo(time_con)
			self.UpdateScenarioDisplay()
			libtcod.console_flush()
			
			# player squad acts first
			for unit in scenario.player_unit.squad:
				unit.MoveToTopOfStack()
				self.UpdateUnitCon()
				self.UpdateScenarioDisplay()
				libtcod.console_flush()
				unit.ai.DoActivation()
				
				# do recover roll for this unit
				unit.DoRecoveryRoll()
				
				# resolve any ap hits caused by this unit
				for unit2 in self.units:
					if not unit2.alive: continue
					if unit2.owning_player == self.active_player: continue
					unit2.ResolveAPHits()
			
			self.advance_phase = True
		
		# enemy action
		elif self.phase == PHASE_ENEMY_ACTION:
			
			DisplayTimeInfo(time_con)
			self.UpdateScenarioDisplay()
			libtcod.console_flush()
			
			# run through list in reverse since we might remove units from play
			for unit in reversed(self.units):
				
				# if player has been destroyed, don't keep attacking
				if not self.player_unit.alive:
					break
				
				if unit.owning_player == 0: continue
				if not unit.alive: continue
				unit.ResetForNewTurn()
				unit.CalculateMoveChances()
				unit.ai.DoActivation()
				
				# resolve any ap hits caused by this unit
				for unit2 in self.units:
					if not unit2.alive: continue
					if unit2.owning_player == self.active_player: continue
					unit2.ResolveAPHits()
			
			self.advance_phase = True
		
		self.UpdateCrewInfoCon()
		self.UpdateUnitInfoCon()
		self.UpdateCmdCon()
		self.UpdateContextCon()
		self.UpdateGuiCon()
		DisplayTimeInfo(time_con)
		self.UpdateScenarioDisplay()
		libtcod.console_flush()
			
	
	# update contextual info console
	# 18x12
	def UpdateContextCon(self):
		libtcod.console_clear(context_con)
		
		# if we're advancing to next phase automatically, don't display anything here
		if self.advance_phase: return
		
		# Command Phase: display info about current crew command
		if self.phase == PHASE_COMMAND:
			position = scenario.player_unit.positions_list[self.selected_position]
			libtcod.console_set_default_foreground(context_con, SCEN_PHASE_COL[self.phase])
			libtcod.console_print(context_con, 0, 0, position.crewman.current_cmd)
			libtcod.console_set_default_foreground(context_con, libtcod.light_grey)
			lines = wrap(session.crew_commands[position.crewman.current_cmd]['desc'], 18)
			y = 2
			for line in lines:
				libtcod.console_print(context_con, 0, y, line)
				y += 1
		
		# Movement Phase
		elif self.phase == PHASE_MOVEMENT:
			
			libtcod.console_set_default_foreground(context_con, libtcod.white)
			libtcod.console_print(context_con, 6, 0, 'Success')
			#libtcod.console_print(context_con, 14, 0, 'Bog')
			
			libtcod.console_print(context_con, 0, 2, 'Fwd')
			libtcod.console_print(context_con, 0, 4, 'Rev')
			libtcod.console_print(context_con, 0, 6, 'Pivot')
			#libtcod.console_print(context_con, 0, 8, 'Repo')
			#libtcod.console_print(context_con, 0, 10, 'HD')
			
			libtcod.console_set_default_foreground(context_con, libtcod.light_grey)
			
			# forward move
			text = str(scenario.player_unit.forward_move_chance) + '%%'
			libtcod.console_print_ex(context_con, 11, 2, libtcod.BKGND_NONE,
				libtcod.RIGHT, text)
			#libtcod.console_print_ex(context_con, 16, 2, libtcod.BKGND_NONE,
			#	libtcod.RIGHT, '10%%')
			
			# reverse move
			text = str(scenario.player_unit.reverse_move_chance) + '%%'
			libtcod.console_print_ex(context_con, 11, 4, libtcod.BKGND_NONE,
				libtcod.RIGHT, text)
			#libtcod.console_print_ex(context_con, 16, 4, libtcod.BKGND_NONE,
			#	libtcod.RIGHT, '20%%')
			
			# pivot
			libtcod.console_print_ex(context_con, 11, 6, libtcod.BKGND_NONE,
				libtcod.RIGHT, '100%%')
			#libtcod.console_print_ex(context_con, 16, 6, libtcod.BKGND_NONE,
			#	libtcod.RIGHT, '1.5%%')
			
			# reposition
			#libtcod.console_print_ex(context_con, 10, 8, libtcod.BKGND_NONE,
			#	libtcod.RIGHT, '75%%')
			#libtcod.console_print_ex(context_con, 16, 8, libtcod.BKGND_NONE,
			#	libtcod.RIGHT, '4%%')
			
			# hull down
			#libtcod.console_print_ex(context_con, 10, 10, libtcod.BKGND_NONE,
			#	libtcod.RIGHT, '70%%')
			#libtcod.console_print_ex(context_con, 16, 10, libtcod.BKGND_NONE,
			#	libtcod.RIGHT, '2%%')
		
		# Shooting Phase
		elif self.phase == PHASE_SHOOTING:
			
			weapon = self.selected_weapon
			if weapon is None:
				return
			
			libtcod.console_set_default_foreground(context_con, libtcod.white)
			libtcod.console_set_default_background(context_con, libtcod.darkest_red)
			libtcod.console_rect(context_con, 0, 0, 18, 1, True, libtcod.BKGND_SET)
			libtcod.console_print(context_con, 0, 0, weapon.stats['name'])
			libtcod.console_set_default_background(context_con, libtcod.darkest_grey)
			
			if weapon.GetStat('mount') is not None:
				libtcod.console_set_default_foreground(context_con, libtcod.light_grey)
				libtcod.console_print_ex(context_con, 17, 0, libtcod.BKGND_NONE,
					libtcod.RIGHT, weapon.stats['mount'])
			
			# if weapon is a gun, display ammo info
			if weapon.GetStat('type') == 'Gun':
				
				# general stores
				y = 3
				for ammo_type in AMMO_TYPES:
					if ammo_type in weapon.ammo_stores:
						
						# highlight if this ammo type currently active
						if weapon.ammo_type is not None:
							if weapon.ammo_type == ammo_type:
								libtcod.console_set_default_background(context_con, libtcod.darker_blue)
								libtcod.console_rect(context_con, 0, y, 18, 1, True, libtcod.BKGND_SET)
								libtcod.console_set_default_background(context_con, libtcod.darkest_grey)
						
						libtcod.console_set_default_foreground(context_con, libtcod.white)
						libtcod.console_print(context_con, 0, y, ammo_type)
						libtcod.console_set_default_foreground(context_con, libtcod.light_grey)
						libtcod.console_print_ex(context_con, 7, y, libtcod.BKGND_NONE,
							libtcod.RIGHT, str(weapon.ammo_stores[ammo_type]))
						y += 1
				y += 1
				libtcod.console_print(context_con, 0, y, 'Max')
				libtcod.console_set_default_foreground(context_con, libtcod.light_grey)
				libtcod.console_print_ex(context_con, 7, y, libtcod.BKGND_NONE,
					libtcod.RIGHT, weapon.stats['max_ammo'])
				
				# TODO: highlight currenly selected ammo type
				#if weapon.ammo_type is not None:
			
			libtcod.console_set_default_foreground(context_con, libtcod.red)
			
			if weapon.fired:
				libtcod.console_print(context_con, 0, 11, 'Fired')
				return
			
			# display info about current target if any
			if self.selected_target is not None:
				result = self.CheckAttack(scenario.player_unit, weapon, self.selected_target)
				if result != '':
					lines = wrap(result, 18)
					y = 9
					for line in lines:
						libtcod.console_print(context_con, 0, y, line)
						y += 1
						if y == 12: break
	
	
	# update player unit info console
	def UpdatePlayerInfoCon(self):
		libtcod.console_clear(player_info_con)
		scenario.player_unit.DisplayMyInfo(player_info_con, 0, 0)
	
	
	# update the player crew info console
	def UpdateCrewInfoCon(self):
		libtcod.console_clear(crew_con)
		
		y = 0
		i = 0
		
		for position in scenario.player_unit.positions_list:
			
			# highlight position if selected and in command phase
			if i == scenario.selected_position and scenario.phase in [PHASE_COMMAND, PHASE_CREW_ACTION]:
				libtcod.console_set_default_background(crew_con, libtcod.darker_blue)
				libtcod.console_rect(crew_con, 0, y, 25, 3, True, libtcod.BKGND_SET)
				libtcod.console_set_default_background(crew_con, libtcod.black)
			
			# display position name and location in vehicle (eg. turret/hull)
			libtcod.console_set_default_foreground(crew_con, libtcod.light_blue)
			libtcod.console_print(crew_con, 0, y, position.name)
			libtcod.console_set_default_foreground(crew_con, libtcod.white)
			libtcod.console_print_ex(crew_con, 0+24, y, libtcod.BKGND_NONE, 
				libtcod.RIGHT, position.location)
			
			# display name of crewman and buttoned up / exposed status if any
			if position.crewman is None:
				libtcod.console_print(crew_con, 0, y+1, 'Empty')
			else:
				
				# use nickname if any
				if position.crewman.nickname != '':
					libtcod.console_print(crew_con, 0, y+1, '"' + position.crewman.nickname + '"')
				else:
				
					# build string of first initial and last name
					text = position.crewman.first_name[0] + '. ' + position.crewman.last_name
					
					# names might have special characters so we encode it before printing it
					libtcod.console_print(crew_con, 0, y+1, text.encode('IBM850'))
				
				# display wound status if any
				if position.crewman.wound != '':
					libtcod.console_put_char_ex(crew_con, 21, y+1, position.crewman.wound[0], libtcod.black, libtcod.red)
				
				if not position.hatch:
					text = '--'
				elif position.crewman.ce:
					text = 'CE'
				else:
					text = 'BU'
				libtcod.console_print_ex(crew_con, 24, y+1, libtcod.BKGND_NONE, libtcod.RIGHT, text)
			
				# display current command
				
				# truncate string if required
				text = position.crewman.current_cmd
				if len(text) + len(position.crewman.status) > 24:
					text = text[:(19 - len(position.crewman.status))] + '...'
				
				libtcod.console_set_default_foreground(crew_con, libtcod.dark_yellow)
				libtcod.console_print(crew_con, 0, y+2, text)
					
				# display current status on same line
				if position.crewman.status != '':
					if position.crewman.status == 'Dead':
						libtcod.console_set_default_foreground(crew_con, libtcod.dark_grey)
					elif position.crewman.status == 'Unconscious':
						libtcod.console_set_default_foreground(crew_con, libtcod.grey)
					elif position.crewman.status == 'Stunned':
						libtcod.console_set_default_foreground(crew_con, libtcod.light_grey)
					libtcod.console_print_ex(crew_con, 24, y+2, libtcod.BKGND_NONE, libtcod.RIGHT, 
						position.crewman.status)
			
			libtcod.console_set_default_foreground(crew_con, libtcod.darker_grey)
			for x in range(25):
				libtcod.console_print(crew_con, x, y+3, '-')
			
			libtcod.console_set_default_foreground(crew_con, libtcod.white)
			y += 4
			i += 1
	
	
	# update player command console
	def UpdateCmdCon(self):
		libtcod.console_clear(cmd_menu_con)
		
		# player not active
		if scenario.active_player == 1: return
		# advancing to next phase automatically
		if self.advance_phase: return
		
		# Any phase in player activation
		libtcod.console_set_default_foreground(cmd_menu_con, ACTION_KEY_COL)
		libtcod.console_print(cmd_menu_con, 1, 10, 'Space')
		libtcod.console_set_default_foreground(cmd_menu_con, libtcod.light_grey)
		libtcod.console_print(cmd_menu_con, 8, 10, 'End Phase')
		
		# Command phase
		if self.phase == PHASE_COMMAND:
			libtcod.console_set_default_foreground(cmd_menu_con, ACTION_KEY_COL)
			libtcod.console_print(cmd_menu_con, 1, 1, EnKey('w').upper() + '/' + EnKey('s').upper())
			libtcod.console_print(cmd_menu_con, 1, 2, EnKey('a').upper() + '/' + EnKey('d').upper())
			libtcod.console_print(cmd_menu_con, 1, 3, 'H')
			
			libtcod.console_set_default_foreground(cmd_menu_con, libtcod.light_grey)
			libtcod.console_print(cmd_menu_con, 8, 1, 'Select Position')
			libtcod.console_print(cmd_menu_con, 8, 2, 'Select Command')
			libtcod.console_print(cmd_menu_con, 8, 3, 'Open/Shut Hatch')
		
		# Crew action phase
		elif self.phase == PHASE_CREW_ACTION:
			libtcod.console_set_default_foreground(cmd_menu_con, ACTION_KEY_COL)
			libtcod.console_print(cmd_menu_con, 1, 1, EnKey('w').upper() + '/' + EnKey('s').upper())
			libtcod.console_set_default_foreground(cmd_menu_con, libtcod.light_grey)
			libtcod.console_print(cmd_menu_con, 8, 1, 'Select Position')
			
			# crew command specific actions
			if self.selected_position is None: return
			position = self.player_unit.positions_list[self.selected_position]
			if position.crewman is None: return
			
		# Movement phase
		elif self.phase == PHASE_MOVEMENT:
			libtcod.console_set_default_foreground(cmd_menu_con, ACTION_KEY_COL)
			libtcod.console_print(cmd_menu_con, 1, 1, EnKey('w').upper() + '/' + EnKey('s').upper())
			libtcod.console_print(cmd_menu_con, 1, 2, EnKey('a').upper() + '/' + EnKey('d').upper())
			#libtcod.console_print(cmd_menu_con, 1, 3, EnKey('r').upper())
			libtcod.console_print(cmd_menu_con, 1, 4, 'H')
			
			libtcod.console_set_default_foreground(cmd_menu_con, libtcod.light_grey)
			libtcod.console_print(cmd_menu_con, 8, 1, 'Forward/Reverse')
			libtcod.console_print(cmd_menu_con, 8, 2, 'Pivot Hull')
			#libtcod.console_print(cmd_menu_con, 8, 3, 'Reposition')
			libtcod.console_print(cmd_menu_con, 8, 4, 'Attempt HD')
		
		# Shooting phase
		elif self.phase == PHASE_SHOOTING:
			libtcod.console_set_default_foreground(cmd_menu_con, ACTION_KEY_COL)
			libtcod.console_print(cmd_menu_con, 1, 1, EnKey('w').upper() + '/' + EnKey('s').upper())
			libtcod.console_print(cmd_menu_con, 1, 2, EnKey('a').upper() + '/' + EnKey('d').upper())
			libtcod.console_print(cmd_menu_con, 1, 3, EnKey('q').upper() + '/' + EnKey('e').upper())
			libtcod.console_print(cmd_menu_con, 1, 4, EnKey('c').upper())
			libtcod.console_print(cmd_menu_con, 1, 5, EnKey('f').upper())
			
			libtcod.console_set_default_foreground(cmd_menu_con, libtcod.light_grey)
			libtcod.console_print(cmd_menu_con, 8, 1, 'Select Weapon')
			libtcod.console_print(cmd_menu_con, 8, 2, 'Select Target')
			libtcod.console_print(cmd_menu_con, 8, 3, 'Rotate Turret')
			libtcod.console_print(cmd_menu_con, 8, 4, 'Cycle Ammo Type')
			libtcod.console_print(cmd_menu_con, 8, 5, 'Fire at Target')

	
	# plot the center of a given in-game hex on the scenario hex map console
	# 0,0 appears in centre of console
	def PlotHex(self, hx, hy):
		x = (hx*7) + 26
		y = (hy*6) + (hx*3) + 21
		return (x,y)
	
	
	# build a dictionary of console locations and their corresponding map hexes
	# only called once when Scenario is created
	def BuildHexmapDict(self):
		for map_hex in self.map_hexes:
			# stop when outer hex ring is reached
			if GetHexDistance(0, 0, map_hex.hx, map_hex.hy) > 3: return
			(x,y) = self.PlotHex(map_hex.hx, map_hex.hy)
			
			# record console positions to dictionary
			for x1 in range(x-2, x+3):
				self.hex_map_index[(x1, y-2)] = map_hex
				self.hex_map_index[(x1, y+2)] = map_hex
			for x1 in range(x-3, x+4):
				self.hex_map_index[(x1, y-1)] = map_hex
				self.hex_map_index[(x1, y+1)] = map_hex
			for x1 in range(x-4, x+5):
				self.hex_map_index[(x1, y)] = map_hex
	
	
	# update hexmap console
	def UpdateHexmapCon(self):
		
		libtcod.console_clear(hexmap_con)
		
		# FUTURE: can use different hex console images for different battlefield types / weather
		scen_hex = LoadXP('scen_hex.xp')
		libtcod.console_set_key_color(scen_hex, KEY_COLOR)
		
		# draw hexes to hex map console
		for map_hex in self.map_hexes:
			if GetHexDistance(0, 0, map_hex.hx, map_hex.hy) > 3: break
			(x,y) = self.PlotHex(map_hex.hx, map_hex.hy)
			libtcod.console_blit(scen_hex, 0, 0, 0, 0, hexmap_con, x-5, y-3)
			
		del scen_hex
	
	
	# update unit layer console
	def UpdateUnitCon(self):
		
		libtcod.console_clear(unit_con)
		for map_hex in self.map_hexes:
			
			# too far away
			if GetHexDistance(0, 0, map_hex.hx, map_hex.hy) > 3: continue
			
			# no units in hex
			if len(map_hex.unit_stack) == 0: continue
			
			# draw top unit in stack
			map_hex.unit_stack[0].DrawMe()
			
			# draw stack number indicator if any
			if len(map_hex.unit_stack) == 1: continue
			if map_hex.unit_stack[0].turret_facing is not None:
				facing = map_hex.unit_stack[0].turret_facing
			else:
				facing = 3
			if facing in [5,0,1]:
				y_mod = 1
			else:
				y_mod = -1
			(x,y) = scenario.PlotHex(map_hex.unit_stack[0].hx, map_hex.unit_stack[0].hy)
			text = str(len(map_hex.unit_stack))
			libtcod.console_set_default_foreground(unit_con, libtcod.grey)
			libtcod.console_set_default_background(unit_con, libtcod.black)
			libtcod.console_print_ex(unit_con, x, y+y_mod, libtcod.BKGND_SET, libtcod.CENTER,
				text)
		
	
	# update GUI console
	def UpdateGuiCon(self):
		
		libtcod.console_clear(gui_con)
		
		# display field of view if in command phase
		if self.phase == PHASE_COMMAND:
			
			position = scenario.player_unit.positions_list[scenario.selected_position]
			for (hx, hy) in position.visible_hexes:
				(x,y) = scenario.PlotHex(hx, hy)
				libtcod.console_blit(session.scen_hex_fov, 0, 0, 0, 0, gui_con,
					x-5, y-3)
		
		# crew action phase
		elif self.phase == PHASE_CREW_ACTION:
			
			pass
			
		
		# shooting phase
		elif self.phase == PHASE_SHOOTING:
			
			# display covered hexes if a weapon is selected
			if self.selected_weapon is not None:
				for (hx, hy) in self.selected_weapon.covered_hexes:
					(x,y) = scenario.PlotHex(hx, hy)
					libtcod.console_blit(session.scen_hex_fov, 0, 0, 0, 0, gui_con,
						x-5, y-3)
			
			# display target recticle if a target is selected
			if self.selected_target is not None:
				(x1,y1) = self.PlotHex(0,0)
				(x2,y2) = self.PlotHex(self.selected_target.hx, self.selected_target.hy)
				
				libtcod.console_put_char_ex(gui_con, x2-1, y2-1, 218, libtcod.red, libtcod.black)
				libtcod.console_put_char_ex(gui_con, x2+1, y2-1, 191, libtcod.red, libtcod.black)
				libtcod.console_put_char_ex(gui_con, x2-1, y2+1, 192, libtcod.red, libtcod.black)
				libtcod.console_put_char_ex(gui_con, x2+1, y2+1, 217, libtcod.red, libtcod.black)
	
	
	# update the scenario info console, on the top right of the screen
	# will display current weather and terrain type
	# 18x12
	def UpdateScenarioInfoCon(self):
		libtcod.console_clear(scen_info_con)
		
		libtcod.console_set_default_foreground(scen_info_con, libtcod.light_grey)
		
		DisplayWeatherInfo(scen_info_con)
		
		# terrain
		libtcod.console_print(scen_info_con, 0, 10, 'Terrain:')
		libtcod.console_print(scen_info_con, 1, 11, self.cd_map_hex.terrain_type)
	
	
	# update the tank/crew status console, which displays urgent information for the player
	# 18x11
	def UpdateStatusCon(self):
		libtcod.console_clear(status_con)
		
		
	# update the unit info console, which displays basic information about a unit under
	# the mouse cursor
	# 18x11
	def UpdateUnitInfoCon(self):
		libtcod.console_clear(unit_info_con)
		
		# mouse cursor outside of map area
		if mouse.cx < 32: return
		
		# check that cursor is on a map hex
		x = mouse.cx - 32
		y = mouse.cy - 9
		if (x,y) not in self.hex_map_index: return
		
		map_hex = self.hex_map_index[(x,y)]
	
		# no units in hex
		if len(map_hex.unit_stack) == 0: return
		
		# display unit info
		unit = map_hex.unit_stack[0]
		
		if unit.owning_player == 1 and not unit.spotted:
			libtcod.console_set_default_foreground(unit_info_con, UNKNOWN_UNIT_COL)
			libtcod.console_print(unit_info_con, 0, 0, 'Unspotted Enemy')
		else:
			if unit == scenario.player_unit:
				col = libtcod.white
			elif unit.owning_player == 0:
				col = ALLIED_UNIT_COL
			else:
				col = ENEMY_UNIT_COL
	
			libtcod.console_set_default_foreground(unit_info_con, col)
			libtcod.console_print(unit_info_con, 0, 0, unit.unit_id)
			
			libtcod.console_set_default_foreground(unit_info_con, libtcod.light_grey)
			libtcod.console_print(unit_info_con, 0, 1,
				session.nations[unit.nation]['adjective'])
			libtcod.console_print(unit_info_con, 0, 2, unit.GetStat('class'))
			
			# moving/fired status
			if unit.moving:
				libtcod.console_print(unit_info_con, 0, 3, 'Moving')
			if unit.fired:
				libtcod.console_print(unit_info_con, 7, 3, 'Fired')
			
			# acquired target
			libtcod.console_set_default_foreground(unit_info_con, libtcod.white)
			if scenario.player_unit.acquired_target is not None:
				(target, level) = scenario.player_unit.acquired_target
				if target == unit:
					text = 'AC'
					if level:
						text += '2'
					libtcod.console_print(unit_info_con, 0, 4, text)
			
			libtcod.console_set_default_foreground(unit_info_con, ENEMY_UNIT_COL)
			if unit.acquired_target is not None:
				(target, level) = unit.acquired_target
				if target == scenario.player_unit:
					text = 'AC'
					if level:
						text += '2'
					libtcod.console_print(unit_info_con, 4, 4, text)
			
			# facing if any
			if unit.facing is not None and unit.GetStat('category') != 'Infantry':
				libtcod.console_put_char_ex(unit_info_con, 0, 6, 'H',
					libtcod.light_grey, libtcod.darkest_grey)
				libtcod.console_put_char_ex(unit_info_con, 1, 6,
					GetDirectionalArrow(unit.facing), libtcod.light_grey,
					libtcod.darkest_grey)
			
			# HD status if any
			if len(unit.hull_down) > 0:
				libtcod.console_set_default_foreground(unit_info_con, libtcod.sepia)
				libtcod.console_print(unit_info_con, 3, 6, 'HD')
				libtcod.console_put_char_ex(unit_info_con, 5, 6,
					GetDirectionalArrow(unit.hull_down[0]), libtcod.sepia,
					libtcod.darkest_grey)
			
			# current terrain
			if unit.terrain is not None:
				libtcod.console_set_default_foreground(unit_info_con, libtcod.dark_green)
				libtcod.console_print(unit_info_con, 0, 7, unit.terrain)
			
			libtcod.console_set_default_foreground(unit_info_con, libtcod.light_grey)
			libtcod.console_print(unit_info_con, 0, 10, 'R-Click for info')
		
		
	
	# draw all scenario consoles to the screen
	def UpdateScenarioDisplay(self):
		
		libtcod.console_clear(con)
		
		# left column
		if self.attack_con_active:
			libtcod.console_blit(attack_con, 0, 0, 0, 0, con, 0, 0)
		else:
			libtcod.console_blit(bkg_console, 0, 0, 0, 0, con, 0, 0)
			libtcod.console_blit(player_info_con, 0, 0, 0, 0, con, 1, 1)
			libtcod.console_blit(crew_con, 0, 0, 0, 0, con, 1, 21)
			libtcod.console_blit(cmd_menu_con, 0, 0, 0, 0, con, 1, 47)
		
		# main map display
		libtcod.console_blit(hexmap_con, 0, 0, 0, 0, con, 32, 9)
		libtcod.console_blit(unit_con, 0, 0, 0, 0, con, 32, 9, 1.0, 0.0)
		libtcod.console_blit(gui_con, 0, 0, 0, 0, con, 32, 9, 1.0, 0.0)
		libtcod.console_blit(animation_con, 0, 0, 0, 0, con, 32, 9, 1.0, 0.0)
		
		# consoles around the edge of map
		libtcod.console_blit(context_con, 0, 0, 0, 0, con, 28, 1)
		libtcod.console_blit(time_con, 0, 0, 0, 0, con, 48, 1)
		libtcod.console_blit(scen_info_con, 0, 0, 0, 0, con, 71, 1)
		libtcod.console_blit(unit_info_con, 0, 0, 0, 0, con, 28, 48)
		libtcod.console_blit(status_con, 0, 0, 0, 0, con, 71, 48)
		
		libtcod.console_blit(con, 0, 0, 0, 0, 0, 0, 0)
		libtcod.console_flush()
	
	
	# main input loop for scenarios
	def DoScenarioLoop(self):
		
		# set up and load scenario consoles
		global bkg_console, crew_con, cmd_menu_con, scen_info_con
		global player_info_con, context_con, time_con, hexmap_con, unit_con, gui_con
		global status_con, animation_con, attack_con, unit_info_con
		
		# background outline console for left column
		bkg_console = LoadXP('bkg.xp')
		
		player_info_con = NewConsole(25, 18, libtcod.black, libtcod.white)
		crew_con = NewConsole(25, 24, libtcod.black, libtcod.white)
		cmd_menu_con = NewConsole(25, 12, libtcod.black, libtcod.white)
		context_con = NewConsole(18, 12, libtcod.darkest_grey, libtcod.white)
		time_con = NewConsole(21, 6, libtcod.darkest_grey, libtcod.white)
		scen_info_con = NewConsole(18, 12, libtcod.darkest_grey, libtcod.white)
		unit_info_con = NewConsole(18, 11, libtcod.darkest_grey, libtcod.white)
		status_con = NewConsole(18, 11, libtcod.darkest_grey, libtcod.white)
		hexmap_con = NewConsole(53, 43, libtcod.black, libtcod.black)
		unit_con = NewConsole(53, 43, KEY_COLOR, libtcod.white, key_colour=True)
		gui_con = NewConsole(53, 43, KEY_COLOR, libtcod.white, key_colour=True)
		animation_con = NewConsole(53, 43, KEY_COLOR, libtcod.white, key_colour=True)
		attack_con = NewConsole(27, 60, libtcod.black, libtcod.white)
		
		# we're starting a new scenario
		if not self.init_complete:
		
			# set up player unit
			self.player_unit = campaign.player_unit
			self.player_unit.facing = 0
			self.player_unit.turret_facing = 0
			self.player_unit.squad = []
			self.player_unit.SpawnAt(0,0)
			self.player_unit.spotted = True
			
			# set up player squad
			player_unit_class = self.player_unit.GetStat('class')
			if player_unit_class == 'Tankette':
				squad_num = 4
			elif player_unit_class == 'Light Tank':
				squad_num = 3
			elif player_unit_class == 'Medium Tank':
				squad_num = 2
			elif player_unit_class == 'Heavy Tank':		# for FUTURE
				squad_num = 1
			
			for i in range(squad_num):
				unit = Unit(self.player_unit.unit_id)
				unit.nation = self.player_unit.nation
				unit.ai = AI(unit)
				unit.GenerateNewPersonnel()
				unit.facing = 0
				unit.turret_facing = 0
				unit.spotted = True
				unit.SpawnAt(0,0)
				self.player_unit.squad.append(unit)
			
			# generate enemy units
			self.SpawnEnemyUnits()
			
			# set up player unit for first activation
			self.player_unit.BuildCmdLists()
			self.player_unit.ResetForNewTurn()
			for unit in self.player_unit.squad:
				unit.BuildCmdLists()
				unit.ResetForNewTurn()
			
			self.init_complete = True
		
		# generate consoles and draw scenario screen for first time
		self.UpdateContextCon()
		DisplayTimeInfo(time_con)
		self.UpdateScenarioInfoCon()
		self.UpdateStatusCon()
		self.UpdatePlayerInfoCon()
		self.UpdateCrewInfoCon()
		self.UpdateCmdCon()
		self.UpdateUnitCon()
		self.UpdateGuiCon()
		self.UpdateHexmapCon()
		self.UpdateScenarioDisplay()
		
		# check for support attack
		if self.cd_map_hex.arty_support or self.cd_map_hex.air_support:
			if self.cd_map_hex.arty_support:
				ShowMessage('Friendly artillery bombardment inbound!')
				self.ArtilleryAttack()
				self.cd_map_hex.arty_support = False
			else:
				ShowMessage('Friendly air attack inbound!')
				self.AirAttack()
				self.cd_map_hex.air_support = False
			
			# resolve any fp from support attacks on enemy units
			for unit in reversed(self.units):
				if not unit.alive: continue
				if unit.owning_player == 0: continue
				unit.ResolveFP()
		
		# record mouse cursor position to check when it has moved
		mouse_x = -1
		mouse_y = -1
		
		exit_scenario = False
		while not exit_scenario:
			
			# check for exiting game
			if session.exiting:
				return
			
			# check for scenario finished, return to campaign day map
			if scenario.finished:
				# TODO: is this required? seems to be...
				campaign.player_unit = scenario.player_unit
				return
			
			if libtcod.console_is_window_closed(): sys.exit()
			libtcod.console_flush()
			
			# trigger advance to next phase
			if self.advance_phase:
				self.advance_phase = False
				self.AdvanceToNextPhase()
				SaveGame()
				continue
			
			keypress = GetInputEvent()
			
			##### Mouse Commands #####
			
			# check to see if mouse cursor has moved
			if mouse.cx != mouse_x or mouse.cy != mouse_y:
				mouse_x = mouse.cx
				mouse_y = mouse.cy
				self.UpdateUnitInfoCon()
				self.UpdateScenarioDisplay()
			
			# mouse wheel has moved or right mouse button clicked
			if mouse.wheel_up or mouse.wheel_down or mouse.rbutton_pressed:
				
				# see if cursor is over a hex with 1+ units in it
				x = mouse.cx - 32
				y = mouse.cy - 9
				if (x,y) in self.hex_map_index:
					map_hex = self.hex_map_index[(x,y)]
					if len(map_hex.unit_stack) > 0:
						if mouse.rbutton_pressed:
							unit = map_hex.unit_stack[0]
							if not (unit.owning_player == 1 and not unit.spotted):
								self.ShowUnitInfoWindow(unit)
							continue
						elif len(map_hex.unit_stack) > 1:
						
							if mouse.wheel_up:
								map_hex.unit_stack[:] = map_hex.unit_stack[1:] + [map_hex.unit_stack[0]]
							elif mouse.wheel_down:
								map_hex.unit_stack.insert(0, map_hex.unit_stack.pop(-1))
						self.UpdateUnitCon()
						self.UpdateUnitInfoCon()
						self.UpdateScenarioDisplay()
						continue
			
			
			##### Player Keyboard Commands #####
			
			# no keyboard input
			if not keypress: continue
			
			# game menu
			if key.vk == libtcod.KEY_ESCAPE:
				ShowGameMenu()
				continue
			
			# debug menu
			elif key.vk == libtcod.KEY_F2:
				if not DEBUG: continue
				ShowDebugMenu()
				continue
			
			# player not active
			if scenario.active_player == 1: continue
			
			# key commands
			key_char = DeKey(chr(key.c).lower())
			
			# Any Phase
			
			# advance to next phase
			if key.vk == libtcod.KEY_SPACE:
				self.advance_phase = True
				continue
			
			# Command or Crew Action phase
			
			
			# Command Phase
			if self.phase in [PHASE_COMMAND, PHASE_CREW_ACTION]:
			
				# change selected crew position
				if key_char in ['w', 's']:
					
					if key_char == 'w':
						self.selected_position -= 1
						if self.selected_position < 0:
							self.selected_position = len(self.player_unit.positions_list) - 1
					
					else:
						self.selected_position += 1
						if self.selected_position == len(self.player_unit.positions_list):
							self.selected_position = 0
				
					self.UpdateContextCon()
					self.UpdateCrewInfoCon()
					self.UpdateCmdCon()
					self.UpdateGuiCon()
					self.UpdateScenarioDisplay()
					continue
			
			# command phase only
			if self.phase == PHASE_COMMAND:
			
				# change current command for selected crewman
				if key_char in ['a', 'd']:
					
					# no crewman in selected position
					crewman = self.player_unit.positions_list[self.selected_position].crewman
					if crewman is None:
						continue
					
					crewman.SelectCommand(key_char == 'a')
					
					self.player_unit.positions_list[self.selected_position].UpdateVisibleHexes()
					
					self.UpdateContextCon()
					self.UpdateCrewInfoCon()
					self.UpdateGuiCon()
					self.UpdateScenarioDisplay()
					continue
				
				# toggle hatch for selected crewman (not mapped)
				elif chr(key.c).lower() == 'h':
					
					# no crewman in selected position
					crewman = self.player_unit.positions_list[self.selected_position].crewman
					if crewman is None:
						continue
					
					if crewman.ToggleHatch():
						self.player_unit.positions_list[self.selected_position].UpdateVisibleHexes()
						self.UpdateCrewInfoCon()
						self.UpdateGuiCon()
						self.UpdateScenarioDisplay()
						continue
			
			# crew action phase only
			elif self.phase == PHASE_CREW_ACTION:
				
				if self.selected_position is None: continue
				position = self.player_unit.positions_list[self.selected_position]
				if position.crewman is None: continue
			
			# Movement phase only
			elif scenario.phase == PHASE_MOVEMENT:
				
				# move forward/backward (also ends the phase)
				if key_char in ['w', 's']:
					self.MovePlayer(key_char == 'w')
					self.UpdateContextCon()
					self.UpdateUnitInfoCon()
					self.UpdateScenarioDisplay()
					continue
				
				# pivot hull
				elif key_char in ['a', 'd']:
					self.PivotPlayer(key_char == 'd')
					self.UpdatePlayerInfoCon()
					self.UpdateContextCon()
					self.UpdateUnitInfoCon()
					self.UpdateScenarioDisplay()
					continue
				
				# attempt HD (not keymapped)
				elif chr(key.c).lower() == 'h':
					
					# already in HD position
					if len(self.player_unit.hull_down) > 0:
						if self.player_unit.hull_down[0] == self.player_unit.facing:
							continue
					
					# set statuses and play sound
					self.player_unit.moving = True
					self.player_unit.ClearAcquiredTargets()
					PlaySoundFor(self.player_unit, 'movement')
					
					result = self.player_unit.CheckForHD(driver_attempt=True)
					if result:
						ShowMessage('You move into a Hull Down position')
					else:
						ShowMessage('You were unable to move into a Hull Down position')
					self.UpdatePlayerInfoCon()
					self.UpdateUnitInfoCon()
					self.UpdateScenarioDisplay()
					
					# end movement phase
					self.advance_phase = True
					continue
				
			# Shooting phase
			elif scenario.phase == PHASE_SHOOTING:
				
				# select player weapon
				if key_char in ['w', 's']:
					self.SelectWeapon(key_char == 's')
					self.UpdateGuiCon()
					self.UpdateContextCon()
					self.UpdateScenarioDisplay()
					continue
				
				# cycle player target
				elif key_char in ['a', 'd']:
					self.CycleTarget(key_char == 'd')
					self.UpdateGuiCon()
					self.UpdateContextCon()
					self.UpdateScenarioDisplay()
					continue
				
				# rotate turret
				elif key_char in ['q', 'e']:
					self.RotatePlayerTurret(key_char == 'e')
					self.UpdateContextCon()
					self.UpdateScenarioDisplay()
					continue
				
				# cycle ammo type
				elif key_char == 'c':
					result = scenario.selected_weapon.CycleAmmo()
					if result:
						self.UpdateContextCon()
						self.UpdateScenarioDisplay()
					continue
				
				# player fires active weapon at selected target
				elif key_char == 'f':
					result = scenario.player_unit.Attack(scenario.selected_weapon,
						scenario.selected_target)
					if result:
						self.UpdateUnitInfoCon()
						self.UpdateContextCon()
						self.UpdateScenarioDisplay()
					continue



##########################################################################################
#                                  General Functions                                     #
##########################################################################################	


# shortcut for generating consoles
def NewConsole(x, y, bg, fg, key_colour=False):
	new_con = libtcod.console_new(x, y)
	libtcod.console_set_default_background(new_con, bg)
	libtcod.console_set_default_foreground(new_con, fg)
	if key_colour:
		libtcod.console_set_key_color(new_con, KEY_COLOR)
	libtcod.console_clear(new_con)
	return new_con


# return a text description of a given calendar date
def GetDateText(dictionary):
	return (MONTH_NAMES[int(dictionary['month'])] + ' ' + str(dictionary['day']) + 
		', ' + str(dictionary['year']))


# display date, time, and phase information to a console
# console should be 21x6
def DisplayTimeInfo(console):
	libtcod.console_clear(console)
	libtcod.console_set_default_foreground(console, libtcod.white)
	
	if campaign is None: return
	
	libtcod.console_print_ex(console, 10, 0, libtcod.BKGND_NONE, libtcod.CENTER, GetDateText(campaign.today))
	
	if campaign_day is None: return
	
	# depiction of time remaining in day
	libtcod.console_set_default_background(console, libtcod.darker_yellow)
	libtcod.console_rect(console, 0, 1, 21, 1, True, libtcod.BKGND_SET)
	
	hours = campaign_day.day_clock['hour'] - int(campaign.today['start_hour'])
	minutes = campaign_day.day_clock['minute'] - int(campaign.today['start_minute'])
	if minutes < 0:
		hours -= 1
		minutes += 60
	minutes += (hours * 60)
	x = int(21.0 * float(minutes) / float(campaign_day.day_length))
	libtcod.console_set_default_background(console, libtcod.dark_yellow)
	libtcod.console_rect(console, 0, 1, x, 1, True, libtcod.BKGND_SET)
	libtcod.console_set_default_background(console, libtcod.black)
	
	text = str(campaign_day.day_clock['hour']).zfill(2) + ':' + str(campaign_day.day_clock['minute']).zfill(2)
	libtcod.console_print_ex(console, 10, 1, libtcod.BKGND_NONE, libtcod.CENTER, text)
	
	if campaign_day.scenario is None: return
	libtcod.console_set_default_foreground(console, SCEN_PHASE_COL[scenario.phase])
	libtcod.console_print_ex(console, 10, 5, libtcod.BKGND_NONE, libtcod.CENTER, 
		SCEN_PHASE_NAMES[scenario.phase] + ' Phase')


# display weather conditions info to a console, minimum width 12
def DisplayWeatherInfo(console):
	
	libtcod.console_clear(console)
	
	w = libtcod.console_get_width(console)
	
	# current temperature (TEMP static)
	libtcod.console_print(console, 0, 0, 'Mild')
	
	# cloud cover
	text = 'Clouds: ' + campaign_day.weather['Cloud Cover']
	libtcod.console_print(console, 0, 2, text)
	
	# precipitation
	text = 'Precip: ' + campaign_day.weather['Precipitation']
	libtcod.console_print(console, 0, 4, text)
	
	# ground conditions
	text = 'Ground: ' + campaign_day.weather['Ground']
	libtcod.console_print(console, 0, 6, text)
	
	# wind strength and direction (TEMP static)
	libtcod.console_print_ex(console, w-1, 0, libtcod.BKGND_NONE,
		libtcod.RIGHT, 'No wind')
	
	# fog level if any (TEMP static)
	libtcod.console_print_ex(console, w-1, 4, libtcod.BKGND_NONE,
		libtcod.RIGHT, '')


# draw an ArmCom2-style frame to the given console
def DrawFrame(console, x, y, w, h):
	libtcod.console_put_char(console, x, y, 249)
	libtcod.console_put_char(console, x+w-1, y, 249)
	libtcod.console_put_char(console, x, y+h-1, 249)
	libtcod.console_put_char(console, x+w-1, y+h-1, 249)
	for x1 in range(x+1, x+w-1):
		libtcod.console_put_char(console, x1, y, 196)
		libtcod.console_put_char(console, x1, y+h-1, 196)
	for y1 in range(y+1, y+h-1):
		libtcod.console_put_char(console, x, y1, 179)
		libtcod.console_put_char(console, x+w-1, y1, 179)


# display a pop-up message window on the screen, pause, and then clear message
# FUTURE: more options, add text to message log
# FUTURE: integrate with animation?
def ShowMessage(text, portrait=None):
	
	# create message console: 29x19
	msg_con = libtcod.console_new(29, 19)
	libtcod.console_set_default_background(msg_con, libtcod.darkest_grey)
	libtcod.console_set_default_foreground(msg_con, libtcod.white)
	libtcod.console_clear(msg_con)
	DrawFrame(msg_con, 0, 0, 29, 19)
	y = 1
	
	# display portrait if any
	if portrait is not None:
		libtcod.console_set_default_background(msg_con, PORTRAIT_BG_COL)
		libtcod.console_rect(msg_con, 1, 1, 27, 8, True, libtcod.BKGND_SET)
		libtcod.console_blit(LoadXP(portrait), 0, 0, 0, 0, msg_con, 2, 1)
		libtcod.console_set_default_background(msg_con, libtcod.black)
		y = 10
	
	# display message
	lines = wrap(text, 27)
	
	# try to center message vertically in window
	ym = 9 - int(len(lines) / 2)
	
	if ym >= y:
		y = ym
	
	for line in lines:
		libtcod.console_print_ex(msg_con, 14, y, libtcod.BKGND_NONE, libtcod.CENTER, line.encode('IBM850'))
		if y == 17: break
		y += 1
	
	# display closer to centre if we appear to be in the campaign day view
	if scenario is None:
		x = 31
	else:
		x = 44
	
	# display message console
	libtcod.console_blit(msg_con, 0, 0, 0, 0, 0, x, 21)
	libtcod.console_flush()
	
	Wait(140)
	
	# re-draw screen
	libtcod.console_blit(con, 0, 0, 0, 0, 0, 0, 0)
	libtcod.console_flush()
	del msg_con


# get keyboard and/or mouse event; returns False if no new key press
def GetInputEvent():
	event = libtcod.sys_check_for_event(libtcod.EVENT_KEY_RELEASE|libtcod.EVENT_KEY_PRESS|libtcod.EVENT_MOUSE,
		key, mouse)
	if session.key_down:
		if event != libtcod.EVENT_KEY_RELEASE:
			return False
		session.key_down = False
	if event != libtcod.EVENT_KEY_PRESS:
		return False
	session.key_down = True
	return True


# clear all keyboard events
def FlushKeyboardEvents():
	exit = False
	while not exit:
		if libtcod.console_is_window_closed(): sys.exit()
		libtcod.console_flush()
		event = libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS, key, mouse)
		if event != libtcod.EVENT_KEY_PRESS: exit = True
	session.key_down = False


# wait for a specified amount of miliseconds, refreshing the screen in the meantime
def Wait(wait_time):
	wait_time = wait_time * 0.01
	start_time = time.time()
	while time.time() - start_time < wait_time:
		if libtcod.console_is_window_closed(): sys.exit()
		FlushKeyboardEvents()


# wait for player to press continue key
# option to allow backspace pressed instead, returns True if so 
def WaitForContinue(allow_cancel=False):
	end_pause = False
	cancel = False
	while not end_pause:
		if libtcod.console_is_window_closed(): sys.exit()
		libtcod.console_flush()
		if not GetInputEvent(): continue
		
		if key.vk == libtcod.KEY_BACKSPACE and allow_cancel:
			end_pause = True
			cancel = True
		elif key.vk == libtcod.KEY_TAB:
			end_pause = True
	if allow_cancel and cancel:
		return True
	return False


# load a console image from an .xp file
def LoadXP(filename):
	xp_file = gzip.open(DATAPATH + filename)
	raw_data = xp_file.read()
	xp_file.close()
	xp_data = xp_loader.load_xp_string(raw_data)
	console = libtcod.console_new(xp_data['width'], xp_data['height'])
	xp_loader.load_layer_to_console(console, xp_data['layer_data'][0])
	return console


# Bresenham's Line Algorithm (based on an implementation on the roguebasin wiki)
# returns a series of x, y points along a line
# if los is true, does not include the starting location in the line
def GetLine(x1, y1, x2, y2, los=False):
	points = []
	issteep = abs(y2-y1) > abs(x2-x1)
	if issteep:
		x1, y1 = y1, x1
		x2, y2 = y2, x2
	rev = False
	if x1 > x2:
		x1, x2 = x2, x1
		y1, y2 = y2, y1
		rev = True
	deltax = x2 - x1
	deltay = abs(y2-y1)
	error = int(deltax / 2)
	y = y1
	
	if y1 < y2:
		ystep = 1
	else:
		ystep = -1
	for x in range(x1, x2 + 1):
		if issteep:
			points.append((y, x))
		else:
			points.append((x, y))
		error -= deltay
		if error < 0:
			y += ystep
			error += deltax
			
	# Reverse the list if the coordinates were reversed
	if rev:
		points.reverse()
	
	# chop off the first location if we're doing line of sight
	if los and len(points) > 1:
		points = points[1:]
	
	return points


# constrain a direction to a value 0-5
def ConstrainDir(direction):
	while direction < 0:
		direction += 6
	while direction > 5:
		direction -= 6
	return direction


# transforms an hx, hy hex location to cube coordinates
def GetCubeCoords(hx, hy):
	x = int(hx - (hy - hy&1) / 2)
	z = hy
	y = 0 - hx - z
	return (x, y, z)


# returns distance in hexes between two hexes
def GetHexDistance(hx1, hy1, hx2, hy2):
	(x1, y1, z1) = GetCubeCoords(hx1, hy1)
	(x2, y2, z2) = GetCubeCoords(hx2, hy2)
	return int((abs(x1-x2) + abs(y1-y2) + abs(z1-z2)) / 2)


# rotates a hex location around 0,0 clockwise r times
def RotateHex(hx, hy, r):
	# convert to cube coords
	(xx, yy, zz) = GetCubeCoords(hx, hy)
	for r in range(r):
		xx, yy, zz = -zz, -xx, -yy
	# convert back to hex coords
	return(int(xx + (zz - zz&1) / 2), zz)


# returns the adjacent hex in a given direction
def GetAdjacentHex(hx, hy, direction):
	direction = ConstrainDir(direction)
	(hx_mod, hy_mod) = DESTHEX[direction]
	return (hx+hx_mod, hy+hy_mod)


# returns arrow character used to indicate given direction
def GetDirectionalArrow(direction):
	if direction == 0:
		return chr(24)
	elif direction == 1:
		return chr(228)
	elif direction == 2:
		return chr(229)
	elif direction == 3:
		return chr(25)
	elif direction == 4:
		return chr(230)
	elif direction == 5:
		return chr(231)
	return ''


# returns a ring of hexes around a center point for a given radius
def GetHexRing(hx, hy, radius):
	if radius == 0: return [(hx, hy)]
	hex_list = []
	# get starting point
	hx -= radius
	hy += radius
	direction = 0
	for hex_side in range(6):
		for hex_steps in range(radius):
			hex_list.append((hx, hy))
			(hx, hy) = GetAdjacentHex(hx, hy, direction)
		direction += 1
	return hex_list



# returns the direction to an adjacent hex
def GetDirectionToAdjacent(hx1, hy1, hx2, hy2):
	hx_mod = hx2 - hx1
	hy_mod = hy2 - hy1
	if (hx_mod, hy_mod) in DESTHEX:
		return DESTHEX.index((hx_mod, hy_mod))
	# hex is not adjacent
	return -1



# returns the best facing to point in the direction of the target hex
def GetDirectionToward(hx1, hy1, hx2, hy2):
	
	(x1, y1) = scenario.PlotHex(hx1, hy1)
	(x2, y2) = scenario.PlotHex(hx2, hy2)
	bearing = GetBearing(x1, y1, x2, y2)
	
	if bearing >= 330 or bearing <= 30:
		return 0
	elif bearing <= 90:
		return 1
	elif bearing >= 270:
		return 5
	elif bearing <= 150:
		return 2
	elif bearing >= 210:
		return 4
	return 3


# return a list of hexes covered by the given hextant in direction d from hx, hy
# max range is 3
def GetCoveredHexes(hx, hy, d):
	hex_list = []
	hex_list.append((hx, hy))
	for i in range(2):
		(hx, hy) = GetAdjacentHex(hx, hy, d)
	hex_list.append((hx, hy))
	hex_list += GetHexRing(hx, hy, 1)
	return hex_list


# returns the compass bearing from x1, y1 to x2, y2
def GetBearing(x1, y1, x2, y2):
	return int((degrees(atan2((y2 - y1), (x2 - x1))) + 90.0) % 360)


# returns a bearing from 0-359 degrees
def RectifyBearing(h):
	while h < 0: h += 360
	while h > 359: h -= 360
	return h


# get the bearing from unit1 to unit2, rotated for unit1's facing
def GetRelativeBearing(unit1, unit2):
	(x1, y1) = scenario.PlotHex(unit1.hx, unit1.hy)
	(x2, y2) = scenario.PlotHex(unit2.hx, unit2.hy)
	bearing = GetBearing(x1, y1, x2, y2)
	return RectifyBearing(bearing - (unit1.facing * 60))


# get the relative facing of one unit from the point of view of another unit
# unit1 is the observer, unit2 is being observed
def GetFacing(attacker, target, turret_facing=False):
	bearing = GetRelativeBearing(target, attacker)
	if turret_facing and target.turret_facing is not None:
		turret_diff = target.turret_facing - target.facing
		bearing = RectifyBearing(bearing - (turret_diff * 60))
	if bearing >= 300 or bearing <= 60:
		return 'Front'
	return 'Side'


# return a random float between 0.0 and 100.0
def GetPercentileRoll():
	return float(libtcod.random_get_int(0, 0, 1000)) / 10.0


# round and restrict odds to between 3.0 and 97.0
def RestrictChance(chance):
	chance = round(chance, 1)
	if chance < 3.0: return 3.0
	if chance > 97.0: return 97.0
	return chance


# save the current game in progress
def SaveGame():
	save = shelve.open('savegame', 'n')
	save['campaign'] = campaign
	save['campaign_day'] = campaign_day
	save['scenario'] = scenario
	save['version'] = VERSION		# for now the saved version must be identical to the current one
	save.close()


# load a saved game
def LoadGame():
	global campaign, campaign_day, scenario
	save = shelve.open('savegame')
	campaign = save['campaign']
	campaign_day = save['campaign_day']
	scenario = save['scenario']
	save.close()


# check the saved game to see if it is compatible with the current game version
def CheckSavedGameVersion():
	save = shelve.open('savegame')
	saved_version = save['version']
	save.close()
	
	# for now, version must be the same, but future will allow backward-compatable updates
	if saved_version == VERSION:
		return ''
	return saved_version
	
	#version_list = saved_version.split('.')
	#major_saved_version = version_list[0] + version_list[1]
	#version_list = VERSION.split('.')
	#major_current_version = version_list[0] + version_list[1]
	#if major_saved_version == major_current_version:
	#	return ''
	#return saved_version


# remove a saved game
def EraseGame():
	os.remove('savegame.dat')
	os.remove('savegame.dir')
	os.remove('savegame.bak')


# try to load game settings from config file
def LoadCFG():
	
	global config
	
	config = ConfigParser()
	
	# create a new config file
	if not os.path.exists(DATAPATH + 'armcom2.cfg'):
		
		config['ArmCom2'] = {
			'large_display_font' : 'true',
			'sounds_enabled' : 'true',
			'keyboard' : '0'
		}
		
		# write to disk
		with open(DATAPATH + 'armcom2.cfg', 'w') as configfile:
			config.write(configfile)
	else:
		# load config file
		config.read(DATAPATH + 'armcom2.cfg')


# save current config to file
def SaveCFG():
	with open(DATAPATH + 'armcom2.cfg', 'w') as configfile:
		config.write(configfile)


# display a pop-up message on the root console
# can be used for yes/no confirmation
def ShowNotification(text, confirm=False):
	
	# determine window x, height, and y position
	x = WINDOW_XM - 30
	lines = wrap(text, 56)
	h = len(lines) + 6
	y = WINDOW_YM - int(h/2)
	
	# create a local copy of the current screen to re-draw when we're done
	temp_con = libtcod.console_new(WINDOW_WIDTH, WINDOW_HEIGHT)
	libtcod.console_blit(0, 0, 0, 0, 0, temp_con, 0, 0)
	
	# darken background 
	libtcod.console_blit(darken_con, 0, 0, 0, 0, 0, 0, 0, 0.0, 0.5)
	
	# draw a black rect and an outline
	libtcod.console_rect(0, x, y, 60, h, True, libtcod.BKGND_SET)
	DrawFrame(0, x, y, 60, h)
	
	# display message
	ly = y+2
	for line in lines:
		libtcod.console_print(0, x+2, ly, line)
		ly += 1
	
	# if asking for confirmation, display yes/no choices, otherwise display a simple messages
	if confirm:
		text = 'Proceed? Y/N'
	else:
		text = 'Enter to Continue'
	
	libtcod.console_print_ex(0, WINDOW_XM, y+h-2, libtcod.BKGND_NONE, libtcod.CENTER,
		text)
	
	# show to screen
	libtcod.console_flush()
	
	exit_menu = False
	while not exit_menu:
		if libtcod.console_is_window_closed(): sys.exit()
		libtcod.console_flush()
		
		if not GetInputEvent(): continue
		key_char = chr(key.c).lower()
		
		if confirm:
			
			if key_char == 'y':
				# restore original screen before returning
				libtcod.console_blit(temp_con, 0, 0, 0, 0, 0, 0, 0)
				del temp_con
				return True
			elif key_char == 'n':
				libtcod.console_blit(temp_con, 0, 0, 0, 0, 0, 0, 0)
				del temp_con
				return False
		else:
			if key.vk == libtcod.KEY_ENTER:
				exit_menu = True
	
	libtcod.console_blit(temp_con, 0, 0, 0, 0, 0, 0, 0)
	del temp_con



# display the in-game menu: 84x54
def ShowGameMenu():
	
	# draw the contents of the currently active tab to the menu console
	def DrawMenuCon(active_tab, selected_position):
		# blit menu background to game menu console
		libtcod.console_blit(session.game_menu_bkg, 0, 0, 0, 0, game_menu_con, 0, 0)
		
		# highlight active tab title
		x1 = 2 + (active_tab * 11)
		for x in range(x1+2, x1+5):
			libtcod.console_set_char_foreground(game_menu_con, x, 1, ACTION_KEY_COL)
		for x in range(x1, x1+9):
			libtcod.console_set_char_foreground(game_menu_con, x, 2, libtcod.white)
		
		# erase part of line so it appears that tab is in foreground
		x1 = 1 + (active_tab * 11)
		for x in range(x1, x1+10):
			libtcod.console_put_char(game_menu_con, x, 3, chr(0))
		
		# fill in active tab info
		
		# Root Game Menu
		if active_tab == 0:
			
			libtcod.console_set_default_foreground(game_menu_con, libtcod.white)
			libtcod.console_print_ex(game_menu_con, 42, 8, libtcod.BKGND_NONE,
				libtcod.CENTER, NAME)
			libtcod.console_print_ex(game_menu_con, 42, 9, libtcod.BKGND_NONE,
				libtcod.CENTER, 'Version: ' + VERSION)
			
			
			libtcod.console_set_default_foreground(game_menu_con, ACTION_KEY_COL)
			libtcod.console_print(game_menu_con, 36, 22, 'Q')
			libtcod.console_set_default_foreground(game_menu_con, libtcod.lighter_grey)
			libtcod.console_print(game_menu_con, 40, 22, 'Save and Quit')
		
		# Commander Menu
		elif active_tab == 1:
			
			crewman = campaign.player_unit.positions_list[0].crewman
			if crewman is not None:
				DisplayPersonnelInfo(crewman, game_menu_con, 5, 8)
			
			# FUTURE: display more detailed character information here
			
		
		# Crew Menu
		elif active_tab == 2:
			
			# display list of crew in the player tank
			DisplayCrew(campaign.player_unit, game_menu_con, 6, 8, selected_position)
			
			# display details on crewman in highlighted position
			crewman = campaign.player_unit.positions_list[selected_position].crewman
			if crewman is not None:
				DisplayPersonnelInfo(crewman, game_menu_con, 38, 7)
			
			# crew menu options if any
			if crewman is not None:
				if crewman.nickname == '':
					libtcod.console_set_default_foreground(game_menu_con, ACTION_KEY_COL)
					libtcod.console_print(game_menu_con, 8, 47, 'N')
					libtcod.console_set_default_foreground(game_menu_con, libtcod.lighter_grey)
					libtcod.console_print(game_menu_con, 10, 47, 'Set Crewman Nickname')
		
		
		# Tank Menu
		elif active_tab == 3:
			
			# display player tank info
			campaign.player_unit.DisplayMyInfo(game_menu_con, 27, 7)
			
			# unit description
			text = ''
			for t in campaign.player_unit.GetStat('description'):
				text += t
			lines = wrap(text, 33)
			y = 25
			libtcod.console_set_default_foreground(game_menu_con, libtcod.light_grey)
			for line in lines[:20]:
				libtcod.console_print(game_menu_con, 23, y, line)
				y+=1
			
			# display ammo stores for main gun
			weapon = campaign.player_unit.weapon_list[0]
			if weapon.GetStat('type') == 'Gun':
				y = 17
				for ammo_type in AMMO_TYPES:
					if ammo_type in weapon.ammo_stores:
						libtcod.console_print(game_menu_con, 54, y, ammo_type)
						libtcod.console_print_ex(game_menu_con, 59, y, libtcod.BKGND_NONE,
							libtcod.RIGHT, str(weapon.ammo_stores[ammo_type]))
						y += 1
			
		
		# Options Menu
		elif active_tab == 4:
			
			# display game options commands
			DisplayGameOptions(game_menu_con, WINDOW_XM-15, 18, skip_esc=True)
		
		libtcod.console_blit(game_menu_con, 0, 0, 0, 0, 0, 3, 3)
		libtcod.console_flush()
		
	
	# create a local copy of the current screen to re-draw when we're done
	temp_con = libtcod.console_new(WINDOW_WIDTH, WINDOW_HEIGHT)
	libtcod.console_blit(0, 0, 0, 0, 0, temp_con, 0, 0)
	
	# darken screen background
	libtcod.console_blit(darken_con, 0, 0, 0, 0, 0, 0, 0, 0.0, 0.7)
	
	# always start on root menu
	active_tab = 0
	
	# selected crew position in the player unit
	selected_position = 0
	
	# generate menu console for the first time and blit to screen
	DrawMenuCon(active_tab, selected_position)
	
	# get input from player
	exit_menu = False
	while not exit_menu:
		if libtcod.console_is_window_closed(): sys.exit()
		libtcod.console_flush()
		if not GetInputEvent(): continue
		
		key_char = DeKey(chr(key.c).lower())
		
		# Switch Active Menu
		if key.vk == libtcod.KEY_ESCAPE or key_char in ['1', '2', '3', '4']:
			
			# close menu
			if key.vk == libtcod.KEY_ESCAPE and active_tab == 0:
				exit_menu = True
				continue
			
			# switch tab
			if key.vk == libtcod.KEY_ESCAPE:
				active_tab = 0
			else:
				active_tab = int(key_char)
			DrawMenuCon(active_tab, selected_position)
			continue
		
		# Root Game Menu
		if active_tab == 0:
			# not mapped
			if chr(key.c).lower() == 'q':
				SaveGame()
				session.exiting = True
				exit_menu = True
		
		# Crew Menu
		elif active_tab == 2:
			# cycle selected position
			if key_char in ['w', 's']:
				if key_char == 'w':
					selected_position -= 1
					if selected_position < 0:
						selected_position = len(campaign.player_unit.positions_list) - 1
				
				else:
					selected_position += 1
					if selected_position == len(campaign.player_unit.positions_list):
						selected_position = 0
				
				DrawMenuCon(active_tab, selected_position)
				continue
			
			# set crewman nickname
			elif key_char == 'n':
				crewman = campaign.player_unit.positions_list[selected_position].crewman
				if crewman is None: continue
				if crewman.nickname != '': continue
				nickname = ShowTextInputMenu('Enter a nickname for ' + crewman.GetFullName(), '', MAX_NICKNAME_LENGTH, [])
				# no text entered
				if nickname == '':
					DrawMenuCon(active_tab, selected_position)
					continue
				result = ShowNotification("Once set this cannot be changed, are you certain you want this crewman's nickname to be '" + nickname + "'?", confirm=True)
				# nickname confirmed
				if result:
					crewman.nickname = nickname
					# update crew info console if we are in a scenario
					if scenario is not None:
						scenario.UpdateCrewInfoCon()
				DrawMenuCon(active_tab, selected_position)
				continue
		
		# Tank Menu
		elif active_tab == 3:
			pass
		
		
		# Options Menu
		elif active_tab == 4:
			if ChangeGameSettings(key_char):
				# redraw menu to reflect new settings
				DrawMenuCon(active_tab, selected_position)
				continue
	
	libtcod.console_blit(temp_con, 0, 0, 0, 0, 0, 0, 0)
	del temp_con



# display info about a crewman to a console
def DisplayPersonnelInfo(crewman, console, x, y):
	
	# outline and section dividers
	libtcod.console_set_default_foreground(console, libtcod.grey)
	DrawFrame(console, x, y, 31, 41)
	libtcod.console_hline(console, x+1, y+4, 29)
	libtcod.console_hline(console, x+1, y+7, 29)
	libtcod.console_hline(console, x+1, y+9, 29)
	libtcod.console_hline(console, x+1, y+11, 29)
	libtcod.console_hline(console, x+1, y+14, 29)
	libtcod.console_hline(console, x+1, y+20, 29)
	libtcod.console_hline(console, x+1, y+28, 29)
	
	# section titles
	libtcod.console_set_default_foreground(console, libtcod.lighter_blue)
	libtcod.console_print(console, x+1, y+2, 'Crewman Report')
	libtcod.console_print(console, x+1, y+5, 'Name')
	libtcod.console_print(console, x+1, y+8, 'Age')
	libtcod.console_print(console, x+1, y+10, 'Rank')
	libtcod.console_print(console, x+1, y+12, 'Current')
	libtcod.console_print(console, x+1, y+13, 'Position')
	libtcod.console_print(console, x+1, y+15, 'Assessment')
	libtcod.console_print(console, x+1, y+21, 'Injuries')
	libtcod.console_print(console, x+1, y+29, 'Status')
	
	# info
	libtcod.console_set_default_foreground(console, libtcod.white)
	libtcod.console_print(console, x+10, y+5, crewman.GetFullName().encode('IBM850'))
	if crewman.nickname != '':
		libtcod.console_print(console, x+10, y+6, '"' + crewman.nickname + '"')
	
	# FUTURE: have not been added yet
	#libtcod.console_print(console, x+10, y+7, str(crewman.age))
	#libtcod.console_print(console, x+10, y+9, crewman.rank_desc)
	
	libtcod.console_print(console, x+10, y+12, campaign.player_unit.unit_id)
	libtcod.console_print(console, x+10, y+13, crewman.current_position.name)
	
	# list traits
	y1 = y+16
	
	libtcod.console_put_char_ex(console, x+7, y1, chr(4), libtcod.yellow, libtcod.black)
	libtcod.console_put_char_ex(console, x+7, y1+1, chr(3), libtcod.red, libtcod.black)
	libtcod.console_put_char_ex(console, x+7, y1+2, chr(5), libtcod.blue, libtcod.black)
	libtcod.console_put_char_ex(console, x+7, y1+3, chr(6), libtcod.green, libtcod.black)
	
	for t in ['Perception', 'Morale', 'Grit', 'Knowledge', ]:
		libtcod.console_set_default_foreground(console, libtcod.white)
		libtcod.console_print(console, x+9, y1, t)
		libtcod.console_set_default_foreground(console, libtcod.light_grey)
		libtcod.console_print_ex(console, x+21, y1, libtcod.BKGND_NONE, libtcod.RIGHT,
			str(crewman.stats[t]))
		y1 += 1
	
	libtcod.console_set_default_background(console, libtcod.darkest_grey)
	libtcod.console_rect(console, x+7, y+17, 15, 1, False, libtcod.BKGND_SET)
	libtcod.console_rect(console, x+7, y+19, 15, 1, False, libtcod.BKGND_SET)
	libtcod.console_set_default_background(console, libtcod.black)
	
	# current status if any
	if crewman.status != '':
	
		y1 = y+30
		libtcod.console_set_default_foreground(console, libtcod.red)
		libtcod.console_print(console, x+2, y1, crewman.status)
		
		libtcod.console_set_default_foreground(console, libtcod.light_grey)
		text = ''
		if crewman.status == 'Stunned':
			text = 'Less effective but still in the fight.'
		elif crewman.status == 'Unconscious':
			text = 'Cannot act or bail out.'
		elif crewman.status == 'Dead':
			text = 'Out of action.'
		libtcod.console_print(console, x+2, y1+1, text)
	
	libtcod.console_set_default_foreground(console, libtcod.white)
	libtcod.console_set_default_background(console, libtcod.black)



# display a list of game options and current settings
def DisplayGameOptions(console, x, y, skip_esc=False):
	for (char, text) in [('F', 'Font Size'), ('S', 'Sound Effects'), ('K', 'Keyboard'), ('Esc', 'Return to Main Menu')]:
		
		if char == 'Esc' and skip_esc: continue
		
		# extra spacing
		if char == 'Esc': y += 1
		
		libtcod.console_set_default_foreground(console, ACTION_KEY_COL)
		libtcod.console_print(console, x, y, char)
		
		libtcod.console_set_default_foreground(console, libtcod.lighter_grey)
		libtcod.console_print(console, x+4, y, text)
		
		# current option settings
		libtcod.console_set_default_foreground(console, libtcod.light_blue)
		
		# toggle font size
		if char == 'F':
			if config['ArmCom2'].getboolean('large_display_font'):
				text = '16x16'
			else:
				text = '8x8'
			libtcod.console_print(console, x+20, y, text)
		
		# sound effects
		elif char == 'S':
			if config['ArmCom2'].getboolean('sounds_enabled'):
				text = 'ON'
			else:
				text = 'OFF'
			libtcod.console_print(console, x+20, y, text)
		
		# keyboard settings
		elif char == 'K':
			libtcod.console_print(console, x+20, y, KEYBOARDS[config['ArmCom2'].getint('keyboard')])
		
		y += 1


# take a keyboard input and change game settings
def ChangeGameSettings(key_char):
	
	if key_char not in ['f', 's', 'k']:
		return False
	
	# switch font size
	if key_char == 'f':
		libtcod.console_delete(0)
		if config.getboolean('ArmCom2', 'large_display_font'):
			config['ArmCom2']['large_display_font'] = 'false'
			fontname = 'c64_8x8.png'
		else:
			config['ArmCom2']['large_display_font'] = 'true'
			fontname = 'c64_16x16.png'
		libtcod.console_set_custom_font(DATAPATH+fontname,
			libtcod.FONT_LAYOUT_ASCII_INROW, 0, 0)
		libtcod.console_init_root(WINDOW_WIDTH, WINDOW_HEIGHT,
			NAME + ' - ' + VERSION, fullscreen = False,
			renderer = RENDERER)
	
	# toggle sound effects on/off
	elif key_char == 's':
		if config['ArmCom2'].getboolean('sounds_enabled'):
			config['ArmCom2']['sounds_enabled'] = 'false'
		else:
			config['ArmCom2']['sounds_enabled'] = 'true'
			# try to init mixer
			session.InitMixer()
		
	# switch keyboard layout
	elif key_char == 'k':
		
		i = config['ArmCom2'].getint('keyboard')
		if i == len(KEYBOARDS) - 1:
			i = 0
		else:
			i += 1
		config['ArmCom2']['keyboard'] = str(i)
		GenerateKeyboards()
		
	SaveCFG()
	return True


# display a pop-up window with a prompt and allow player to enter a text string
# can also generate randomly selected strings from a given list
# returns the final string
def ShowTextInputMenu(prompt, original_text, max_length, string_list):
	
	# display the most recent text string to screen
	def ShowText(text):
		libtcod.console_rect(0, 28, 30, 32, 1, True, libtcod.BKGND_SET)
		libtcod.console_print_ex(0, 45, 30, libtcod.BKGND_NONE, libtcod.CENTER, text)
	
	# start with the original text string, can cancel input and keep this
	text = original_text
	
	# create a local copy of the current screen to re-draw when we're done
	temp_con = libtcod.console_new(WINDOW_WIDTH, WINDOW_HEIGHT)
	libtcod.console_blit(0, 0, 0, 0, 0, temp_con, 0, 0)
	
	# darken screen background
	libtcod.console_blit(darken_con, 0, 0, 0, 0, 0, 0, 0, 0.0, 0.7)
	
	# draw the text input menu to screen
	libtcod.console_rect(0, 27, 20, 34, 20, True, libtcod.BKGND_SET)
	DrawFrame(0, 27, 20, 34, 20)
	lines = wrap(prompt, 24)
	y = 23
	libtcod.console_set_default_foreground(0, libtcod.light_grey)
	for line in lines:
		libtcod.console_print_ex(0, 45, y, libtcod.BKGND_NONE, libtcod.CENTER, line.encode('IBM850'))
		y += 1
	
	libtcod.console_set_default_foreground(0, ACTION_KEY_COL)
	libtcod.console_print(0, 31, 35, 'Del')
	libtcod.console_print(0, 31, 37, 'Enter')
	
	libtcod.console_set_default_foreground(0, libtcod.white)
	libtcod.console_print(0, 37, 35, 'Clear')
	libtcod.console_print(0, 37, 37, 'Confirm and Continue')
	
	if len(string_list) > 0:
		libtcod.console_set_default_foreground(0, ACTION_KEY_COL)
		libtcod.console_print(0, 31, 36, 'Tab')
		libtcod.console_set_default_foreground(0, libtcod.white)
		libtcod.console_print(0, 37, 36, 'Generate Random')
	
	# display current text string
	ShowText(text)
	
	exit_menu = False
	while not exit_menu:
		if libtcod.console_is_window_closed(): sys.exit()
		libtcod.console_flush()
		if not GetInputEvent(): continue
		
		# ignore shift key being pressed
		if key.vk == libtcod.KEY_SHIFT:
			session.key_down = False
		
		# cancel text input
		if key.vk == libtcod.KEY_ESCAPE:
			# re-draw original screen and return original text string
			libtcod.console_blit(temp_con, 0, 0, 0, 0, 0, 0, 0)
			del temp_con
			return original_text
		
		# confirm and return
		elif key.vk == libtcod.KEY_ENTER:
			exit_menu = True
			continue
		
		# select random string from list if any
		elif key.vk == libtcod.KEY_TAB:
			if len(string_list) == 0: continue
			text = choice(string_list)
		
		# clear string
		elif key.vk == libtcod.KEY_DELETE:
			text = ''
		
		# delete last character in string
		elif key.vk == libtcod.KEY_BACKSPACE:
			if len(text) == 0: continue
			text = text[:-1]
		
		# enter a new character
		else:
			# not a valid character
			if key.c == 0: continue
			
			# can't get any longer
			if len(text) == max_length: continue
			
			key_char = chr(key.c)
			if key.shift: key_char = key_char.upper()
			
			# filter key input
			if not ((32 <= ord(key_char) <= 126)):
				continue
			
			text += key_char
		
		FlushKeyboardEvents()
		ShowText(text)
		
	
	libtcod.console_blit(temp_con, 0, 0, 0, 0, 0, 0, 0)
	del temp_con
	return text


# display the debug flags menu, not enabled in distribution versions
def ShowDebugMenu():
	
	# draw the debug menu to screen
	def DrawDebugMenu():
		libtcod.console_clear(con)
		libtcod.console_set_default_foreground(con, libtcod.light_red)
		libtcod.console_print_ex(con, WINDOW_XM, 2, libtcod.BKGND_NONE, libtcod.CENTER, 'DEBUG MENU')
		
		y = 6
		n = 1
		for k, value in session.debug.items():
			libtcod.console_set_default_foreground(con, ACTION_KEY_COL)
			libtcod.console_print(con, 33, y, chr(n+64))
			if value:
				libtcod.console_set_default_foreground(con, libtcod.white)
			else:
				libtcod.console_set_default_foreground(con, libtcod.dark_grey)
			libtcod.console_print(con, 35, y, k)
			y += 2
			n += 1
		
		libtcod.console_set_default_foreground(con, ACTION_KEY_COL)
		libtcod.console_print(con, 33, 56, 'Esc')
		libtcod.console_print(con, 33, 57, 'Enter')
		libtcod.console_set_default_foreground(con, libtcod.white)
		libtcod.console_print(con, 39, 56, 'Return to Game')
		libtcod.console_print(con, 39, 57, 'Save and Return')
		
		libtcod.console_blit(con, 0, 0, 0, 0, 0, 0, 0)
		
	# build a dictionary of ordered letter to key values
	letter_dict = {}
	n = 1
	for k, value in session.debug.items():
		letter_dict[chr(n+64)] = k
		n += 1
	
	# save the current root console
	temp_con = libtcod.console_new(WINDOW_WIDTH, WINDOW_HEIGHT)
	libtcod.console_blit(0, 0, 0, 0, 0, temp_con, 0, 0)
	
	# draw the menu for the first time
	DrawDebugMenu()
	
	exit_menu = False
	while not exit_menu:
		if libtcod.console_is_window_closed(): sys.exit()
		libtcod.console_flush()
		if not GetInputEvent(): continue
		
		if key.vk == libtcod.KEY_ESCAPE:
			exit_menu = True
			continue
		
		elif key.vk == libtcod.KEY_ENTER:
			# save current debug settings
			with open(DATAPATH + 'debug.json', 'w', encoding='utf8') as data_file:
				json.dump(session.debug, data_file, indent=1)
			
			exit_menu = True
			continue
		
		key_char = chr(key.c).upper()
		
		if key_char in letter_dict:
			k = letter_dict[key_char]
			# flip the flag setting
			session.debug[k] = not session.debug[k]
			DrawDebugMenu()
			continue
	
	# re-draw original root console
	libtcod.console_blit(temp_con, 0, 0, 0, 0, 0, 0, 0)
	del temp_con



# display a list of crew positions and their crewmen to a console
def DisplayCrew(unit, console, x, y, highlight):
	
	for position in unit.positions_list:
		
		# highlight selected position and crewman
		if highlight is not None:
			if unit.positions_list.index(position) == highlight:
				libtcod.console_set_default_background(console, libtcod.darker_blue)
				libtcod.console_rect(console, x, y, 24, 4, True, libtcod.BKGND_SET)
				libtcod.console_set_default_background(console, libtcod.black)
		
		# display position name and location in vehicle (eg. turret/hull)
		libtcod.console_set_default_foreground(console, libtcod.light_blue)
		libtcod.console_print(console, x, y, position.name)
		libtcod.console_set_default_foreground(console, libtcod.white)
		libtcod.console_print_ex(console, x+23, y, libtcod.BKGND_NONE, 
			libtcod.RIGHT, position.location)
		
		# display last name of crewman and buttoned up / exposed status if any
		if position.crewman is None:
			libtcod.console_print(console, x, y+1, 'Empty')
		else:
			
			# names might have special characters so we encode it before printing it
			libtcod.console_print(console, x, y+1, position.crewman.first_name.encode('IBM850'))
			libtcod.console_print(console, x+1, y+2, position.crewman.last_name.encode('IBM850'))
		
			if position.crewman.ce:
				text = 'CE'
			else:
				text = 'BU'
			libtcod.console_print_ex(console, x+23, y+1, libtcod.BKGND_NONE, libtcod.RIGHT, text)
			
			# display current nickname if any
			if position.crewman.nickname != '':
				libtcod.console_print(console, x, y+3, '"' + position.crewman.nickname + '"')
			
			# display current status if any
			if position.crewman.status != '':
				libtcod.console_set_default_foreground(console, libtcod.red)
				libtcod.console_print_ex(console, x+23, y+3, libtcod.BKGND_NONE, libtcod.RIGHT, 
					position.crewman.status)
			
		libtcod.console_set_default_foreground(console, libtcod.white)
		y += 5


# generate keyboard encoding and decoding dictionaries
def GenerateKeyboards():
	
	global keyboard_decode, keyboard_encode

	keyboard_decode = {}
	keyboard_encode = {}
	with open(DATAPATH + 'keyboard_mapping.json', encoding='utf8') as data_file:
		keyboards = json.load(data_file)
	dictionary = keyboards[KEYBOARDS[config['ArmCom2'].getint('keyboard')]]
	for key, value in dictionary.items():
		keyboard_decode[key] = value
		keyboard_encode[value] = key



# turn an inputted key into a standard key input
def DeKey(key_char):
	if key_char in keyboard_decode:
		return keyboard_decode[key_char]
	return key_char



# turn a standard key into the one for the current keyboard layout
def EnKey(key_char):
	if key_char in keyboard_encode:
		return keyboard_encode[key_char]
	return key_char
	


##########################################################################################
#                                     Sound Effects                                      #
##########################################################################################

# play a given sample, and return the channel it is playing on
def PlaySound(sound_name):
	
	sample = mixer.Mix_LoadWAV((SOUNDPATH + sound_name + '.ogg').encode('ascii'))
	if sample is None:
		print('ERROR: Sound not found: ' + sound_name)
		return
	
	channel = mixer.Mix_PlayChannel(-1, sample, 0)
	
	del sample
	
	if channel == -1:
		print('ERROR: could not play sound: ' + sound_name)
		print(mixer.Mix_GetError())
		return
	
	return channel


# select and play a sound effect for a given situation
def PlaySoundFor(obj, action):
	
	# sounds disabled
	if not config['ArmCom2'].getboolean('sounds_enabled'):
		return
	
	if action == 'fire':
		if obj.GetStat('type') == 'Gun':
			
			if obj.GetStat('name') == 'AT Rifle':
				PlaySound('at_rifle_firing')
				return
			
			# temp - used for all large guns for now
			PlaySound('37mm_firing_0' + str(libtcod.random_get_int(0, 0, 3)))
			return
			
		if obj.stats['type'] in MG_WEAPONS:
			PlaySound('zb_53_mg_00')
			return
		
		if obj.GetStat('name') == 'Rifles':
			PlaySound('rifle_fire_0' + str(libtcod.random_get_int(0, 0, 3)))
			return
	
	elif action == 'he_explosion':
		PlaySound('37mm_he_explosion_0' + str(libtcod.random_get_int(0, 0, 1)))
		return
	
	elif action == 'armour_save':
		PlaySound('armour_save_0' + str(libtcod.random_get_int(0, 0, 1)))
		return
	
	elif action == 'vehicle_explosion':
		PlaySound('vehicle_explosion_00')
		return
	
	elif action == 'movement':
		
		if obj.GetStat('movement_class') in ['Wheeled', 'Fast Wheeled']:
			PlaySound('wheeled_moving_0' + str(libtcod.random_get_int(0, 0, 2)))
			return
		
		elif obj.GetStat('class') in ['Tankette', 'Light Tank', 'Medium Tank']:
			PlaySound('light_tank_moving_0' + str(libtcod.random_get_int(0, 0, 2)))
			return
	
	elif action == 'plane_incoming':
		PlaySound('plane_incoming_00')
		return
	
	elif action == 'stuka_divebomb':
		PlaySound('stuka_divebomb_00')
		return
	
	print ('ERROR: Could not determine which sound to play')
			



##########################################################################################
#                                      Main Script                                       #
##########################################################################################

global main_title, main_theme
global campaign, campaign_day, scenario, session
global keyboard_decode, keyboard_encode

print('Starting ' + NAME + ' version ' + VERSION)	# startup message

# try to load game settings from config file, will create a new file if none present
LoadCFG()

os.putenv('SDL_VIDEO_CENTERED', '1')			# center game window on screen

# determine font to use based on settings file
if config['ArmCom2'].getboolean('large_display_font'):
	fontname = 'c64_16x16.png'
else:
	fontname = 'c64_8x8.png'

# set up custom font and root console
libtcod.console_set_custom_font(DATAPATH+fontname, libtcod.FONT_LAYOUT_ASCII_INROW,
        0, 0)
libtcod.console_init_root(WINDOW_WIDTH, WINDOW_HEIGHT, NAME + ' - ' + VERSION,
	fullscreen = False, renderer = RENDERER)

libtcod.sys_set_fps(LIMIT_FPS)
libtcod.console_set_default_background(0, libtcod.black)
libtcod.console_set_default_foreground(0, libtcod.white)
libtcod.console_clear(0)

# display loading screen
libtcod.console_print_ex(0, WINDOW_XM, WINDOW_YM, libtcod.BKGND_NONE, libtcod.CENTER,
	'Loading...')
libtcod.console_flush()

# create new session object
session = Session()

# try to init sound mixer and load sounds if successful
main_theme = None
if config['ArmCom2'].getboolean('sounds_enabled'):
	if session.InitMixer():
		# load and play main menu theme
		main_theme = mixer.Mix_LoadMUS((SOUNDPATH + 'armcom2_theme.ogg').encode('ascii'))
		mixer.Mix_PlayMusic(main_theme, -1)
	else:
		config['ArmCom2']['sounds_enabled'] = 'false'
		print('Not able to init mixer, sounds disabled')
else:
	print('Sounds disabled')

# generate keyboard mapping dictionaries
GenerateKeyboards()
print('Current keyboard layout: ' + KEYBOARDS[config['ArmCom2'].getint('keyboard')])

# create double buffer console
con = libtcod.console_new(WINDOW_WIDTH, WINDOW_HEIGHT)
libtcod.console_set_default_background(con, libtcod.black)
libtcod.console_set_default_foreground(con, libtcod.white)
libtcod.console_clear(con)

# create darken screen console
darken_con = libtcod.console_new(WINDOW_WIDTH, WINDOW_HEIGHT)
libtcod.console_set_default_background(darken_con, libtcod.black)
libtcod.console_set_default_foreground(darken_con, libtcod.black)
libtcod.console_clear(darken_con)

# create game menu console: 84x54
game_menu_con = libtcod.console_new(84, 54)
libtcod.console_set_default_background(game_menu_con, libtcod.black)
libtcod.console_set_default_foreground(game_menu_con, libtcod.white)
libtcod.console_clear(game_menu_con)

# create mouse and key event holders
mouse = libtcod.Mouse()
key = libtcod.Key()


##########################################################################################
#                                        Main Menu                                       #
##########################################################################################

# load and generate main title background
main_title = LoadXP('main_title.xp')
TANK_IMAGES = [
	'unit_7TP.xp', 'unit_TK3.xp', 'unit_TKS.xp', 'unit_TKS_20mm.xp', 'unit_vickers_ejw.xp',
	'unit_pz_I_B.xp', 'unit_pz_II.xp', 'unit_pz_35t.xp', 'unit_pz_38t_a.xp',
	'unit_pz_III_D.xp', 'unit_pz_III_F.xp', 'unit_pz_IV_A.xp', 'unit_pz_IV_C.xp',
	'unit_t26_m39.xp', 'unit_bt5_m34.xp', 'unit_bt7_m37.xp', 'unit_t28_m34.xp'
]
libtcod.console_blit(LoadXP(choice(TANK_IMAGES)), 0, 0, 0, 0, main_title, 7, 6)
# display version number and program info
libtcod.console_set_default_foreground(main_title, libtcod.red)
libtcod.console_print_ex(main_title, WINDOW_XM, WINDOW_HEIGHT-8, libtcod.BKGND_NONE,
	libtcod.CENTER, 'Development Build: Has bugs and incomplete features')
libtcod.console_set_default_foreground(main_title, libtcod.light_grey)
libtcod.console_print_ex(main_title, WINDOW_XM, WINDOW_HEIGHT-6, libtcod.BKGND_NONE,
	libtcod.CENTER, VERSION)
libtcod.console_print_ex(main_title, WINDOW_XM, WINDOW_HEIGHT-4,
	libtcod.BKGND_NONE, libtcod.CENTER, 'Copyright 2019')
libtcod.console_print_ex(main_title, WINDOW_XM, WINDOW_HEIGHT-3,
	libtcod.BKGND_NONE, libtcod.CENTER, 'Free Software under the GNU GPL')
libtcod.console_print_ex(main_title, WINDOW_XM, WINDOW_HEIGHT-2,
	libtcod.BKGND_NONE, libtcod.CENTER, 'www.armouredcommander.com')

libtcod.console_blit(LoadXP('poppy.xp'), 0, 0, 0, 0, main_title, 1, WINDOW_HEIGHT-8)

# gradient animated effect for main menu
GRADIENT = [
	libtcod.Color(51, 51, 51), libtcod.Color(64, 64, 64), libtcod.Color(128, 128, 128),
	libtcod.Color(192, 192, 192), libtcod.Color(255, 255, 255), libtcod.Color(192, 192, 192),
	libtcod.Color(128, 128, 128), libtcod.Color(64, 64, 64), libtcod.Color(51, 51, 51),
	libtcod.Color(51, 51, 51)
]

# set up gradient animation timing
time_click = time.time()
gradient_x = WINDOW_WIDTH + 10

# draw the main title to the screen and display menu options
# if options_menu_active, draw the options menu instead
def UpdateMainTitleCon(options_menu_active):
	libtcod.console_blit(main_title, 0, 0, 0, 0, con, 0, 0)
	
	y = 38
	if options_menu_active:
		
		# display game options commands
		DisplayGameOptions(con, WINDOW_XM-10, 38)
		
	else:
		
		for (char, text) in [('C', 'Continue'), ('N', 'New Campaign Day'), ('O', 'Options'), ('Q', 'Quit')]:
			# grey-out continue game option if no saved game present
			disabled = False
			if char == 'C' and not os.path.exists('savegame.dat'):
				disabled = True
			
			if disabled:
				libtcod.console_set_default_foreground(con, libtcod.dark_grey)
			else:
				libtcod.console_set_default_foreground(con, ACTION_KEY_COL)
			libtcod.console_print(con, WINDOW_XM-5, y, char)
			
			if disabled:
				libtcod.console_set_default_foreground(con, libtcod.dark_grey)
			else:
				libtcod.console_set_default_foreground(con, libtcod.lighter_grey)
			libtcod.console_print(con, WINDOW_XM-3, y, text)	
			
			y += 1
	
	libtcod.console_blit(con, 0, 0, 0, 0, 0, 0, 0)


# update the animation effect
def AnimateMainMenu():
	
	global gradient_x
	
	for x in range(0, 10):
		if x + gradient_x > WINDOW_WIDTH: continue
		for y in range(19, 34):
			char = libtcod.console_get_char(con, x + gradient_x, y)
			fg = libtcod.console_get_char_foreground(con, x + gradient_x, y)
			if char != 0 and fg != GRADIENT[x]:
				libtcod.console_set_char_foreground(con, x + gradient_x,
					y, GRADIENT[x])
	gradient_x -= 2
	if gradient_x <= 0: gradient_x = WINDOW_WIDTH + 10

# activate root menu to start
options_menu_active = False

# draw the main title console to the screen for the first time
UpdateMainTitleCon(options_menu_active)


# Main Menu loop
exit_game = False

while not exit_game:
	
	# emergency exit in case of endless loop
	if libtcod.console_is_window_closed(): sys.exit()
	
	# trigger animation and update screen
	if time.time() - time_click >= 0.06:
		AnimateMainMenu()
		libtcod.console_blit(con, 0, 0, 0, 0, 0, 0, 0)
		time_click = time.time()
	
	libtcod.console_flush()
	
	if not GetInputEvent(): continue
	
	key_char = chr(key.c).lower()
	
	# options sub-menu
	if options_menu_active:
		
		if ChangeGameSettings(key_char):
			UpdateMainTitleCon(options_menu_active)
			
		# exit options menu
		elif key.vk == libtcod.KEY_ESCAPE:
			options_menu_active = False
			UpdateMainTitleCon(options_menu_active)
	
	# root main menu
	else:
		
		if key_char == 'q':
			exit_game = True
			continue
		
		elif key_char == 'o':
			options_menu_active = True
			UpdateMainTitleCon(options_menu_active)
			continue
		
		# start or continue a campaign
		elif key_char in ['n', 'c']:
			
			# check/confirm menu option
			if key_char == 'c':
				if not os.path.exists('savegame.dat'):
					continue
				
				result = CheckSavedGameVersion() 
				if result != '':
					text = 'Saved game was saved with an older version of the program (' + result + '), cannot continue.'
					ShowNotification(text)
					libtcod.console_blit(con, 0, 0, 0, 0, 0, 0, 0)
					continue
				
				libtcod.console_clear(0)
				libtcod.console_print_ex(0, WINDOW_XM, WINDOW_YM, libtcod.BKGND_NONE, libtcod.CENTER,
					'Loading...')
				libtcod.console_flush()
				
				# load the saved game
				LoadGame()
			
			else:
				# confirm savegame overwrite
				if os.path.exists('savegame.dat'):
					text = 'Starting a new campaign will PERMANTLY ERASE the existing saved campaign.'
					result = ShowNotification(text, confirm=True)
					# cancel and return to main menu
					if not result:
						libtcod.console_blit(con, 0, 0, 0, 0, 0, 0, 0)
						continue
			        
			        # create a new campaign object and select a campaign
				campaign = Campaign()
				result = campaign.CampaignSelectionMenu()
				
				# player canceled new campaign start
				if not result:
					campaign = None
					UpdateMainTitleCon(options_menu_active)
					continue
				
				# allow player to select their tank and tank name
				(unit_id, tank_name) = campaign.TankSelectionMenu()
				
				# create the player unit
				campaign.player_unit = Unit(unit_id)
				campaign.player_unit.unit_name = tank_name
				campaign.player_unit.nation = campaign.stats['player_nation']
				campaign.player_unit.GenerateNewPersonnel()
				
				# clear ammo load in player unit guns
				for weapon in campaign.player_unit.weapon_list:
					if weapon.GetStat('type') != 'Gun': continue
					for ammo_type in AMMO_TYPES:
						if ammo_type in weapon.ammo_stores:
							weapon.ammo_stores[ammo_type] = 0
				
				# TODO: allow player to review crew and set nicknames if any
				
				# show start-of-day briefing
				# FUTURE: can return to calendar view from here instead of starting day
				# for now, another chance to cancel campaign day
				result = campaign.ShowCDBriefing()
				if not result:
					campaign = None
					UpdateMainTitleCon(options_menu_active)
					continue
				
				# generate a new campaign day object
				campaign_day = CampaignDay()
				
				# placeholder for the currently active scenario
				scenario = None
				
				# allow player to load ammo
				campaign_day.AmmoReloadMenu()
			
			# pause main theme if playing
			if main_theme is not None:
				mixer.Mix_PauseMusic()
			
			campaign_day.DoCampaignDayLoop()
			
			# reset exiting flag
			session.exiting = False
			
			# restart main theme if playing
			if main_theme is not None:
				mixer.Mix_RewindMusic()
				mixer.Mix_ResumeMusic()
			
			UpdateMainTitleCon(options_menu_active)
			libtcod.console_blit(con, 0, 0, 0, 0, 0, 0, 0)

print(NAME + ' shutting down')			# shutdown message
# END #

