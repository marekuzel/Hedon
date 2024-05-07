#!/usr/bin/python3

import os
from telethon.sync import TelegramClient
from telethon.tl.functions.messages import GetDialogsRequest
from functionsHedon import *
from datetime import datetime
import sys
import argparse

#checks for config file
api_id, api_hash, username = getConfig()

#gets the api_id and api_hash
with TelegramClient(username, api_id, api_hash) as client:
    result = client(GetDialogsRequest(
        offset_date=0,
        offset_id=0,
        offset_peer="username",
        limit=100,
        hash=0,
    ))

parser = argparse.ArgumentParser(description="Downloads messages from telegram chats and saves them to a csv file")
parser.add_argument("-n", "--names", help="downloads messages with count of subject mentions. Subject file should contain each subject/name on a new line. Experimental feature", action="store_true")
parser.add_argument("-c", "--channels", help="Creates a file with the list of channels", action="store_true")

names = False

args = parser.parse_args()
if args.names:
    names = True
elif args.channels:
    generateChannelsFile(result)
    exit()

#checks if the channels file exists and create list of channels
listOfChannels = tryListOfChannels(result)

#check if the channels selected should be downloaded
d = {}
if channelVerif(result, listOfChannels, d):
    exit()

# gets the start and end dates from the user
start_date, end_date = getDates()
if nOfDays(start_date, end_date):
    print ("The start date should be before the end date")
    exit()


subjects = {}
#goes through the chats and messages and adds them to a dictionary
with TelegramClient(username, api_id, api_hash) as client:
    for chat in result.chats:
        if checkChat(chat, listOfChannels):
            continue
        print (f"{chat.title} in progress...")
        for message in client.iter_messages(chat.id):
            if message.date.replace(tzinfo=None) > end_date:
                continue
            elif message.date.replace(tzinfo=None) < start_date:
                break
            if names:
                subjectsPerMessage = countSubjects(message.text)
                for name in subjectsPerMessage:
                    if name not in subjects:
                        subjects[name] = subjectsPerMessage[name]
                    else:
                        subjects[name] += subjectsPerMessage[name]
            else:
                subjectsPerMessage ={}
            d["message{0}".format(message.id)] = formatMessage(message, names, subjectsPerMessage, client)
            subjectsPerMessage = {key: 0 for key in subjectsPerMessage}
#writing to csv file
csvWriter(names,subjects,d)