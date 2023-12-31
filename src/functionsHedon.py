import re
from datetime import datetime
from fuzzywuzzy import fuzz

def parseReactions(text: str) -> int:
    """Parses the number of reactions from a string.

    Args:
        text (str): message.reactions

    Returns:
        int: total number of reactions
    """
    pattern = r'count=\D*(\d+)'  # Regular expression pattern to match numbers after "count=15"
    numbers = re.findall(pattern, text)
    total_sum = sum(map(int, numbers))
    return total_sum

def get_message_link(chat_id: int, message_id: int) -> str:
    """Returns the link to a message.

    Args:
        chat_id (int): chat_id
        message_id (int): message_id

    Returns:
        str: link to the message
    """
    base_url = "https://t.me/c/"
    return f"{base_url}{chat_id}/{message_id}"

def formatMessage(message: str, names: bool, subjects:dict, client)->list:
    """Formats the messages into a list.

    Args:
        message (str): message.text
        names (bool): True if names are to be counted
        subjects (dict): Dictionary storing appearances of each subject

    Returns:
        list: list of message attributes
    """
    list = []
    title = str(message.text).split(" ")
    msg_title = " ".join(title[:4])
    list.append(message.sender.username) 
    list.append(msg_title)
    list.append(parseReactions(str(message.reactions)))
    list.append(message.views)
    list.append(str(message.date.replace(tzinfo=None)))
    list.append(message.text)
    list.append(get_message_link(message.chat.id, message.id))
    try:
        list.append((client.get_entity(message.fwd_from.from_id)).username)
    except:
        list.append("None")
    
    if names:
        for subject in subjects:
            list.append(subjects[subject])
    return list

def generateChannelsFile(result) -> None:
    """Generates a list of channels from the result of GetDialogsRequest.

    Args:
        result (): result of GetDialogsRequest
    """
    print ("No channel list exists. Do you want to generate one? (y/n)")
    if input() == "n":
        exit()
    with open("channels.txt", "w") as f:
        for chat in result.chats:
            f.write(chat.title + "\n")
    print ("Channel list generated. Please edit channels.txt and run the script again.")
    exit()

def createListOfChannels()->list:
    """Creates a list of channels from channels.txt.

    Returns:
        list: list of channels
    """
    with open ("channels.txt", "r") as f:
        listOfChannels = f.readlines()
    listOfChannels = [x.strip() for x in listOfChannels]
    return listOfChannels

def checkChat(chat, listOfChannels:list) -> bool:
    """Checks if the chat is a channel and if it is in the channel list.

    Args:
        chat (_type_): chat object
        listOfChannels (list): list of channels

    Returns:
        bool: True if chat is not a channel or if it is not in the channel list
    """
    try:
        if chat.megagroup:
            print (f"{chat.title} is not a channel. Skipping...")
            return True
        elif chat.title not in listOfChannels:
            print (f"{chat.title} is not in the channel list. Skipping...")
            return True
    except AttributeError:
        print ("AttributeError")
        return True
def get_datetime_from_user(string: str) -> datetime:
    """Gets the date and time from the user.

    Args:
        string (str): Input from user

    Returns:
        datetime: datetime object
    """
    while True:
        try:
            date_string = input(string)
            datetime_obj = datetime.strptime(date_string, "%Y-%m-%d")
            if checkToday(datetime_obj):
                print ("Starting date is incorrect. Maybe date entered is in the future?")
            else:
                return datetime_obj
        except ValueError:
            print("Invalid input. Please enter the date and time in the correct format.")

def nOfDays(startDate: datetime, endDate: datetime) -> bool:
    """Checks if the number of days between the start and end date is less than or equal to 0.

    Args:
        startDate (datetime): Starting day of the period
        endDate (datetime): Ending day of the period

    Returns:
        bool: True if the number of days is less than or equal to 0
    """
    delta = endDate - startDate
    if delta.days <= 0:
        return True
    
def checkToday(date: datetime) -> bool:
    """Checks if the date is in the future.

    Args:
        date (datetime): date

    Returns:
        bool: True if the date is in the future
    """
    dayDiff = date - datetime.today()
    if dayDiff.days > 0:
        return True
    
def getDates () -> tuple:
    """Gets the start and end date from the user.

    Returns:
        tuple: start and end date
    """
    start_date = get_datetime_from_user ("Enter the starting date. The format should be YYYY-MM-DD: ")
    end_date = get_datetime_from_user ("Enter the date of the end of downloaded period. The format should be YYYY-MM-DD: ")
    return start_date, end_date
    
def printHelp():
    """Prints help information
    """
    print ("Usage: python3 hedon.py [OPTIONS]")
    print ("Options:")
    print ("  -h, --help        show this help message and exit")
    print ("  -n, --names       downloads messages with count of names in subjects.txt file. Subject file should contain each subject/name on a new line")
    print ("  -c, --channels    generate a list of channels")
    print ("  run without options to download messages from selected time period")
    exit()

def tryListOfChannels(listOfChannels:list) -> list:
    try:
        listOfChannels = createListOfChannels()
    except FileNotFoundError:
        print(f"Error: No channel list found. Run the command -c or --channels to generate a channel list.")
        exit()
    except IOError as e:
        print(f"An error occurred: {str(e)}")
    return listOfChannels

def getListOfSubjects(File:str) -> dict:
    """creates list of names of the subjects to count from the text file

    Args:
        File (str): name of the text file

    Returns:
        list: list of subjects
    """
    subjects = []
    try:
        with open(File, "r") as f:
            listOfSubjects = f.readlines()
    except:
        print(f"Error: No subjects.txt found in working directory. Create a text file with one name/subject on each line")
        exit()
    for line in listOfSubjects:
        line = line.strip()
        line = line.lower()
        subjects.append(line)
    return subjects

def countSubjects(text:str) -> dict:
    """counts number of subjects in the given text

    Args:
        text (str): text body of the message
    Returns:
        dict: dictionary of subjects and their count
    """
    subjects = getListOfSubjects("subjects.txt")
    subjectsD = {}
    for name in subjects:
        subjectsD[name] = 0
    SIMILARITY_THRESHOLD=70 #this seemed to work fine for me, however, this feature is very unreliable and should be used only for estimates
    textList = text.lower().split()
    for subject in subjects:
        for word in textList:
            similarity = fuzz.ratio(subject, word)
            if similarity >= SIMILARITY_THRESHOLD:
                subjectsD[subject] += 1
                with open("spravy.txt", "a") as w:
                    w.write(text)
                    w.write("\n-----------------------\n")
    return subjectsD