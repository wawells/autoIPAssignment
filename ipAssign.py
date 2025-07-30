""" 
Relevant Header Info:
Location | Manufacturer | Model | Design Name | Switch | Switch Port | Mac Address | Serial Number | Firmware Version | Primary IP address | Secondary IP Address | Subnet | Gateway | VLAN | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | User Name | Password

IP Ranges 132.1.0.xxx

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

Device Types = {
    "processor":"CPRO",
    "dsp":"DSP",
    "mics":"MIC",
    "cams":"CAM",
    "touchpanels":"TPT",
    "audioDev","AMP",
    "expander":"EXP",
    "avb":"AVB",
    "pdu":"PDU"
    "encoder": "ENC"
    "decoder": "DEC"
    "Switch": "NSW"
    "Access Point": "WAP"

}


1. have user paste deivce list directly or import CSV from file
2. Delimit file based on comma, tab, or 3+ spaces
3. Separate devices into multi-dimensional array, assume 3+ blank rows indicates end of file
4. Assign IPs for devices, microphones CAN use multiple IPs, gather this from "Dante" in mac address field
5. Create CSV with updated devices, place in downloads folder, show header and first 3 rows of data in command line. How else can we show the output to make it convenient to paste into file?

"""

#global resources
sourceFile = "DNE"
sourceInput = "DNE"
header = "DNE"
outputFile = ""
ips = {}
devices = {}
fileLines = []
unknownDevs = []
blankLine = "---,---,---,---,---,---,---,---,---,---,---,---,---,---,---,---,---,---,---,---,---,---,---,---,---,---,\n"

INVALID = -1
PASTING_VALS = 1
PROVIDING_PATH = 2
IPSTART = "132.1.0."
numDevices = 0


#test path
testPath = '/Users/alex/Downloads/TED(Project- TED- Training - Colab ).csv'

#--------------------------------------METHODS--------------------------------------#

#Prompts user for input format and data, then executes populates IPs for the provided data if possible
def getInput():
    """
    importType = INVALID
    while not isValid(importType, [PASTING_VALS, PROVIDING_PATH]):
        importType = input("Will you be (1)pasting values or (2)providing a CSV file path? ")
    

    if int(importType) == PASTING_VALS:
        data = input("Enter pasted values here: ")
        parseData(data)
    else:
    """
    if True:
        #file path
        validFile = False
        while not validFile:
            #file_path = input("Enter the full path to the CSV file here: ")
            file_path = testPath
            try:
                with open(file_path, "r") as file:
                    if file_path.endswith(".csv"): 
                        validFile = True
                    else:
                        print("Invalid File Format. Please Use a CSV")
                    numBlanks = 0
                    currentLine = file.readline()
                    while currentLine != "" and numBlanks < 3:
                        #3 consecutive "blank" lines assumes EoF
                        if currentLine == blankLine:
                            numBlanks = numBlanks + 1
                        else: 
                            numBlanks = 0
                        fileLines.append(currentLine)
                        currentLine = file.readline()
                        
            except FileNotFoundError:
                print(f"File not found at '{file_path}'. Please try again.")
            except PermissionError:
                print(f"No permission to access '{file_path}'. Please try again.")
            except Exception as e:
                print(f"Unexpected error: {e}. Please try again.")    

    #at this point we should have populated the fileLines from either paste or file parsing, now we group devices and assign IPs
    if len(fileLines) > 0:
        assignDevices()
    
    if len(unknownDevs) > 0:
        fixUnknowns()

#establishes the IP scheme for the program
def createPools():
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


#Parses the pasted device table from user input
def parseData(data: str):
    return 0


#Given the type of the device, determines the next IP in the range to assign to the device
def getAddress(typeName: str) -> int:
    #get leading values of IP
    newAddress = str(IPSTART)
    
    #find next IP to assign based on device type
    num = ips.get(typeName)
    newAddress = newAddress + str(num)

    #increment next available IP and update dict
    num = num + 1
    ips[typeName] = num

    return newAddress


#Iterates through populated list of lines provided by user and assigns IPs
def assignDevices():
    for line in range(len(fileLines)):
        #if we have -, we are likely looking at rows with devices
        if "-" in fileLines[line]:
            #separate line into individual fields
            parsedLine = fileLines[line].split(",")

            #extract the device from the information
            if len(parsedLine) > 3:
                deviceID = parsedLine[3].strip()
                deviceID = str(deviceID)

                curType = getType(deviceID)
                if curType != "unknown":
                    ipaddr = getAddress(curType)
                    devices[curType].append(deviceID)
                    # TODO write the generated IP address to the list
                else:
                    #determine if the unknown is valid or a parsing error
                    if not deviceID.isspace() and deviceID != "---":
                        hyphenInd = deviceID.find("-")
                        if hyphenInd > 0:
                            devNum = deviceID[hyphenInd+1:]
                            if devNum.isdigit():
                                unknownDevs.append(deviceID)
                            else:
                                print("Unknown Device Skipped; Non-numeric: " + deviceID)
                        else:
                           print("Unknown Device Skipped; Missing '-': " + deviceID)     
                    else:
                        print("Unknown Device Skipped; Missing Device: " + deviceID)



#Requests user assistance with assigning IPs to atypical devices
def fixUnknowns():
    if len(unknownDevs) > 0:
        print("The following devices were unable to be identified: ")
        for dev in range(len(unknownDevs)):
            adjNum = dev + 1
            print(str(adjNum) + ") " + unknownDevs[dev])

        unknownSel = INVALID
        while not isValidRange(unknownSel, 1, len(unknownDevs)):
            unknownSel = input("Select a device to assign to a category: ")
        adjSel = int(unknownSel) - 1
            
        print("Selected Device: " + unknownDevs[adjSel])
        print("0) Back\n1) Processor\n2) DSP\n3) Microphone\n4) Camera\n5) Touchpanel\n6) Audio Device\n7) Transmitter\n8) Receiver\n9) Network")

        catSel = INVALID
        while not isValidRange(catSel, 0, 9):
            catSel = input("Select a category for the selected device, or go back: ")


#--------------------------------------Helper Methods--------------------------------------#
#Determines if any one object in accepted matches provided
def isValid(provided: int, accepted) -> bool:
    valid = False
    for num in accepted:
        if int(provided) == num:
            valid = True
            break

    return valid

#Determines if provided value is between 1 and the maxAccepted value.
def isValidRange(provided: str, minAccepted: int, maxAccepted: int) -> bool:
    valid = False
    if str(provided).isdigit():
        valid = int(provided) >= int(minAccepted) and int(provided) <= maxAccepted
    return valid

#Determines the device type given the device name, assuming standard format (e.g. DEC-101)
def getType(name: str) -> str:
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
            devType = "netVidTx" #TODO figure out a better IP scheme assignment here
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

#--------------------------------------Main--------------------------------------#

def main():
    createPools()
    getInput()


#main()

unknownDevs.append("WOW-101")
unknownDevs.append("WOW-102")

fixUnknowns()