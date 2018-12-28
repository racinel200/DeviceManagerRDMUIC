import subprocess
import sys
import os
import json
from flask import Flask, render_template, jsonify, request, make_response
from flask_socketio import SocketIO,send,emit,join_room,leave_room
import urllib
import signal
import shlex
import signal
from threading import Timer
import mysql.connector
from discord_webhook import DiscordWebhook
import shutil
import threading
import time
from time import gmtime, strftime
from datetime import datetime
from flask import send_file

reload(sys)
sys.setdefaultencoding('utf8')

Devices = dict()
DeviceProcesses = dict()




app= Flask(__name__)
app.config['SECRET_KEY'] = "mysecret"
socketio = SocketIO(app)
checkDevicesFlag = True
currentBuilds = 0

maxBuildsMessageSent = 0
StartedUpMessageSent = dict()

@app.route("/DeviceManager/ReloadConfig",methods=['GET'])
def LoadConfig():

    f= open("DeviceManagerConfig.json","r+")

    configString = f.read()
    configJson = json.loads(configString)

    global mySqlHost
    mySqlHost = configJson["mySqlHost"]
    global dbUser
    dbUser = configJson["dbUser"]
    global dbPW
    dbPW = configJson["dbPW"]
    global dbPort
    dbPort = configJson["dbPort"]
    global dbTimeout
    dbTimeout = configJson["dbTimeout"]
    ### WEbhook Discord Messages are sent to ###
    global NotificationWebhookURL
    NotificationWebhookURL = configJson["NotificationWebhookURL"]
    ##Default UI Folder###
    global uiControlFolder
    uiControlFolder = configJson["uiControlFolder"]
    #Time Between running check on All Devices
    global delayTime
    delayTime = configJson["delayTime"]
    ##Default Backend URL##
    global backendURL
    backendURL = configJson["backendURL"]
    ###Max Number of Builds At the Same Time###
    global maxBuilds
    maxBuilds = configJson["maxBuilds"]
    ## max Raid Time #####
    global raidMaxTime
    raidMaxTime = configJson["raidMaxTime"]
    ##Number ofLog files to keep for Device ###
    global logFilesToKeep
    logFilesToKeep = configJson["logFilesToKeep"]
    ##### Times you want to keep trying to start a device before removing it from building interval####
    
    ##### Time between Each IPA Install####
    global IpaDelay
    IpaDelay = configJson["IpaDelay"]
    ###How long you want to wait to restart the build if it doesnt start####
    global StartupWaitTime
    StartupWaitTime = configJson["StartupWaitTime"]
    ###How long to wait before sending a message that a device has not contacted the DB in a while##
    global DBLastUpdatedThreshold
    DBLastUpdatedThreshold = configJson["DBLastUpdatedThreshold"]
    ###How long to wait after the app has started for it to contact the db###
    global DeviceStartupDBContactDelay
    DeviceStartupDBContactDelay = configJson["DeviceStartupDBContactDelay"]
    global Errors
    Errors = configJson["Errors"]
    global UninstallErrors
    UninstallErrors= configJson["UninstallErrors"]
    global DDFolderRebuildErrors
    DDFolderRebuildErrors = configJson["DDFolderRebuildErrors"]
    global NoContactDBRestartTime
    NoContactDBRestartTime = configJson["NoContactDBRestartTime"]
    global minDelayLogout
    minDelayLogout = configJson["minDelayLogout"]
    global targetMaxDistance
    targetMaxDistance = configJson["targetMaxDistance"]
    global DeviceManagerAPIPort
    DeviceManagerAPIPort = configJson["DeviceManagerAPIPort"]
    print("ConfigFileLoaded")
    global DeviceManagerTableString
    DeviceManagerTableString = configJson["DeviceManagerTableString"]
    global dashboardURL
    dashboardURL = configJson["dashboardURL"]
    return "Config File Loaded"



f= open("RDM_Devices.json","r+")

DeviceString = f.read()
Devices = json.loads(DeviceString)

def startDeviceProcessArgument(device):
    
    global backendURL
    global Devices
    
    
    
    
    
    print(device)
    
    LogDir = "DeviceLogs/" + str(device) + "/"
    deviceName = device
    if not os.path.exists(os.path.dirname(LogDir)):
        os.makedirs(os.path.dirname(LogDir))

    
    ConsoleFile= open("DeviceLogs/" + str(device) + "/Output.log","w")
    ErrFile= open("DeviceLogs/" + str(device) + "/Err.log","w")
    
    for dk,d in Devices.items():
        if device == d['DeviceName']:
            deviceName = d['DeviceName']
            Devices[dk]["DeviceBuilding"] = True
            print("Found "+ deviceName)
            device = dk
            if d['DeviceFolder'] != "":
                cwdF = d['DeviceFolder']
            else:
                cwdF = uiControlFolder
            if len(d['BackEndUrl']) > 0:
                backendURL = d['BackEndUrl']
            else:
                backendURL = backendURL
            
            if len(d['EnableAccountManager']) > 0:
                enableAccountManager = d['EnableAccountManager']
            else:
                enableAccountManager = 'true'
            
            print("Device ID")
            print(dk)

    print("BackendURL is " + str(backendURL))
    cd = os.getcwd()

    workspacePath = cd +"/"+ cwdF
    print(cwdF)
    
    #RealDeviceMap-UIControl-Beta-Iphone10

    
    filePath = cwdF + "/" + Devices[device]['DeviceFolder']
    print(filePath)
    DdFilePath = "../DD/"+deviceName
    print("######Workspace PAth##########")
    print("DD/"+deviceName)
    print("####################")
    print("Device Id Starting process" + str(device))
    if os.path.exists("DD/"+deviceName):
        print("####################")
        print("Starting without build")
        print("####################")
        proc = subprocess.Popen(shlex.split('xcodebuild test-without-building -workspace RealDeviceMap-UIControl.xcworkspace -scheme "RealDeviceMap-UIControl" -destination "id={}" -allowProvisioningUpdates -destination-timeout 90 -derivedDataPath "{}" name="{}" enableAccountManager="{}" backendURL="{}" fastIV="{}" raidMaxTime="{}" minDelayLogout="{}" targetMaxDistance="{}"'.format(device,DdFilePath, deviceName, enableAccountManager, backendURL, Devices[device]['FastIV'],  raidMaxTime, minDelayLogout, targetMaxDistance)), stdout=ConsoleFile, cwd=workspacePath,preexec_fn=os.setsid, stderr = ErrFile )
    else:
        print("####################")
        print("Starting with build")
        print("####################")
        try:
           shutil.rmtree("DD/" + d['DeviceName'])
        except:
            print("Unable to remove Directory")

        print("Copying DD Folder from Base Template")
        shutil.copytree("DD/Base_" + cwdF, "DD/" + d['DeviceName'])
        proc = subprocess.Popen(shlex.split('xcodebuild test-without-building -workspace RealDeviceMap-UIControl.xcworkspace -scheme "RealDeviceMap-UIControl" -destination "id={}" -allowProvisioningUpdates -destination-timeout 90 -derivedDataPath "{}" name="{}" enableAccountManager="{}" backendURL="{}" fastIV="{}" raidMaxTime="{}" minDelayLogout="{}" targetMaxDistance="{}"'.format(device,DdFilePath, deviceName, enableAccountManager, backendURL, Devices[device]['FastIV'],  raidMaxTime, minDelayLogout, targetMaxDistance)), stdout=ConsoleFile, cwd=workspacePath,preexec_fn=os.setsid, stderr = ErrFile )

#proc = subprocess.Popen(shlex.split('xcodebuild test -workspace RealDeviceMap-UIControl.xcworkspace -scheme "RealDeviceMap-UIControl" -destination "id={}" -allowProvisioningUpdates -destination-timeout 90 -derivedDataPath "{}" name="{}" enableAccountManager="{}" backendURL="{}" fastIV="{}"  raidMaxTime="{}"'.format(device,DdFilePath, deviceName, enableAccountManager, backendURL, Devices[device]['FastIV'], raidMaxTime)), stdout=ConsoleFile, cwd=workspacePath,preexec_fn=os.setsid , stderr=ErrFile)

    
    #proc = subprocess.Popen('python run.py', cwd=filePath, shell=True, preexec_fn=os.setsid, stdout=ConsoleFile)
    Devices[dk]["DeviceStatus"] = "Building"
    Devices[device]['DeviceProcess'] = proc
    curTime = int(time.time())
    Devices[dk]["AttemptedStartTime"] = curTime
    #out,err = proc.communicate()
    Devices[device]['DeviceProcOut'] = ConsoleFile
    #Devices[device]['DeviceProcErr'] = err
    
    return "Device " +Devices[device]['DeviceName'] + " Started"

def stopDeviceArgument(device):
    
    
    for dk,d in Devices.items():
        if device == d['DeviceName']:
            device = dk
    pro = Devices[device]['DeviceProcess']
    Devices[device]["DeviceStatus"] = "Disabled"

    os.killpg(os.getpgid(pro.pid), signal.SIGTERM)

    return "Device " + str(Devices[device]['DeviceName']) + " Stopped"


@app.route("/DeviceManager/GetDeviceScreenshot",methods=['GET'])
def GetDeviceScreenshot():
    device = request.args.get('Device')
    for dk,d in Devices.items():
        if device == d['DeviceName']:
            device = dk
    GetDeviceCapture(device)

    filename = "DeviceCapture"+ str(device) + ".png"
    return send_file(filename, mimetype='image/png')

def GetDeviceCapture(device):

    proc = subprocess.Popen("idevicescreenshot DeviceCapture" + str(device) + ".png -u " + str(device) , shell=True)
    proc.communicate()
    print("Took Screenshot")



@app.route("/DeviceManager/GetDeviceStatus",methods=['GET'])
def getProcessStatus():
    
    
    device = request.args.get('Device')
    #Devices[dk]["DeviceInstance"]
    statusString = ""
    tableMiddleString = ""
    for dk, d in Devices.items():
        deviceStopButton = '<button onclick="window.location.href=' + "'/DeviceManager/StopDevice?Device=" + d["DeviceName"] + "'" + '">Disable</button>'
        deviceStartButton = '<button onclick="window.location.href=' + "'/DeviceManager/StartDevice?Device=" + d["DeviceName"] + "'" + '">Enable</button>'
        deviceOutputLogButton = '<button onclick="window.location.href=' + "'/DeviceManager/GetDeviceOutput?Device=" + d["DeviceName"] + "'" + '">Ouput Log Current</button>'
        deviceErrLogButton = '<button onclick="window.location.href=' + "'/DeviceManager/GetDeviceErrLog?Device=" + d["DeviceName"] + "'" + '">Err Log Current</button>'
        deviceOutputLogBackupButton = '<button onclick="window.location.href=' + "'/DeviceManager/GetDeviceOutput?Latest=yes&Device=" + d["DeviceName"] + "'" + '">Ouput Log Backup</button>'
        deviceEditInstanceButton = '<button onclick="window.location.href=' + "'" + dashboardURL+ "/device/assign/" + d["DeviceName"] + "'" + '">Edit Instance</button>'
        deviceErrLogBackupButton = '<button onclick="window.location.href=' + "'/DeviceManager/GetDeviceErrLog?Latest=yes&Device=" + d["DeviceName"] + "'" + '">Err Log Backup</button>'
        deviceDeleteUIControlButton = '<button onclick="window.location.href=' + "'/DeviceManager/UninstallUIControl?Device=" + d["DeviceName"] + "'" + '">Uninstall UI Controller</button>'
        deviceRebuildDDFolderButton = '<button onclick="window.location.href=' + "'/DeviceManager/RebuildDDFolder?Device=" + d["DeviceName"] + "'" + '">Rebuild DD Folder</button>'
        deviceScreenshotButton = '<button onclick="window.location.href=' + "'/DeviceManager/GetDeviceScreenshot?Device=" + d["DeviceName"] + "'" + '">View(USBOnly)</button>'
        print(deviceStartButton)
        tableMiddleString = tableMiddleString + '<tr> <td><b>' + d["DeviceName"] + "</b>&nbsp" + deviceStopButton +deviceStartButton + '</td> <td>' + d["DeviceStatus"] + '</td> <td>' + d["DeviceInstance"] + "&nbsp" + '</td> <td>' + str(d["DeviceLastUpdatedDB"]) +'</td> <td><div>' +deviceOutputLogButton + "&nbsp" + deviceErrLogButton+ deviceDeleteUIControlButton + "&nbsp" + deviceScreenshotButton+ "</div><div>" + deviceOutputLogBackupButton + "&nbsp" + deviceErrLogBackupButton + "&nbsp" + deviceRebuildDDFolderButton + '</div></td> </tr> '
    #statusString = statusString + "<b>" + d["DeviceName"] + "</b> has a status of <b>" + d["DeviceStatus"] + "</b>  and was last updated in the DB <b>" + str(Devices[dk]["DeviceLastUpdatedDB"]) + "</b> seconds ago <br />"

    tableString = DeviceManagerTableString

    tableEndString = '</tbody> </table> '

    returnString = tableString +tableMiddleString + tableEndString
    return returnString

@app.route("/DeviceManager/StartDevice",methods=['GET'])
def startDeviceProcess():
    
    
    global backendURL
    global Devices
  
    print("BackendURL is " + str(backendURL))

    
    device = request.args.get('Device')
    print(device)
    
    for dk,d in Devices.items():
        if device == d['DeviceName']:
            device = dk
            Devices[device]["Enabled"] = "true"
    return device + " Started"



@app.route("/DeviceManager/StartAll",methods=['GET'])
def startAllDeviceProcess():
    global Devices
    
    checkDevicesFlag = False

    for dk,d in Devices.items():
        Devices[dk]["Enabled"] = "true"





@app.route("/DeviceManager/GetDeviceOutput",methods=['GET'])
def getDeviceOutput():
    device = request.args.get('Device')
    try:
        latest = request.args.get('Latest')
    except:
        latest = False
    try:
        number = request.args.get('Number')
    except:
        number = False
    deviceKey = ""
    for dk,d in Devices.items():
        if device == d['DeviceName']:
            deviceKey = dk
    
    Devices[deviceKey]["LogFileNumber"]


    
    if latest != False:
        latestLogNumber = int(Devices[deviceKey]["LogFileNumber"])
        f= open("DeviceLogs/" + str(device) + "/Output_Backup" + str(latestLogNumber)+ ".log","r")
    elif number != False:
        f= open("DeviceLogs/" + str(device) + "/Output_Backup" + str(number)+ ".log","r")
    else:
        f= open("DeviceLogs/" + str(device) + "/Output.log","r")

    output = f.read()
    response = make_response(output)
    response.headers["content-type"] = "text/plain"
    
    f.close()
    
    
    return output

@app.route("/DeviceManager/GetDeviceErrLog",methods=['GET'])
def getDeviceErrLog():
    device = request.args.get('Device')
    
    try:
        latest = request.args.get('Latest')
    except:
        latest = False
    try:
        number = request.args.get('Number')
    except:
        number = False
    
    if latest != False:
        latestLogNumber = int(Devices[deviceKey]["LogFileNumber"])
        f= open("DeviceLogs/" + str(device) + "/Err_Backup" + str(latestLogNumber)+ ".log","r")
    elif number != False:
        f= open("DeviceLogs/" + str(device) + "/Err_Backup" + str(number)+ ".log","r")
    else:
        f= open("DeviceLogs/" + str(device) + "/Err.log","r")
    
    output = f.read()
    response = make_response(output)
    response.headers["content-type"] = "text/plain"
    
    f.close()
    
    
    return output


@app.route("/DeviceManager/StopDevice",methods=['GET'])
def stopDevice():
    global currentBuilds
    device = request.args.get('Device')
    
    for dk,d in Devices.items():
        if device == d['DeviceName']:
            device = dk
    pro = Devices[device]['DeviceProcess']
    Devices[device]["Enabled"] = "false"
    if Devices[device]["DeviceStatus"] == "Building" or Devices[device]["DeviceStatus"] == "Started Building":
        currentBuilds = currentBuilds - 1

    try:
        os.killpg(os.getpgid(pro.pid), signal.SIGTERM)
    except:
        print("Device Already Stopped")

    return "Device " + str(Devices[device]['DeviceName']) + " Stopped"




@app.route("/DeviceManager/StopAll",methods=['GET'])
def stopAllDevice():
    
    checkDevicesFlag = False
    
    for dk,d in Devices.items():
        pro = Devices[dk]['DeviceProcess']
        if "subprocess" in str(pro):
            try:
                Devices[dk]["Enabled"] = "false"
                os.killpg(os.getpgid(pro.pid), signal.SIGTERM)
                print("Process for " + Devices[dk]['DeviceName'] + " Stopped")
            except:
                continue


    print("Check Device Flag = " + str(checkDevicesFlag))
    return "All Devices Stopped"

@app.route("/DeviceManager/RebuildDDFolder",methods=['GET'])
def RebuildDDFolderOnDemand():
    device = request.args.get('Device')
    for dk,d in Devices.items():
        if device == d['DeviceName']:
            device = dk

    RebuildDDFolder(device)

    return "Device Folder rebuilt"

def RebuildDDFolder(device):
    

    if Devices[device]['DeviceFolder'] != "":
        cwdF = Devices[device]['DeviceFolder']
    else:
        cwdF = uiControlFolder
    print("Rebuild Path")
    print(cwdF)
    try:
        shutil.rmtree("DD/" + Devices[device]['DeviceName'])
    except:
        print("Unable to remove Directory")

    print("Copying DD Folder from Base Template")
    shutil.copytree("DD/Base_" + cwdF, "DD/" + Devices[device]['DeviceName'])

def CheckProcess():
    global currentBuilds
    global Devices
    global maxBuildsMessageSent
    global DeviceStartupDBContactDelay
    
    if checkDevicesFlag == False:
        print("Stopped Device Check")
        return " Stopping Check"
    
    #print("Current Builds " + str(currentBuilds))
    for dk,d in Devices.items():
        DeviceStartedForFirstTime = False
        device = dk
        deviceName = d['DeviceName']
        deviceEnabled = d['Enabled']
        pro = Devices[dk]['DeviceProcess']
        if "LogFileNumber" not in Devices[dk]:
            Devices[dk]["LogFileNumber"] = 0
        if "StartTime" not in Devices[dk]:
            Devices[dk]["StartTime"] = 0
        if "AttemptedStartTime" not in Devices[dk]:
            Devices[dk]["AttemptedStartTime"] = 0
        if "DeviceBuilding" not in Devices[dk]:
            Devices[dk]["DeviceBuilding"] = False
        if "StartedUpMessageSent" not in Devices[dk]:
            Devices[dk]["StartedUpMessageSent"] = 0
        if "DeviceStatus" not in Devices[dk]:
            Devices[dk]["DeviceStatus"] = "Not Started"
        if "DeviceLastUpdatedDB" not in Devices[dk]:
            Devices[dk]["DeviceLastUpdatedDB"] = "Has Not Contacted Yet"
        if "DeviceInstance" not in Devices[dk]:
            Devices[dk]["DeviceInstance"] = "Unknown"



    


        curTime = int(time.time())
        logFilePath = "DeviceLogs/" + str(deviceName) + "/Output.log"

        DeviceBuilding = Devices[dk]["DeviceBuilding"]




        ##### Check if Device is Enabled Stop if not#####
        if deviceEnabled != "true":
            Devices[dk]["DeviceStatus"] = "Disabled"
            try:
                os.killpg(os.getpgid(pro.pid), signal.SIGTERM)
                print("Process Terminated")
                continue
            except:
                continue
        #########################


        try:
            curTime = int(time.time())
            mydb = mysql.connector.connect(host= mySqlHost ,user= dbUser,passwd=dbPW, database="rdmdb", port=dbPort, connection_timeout = dbTimeout)
            mycursor = mydb.cursor()
            mycursor.execute("select uuid, instance_name, last_seen from rdmdb.device where uuid = '"+deviceName +"'")
            try:
                myresult = mycursor.fetchone()
                DeviceLastUpdatedSeconds = curTime - myresult[2]
                Devices[dk]["DeviceLastUpdatedDB"] = DeviceLastUpdatedSeconds
                Devices[dk]["DeviceInstance"] = myresult[1]
            except:
                print("DB Connection Timeout")
                DeviceLastUpdatedSeconds = 0
            mydb.close()
        except:
            print("Error connecting to DB")
            print(str(datetime.now()))
            DeviceLastUpdatedSeconds =0
            Devices[dk]["DeviceLastUpdatedDB"] = DeviceLastUpdatedSeconds

       ###############Chekc if Device Has Started for first TIME#########
        if "subprocess" in str(pro):
            DeviceStartedForFirstTime = True

        #######Device Has Never Started#####
        else:
            if currentBuilds == maxBuilds:
                Devices[dk]["DeviceStatus"] = "Queued"
                if maxBuildsMessageSent < curTime -10:
                    maxBuildsMessageSent = curTime
                    Devices[dk]["DeviceStatus"] = "Queued"
                    print("Max Builds Reached Continuing")
                    print(str(datetime.now()))
                #time.sleep(5)
                continue
            print("########################################")
            print("Starting Process for first time for " + d['DeviceName'])
            print("########################################")
            currentBuilds = currentBuilds + 1
            Devices[dk]["AttemptedStartTime"] = curTime
            Devices[dk]["StartTime"] = 0
            startDeviceProcessArgument(d['DeviceName'])
            break





       ######If Device HAs started for first time check if it is Building########

        if DeviceBuilding :
            mtime = int(os.path.getmtime(logFilePath))
            secondsSinceUpdate = (curTime - mtime)
            
            ConsoleFile= open("DeviceLogs/" + str(deviceName) + "/Output.log","r")
            #ErrFile= open("DeviceLogs/" + str(device) + "/Err.log","w")
            devicelg = ConsoleFile.read()
            ConsoleFile.close()
            ####Check for Started Status in Device Log#####
            if "[STATUS] Started" in devicelg:
                Devices[device]['StartTime'] = int(time.time())
                timeSinceStart = curTime -  Devices[device]['StartTime']
                Devices[dk]["DeviceBuilding"] = False
                Devices[dk]["DeviceStatus"] = "Started Up"
                currentBuilds = currentBuilds - 1
                print("##################################")
                print(deviceName + " Has Started")
                print("##################################")
            ####Device Not Done Building
            else:
                Devices[dk]["DeviceStatus"] = "Started Building"
                print("Device " + deviceName + " Attempting to start")
                ## Check for no process
                try:
                    id = (os.getpgid(pro.pid))
                ### Check for no Log Updates
                except:
                    id = None
                ######IF Devce IS starting and the the process Failed####
                if id == None:
                    currentBuilds = currentBuilds - 1
                    Devices[dk]["AttemptedStartTime"] = curTime
                    restartProcess(dk, deviceName)
                    continue
                    ###Check for Max builds###
                    
                        ###If The build has not started check for startup wiat time####
                else:
                    curTime = int(time.time())
                    tryingToStartTime = curTime - Devices[dk]["AttemptedStartTime"]
                    if tryingToStartTime > StartupWaitTime:
                        print("Device " + deviceName + " took longer than the StartupWaitTime to Startup. Restarting Device")
                        try:
                            print(str(datetime.now()))
                        except:
                            print("Error with Time")
                        currentBuilds = currentBuilds - 1
                        Devices[dk]["AttemptedStartTime"] = curTime
                        try:
                            os.killpg(os.getpgid(pro.pid), signal.SIGTERM)
                        except:
                            print("No Process")
                        restartProcess(dk, deviceName)
                        continue
        #######IF Device IS Not Building######
        else:
            mtime = int(os.path.getmtime(logFilePath))
            secondsSinceUpdate = (curTime - mtime)
            if currentBuilds == maxBuilds:
                if maxBuildsMessageSent < curTime -10:
                    maxBuildsMessageSent = curTime
                    print("Max Builds Reached Continuing")
                    print(str(datetime.now()))
                continue
            timeSinceStart = curTime -  Devices[device]['StartTime']
            #####Chekc For RUnning Process#####
            try:
                id = (os.getpgid(pro.pid))
                Devices[dk]["DeviceStatus"] = "Started Up"
                #print("ProcessId " + str(id) + " started for" + d['DeviceName'])
            except:
                print("Device" + deviceName + " Restarting Due to no process Found")
                restartProcess(dk, deviceName)
                break
                        
            ###Check the DB#####
            '''
            try:
                curTime = int(time.time())
                mydb = mysql.connector.connect(host= mySqlHost ,user= dbUser,passwd=dbPW, database="rdmdb", port=dbPort, connection_timeout = dbTimeout)
                mycursor = mydb.cursor()
                mycursor.execute("select uuid, instance_name, last_seen from rdmdb.device where uuid = '"+deviceName +"'")
                try:
                    myresult = mycursor.fetchone()
                    DeviceLastUpdatedSeconds = curTime - myresult[2]
                    Devices[dk]["DeviceLastUpdatedDB"] = DeviceLastUpdatedSeconds
                except:
                    print("DB Connection Timeout")
                    
                    DeviceLastUpdatedSeconds = 0
                mydb.close()
            except:
                print("Error connecting to DB")
                print(str(datetime.now()))
                DeviceLastUpdatedSeconds =0
                Devices[dk]["DeviceLastUpdatedDB"] = DeviceLastUpdatedSeconds
            '''
            ######Send Discord Message#####
            try:
                secondsSinceLastMessage = curTime - int(Devices[dk]['RestartMessageSent'])
                if DeviceLastUpdatedSeconds > DBLastUpdatedThreshold and (secondsSinceLastMessage > 3600 or Devices[dk]['RestartMessageSent'] <= 0) :
                    print("***********************")
                    print("Sending Discord Message")
                    Devices[dk]["DeviceStatus"] = "Not Updated In a While"
                    messageText = deviceName + " has not been updated in the db in " + str(DeviceLastUpdatedSeconds) + " . You may have to restart the device"
                    Devices[dk]['RestartMessageSent'] = curTime
                    Devices[dk]["StartTime"] = 0
                    webhook = DiscordWebhook(url=NotificationWebhookURL, content='@here ' + messageText)
                    webhook.execute()
            except:
                print("Error Sending Discord Message")
                print(str(datetime.now()))

            if secondsSinceUpdate > 180 or (DeviceLastUpdatedSeconds > NoContactDBRestartTime and timeSinceStart > DeviceStartupDBContactDelay):
                print("Restarting Device" + deviceName +"  due to no Log File update or no DB Update in 3 min" )
                print("Time Since Started " + str(timeSinceStart))
                
                print(str(datetime.now()))
                try:
                    os.killpg(os.getpgid(pro.pid), signal.SIGTERM)
                except:
                    print("Process Already Dead")
                uninstallUiController(dk)
                restartProcess(dk, deviceName)
                continue
            else:
                if Devices[dk]["StartedUpMessageSent"] < curTime -30:
                    Devices[dk]["StartedUpMessageSent"] = curTime
                    print("Device " + deviceName + " Started up and running")
                    print(str(datetime.now()))
                    
    if checkDevicesFlag == True:
        t = Timer(delayTime, CheckProcess )
        t.start()
                
@app.route("/DeviceManager/ReloadDeviceJson",methods=['GET'])
def reloadDeviceFile():
    
    global Devices
    f= open("RDM_Devices.json","r+")

    DeviceString = f.read()
    DevicesJson = json.loads(DeviceString)
    for dk, d in DevicesJson.items():
        if dk not in Devices:
            Devices[dk] = d
            print("Added " + d['DeviceName'] +" To Json")
        else:
            Devices[dk]["Enabled"] = DevicesJson[dk]["Enabled"]
            Devices[dk]["DeviceFolder"] = DevicesJson[dk]["DeviceFolder"]
            Devices[dk]["FastIV"] = DevicesJson[dk]["FastIV"]
            Devices[dk]["EnableAccountManager"] = DevicesJson[dk]["EnableAccountManager"]
            Devices[dk]["IpaPath"] = DevicesJson[dk]["IpaPath"]



            

    for dk, d in Devices.items():
        
        if os.path.exists("DD/" + d['DeviceName']):
            print("Found DD Folder for " + d['DeviceName'])
        else:
            if d['DeviceFolder'] != "" :
                cwdF = d['DeviceFolder']
            else:
                cwdF = uiControlFolder
            cd = os.getcwd()
            workspacePath = cd +"/"+ cwdF
            print(workspacePath)
            DDWorkspacePath = cwdF + "/RealDeviceMap-UIControl.xcworkspace"
            print(DDWorkspacePath)
            if os.path.exists("DD/Base_" + cwdF):
                print("Found DD Base for this workspace Copying folder for " + d['DeviceName'])
                
                shutil.copytree("DD/Base_" + cwdF, "DD/" + d['DeviceName'])
                print("Copied DD Folder for " + d['DeviceName'] )
            else:
                print("Unable to find DD Base for " + cwdF+ " Starting creation of it")
                proc = subprocess.Popen("xcodebuild build-for-testing -workspace "+ DDWorkspacePath + " -scheme RealDeviceMap-UIControl -allowProvisioningUpdates -allowProvisioningDeviceRegistration -destination 'generic/platform=iOS' -derivedDataPath DD/Base_" + cwdF, shell=True)
                proc.communicate()
                print("Succesfuly Built DD Folder for " + d['DeviceName'])
                shutil.copytree("DD/Base_" + cwdF, "DD/" + d['DeviceName'])
                print("Copied DD Folder for " + d['DeviceName'] )

    return "Reloaded Json"

def uninstallUiController(device):

    try:
        proc = subprocess.Popen("ios-deploy --id " + device + " --uninstall_only --bundle_id com.apple.test.RealDeviceMap-UIControlUITests-Runner", shell=True)
        proc.communicate()
        print("Uninstalled App")
    except:
        print("Unable to uninstall App")

@app.route("/DeviceManager/UninstallUIControl",methods=['GET'])
def uninstallUiControllerOnDemand():
    device = request.args.get('Device')
    
    for dk,d in Devices.items():
        if device == d['DeviceName']:
            device = dk
    

    try:
        uninstallCommandString = "ios-deploy --id " + device + " --uninstall_only --bundle_id com.apple.test.RealDeviceMap-UIControlUITests-Runner"
        print(uninstallCommandString)
        proc = subprocess.Popen(uninstallCommandString, shell=True)
        proc.communicate()
        print("Uninstalled App")
        resp = "Uninstalled App"
    except:
        resp = "Unable to uninstall App"
        print("Unable to uninstall App")

    return str(resp)

def restartProcess(device, deviceName):
    
    global currentBuilds
    global Devices
    
    dk = device
    
    
    Devices[dk]["DeviceStatus"] = "Restarting"
    
    print("Unable to find Process")
    if Devices[dk]["LogFileNumber"] == logFilesToKeep:
        Devices[dk]["LogFileNumber"] = 1
    else:
        Devices[dk]["LogFileNumber"] = Devices[dk]["LogFileNumber"] + 1
        
    ConsoleFile= open("DeviceLogs/" + str(deviceName) + "/Output.log","r")
    ErrFile= open("DeviceLogs/" + str(deviceName) + "/Err.log","r")
    try:
        dlg = str(ConsoleFile.read())
    except:
        print("Error Reading Console File")
    try:
        derlg = str(ErrFile.read())
    except:
        print("Error Reading Error File")

    ConsoleFile.close()
    ErrFile.close()
    ###Error Checker ######
    for err, errResp in Errors.items():
        if err in dlg:
            print(deviceName + " got the error: " + errResp)
            if errResp in UninstallErrors:
                print("Error in uninstall Error. Attempting to uninstall App")
                uninstallUiController(dk)
        
        if err in derlg:
            print(deviceName + " got the error: " + errResp)
            if errResp in UninstallErrors:
                print("Error in uninstall Error. Attempting to uninstall App")
                uninstallUiController(dk)

    ##########################
    ####Restart Log Stuff######
    rl = dict()
    for m, mr in Errors.items():
        if m in dlg:
            rl[mr] = dlg.count(m)
        if m in derlg:
            rl[mr] = derlg.count(m)
    PrettyJson = json.dumps(rl, indent=4, sort_keys=False)
    f= open("DeviceLogs/" + str(deviceName) + "/" +deviceName + "RestartLog" + str(Devices[dk]["LogFileNumber"])+".json" ,"w")

    f.write(str(PrettyJson))

    f.close()
    ##########################
    ###Copy Log File Stuff###


    shutil.copyfile("DeviceLogs/" + str(deviceName) + "/Err.log", "DeviceLogs/" + str(deviceName) + "/Err_Backup" + str(Devices[dk]["LogFileNumber"]) + ".log")
    shutil.copyfile("DeviceLogs/" + str(deviceName) + "/Output.log", "DeviceLogs/" + str(deviceName) + "/Output_Backup" + str(Devices[dk]["LogFileNumber"]) + ".log")
    #########################
    currentBuilds = currentBuilds +1
    Devices[dk]["StartTime"] = 0
    curTime = int(time.time())
    Devices[dk]["AttemptedStartTime"] = curTime
    startDeviceProcessArgument(deviceName)
    print("Restarting Process for " + deviceName)


@app.route("/DeviceManager/InstallAllIpa",methods=['GET'])
def installIpa():
    
    for dk,d in Devices.items():
        device = dk
        try:
            if d["Enabled"] != "false":
                ipaPath = Devices[device]['IpaPath']
                cd = os.getcwd()
                ipaPath = cd + ipaPath
                print("Starting Installation of IPA on " + d["DeviceName"] )
                proc = subprocess.Popen("ipa-deploy " + ipaPath + " --id " + device, cwd= cd, shell=True)
                proc.communicate()
                time.sleep(IpaDelay)
                print("Installed IPA on " + d["DeviceName"] )
            else:
                print("Device" + str(d["DeviceName"]) + " Not Enabled Skipping Install")
        except:
            print("Failed to Install IPA on " + d["DeviceName"] )

    


    return "All Devices Installed"





def signal_handler(sig, frame):
    stopAllDevice()
    print('Gracefully Exiting ')
    sys.exit(0)


if __name__ == "__main__":
    checkDevicesFlag = True
    
    LoadConfig()
    for dk, d in Devices.items() :
        
        if os.path.exists("DD/" + d['DeviceName']):
            print("Found DD Folder for " + d['DeviceName'])
        else:
            if d['DeviceFolder'] != "":
                
                cwdF = d['DeviceFolder']
            else:
                cwdF = uiControlFolder
            cd = os.getcwd()
            workspacePath = cd +"/"+ cwdF
            print(workspacePath)
            DDWorkspacePath = cwdF + "/RealDeviceMap-UIControl.xcworkspace"
            print(DDWorkspacePath)
            if os.path.exists("DD/Base_" + cwdF):
                print("Found DD Base for this workspace Copying folder for " + d['DeviceName'])
                
                shutil.copytree("DD/Base_" + cwdF, "DD/" + d['DeviceName'])
                print("Copied DD Folder for " + d['DeviceName'] )
            else:
                print("Unable to find DD Base for " + cwdF+ " Starting creation of it")
                proc = subprocess.Popen("xcodebuild build-for-testing -workspace "+ DDWorkspacePath + " -scheme RealDeviceMap-UIControl -allowProvisioningUpdates -allowProvisioningDeviceRegistration -destination 'generic/platform=iOS' -derivedDataPath DD/Base_" + cwdF, shell=True)
                proc.communicate()
                print("Succesfuly Built DD Folder for " + d['DeviceName'])
                try:
                    shutil.copytree("DD/Base_" + cwdF, "DD/" + d['DeviceName'])
                    print("Copied DD Folder for " + d['DeviceName'] )
                except:
                    print("Couldnt find the folder path. This is most likley due to an error building or a wrong UI control Folder path with no workspace file")
    

    print("Finished Checking for DD")
    CheckProcess()
    signal.signal(signal.SIGINT, signal_handler)
    socketio.run(app,host='0.0.0.0', port=DeviceManagerAPIPort, debug=False)

