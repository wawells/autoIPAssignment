import csv, os, platform
from pathlib import Path
""" 
A tool to create an IP scheme for established groups of device types
Code by William Wells


TODO:
- check for IP conflicts between adjacent device groups on assignment
- check device counts before assigning IPs, allows for dynamic adjustment of IP pools
- redefine IP groups and update fixUnknowns group selection list
- pasting excel content as input

Secondary
- when defining device types, group remaining selections of the same type automatically
- allow skipping fixUnknowns
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
141-160: Network Video Tx
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


BLANK_FIELD = "---"
NUM_FIELDS = 27

INVALID = -1
PASTING_VALS = 1
PROVIDING_PATH = 2
IPSTART = "132.1.0."
numDevices = 0

testPath = '/Users/alex/Downloads/TED(Project- TED- Training - Colab ).csv'

#--------------------------------------METHODS--------------------------------------#

def get_input():
    """Prompts user for input format and data, then executes populates IPs for the provided data if possible"""
    importType = INVALID
    while not is_valid(importType, [PASTING_VALS, PROVIDING_PATH]):
        importType = input("Will you be (1)pasting values or (2)providing a CSV file path? ")

    if int(importType) == PASTING_VALS:
        data = input("Enter pasted values here: ")
        parseData(data)
    else:
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
                        
                        #early exit condition for 3 or more blank rows
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
    
    ips["network"] = 1
    devices["network"] = []

    ips["micControl"] = 20
    devices["micControl"] = []

    ips["micWAPS"] = 21
    devices ["micWAPS"] = []

    ips["danteMicWaps"] = 26
    devices["danteMicWaps"] = []

    ips["mics"] = 31
    devices["mics"] = []

    ips["danteMics"] = 51
    devices["danteMics"] = []

    ips["micChargers"] = 70
    devices["micChargers"] = []

    ips["camControl"] = 80
    devices["camControl"] = []

    ips["cams"] = 81
    devices["cams"] = []

    ips["bridges"] = 90
    devices["bridges"] = []

    ips["control"] = 95
    devices["control"] = []

    ips["processor"] = 100
    devices["processor"] = []

    ips["dsp"] = 101
    devices["dsp"] = []

    ips["dante"] = 104
    devices["dante"] = []

    ips["audioDev"] = 105
    devices["audioDev"] = []

    ips["touchpanels"] = 111
    devices["touchpanels"] = []

    ips["netVidRx"] = 121
    devices["netVidRx"] = []

    ips["netVidTx"] = 141
    devices["netVidTx"] = []

    ips["speakers"] = 161
    devices["speakers"] = []

    ips["pdus"] = 181
    devices["pdus"] = []

    ips["displays"] = 201
    devices["displays"] = []

    ips["videowallProc"] = 221
    devices["videowallProc"] = []


def parse_data(data: str):
    """Parses the pasted device table from user input"""
    print("Not yet implemented!")


def get_address(typeName: str) -> int:
    """Given the type of the device, determines the next IP in the range to assign to the device"""
    #get leading values of IP
    newAddress = str(IPSTART)
    
    #find next IP to assign based on device type
    num = ips.get(typeName)
    newAddress = newAddress + str(num)

    #increment next available IP and update dict
    num = num + 1
    ips[typeName] = num

    return newAddress


def assign_devices():
    """Iterates through populated list of lines provided by user and assigns IPs"""
    for line, currentRow in enumerate(fileLines):
        if len(currentRow) >= NUM_FIELDS:
            #if we have -, we are likely looking at rows with devices
            if "-" in currentRow[3] and currentRow[3] != BLANK_FIELD:
                #extract the device from the information
                deviceID = str(currentRow[3].strip())
                curType = get_type(deviceID)
                if curType != "unknown":
                    ipaddr = get_address(curType)
                    devices[curType].append(deviceID)
                    currentRow[9] = ipaddr
                else:
                    hyphenInd = deviceID.find("-")
                    if hyphenInd > 0:
                        devNum = deviceID[hyphenInd+1:]
                        if devNum.isdigit():
                            #we have determined the device has some sort of number associated, indicating it is likely valid
                            unknownDevs[deviceID] = line
                        else:
                            print("Unknown Device Skipped; Non-numeric: " + deviceID)
                    else:
                        print("Unknown Device Skipped; Missing '-': " + deviceID)     


def fix_unknowns():
    """Requests user assistance with assigning IPs to atypical devices"""
    unknownList = list(unknownDevs.keys())
    
    while len(unknownList) > 0:
        print("The following devices were unable to be identified: ")
        for dev in range(len(unknownList)):
            adjNum = dev + 1
            print(str(adjNum) + ") " + unknownList[dev])

        unknownSel = INVALID
        while not is_valid_range(unknownSel, 1, len(unknownList)):
            unknownSel = input("Select a device to assign to a category: ")
        adjSel = int(unknownSel) - 1
        
        selectedDev = unknownList[adjSel]
        print("Selected Device: " + selectedDev)
        print("0) Back\n1) Processor\n2) DSP\n3) Microphone\n4) Camera\n5) Touchpanel\n6) Audio Device\n7) Transmitter\n8) Receiver\n9) Network\n10) Power")

        catSel = INVALID
        while not is_valid_range(catSel, 0, 10):
            catSel = input("Select a category for the selected device, or go back: ")
            
        if int(catSel) > 0:
            match int(catSel):
                case 1:
                    curType = "processor"
                case 2:
                    curType = "dsp"
                case 3:
                    curType = "mics"
                case 4:
                    curType = "cams"
                case 5:
                    curType = "touchpanels"
                case 6:
                    curType = "audioDev"
                case 7:
                    curType = "netVidTx"
                case 8:
                    curType = "netVidRx"
                case 9:
                    curType = "network"
                case 10:
                    curType = "pdus"
                case _:
                    curType = "unknown"
                    
            if curType != "unknown":
                curIP = get_address(curType)
                #find line referenced by unknownDev to update IP
                line = unknownDevs[selectedDev]
                csvLine = fileLines[line]
                if len(csvLine) >= NUM_FIELDS:
                    csvLine[9] = curIP
                
                devices[curType].append(selectedDev)
                unknownList.remove(selectedDev)
                

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
def is_valid(provided: int, accepted) -> bool:
    """Determines if any one object in accepted matches provided"""
    valid = False
    for num in accepted:
        if int(provided) == num:
            valid = True
            break

    return valid

def is_valid_range(provided: str, minAccepted: int, maxAccepted: int) -> bool:
    """Determines if provided value is between 1 and the maxAccepted value."""

    valid = False
    if str(provided).isdigit():
        valid = int(provided) >= int(minAccepted) and int(provided) <= maxAccepted
    return valid

def get_type(name: str) -> str:
    """Determines the device type given the device name, assuming standard format (e.g. DEC-101 -> DEC)"""

    #filter out device number
    hyphenInd = name.find("-")
    filteredName = name[:hyphenInd]

    match filteredName:
        case "CPRO":
            devType = "processor"
        case "DSP":
            devType = "dsp"
        case "MIC":
            devType = "mics"
        case "CAM":
            devType = "cams"
        case "TPT":
            devType = "touchpanels"
        case "TP":
            devType = "touchpanels"
        case "AMP":
            devType = "audioDev"
        case "EXP":
            devType = "netVidTx"
        case "AVB":
            devType = "netVidTx"
        case "PDU":
            devType = "pdus"
        case "ENC":
            devType = "netVidTx"
        case "DEC":
            devType = "netVidRx"
        case "NSW":
            devType = "network"
        case "WAP":
            devType = "network"
        case _:
            devType = "unknown"

    return devType

def get_dl_path():
    """__Determine the path to the downloads folder based on OS"""
    system = platform.system()
    
    if system == 'Windows':
        dlPath = Path(os.environ['USERPROFILE']) / 'Downloads'
    elif system in ('Linux', 'Darwin'): #Darwin == OSX
        dlPath = Path.home() / 'Downloads'
    else:
        raise OSError(f"Unsupported Operating System: {system}")
    #TODO add ability for user to specify output path
    
    
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
        assigned = True
    #if we find any devices we can't identify, fix them
    if len(unknownDevs) > 0:
        fix_unknowns()
    
    if assigned:
        write_file()


main()
