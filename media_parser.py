#!/usr/bin/python2.7

# Possible log states:
	# DEBUG, INFO, WARNING, ERROR, CRITICAL

# Dependencies:
	# - pyxmpp2. Can install using `sudo easy_install pyxmpp2` 

# Possible torrents the parser can handle
# - A range of TV show episodes (Determined by 'S{Digit}{Digit}E{Digit}{Digit}-E{Digit}{Digit}')
# - A single TV show episode (Determined by 'S{Digit}{Digit}E{Digit}{Digit}')
	# Additionally the sub-directory must have less than 5 files in it.
# - The daily show (specific sorting) (Determined by 'The Daily show')
# - A complete TV season (Determined by 'Season' + 'digit' + 'complete')
# - A movie (Determined by 'Movie title' + 'date')

import sys
import json
from datetime import datetime
import os
import re
import shutil
from pyxmpp2.simple import send_message as send_xmpp_message
import platform
from random import randint
from threading import Thread

# User paramaters from the config file to send a jabber message using the XMPP protocol.
def send_message(message, message_type):
	if notifications_enabled == "true":
		if message_type == "success":
			for receiver_username in receiver_usernames:
				send_xmpp_message(sender_username, sender_password, receiver_username, message)
		else:
			send_xmpp_message(sender_username, sender_password, receiver_usernames[0], message)
	
# Creates a new thread for each message sent
def send_message_helper(message, message_type):
	send_message_thread = Thread(target = send_message, args = (message, message_type))
	send_message_thread.start()

# Parse every media inside of directory_to_parse
def parse_directory():
	# Search through all files in directory filtering out any hidden and non-directory files.
	for root, dirs, files in os.walk(directory_to_parse):
		# Remove any files that start with '.'
		files = [f for f in files if not f.startswith('.')]

		if files: # Only process directories that contain valid media
			# Extract media name from the full path
			try:
				torrent_name = os.path.split(root)[1]
			except AttributeError:
				write_to_log("errors_log_file", "ERROR", "Unable to extract media name from the full path")
				send_message_helper("Unable to extract name from: " + root, "error")
				shutil.move(root, manual_sort_directory)
				continue

			# Update the list of files to absolute paths
			files = [os.path.join(root, f) for f in files]
			largest_file = find_largest_file(files)

			# A range of episodes
			if re.search('(s|S)[0-9]{2}(e|E)[0-9]{2}-[0-9]{2}', torrent_name):
				write_to_log("log_file", "INFO", "Starting parse on: " + torrent_name)
				process_range_of_episodes(root, torrent_name)
			# Single TV show episode
			elif re.search('(s|S)[0-9]{2}(e|E)[0-9]{2}', torrent_name):
				write_to_log("log_file", "INFO", "Starting parse on: " + torrent_name)
				process_single_episode(root, torrent_name, largest_file)
			# The daily show
			elif re.search('The.Daily.Show', torrent_name):
				write_to_log("log_file", "INFO", "Starting parse on: " + torrent_name)
				process_the_daily_show(root, torrent_name, largest_file)
			elif re.search('Stephen.Colbert', torrent_name):  #Stephen.Colbert.2016.03.29.Adam.Driver.720p.HDTV.X264-UAV.mkv
				write_to_log("log_file", "INFO", "Starting parse on: " + torrent_name)
				process_the_colbert_report(root, torrent_name, largest_file)
			# A complete TV season
			elif re.search('(S|s)eason[\ \.][0-9]', torrent_name):
				write_to_log("log_file", "INFO", "Starting parse on: " + torrent_name)
				process_complete_season(root, torrent_name)
			# A Movie
			elif re.search('[A-Za-z\ \.\(]+[0-9]{4}', torrent_name):
				write_to_log("log_file", "INFO", "Starting parse on: " + torrent_name)
				process_movie(root, torrent_name, largest_file)
			else:
				try:
					if torrent_name == "":
						shutil.move(files[0], manual_sort_directory)
						write_to_log("log_file", "INFO", "Only a file was downloaded and it was moved to the manual sort directory\n\t" + "path: " + files[0])
						send_message_helper(files[0] + " - was downloaded but needs manual sorting", "error")
					elif torrent_name == os.path.split(directory_to_parse)[1]:
						write_to_log("errors_log_file", "WARNING", "Downloader tried to move top level of directory to parse")
						send_message_helper("WARNING - Downloader tried to move top level of directory to parse", "error")
					else:
						print "in else"
						shutil.move(root, manual_sort_directory)
						write_to_log("log_file", "INFO", torrent_name + " - was moved to the manual sort directory")
						send_message_helper(torrent_name + " - was downloaded but needs manual sorting", "error")
				except shutil.Error: # Duplicate directory name, append a random number
					random_num = str(randint(0, sys.maxint))
					os.rename(root, root + random_num)
					shutil.move(root + random_num, manual_sort_directory)

def process_range_of_episodes(root, torrent_name):
	write_to_log("log_file", "INFO", torrent_name + " is a range of episodes moving to manul sort directory")
	send_message_helper(torrent_name + " is a range of episodes moving to manual sort directory", "error")
	# move_media(root, torrent_name, manual_sort_directory)
	shutil.move(root, manual_sort_directory)

def process_single_episode(root, torrent_name, path_to_episode): #.../Firefly/Season X/Firefly - s01e05
	# Need to extract the episode name, episode season, episode number, and file extension.
	episode_name = re.search('[^0-9]+', torrent_name).group(0)
	# Remove the '.S' from the episode name

	# Problem is that archer torrent name is 'Archer.year.season.episode.etc' Compared to the usual "ShowName.season.year"
	if episode_name == "Archer.":
		episode_name = episode_name[:-1]
	else:
		episode_name = episode_name[:-2]

	season_and_episode = re.search('[Ss][0-9]{2}[Ee][0-9]{2}', torrent_name).group(0).lower()

	episode_sort_location = os.path.join(tv_directory, episode_name, "Season." + season_and_episode[1:3])

	# Check if there is a directory for this TV show, if not create one
	if not os.path.isdir(os.path.join(tv_directory, episode_name)):
		# ADD LOG MESSAGE
		os.makedirs(os.path.join(tv_directory, episode_name))
		write_to_log("log_file", "INFO", "Creating directory: " + os.path.join(tv_directory, episode_name))

	# Check if there is a directory for this season for this tv show, if not create one
	if not os.path.isdir(episode_sort_location):
		os.makedirs(episode_sort_location)
		write_to_log("log_file", "INFO", "Creating directory: " + episode_sort_location)

	# Move the episode to its sorted location
	if move_media(root, path_to_episode, episode_sort_location) == 0: # Success
		send_message_helper(episode_name + " - " + season_and_episode + ", has been downloaded and is ready to watch", "success")		
	else: # Error
		send_message_helper("There was an error while processing: " + episode_name + " - " + season_and_episode, "error")

def process_the_daily_show(root, torrent_name, path_to_episode): #The.Daily.Show.2015.12.09.Marion.Cotillard.720p.CC.WEBRip.AAC2.0.x264-BTW[rarbg]
	daily_show_name = "The.Daily.Show"
	date = re.search('[0-9]{4}\.[0-9]{2}\.[0-9]{2}', torrent_name).group(0) #YYYY.MM.DD
	# Extract the daily show guest, and remove leading and trailing '.'
	guest = re.search('([0-9]{4}\.[0-9]{2}\.[0-9]{2})([^0-9]+)', torrent_name).group(2).strip(".")

	daily_show_sort_location = os.path.join(tv_directory, daily_show_name)

	if not os.path.isdir(daily_show_sort_location):
		os.makedirs(daily_show_sort_location)
		write_to_log("log_file", "INFO", "Creating directory: " + daily_show_sort_location)

	# Move the episode to its sorted location
	if move_media(root, path_to_episode, daily_show_sort_location) == 0: # Success
		send_message_helper(daily_show_name + " - " + date + " - " + guest + " has been downloaded and is ready to watch", "success")		
	else: # Error
		send_message_helper("There was an error while processing: " + daily_show_name + " - " + date + " - " + guest, "error")

def process_the_colbert_report(root, torrent_name, path_to_episode): # Stephen.Colbert.2016.03.29.Adam.Driver.720p.HDTV.X264-UAV.mkv  
	colbert_show_name = "Stephen.Colbert.2016"
	date = re.search('[0-9]{4}\.[0-9]{2}\.[0-9]{2}', torrent_name).group(0) #YYYY.MM.DD
	# Extract the colbert report guest and remote leading and trailing '.'
	guest = re.search('([0-9]{4}\.[0-9]{2}\.[0-9]{2})([^0-9]+)', torrent_name).group(2).strip(".")

	colbert_sort_location = os.path.join(tv_directory, colbert_show_name)

	if not os.path.isdir(colbert_sort_location):
		os.makedirs(colbert_sort_location)
		write_to_log("log_file", "INFO", "Creating directory: " + colbert_sort_location)

	# move episode to sorted location
	if move_media(root, path_to_episode, colbert_sort_location) == 0: # Success
		send_message_helper(colbert_show_name + " - " + date + " - " + guest + " has been downloaded and is ready to watch", "success")
	else: # Error
		send_message_helper("There was an error while processing: " + colbert_show_name + " - " + date + " - " + guest, "error")


def process_complete_season(root, torrent_name):
	write_to_log("log_file", "INFO", torrent_name + " is a complete season, moving to manual sort directory")
	send_message_helper(torrent_name + " is a complete season, moving to manual sort directory", "error")
	# move_media(root, torrent_name, manual_sort_directory)
	shutil.move(root, manual_sort_directory)

def process_movie(root, torrent_name, path_to_movie):
	# Extract the movie name and remove leading and trailing '.'
	movie_name = re.search('[^0-9\(]+', torrent_name).group(0).replace(' ', '.').strip(".")
	movie_date = re.search('[0-9]{4}', torrent_name).group(0)
	movie_name_and_date = movie_name + "." + movie_date

	movie_sort_location = os.path.join(movie_directory, movie_name_and_date)	

	# Create directory for movie if it doesn't exist
	if not os.path.isdir(movie_sort_location):
		os.makedirs(movie_sort_location)
		write_to_log("log_file", "INFO", "Creating directory: " + movie_sort_location)

	if move_media(root, path_to_movie, movie_sort_location) == 0: # Success
		send_message_helper(movie_name_and_date + " has been downloaded and is ready to watch", "success")
	else: # Error
		send_message_helper("There was an error while processing: " + movie_name_and_date, "error")

def move_media(root, path_to_media, sort_location):
	# Move the episode to it's sorted location
	try:
		shutil.move(path_to_media, sort_location)
		write_to_log("log_file", "INFO", path_to_media + " has been moved to: " + sort_location)

		# Mark the rest of the directory for deletion
		shutil.move(root, staged_for_deletion_directory)
		write_to_log("log_file", "INFO", root + " has been staged for deletion")
		return 0
	except shutil.Error:
		write_to_log("errors_log_file", "ERROR", path_to_media + " could not be moved to: " + sort_location)
		shutil.move(root, error_while_processing_directory)
		return 1

# Searches a list of absolute filenames to find the biggest file and returns a path to that file
def find_largest_file(files):
	biggest = -1
	path_to_biggest = ""

	for f in files:
		file_size = os.path.getsize(f)
		
		if file_size > biggest:
			biggest = file_size
			path_to_biggest = f

	return path_to_biggest

def write_to_log(which_log, type_of_message, log_message):
	if which_log == "log_file":
		log_file.write(datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S') + " - " + type_of_message + " - " + log_message + "\n")
	elif which_log == "errors_log_file":
		errors_log_file.write(datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S') + " - " + type_of_message + " - " + log_message + "\n")

def exit_program():
	log_file.close()
	errors_log_file.close()
	sys.exit()

if __name__ == '__main__':

	# Load information from the config file.
	platform = platform.system()
	try:	# The following MUST be set to a valid path prior to running the program
		if platform == 'Linux':
			config_file = open("Linux path for config file", "r")
		elif platform == 'Darwin':
			config_file = open("OSX path for config file", "r")
		elif platform == 'Win32':
			config_file = open("Windows path to config file", "r")
		else:
			print "Error determining OS."
			sys.exit()
	except IOError as e:
		print "I/O error({0}): {1}".format(e.errno, e.strerror)
		sys.exit()
	
	# Load the JSON config options
	config_fields = json.load(config_file)
	
	directory_to_parse = config_fields["directory_to_parse"]
	tv_directory = config_fields["tv_directory"]
	movie_directory = config_fields["movie_directory"]
	staged_for_deletion_directory = config_fields["staged_for_deletion_directory"]
	manual_sort_directory = config_fields["manual_sort_directory"]
	error_while_processing_directory = config_fields["error_while_processing_directory"]
	notifications_enabled = config_fields["notifications"]["enabled"].lower()
	log_file = open(config_fields["log_file"], 'a')
	errors_log_file = open(config_fields["errors_log_file"], 'a')

	if (notifications_enabled == "true"):
		sender_username = config_fields["notifications"]["config"]["sender_username"]
		sender_password = config_fields["notifications"]["config"]["sender_password"]
		receiver_usernames = config_fields["notifications"]["config"]["receiver_usernames"]

	# Ensure the manual sort directory exists, if not create it
	if not os.path.isdir(manual_sort_directory):
		os.makedirs(manual_sort_directory)
	# Ensure the staged_for_deletion_directory exists, if not create it
	if not os.path.isdir(staged_for_deletion_directory):
		os.makedirs(staged_for_deletion_directory)
	# Ensure the error_while_processing_directory exists, if not create it
	if not os.path.isdir(error_while_processing_directory):
		os.makedirs(error_while_processing_directory)

	config_file.close()
	
	log_file.write("\n******************** " + datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S') + " - SCRIPT STARTING ********************\n")
	errors_log_file.write("\n******************** " + datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S') + " - SCRIPT STARTING ********************\n")
	write_to_log("log_file","INFO", "Loaded information from config file successfully")

	parse_thread = Thread(target = parse_directory)
	parse_thread.start()
	parse_thread.join()

	log_file.write("******************** " + datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S') + " - SCRIPT ENDING ********************\n\n")
	errors_log_file.write("******************** " + datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S') + " - SCRIPT ENDING ********************\n\n")

	log_file.close()
	errors_log_file.close()
