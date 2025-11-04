""" Tarmac analyzer to add notes to the tarmac file to make debug easier.

This Python application reads in a tarmac trace file and adds notes or annotations to
the tarmac file making analyzing the tarmac file simpler.  This application uses the
list file, source code files, and a list of critical variables and registers to add
notes such as the following:

    o Call tree
    o function prototypes with function entry and exit
    o Global variable and register accesses

A tarmac file is an assembly-level trace file produced during RTL simulation, which
shows a trace of the instructions executed and memory accessed by the processor
during execution of the fimrware in the ARM processor.  The following is an
example of a tarmac file:

      22225 ns IT 10000076 488e        LDR      r0,[pc,#568]  ; [0x100002b0]
      22425 ns MR4_D 100002b0 2001ec00
      22425 ns R r0 2001ec00
      22425 ns IT 10000078 2600        MOVS     r6,#0
      22525 ns MR4_I 1000007c 4a724971
      22525 ns R r6 00000000
      22525 ns IT 1000007a 6006        STR      r6,[r0,#0]
      22625 ns R psr 41000200

The following shows an example of the tarmac file with annotations:

    @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
    LOG_ILogWaypointValue entry (2000afc0) 
    C:\\prod\\tags\\Project_06.07.09.02\\Source\\Log\\Log_Handlers.c
    void LOG_ILogWaypointValue( uint32 logVal )
        Project_AppMain -> Project_AppExecute -> Project_ILogWriteDebugString -> Project_ILogWriteDebugvalue -> LOG_ILogWaypointValue

    454166925 ns IT 2000afc0 b510        PUSH     {r4,lr}
    454167025 ns MR4_I 2000afc4 49076008
    454167125 ns MW4_D 2001fe48 40240000
    454167225 ns MW4_D 2001fe4c 2000a241
    454167225 ns R r13 2001fe48 (MSP)
    ...
    454167825 ns MW4_D 40240a5c 33000609                        ; REGISTER_Waypoint <= 33000609
    454167825 ns IT 2000afc6 4907        LDR      r1,[pc,#28]  ; [0x2000afe4]
    454168025 ns MR4_D 2000afe4 2001ec00
    454168025 ns R r1 2001ec00
    454168025 ns IT 2000afc8 680a        LDR      r2,[r1,#0]
    454168125 ns MR4_I 2000afcc 50e04c06
    454168225 ns MR4_D 2001ec00 00000072                        ; ADDRESS_Glb_LogCounter => 00000072
    454168225 ns R r2 00000072

Set the variableDictionary and default path strings prior to executing this Python
application.  See the argumentParser for a list of available parameters. 

Copyright (c) 2022 - 2025 Twiddleware

Permission is hereby granted, free of charge, to any person obtaining a copy of this
software and associated documentation files (the "Software"), to deal in the Software
without restriction, including without limitation the rights to use, copy, modify,
merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to the following
conditions:

The above copyright notice and this permission notice shall be included in all copies
or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

__author__     = "Chris Gilbert"
__contact__    = "chris@twiddleware.com"
__copyright__  = "Copyright 2022 - 2025, Twiddleware"
__date__       = "2025/08/24"
__deprecated__ = False
__email__      = "chris@twiddleware.com"
__license__    = "GPLv3"
__maintainer__ = "developer"
__status__     = "production"
__version__    = "0.2.0"


# Dependencies
import os
import argparse
import glob
import re

import clang.cindex
from clang.cindex import CursorKind
from datetime import datetime


def ParseCFunctions(sourceFilesPath, functions):
    """
    Parses a .c file and returns a list of function declarations.
    Each function declaration is represented as a dictionary with 'filename', 'returnType', 'name', and 'parameters'.
    """
    sourceFileList = glob.glob(f"{sourceFilesPath}\\**\\*.c", recursive=True)

    if sourceFileList:
        print (os.path.basename(__file__) + ": info: source file path      = " + sourceFilesPath)

        for sourceFileName in sourceFileList:

            if "tinycbor" not in sourceFileName.lower():
                print (os.path.basename(__file__) + ": info: parsing file          = " + sourceFileName)

                try:
                    with open(sourceFileName, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                except FileNotFoundError:
                    print(f"File {sourceFileName} not found.")
                    return []

                # Regular expression to match function declarations
                pattern = r'([a-zA-Z0-9_* ]+) ([a-zA-Z_][a-zA-Z0-9_]*)\(([^)]*)\)'
                matches = re.findall(pattern, content)
                
                for match in matches:
                    returnType = match[0].strip()
                    name = match[1]
                    params = match[2].strip()
                    
                    if returnType != '':
                        # Split parameters into individual params, handling commas within pointers
                        parameterList = []
                        currentParameter = ""
                        depth = 0

                        for char in params:
                            if char == '(':
                                depth += 1
                            elif char == ')':
                                depth -= 1
                            elif char == ',' and depth == 0:
                                parameterList.append(currentParameter.strip())
                                currentParameter = ""
                            else:
                                currentParameter += char

                        if currentParameter:
                            parameterList.append(currentParameter.strip())

                        functions.append({
                            'fileName': sourceFileName,
                            'returnType': returnType,
                            'name': name,
                            'parameters': parameterList
                        })

    return functions

FORMAT_OPCODE_INDEX            = 5
FORMAT_OPCODE_PARAMETER_INDEX  = 6
FORMAT_OPCODE_BL_ADDRESS_INDEX = 10

FORMAT_TRANSACTION_TYPE_INDEX  = 2
FORMAT_ADDRESS_INDEX           = 3
FORMAT_THUMB_INDEX             = 3
FORMAT_THUMB_ADDRESS_INDEX     = 4
FORMAT_THUMB_OPCODE_INDEX      = 5

FORMAT_THUMB_STRING            = "NOT_IN"

BANNER_FUNCTION_START_STRING  = "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@\n"
BANNER_FUNCTION_RETURN_STRING = "########################################################################################################################\n"
BANNER_FUNCTION_RESUME_STRING = "<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<\n"
BANNER_FUNCTION_EXIT_STRING   = ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>\n"

variableDictionary = {
    "20000000": "ADDRESS_RamVecTable",
    "20000000": "ADDRESS_RamVecTable0",
    "20000004": "ADDRESS_RamVecTable1",
    "20000008": "ADDRESS_RamVecTable2",
    "2000000c": "ADDRESS_RamVecTable3",
    "20000010": "ADDRESS_RamVecTable4",
    "20000014": "ADDRESS_RamVecTable5",
    "20000018": "ADDRESS_RamVecTable6",
    "2000001c": "ADDRESS_RamVecTable7",
    "20000020": "ADDRESS_RamVecTable8",
    "20000024": "ADDRESS_RamVecTable9",
    "20000028": "ADDRESS_RamVecTable10",
    "2000002c": "ADDRESS_RamVecTable11",
    "20000030": "ADDRESS_RamVecTable12",
    "20000034": "ADDRESS_RamVecTable13",
    "20000038": "ADDRESS_RamVecTable14",
    "2000003c": "ADDRESS_RamVecTable15",
    "20000040": "ADDRESS_RamVecTable16",
    "20000044": "ADDRESS_RamVecTable17",
    "20000048": "ADDRESS_RamVecTable18",
    "2000004c": "ADDRESS_RamVecTable19",
    "20000050": "ADDRESS_RamVecTable20",
    "20000054": "ADDRESS_RamVecTable21",
    "20000058": "ADDRESS_RamVecTable22",
    "2000005c": "ADDRESS_RamVecTable23",
    "20000060": "ADDRESS_RamVecTable24",
    "20000064": "ADDRESS_RamVecTable25",

    # Registers
    "40240000": "REGISTER_AdcOutput0",
    "40240004": "REGISTER_AdcOutput0",
    "40240008": "REGISTER_AdcOutput0",
    "4024000c": "REGISTER_AdcOutput0",
}

# Default Path Strings
PATH_SOURCE_DEFAULT       = "C:\\Projects\\Fw\\prod\\branches\\"
PATH_TAGS_DEFAULT         = "C:\\Projects\\Fw\\prod\\tags\\"
PATH_INFO_SUBFOLDER       = "\\Release\\Deliverables\\Info\\"

FILENAME_ASSEMBLY_EXT_DEFAULT   = ".txt"
FILENAME_ASSEMBLY_DEFAULT       = "Project_Assembly"
FILENAME_ASSEMBLY_FULL_DEFAULT  = FILENAME_ASSEMBLY_DEFAULT + FILENAME_ASSEMBLY_EXT_DEFAULT

# Process the application arguments.
argumentParser = argparse.ArgumentParser(description='Annotate the tarmac file with additional information for analysis.',
                                         epilog='Example: > python tarmac-plus-notes.py 20250814\\tarmac.log --tag Tag_01.02.03')

# Required positional argument
argumentParser.add_argument('tarmacFilename',    help='Input tarmac filename.')
argumentParser.add_argument('listFilename',      nargs='?', default=".txt", help='Input list filename.')
argumentParser.add_argument('annotatedFilename', nargs='?', default=".log", help='Output annotated tarmac filename.')
argumentParser.add_argument('--path',            type=str, default="", help='Path to the C source files for function parameter annotation.')
argumentParser.add_argument('--stack',           default=False, action='store_true', help='Generate a stack trace file.')
argumentParser.add_argument('--source',          default=False, action='store_true', help='Add assembly code annotation.')
argumentParser.add_argument('--tag',             type=str, default="", help='SVN tag to append to the default path, e.g. Tag_01.02.03.')
argumentParser.add_argument('--ticket',          type=str, default="", help='Jira ticket ID to append to the default path.')

commandLineArgument = argumentParser.parse_args()

# Verify that the tarmac file exists.
tarmacFilename    = commandLineArgument.tarmacFilename
listFilename      = commandLineArgument.listFilename
annotatedFilename = commandLineArgument.annotatedFilename
sourceFilesPath   = commandLineArgument.path
jiraTicket        = commandLineArgument.ticket
svnTag            = commandLineArgument.tag
isStack           = commandLineArgument.stack
isSource          = commandLineArgument.source

if not os.path.isfile(tarmacFilename):
    print (os.path.basename(__file__) + ": error: tarmac file not found - " + tarmacFilename + "\n")
    argumentParser.print_help()
    exit()

if sourceFilesPath:
    print (os.path.basename(__file__) + ": info: source file path      = " + sourceFilesPath)

if jiraTicket:
    sourceFilesPath = PATH_SOURCE_DEFAULT + jiraTicket
    print (os.path.basename(__file__) + ": info: source file path      = " + sourceFilesPath)

if svnTag:
    sourceFilesPath = PATH_TAGS_DEFAULT + svnTag
    print (os.path.basename(__file__) + ": info: source file path      = " + sourceFilesPath)

if not sourceFilesPath:
    sourceFilesPath = PATH_SOURCE_DEFAULT

    if not os.path.isdir(sourceFilesPath):
        print (os.path.basename(__file__) + ": error: default source file path, " + sourceFilesPath + " not found\n")
        argumentParser.print_help()
        exit()
    else:
        print (os.path.basename(__file__) + ": info: default source path   = " + sourceFilesPath)

# Verify that the list file exists or attempt to find the list file.
if listFilename == ".txt":
    # Add the path from the tarmac file to list filename.
    listFilename = FILENAME_ASSEMBLY_FULL_DEFAULT
    listFilename = os.path.join(os.path.dirname(tarmacFilename), listFilename)

    # If the default list file does not exist, search for the first .txt file in the input tarmac file folder. 
    if not os.path.isfile(listFilename):
        listFilename = listFilename.replace(FILENAME_ASSEMBLY_DEFAULT, "*")

        fileList = glob.glob(listFilename)

        if len(fileList) > 0:
            listFilename = fileList[0]

    # If the default list file does not exist, search for the first .txt file in the SVN tag folder. 
    if not os.path.isfile(listFilename):
        if svnTag or jiraTicket:
            listFilename = sourceFilesPath + PATH_INFO_SUBFOLDER + "*" + FILENAME_ASSEMBLY_EXT_DEFAULT

        else:
            listFilename = ""

        if len(listFilename) > 0:
            fileList = glob.glob(listFilename)

            if len(fileList) > 0:
                listFilename = fileList[0]

if not os.path.isfile(listFilename):
    print (os.path.basename(__file__) + ": error: list file not found - " + listFilename + "\n")
    argumentParser.print_help()
    exit()

if annotatedFilename == ".log":
    # Get the current date and time
    currentDateTime = datetime.now()

    # Format the datetime object into a string suitable for a filename
    # Example format: YYYYMMDD_HHMMSS
    timeStampPostFix = "-update-" + currentDateTime.strftime("%Y%m%d-%H%M%S") + "."

    annotatedFilename = tarmacFilename.replace(".", timeStampPostFix)

print (os.path.basename(__file__) + ": info: tarmac file name      = " + tarmacFilename)
print (os.path.basename(__file__) + ": info: list file name        = " + listFilename)
print (os.path.basename(__file__) + ": info: output file name      = " + annotatedFilename)

stackFilename = ""

if isStack:
    stackFilename = tarmacFilename.replace(".", "-stack.")
    print (os.path.basename(__file__) + ": info: stack trace file name = " + stackFilename)

print ("")

functionAddressList = []
functionBranchStack = []
functionNameList    = []
functionStack       = []

sourceDictionary    = {}

functionName        = "default"
isSymbolFound       = False

symbolsMissingCount    = 0
functionExecutionCount = 0

# Process the list file.
print ("List file processing started...........................................")

with open(listFilename, "r") as listFile:
    while line := listFile.readline():
        lineTokens = line.split()

        if len(lineTokens) > 4:
            isIdentifier = re.search("^0x[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]:", lineTokens[0])

            address = lineTokens[0].replace(":", "")
            address = address.replace("0x", "")
            sourceDictionary[address] = f"{lineTokens[3]:<9}{lineTokens[4]}"
        else:
            isIdentifier = False

        if isSymbolFound:
            isSymbolFound = False

            if isIdentifier:
                address = lineTokens[0].replace(":", "")
                address = address.replace("0x", "")
                functionAddressList.append(address)
                functionNameList.append(functionName)

        if not isSymbolFound:
            if len(lineTokens) == 1:
                isIdentifier = re.search("^_*[a-zA-Z]+[a-zA-Z0-9_]+$", lineTokens[0])
                if isIdentifier:
                    isSymbolFound = True
                    functionName = lineTokens[0]

print ("List file processing complete..........................................")

# Process the C source files.
print ("Source file processing started...........................................")

functionDictionary = []
functionDictionary = ParseCFunctions(sourceFilesPath, functionDictionary)

print ("Source file processing complete..........................................")

# Annotate the tarmac file.
print ("Tarmac file processing started.........................................")

countLines    = 0
countProgress = 0

if isStack:
    # Open the stack file if requested.
    stackFile = open(stackFilename, "w")

with open(tarmacFilename, "r") as tarmacFile:
    with open(annotatedFilename, "w") as outputFile:

        isPopInProgress = False
        isEventPending  = False
        isNotThumbState = False

        while line := tarmacFile.readline():
            lineTokens    = line.split()
            newLine       = ""
            newLineSuffix = ""
            newLineAfter  = ""
            functionName  = ""

            # Show progress on longer files.
            countLines += 1

            if countLines > 100000:
                countLines = 0
                countProgress += 1

                if countProgress > 70:
                    countProgress = 1

                if countProgress == 1:
                    print ('Processing...', end = '', flush = True)
                else:
                    print ('.', end = '', flush = True)

            if isNotThumbState:
                if len(lineTokens) == FORMAT_OPCODE_PARAMETER_INDEX:
                    if lineTokens[FORMAT_THUMB_INDEX].startswith(FORMAT_THUMB_STRING):
                        opcodeString = lineTokens[FORMAT_THUMB_OPCODE_INDEX][:2]

                        # Add specific opcodes for additional processing.
                        if opcodeString == "b5":
                            # Reformat the token list, so it appears as a PUSH.
                            # 0       1  2  3                  4        5        6
                            #------------------------------------------------------------
                            # 1727807 ns IT 10001abc           b510     PUSH     {r4,lr}
                            # 1728519 ns IT 10001ad0           bd10     POP      {r4,pc}
                            # 3658031 ns E  NOT_IN_THUMB_STATE 100017a2 b570
                            #
                            thumbLineTokens = lineTokens
                            lineTokens[FORMAT_ADDRESS_INDEX    ] = lineTokens[FORMAT_THUMB_ADDRESS_INDEX    ]
                            lineTokens[FORMAT_ADDRESS_INDEX + 1] = lineTokens[FORMAT_THUMB_ADDRESS_INDEX + 1]
                            lineTokens[FORMAT_ADDRESS_INDEX + 2] = "PUSH"
                            lineTokens.append("{{pc}}")

                        elif opcodeString == "bd":
                            # Search for POP.
                            thumbLineTokens = lineTokens
                            lineTokens[FORMAT_ADDRESS_INDEX    ] = lineTokens[FORMAT_THUMB_ADDRESS_INDEX    ]
                            lineTokens[FORMAT_ADDRESS_INDEX + 1] = lineTokens[FORMAT_THUMB_ADDRESS_INDEX + 1]
                            lineTokens[FORMAT_ADDRESS_INDEX + 2] = "POP"
                            lineTokens.append("{{pc}}")

                        elif lineTokens[FORMAT_THUMB_OPCODE_INDEX] == "bf30":
                            lineTokens[FORMAT_THUMB_OPCODE_INDEX] = "WFI"

                            if not isSource:
                                line = line.rstrip()
                                line = line + "                        ; WFI\n"

                        if isSource:
                            # Add the source code if present.
                            address = lineTokens[FORMAT_THUMB_ADDRESS_INDEX]
                            if not sourceDictionary.get(address) == None:
                                line = line.rstrip()
                                line = f"{line:<60}{sourceDictionary.get(address)}\n"

            if len(lineTokens) > FORMAT_OPCODE_BL_ADDRESS_INDEX:
                if lineTokens[FORMAT_OPCODE_INDEX] == "BL":
                    newLineAfter = BANNER_FUNCTION_RESUME_STRING
                    functionExecutionCount += 1

                    # Extract the address.
                    address = lineTokens[FORMAT_OPCODE_BL_ADDRESS_INDEX]
                    address = address.replace("0x", "")

                    if address in functionAddressList:
                        indexInList  = functionAddressList.index(address)
                        functionName = functionNameList[indexInList]

                        # The branch and link instruction sets the link register.  If there was a
                        # previous value, it is overwritten.  This doesn't need to be a stack, but
                        # is implemented as a stack for future development.
                        functionBranchStack.clear()
                        functionBranchStack.append(functionName)
                        newLineAfter = functionName + "\n" +  newLineAfter
                        isEventPending = True

            elif len(lineTokens) >= FORMAT_OPCODE_PARAMETER_INDEX:
                # If an event is pending, the annotation is paused until a token triggers the
                # information to be printed.
                if isEventPending:
                    if lineTokens[FORMAT_TRANSACTION_TYPE_INDEX] == "IT" or lineTokens[FORMAT_TRANSACTION_TYPE_INDEX] == "E":
                        isEventPending = False

                if isPopInProgress:
                    if lineTokens[FORMAT_TRANSACTION_TYPE_INDEX] == "IT" or lineTokens[FORMAT_TRANSACTION_TYPE_INDEX] == "E":
                        newLine = BANNER_FUNCTION_RESUME_STRING
                        isPopInProgress = False

                        if len(functionStack) > 0:
                            functionName = functionStack[-1]
                            indexInList  = functionNameList.index(functionName)
                            address      = functionAddressList[indexInList]
                            newLine = functionName + " resuming...\n" + newLine

                if lineTokens[FORMAT_OPCODE_INDEX] == "PUSH":
                    isPopInProgress = False
                    newLineAfter    = ""

                    if newLine == "":
                        newLine = BANNER_FUNCTION_START_STRING
                    else:
                        newLine = newLine + BANNER_FUNCTION_START_STRING
                    functionExecutionCount += 1

                    # Extract the address.
                    address = lineTokens[FORMAT_ADDRESS_INDEX]

                    if address in functionAddressList:
                        indexInList  = functionAddressList.index(address)
                        functionName = functionNameList[indexInList]
                        functionStack.append(functionName)
                        newLine = newLine + functionName + " entry (" + address + ") " + "\n"

                        if functionDictionary:
                            functionEntry = next((item for item in functionDictionary if item["name"] == functionName), None)

                            if functionEntry:
                                newLine = newLine + functionEntry["fileName"] + "\n"
                                newLine = newLine + functionEntry["returnType"] + " " + functionEntry["name"] + "( " + ", ".join(functionEntry["parameters"]) + " )\n"

                        # Add an abbreviated call tree.
                        if len(functionStack) > 1:
                            newLineSuffix = "    "

                            if len(functionStack) > 8:
                                newLineSuffix = newLineSuffix + "..." + " -> "

                            if len(functionStack) > 7:
                                newLineSuffix = newLineSuffix + functionStack[-7] + " -> "

                            if len(functionStack) > 6:
                                newLineSuffix = newLineSuffix + functionStack[-6] + " -> "

                            if len(functionStack) > 5:
                                newLineSuffix = newLineSuffix + functionStack[-5] + " -> "

                            if len(functionStack) > 4:
                                newLineSuffix = newLineSuffix + functionStack[-4] + " -> "

                            if len(functionStack) > 3:
                                newLineSuffix = newLineSuffix + functionStack[-3] + " -> "

                            if len(functionStack) > 2:
                                newLineSuffix = newLineSuffix + functionStack[-2] + " -> "

                            newLineSuffix = newLineSuffix + functionStack[-1] + "\n"
                    else:
                        symbolsMissingCount += 1

                elif lineTokens[FORMAT_OPCODE_INDEX] == "POP":
                    newLineAfter = BANNER_FUNCTION_EXIT_STRING

                    if len(functionStack) > 0:
                        functionName = functionStack.pop()
                        indexInList  = functionNameList.index(functionName)
                        address      = functionAddressList[indexInList]
                        newLineAfter = functionName + " exiting...\n" + newLineAfter
                        isPopInProgress = True

                elif lineTokens[FORMAT_OPCODE_INDEX] == "BX":
                    newLineAfter = BANNER_FUNCTION_EXIT_STRING

                    if len(functionBranchStack) > 0:
                        functionName = functionBranchStack.pop()
                        indexInList  = functionNameList.index(functionName)
                        address      = functionAddressList[indexInList]
                        newLineAfter = functionName + " exiting...\n" + newLineAfter
                        isPopInProgress = True

                elif lineTokens[FORMAT_OPCODE_INDEX] == "WFI":
                    if len(functionStack) > 3:
                        # Remove the two functions that do not use pop when the function is complete.
                        if functionStack[-1] == "Main_ResetWakeup":
                            functionStack.pop()
                        if functionStack[-1] == "Reset_Handler_rom":
                            functionStack.pop()

                else:
                    if not isNotThumbState:
                        if lineTokens[FORMAT_TRANSACTION_TYPE_INDEX] == "E":
                            if lineTokens[FORMAT_THUMB_INDEX].startswith(FORMAT_THUMB_STRING):
                                isNotThumbState = True
                                print ("Information: Tarmac file from DIDO resulting in reduced information.")
                
                if isStack:
                    if lineTokens[FORMAT_OPCODE_INDEX] == "(MSP)":
                        if len(functionStack) > 0:
                            newLine = line.rstrip()
                            newLine = newLine + "    ; " + functionStack[-1] + "\n"
                            stackFile.write(newLine)
                            newLine = ""
                        else:
                            stackFile.write(line)
    
            elif len(lineTokens) >= FORMAT_OPCODE_INDEX:
                if lineTokens[FORMAT_TRANSACTION_TYPE_INDEX] == "MR4_D" or lineTokens[FORMAT_TRANSACTION_TYPE_INDEX] == "MW4_D":
                    # Extract the address.
                    address = lineTokens[FORMAT_ADDRESS_INDEX]

                    if not variableDictionary.get(address) == None:
                        line = line.rstrip()
                        line = line + "                        ; " + variableDictionary.get(address)
                        
                        if lineTokens[FORMAT_TRANSACTION_TYPE_INDEX] == "MW4_D":
                            line = line + " <= "
                        else:
                            line = line + " => "
                        
                        line = line + lineTokens[4] + "\n"

            if newLine != "":
                outputFile.write("\n")
                outputFile.write(newLine)

                if newLineSuffix != "":
                    outputFile.write(newLineSuffix)

                outputFile.write("\n")

            outputFile.write(line)

            if not isEventPending:
                if newLineAfter != "":
                    outputFile.write("\n")
                    outputFile.write(newLineAfter)
                    outputFile.write("\n")
            
        # The complete tarmac file was read.

if isStack:
    # Open the stack file if requested.
    stackFile.close()

if countProgress > 0:
    print ("")

print ("Tarmac file processing complete........................................\n")

print('Number of functions from list file          = {:d}'.format(len(functionNameList)))
print('Number of functions executed in tarmac file = {:d}'.format(functionExecutionCount))
print('Missing function name count                 = {:d}'.format(symbolsMissingCount))

if symbolsMissingCount > 5:
    print('A large number of missing function names may mean the tarmac file and the list file are not in sync.')
    print('A number of functions were executed in the tarmac file that were not found in the list of functions.')
    print('Note: only functions executed with PUSH are identified as executed functions.')