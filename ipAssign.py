import csv, os, platform
from pathlib import Path
""" 
A tool to create an IP scheme for established groups of device types
Code by William Wells


TODO:
- check for IP conflicts between adjacent device groups on assignment - utilize a Set of existing IPs to double check an IP doesn't exist, can increment next available IP based on Set contents
- check device counts before assigning IPs, allows for dynamic adjustment of IP pools
- redefine IP groups and update fixUnknowns group selection list
- pasting excel content as input

Secondary
- when defining device types, group remaining selections of the same type automatically
- allow specified output path
- allow specified ip scheme
- allow specified ip blacklist

"""

"""
   0            1           2          3           4          5              6            7                   8                 9                    10               11        12      13        14              15              16           17         18       19        20         21          22         23         24         25        26
Location | Manufacturer | Model | Design Name | Switch | Switch Port | Mac Address | Serial Number | Firmware Version | Primary IP address | Secondary IP Address | Subnet | Gateway | VLAN | Crestron ID | Gatekeeper Addr | System name | 164 Addr | SIP User | SIP # | SIP Port | SIP Proxy | SIP Auth | SIP Pass | User Name | Password | Notes 

1-19: Network Infrastructure 
20: Mic Master Control
21-25: MIC WAPS
26-30: Dante MIC WAPS 
31-49: Ceiling/Table Mics
50: OPEN
51-69: Dante Ceiling/Table Mics
70-79: Mic Network Charging Station
80: Camera Master Control
81-89: Cameras
90-94: VTC Devices (Codec/Bridges)
95-99: Crestron Control
100: Control Processor
101-103: DSP
104: DSP Dante Card
105-110: Audio Device
111-119: Touch Panels
120: OPEN ? 
121-140: Network Video Rx
141: Matrix
142-160: Network Video Tx
161-199: Ceiling Speakers
200: OPEN
201-220: Displays
221-224: Videowall Processors
225-250: DHCP
251-253: Service
254: DNS
255: Broadcast
"""

#--------------------------------------GLOBAL RESOURCES--------------------------------------#
sourceFile = "DNE"
sourceInput = "DNE"
header = "DNE"
outputFile = ""
ips = {}
devices = {}
fileLines = []
unknownDevs = {}
usedIPs = set()
blacklist = set()

BLANK_FIELD = "---"
INVALID = -1
IPSTART = "132.1.0."
NUM_FIELDS = 27
PASTING_VALS = 1
PROVIDING_PATH = 2

groupTypes = {
    "network": {
        "fname": "Network",
        "dname": ["NSW", "WAP"],
        "ip": 1
    },
    "micControl": {
        "fname": "Mic Control",
        "dname": ["MIC"],
        "ip": 20
    },
    "micWaps": {
        "fname": "Mic WAP",
        "dname": ["WAP"],
        "ip": 21
    },
    "danteMicWaps": {
        "fname": "Dante Mic WAP",
        "dname": ["MIC"],
        "ip": 26 
    },
    "mics": {
        "fname": "Mic",
        "dname": ["MIC"],
        "ip": 31
    },
    "danteMics": {
        "fname": "Dante Mic",
        "dname": ["MIC"],
        "ip": 51
    },
    "micChargers": {
        "fname": "Mic Charger",
        "dname": ["NCS"],
        "ip": 70
    },
    "camControl": {
        "fname": "Camera Control",
        "dname": ["mystery"],
        "ip": 80
    }, 
    "cams": {
        "fname": "Camera",
        "dname": ["CAM"],
        "ip": 81
    }, 
    "bridges": {
        "fname": "AV Bridge",
        "dname": ["AVB"],
        "ip": 90
    },
    "control": {
        "fname": "Control Device",
        "dname": ["mystery"],
        "ip": 95
    },
    "processor": {
        "fname": "Processor",
        "dname": ["CPRO", "PRO"],
        "ip": 100
    },
    "dsp": {
        "fname": "DSP",
        "dname": ["DSP"],
        "ip": 101
    },
    "dante": {
        "fname": "Dante",
        "dname": ["mystery"],
        "ip": 104
    },
    "audioDev": {
        "fname": "Audio Device",
        "dname": ["AMP"],
        "ip": 105
    },
    "touchpanels": {
        "fname": "Touchpanel",
        "dname": ["TPT", "TP"],
        "ip": 111
    },
    "netVidRX": {
        "fname": "Receiver",
        "dname": ["DEC"],
        "ip": 121
    },
    "matrix": {
        "fname": "AV Matrix",
        "dname": ["AVMX"],
        "ip": 141
    },
    "netVidTx": {
        "fname": "Transmitter",
        "dname": ["ENC"],
        "ip": 142
    },
    "speakers": {
        "fname": "Speaker",
        "dname": ["SPK"],
        "ip": 161
    },
    "pdus": {
        "fname": "Power Device",
        "dname": ["PDU"],
        "ip": 181
    },
    "displays": {
        "fname": "Display",
        "dname": ["DISP"],
        "ip": 201
    },
    "videoWallProc": {
        "fname": "Videowall Processor",
        "dname": ["VWP"],
        "ip": 221
    }
}            
            
testPath = '/Users/alex/Downloads/TED(Project- TED- Training - Colab ).csv'

#--------------------------------------METHODS--------------------------------------#

def get_input():
    """Prompts user for input format and data, then executes populates IPs for the provided data if possible"""
    importType = INVALID
    while not is_valid(importType, [PASTING_VALS, PROVIDING_PATH]): # type: ignore
        importType = input("Will you be (1)pasting values or (2)providing a CSV file path? ")

    importType = int(importType)
    if importType == PASTING_VALS:
        data = input("Enter pasted values here: ")
        parse_data(data)
    elif importType == PROVIDING_PATH:
        #reading file from path
        validFile = False
        while not validFile:
            file_path = input("Enter the full path to the CSV file here: ")
            #file_path = testPath
            try:
                with open(file_path, "r", newline = '', encoding = 'utf-8') as file:
                    if file_path.endswith(".csv"): 
                        validFile = True
                    else:
                        print("Invalid File Format. Please Use a CSV")
                    
                    reader = csv.reader(file)
                    numBlanks = 0
                    for row in reader:
                        #verify we are looking at data row, and all fields within the row are blank
                        if len(row) == NUM_FIELDS and all(field.strip() in ("", BLANK_FIELD) for field in row):
                            numBlanks += 1
                        else:
                            numBlanks = 0    
                        fileLines.append(row)
                        
                        if numBlanks >= 3: 
                            break
                        
            except FileNotFoundError:
                print(f"File not found at '{file_path}'. Please try again.")
            except PermissionError:
                print(f"No permission to access '{file_path}'. Please try again.")
            except Exception as e:
                print(f"Unexpected error: {e}. Please try again.")    


def create_pools():
    """establishes the IP scheme for the program"""
    for group, info in groupTypes.items():
        devices[group] = []
        ips[group] = info["ip"]
        
        
def parse_data(data: str):
    """Parses the pasted device table from user input"""
    print("parse_data Not yet implemented!")


def get_address(typeName: str) -> int:
    """Given the type of the device, determines the next IP in the range to assign to the device"""
    #get leading values of IP
    address = str(IPSTART)
    
    #find next IP to assign based on device type
    num = ips.get(typeName)
    address = address + str(num)
    usedIPs.add(num)
    #increment next available IP and update dict
    num += 1 # type: ignore
    ips[typeName] = num

    return address # type: ignore


def assign_devices():
    """Iterates through csv lines in user file and assigns devices to groups"""
    for line, currentRow in enumerate(fileLines):
        if len(currentRow) >= NUM_FIELDS:
            if "-" in currentRow[3] and currentRow[3] != BLANK_FIELD:
                deviceID = str(currentRow[3].strip())
                devType = get_type(deviceID)
                if devType != "unknown":
                    devices[devType] = {"deviceID": deviceID, "line": line}
                else:
                    hyphenInd = deviceID.find("-")
                    if hyphenInd > 0:
                        devNum = deviceID[hyphenInd+1:]
                        if devNum.isdigit():
                            unknownDevs[deviceID] = line
                        else:
                            print(f"Unknown Device Skipped; Non-numeric: {deviceID}")
                    else:
                        print(f"Unknown Device Skipped; Missing '-': {deviceID}")     


def fix_unknowns():
    """Requests user assistance with assigning groups to atypical devices"""
    unknownList = list(unknownDevs.keys())
    userQuit = False
    while len(unknownList) > 0 and not userQuit:
        print("The following devices were unable to be identified: ")
        print("0) Quit")
        for index, device in enumerate(unknownList, start = 1):
            print(f"{index}) {device}")

        selection = INVALID
        while not is_valid_range(selection, 0, len(unknownList)): # type: ignore
            selection = input("Select a device to assign to a category, or quit: ")
        
        selection = int(selection)
        if selection == 0:
            userQuit = True
        else:
            selectedDev = unknownList[selection - 1]
            groupList = list(groupTypes.keys())
            
            print("Selected Device: " + selectedDev)
            print("0) Back")
            for index, key in enumerate(groupList, start = 1):
                print(f"{index}) {groupTypes[key]["fname"]}")
           
            userGrp = INVALID
            while not is_valid_range(userGrp, 0, len(groupList)): # type: ignore
                userGrp = input("Select a category for the selected device, or go back: ")
                
            selectedGrp = groupList[int(userGrp) - 1]

            #CSV line associated with deviceID
            line = unknownDevs[selectedDev]                    
            devices[selectedGrp] = {"deviceID": selectedDev, "line": line}
            unknownList.remove(selectedDev)
                    
                
                
def ip_devices():
    """Utilizes populated categories of devices and blacklist to assigns IPs, avoiding conflicts and resizing pools where necessary"""
    """
    if the # of devices for a particular category > the difference between the starting IPs of the adjacent categories, then we need to resize

    e.g.
    121-140: Network Video Rx  == 121
    142-160: Network Video Tx  == 142

    142-121 = 20, *excluding 141*
    
    ipaddr = get_address(curType)
    currentRow[9] = ipaddr
    
    1-19: Network Infrastructure 
    20: Mic Master Control
    21-25: MIC WAPS
    26-30: Dante MIC WAPS 
    31-49: Ceiling/Table Mics
    50: OPEN
    51-69: Dante Ceiling/Table Mics
    70-79: Mic Network Charging Station
    80: Camera Master Control
    81-89: Cameras
    90-94: VTC Devices (Codec/Bridges)
    95-99: Crestron Control
    100: Control Processor
    101-103: DSP
    104: DSP Dante Card
    105-110: Audio Device
    111-119: Touch Panels
    120: OPEN ? 
    121-140: Network Video Rx
    141: Matrix
    142-160: Network Video Tx
    161-199: Ceiling Speakers
    200: OPEN
    201-220: Displays
    221-224: Videowall Processors
    225-250: DHCP
    251-253: Service
    254: DNS
    255: Broadcast
    """
    
    
    print("ip_devices Not yet implemented!")


def write_file():
    """Write the updated device list into a new file in the downloads folder"""
    try:
        downloadFolder = get_dl_path()
        path = downloadFolder / "UPDATED_CSV.csv"
        
        with open(path, 'w', newline = '') as file:
            writer = csv.writer(file)
            writer.writerows(fileLines)
                
    except Exception as e:
        print(f"Error writing to file: {e}")

       


#--------------------------------------Helper Methods--------------------------------------#
def is_valid(provided: str, accepted) -> bool:
    """Determines if any one number in accepted matches provided"""
    valid = False
    for num in accepted:
        if int(provided) == num:
            valid = True
            break

    return valid

def is_valid_range(provided: str, minAccepted: int, maxAccepted: int) -> bool:
    """Determines if provided value is between minAccepted and maxAccepted value inclusively."""
    valid = False
    if str(provided).isdigit():
        valid = int(provided) >= int(minAccepted) and int(provided) <= maxAccepted
    return valid

def get_type(name: str) -> str:
    """Determines the device type given the device name, assuming standard format (e.g. DEC-101 -> DEC)"""
    for group, info in groupTypes.items():
        for devName in info["dname"]:
            if devName in name:
                return group
    return "unknown"

def get_dl_path():
    """__Determine the path to the downloads folder based on OS"""
    system = platform.system()
    
    if system == 'Windows':
        dlPath = Path(os.environ['USERPROFILE']) / 'Downloads'
    elif system in ('Linux', 'Darwin'): #Darwin == OSX
        dlPath = Path.home() / 'Downloads'
    else:
        raise OSError(f"Unsupported Operating System: {system}")
    
    if not dlPath.exists():
        raise FileNotFoundError(f"Downloads folder could not be located")
    
    return dlPath
#--------------------------------------Main--------------------------------------#

def main():
    create_pools()
    get_input()
    #at this point we should have populated the fileLines from either paste or file parsing, now we group devices and assign IPs
    if len(fileLines) > 0:
        assign_devices()
    #if we find any devices we can't identify, fix them
    if len(unknownDevs) > 0:
        fix_unknowns()      
    
    #ip_devices()
    write_file()


main()
