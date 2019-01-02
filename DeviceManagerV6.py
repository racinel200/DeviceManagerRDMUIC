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
from flask_cors import CORS
from threading import Timer
import mysql.connector
from discord_webhook import DiscordWebhook
import shutil
import requests
import threading
import time
from time import gmtime, strftime
from datetime import datetime
from flask import send_file
import flask_login
import flask
from flask_login import LoginManager
from flask_login import current_user, login_user
from flask_wtf import FlaskForm
from wtforms import Form, BooleanField, StringField, PasswordField, validators
from functools import wraps





reload(sys)
sys.setdefaultencoding('utf8')

Devices = dict()
DeviceProcesses = dict()




app= Flask(__name__)
app.config['SECRET_KEY'] = "secretpokemonstuff"
socketio = SocketIO(app)
login_manager = LoginManager()
CORS(app, supports_credentials=True)

login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)


checkDevicesFlag = True
currentBuilds = 0

maxBuildsMessageSent = 0
StartedUpMessageSent = dict()




class User(flask_login.UserMixin):
    pass


@login_manager.user_loader
def user_loader(email):
    if email not in users:
        return
    
    user = User()
    user.id = email
    return user


@login_manager.request_loader
def request_loader(request):
    email = request.form.get('email')
    if email not in users:
        return
    
    user = User()
    user.id = email

    # DO NOT ever store passwords in plaintext and always compare password
    # hashes using constant-time comparison!
    user.is_authenticated = request.form['password'] == users[email]['password']

    return user

def check_auth(username, password):
    """This function is called to check if a username /
    password combination is valid.
    """
    return username == APIUsername and password == APIPassword

def authenticate():
    """Sends a 401 response that enables basic auth"""
    return jsonify('Could not verify your access level for that URL.\n''You have to login with proper credentials', 401,{'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated


@app.route('/login', methods=['GET', 'POST'])
def login():
    if flask.request.method == 'GET':
        return '''
            <form action='login' method='POST'>
            <input type='text' name='email' id='email' placeholder='email'/>
            <input type='password' name='password' id='password' placeholder='password'/>
            <input type='submit' name='submit'/>
            </form>
            '''
    
    email = flask.request.form['email']
    if flask.request.form['password'] == users[email]['password']:
        user = User()
        user.id = email
        flask_login.login_user(user)
        return flask.redirect("/DeviceManager/GetDeviceStatus")
    
    return 'Bad login'

@app.route('/logout')
def logout():
    flask_login.logout_user()
    return 'Logged out'

@login_manager.unauthorized_handler
def unauthorized_handler():
    return flask.redirect(flask.url_for('login'))

@app.route('/protected')
@flask_login.login_required
def protected():
    return 'Logged in as: ' + flask_login.current_user.id


@app.route("/DeviceManager/ReloadConfig",methods=['GET'])
def LoadConfigRequest():

    LoadConfig()

    return "Config File Loaded"

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
    global DBLastUpdatedTimeMessageThreshold
    DBLastUpdatedTimeMessageThreshold = configJson["DBLastUpdatedTimeMessageThreshold"]
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
    global users
    users = configJson["users"]
    global destinationTimeout
    global CSRF
    CSRF = configJson["CSRF"]
    global APIUsername
    APIUsername = configJson["APIUsername"]
    global APIPassword
    APIPassword = configJson["APIPassword"]
    global SessionToken
    SessionToken = configJson["SessionToken"]
    try:
        destinationTimeout = configJson["destinationTimeout"]
    except:
        destinationTimeout = 180
        
        
    
    
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
        proc = subprocess.Popen(shlex.split('xcodebuild test-without-building -workspace RealDeviceMap-UIControl.xcworkspace -scheme "RealDeviceMap-UIControl" -destination "id={}" -allowProvisioningUpdates -destination-timeout "{}" -derivedDataPath "{}" name="{}" enableAccountManager="{}" backendURL="{}" fastIV="{}" raidMaxTime="{}" minDelayLogout="{}" targetMaxDistance="{}"'.format(device,destinationTimeout, DdFilePath, deviceName, enableAccountManager, backendURL, Devices[device]['FastIV'],  raidMaxTime, minDelayLogout, targetMaxDistance)), stdout=ConsoleFile, cwd=workspacePath,preexec_fn=os.setsid, stderr = ErrFile )
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
    Devices[dk]["OldDeviceStatus"] = Devices[dk]["DeviceStatus"]
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
    Devices[dk]["OldDeviceStatus"] = Devices[dk]["DeviceStatus"]
    Devices[device]["DeviceStatus"] = "Disabled"

    os.killpg(os.getpgid(pro.pid), signal.SIGTERM)

    return "Device " + str(Devices[device]['DeviceName']) + " Stopped"

@app.route("/DeviceManager/RestartDevice",methods=['GET'])
@flask_login.login_required
def RestartDeviceOnDemand():
    device = request.args.get('Device')
    for dk,d in Devices.items():
        if device == d['DeviceName']:
            device = dk
    RestartDevice(device)
    return "Restart Sent to Device"

def RestartDevice(device):
    
    global currentBuilds
    global Devices
    
    Devices[device]["Enabled"] = "false"
    if Devices[device]["DeviceStatus"] == "Building" or Devices[device]["DeviceStatus"] == "Started Building":
        if currentBuilds > 0:
            currentBuilds = currentBuilds - 1
    Devices[device]["DeviceBuilding"] = False
    Devices[device]["DeviceProcess"] = "None"
    Devices[dk]["OldDeviceStatus"] = Devices[dk]["DeviceStatus"]
    Devices[device]["DeviceStatus"] = "Rebooting Device"
    

    proc = subprocess.Popen("idevicediagnostics -u " + str(device) + " restart", shell=True)
    proc.communicate()
    Devices[device]["Enabled"] = "true"


@app.route("/DeviceManager/GetDeviceScreenshot",methods=['GET'])
@flask_login.login_required
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
@flask_login.login_required
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
        deviceRestartButton = '<button onclick="window.location.href=' + "'/DeviceManager/RestartDevice?Device=" + d["DeviceName"] + "'" + '">Restart(USBOnly)</button>'
        tableMiddleString = tableMiddleString + '<tr> <td><b>' + d["DeviceName"] + "</b>&nbsp" + deviceStopButton +deviceStartButton + '</td> <td>' + d["DeviceStatus"] + '</td> <td>' + d["DeviceInstance"] + "&nbsp" + '</td> <td>' + str(d["DeviceLastUpdatedDB"]) +'</td> <td><div>' +deviceOutputLogButton + "&nbsp" + deviceErrLogButton+ deviceDeleteUIControlButton + "&nbsp" + deviceScreenshotButton+ "</div><div>" + deviceOutputLogBackupButton + "&nbsp" + deviceErrLogBackupButton + "&nbsp" + deviceRebuildDDFolderButton + "&nbsp" + deviceRestartButton+ '</div></td> </tr> '
    #statusString = statusString + "<b>" + d["DeviceName"] + "</b> has a status of <b>" + d["DeviceStatus"] + "</b>  and was last updated in the DB <b>" + str(Devices[dk]["DeviceLastUpdatedDB"]) + "</b> seconds ago <br />"

    tableString = DeviceManagerTableString

    tableEndString = '</tbody> </table> '

    returnString = tableString +tableMiddleString + tableEndString
    return returnString

@app.route("/DeviceManager/StartDevice",methods=['GET'])
@flask_login.login_required
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
@flask_login.login_required
def startAllDeviceProcess():
    global Devices
    
    checkDevicesFlag = False

    for dk,d in Devices.items():
        Devices[dk]["Enabled"] = "true"





@app.route("/DeviceManager/GetDeviceOutput",methods=['GET'])
@flask_login.login_required
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
    print(number)
    print(latest)
    deviceKey = ""
    for dk,d in Devices.items():
        if device == d['DeviceName']:
            deviceKey = dk
    
    


    
    if latest == "yes":
        latestLogNumber = int(Devices[deviceKey]["LogFileNumber"])
        f= open("DeviceLogs/" + str(device) + "/Output_Backup" + str(latestLogNumber)+ ".log","r")
    elif number:
        f= open("DeviceLogs/" + str(device) + "/Output_Backup" + str(number)+ ".log","r")
    else:
        f= open("DeviceLogs/" + str(device) + "/Output.log","r")

    output = f.read()
    response = make_response(output)
    response.headers["content-type"] = "text/plain"
    
    f.close()
    
    
    return "<pre>" + output + "</pre>"

@app.route("/DeviceManager/GetDeviceErrLog",methods=['GET'])
@flask_login.login_required
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
    
    deviceKey = ""
    for dk,d in Devices.items():
        if device == d['DeviceName']:
            deviceKey = dk

    if latest == "yes":
        latestLogNumber = int(Devices[deviceKey]["LogFileNumber"])
        f= open("DeviceLogs/" + str(device) + "/Err_Backup" + str(latestLogNumber)+ ".log","r")
    elif number:
        f= open("DeviceLogs/" + str(device) + "/Err_Backup" + str(number)+ ".log","r")
    else:
        f= open("DeviceLogs/" + str(device) + "/Err.log","r")
    
    output = f.read()
    response = make_response(output)
    response.headers["content-type"] = "text/plain"
    
    f.close()
    
    
    return "<pre>" + output + "</pre>"


@app.route("/DeviceManager/StopDevice",methods=['GET'])
@flask_login.login_required
def stopDevice():
    global currentBuilds
    device = request.args.get('Device')
    
    for dk,d in Devices.items():
        if device == d['DeviceName']:
            device = dk
    pro = Devices[device]['DeviceProcess']
    Devices[device]["Enabled"] = "false"
    if Devices[device]["DeviceStatus"] == "Building" or Devices[device]["DeviceStatus"] == "Started Building":
        if currentBuilds > 0:
            currentBuilds = currentBuilds - 1

    try:
        os.killpg(os.getpgid(pro.pid), signal.SIGTERM)
    except:
        print("Device Already Stopped")

    return "Device " + str(Devices[device]['DeviceName']) + " Stopped"




@app.route("/DeviceManager/StopAll",methods=['GET'])
@flask_login.login_required
def stopAllDevice():
    global currentBuilds
    checkDevicesFlag = False
    
    for dk,d in Devices.items():
        pro = Devices[dk]['DeviceProcess']
        if "subprocess" in str(pro):
            try:
                if Devices[dk]["DeviceStatus"] == "Building" or Devices[device]["DeviceStatus"] == "Started Building":
                    if currentBuilds > 0:
                        currentBuilds = currentBuilds - 1
                Devices[dk]["Enabled"] = "false"
                os.killpg(os.getpgid(pro.pid), signal.SIGTERM)
                print("Process for " + Devices[dk]['DeviceName'] + " Stopped")
            except:
                continue


    print("Check Device Flag = " + str(checkDevicesFlag))
    return "All Devices Stopped"

def stopAllDeviceManual():
    global currentBuilds
    checkDevicesFlag = False
    
    proc = subprocess.Popen("killall xcodebuild" , shell=True)
    proc.communicate()
    
    for dk,d in Devices.items():
        pro = Devices[dk]['DeviceProcess']
        if Devices[dk]["DeviceStatus"] == "Building" or Devices[dk]["DeviceStatus"] == "Started Building":
            if currentBuilds > 0:
                currentBuilds = currentBuilds - 1
        Devices[dk]["Enabled"] = "false"
        try:
            os.killpg(os.getpgid(pro.pid), signal.SIGTERM)
            print("Process for " + Devices[dk]['DeviceName'] + " Stopped")
        except:
            print("Unable To Stop Process")



    return "All Devices Stopped"


@app.route("/DeviceManager/RebuildDDFolder",methods=['GET'])
@flask_login.login_required
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
	if "OldDeviceStatus" not in Devices[dk]:
            Devices[dk]["OldDeviceStatus"] = "Not Started"



    


        curTime = int(time.time())
        logFilePath = "DeviceLogs/" + str(deviceName) + "/Output.log"

        DeviceBuilding = Devices[dk]["DeviceBuilding"]




        ##### Check if Device is Enabled Stop if not#####
        if deviceEnabled != "true":
	    Devices[dk]["OldDeviceStatus"] = Devices[dk]["DeviceStatus"]
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
		if DeviceLastUpdatedSeconds > 300:
			Devices[dk]["OldDeviceStatus"] = Devices[dk]["DeviceStatus"]
           		Devices[dk]["DeviceStatus"] = "Not Updated In A While"
		
		if Devices[dk]["OldDeviceStatus"] != Devices[dk]["DeviceStatus"]:
			try:
           			mycursor.execute("update DeviceManagerDevices set deviceStatus='" + Devices[dk]["DeviceStatus"] + "' where uuid = '" + dk + "'"
				mydb.commit()
			except:
				print("Unable to update device Status")
				
				
			
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
		Devices[dk]["OldDeviceStatus"] = Devices[dk]["DeviceStatus"]
                Devices[dk]["DeviceStatus"] = "Started Up"
                if currentBuilds > 0:
                    currentBuilds = currentBuilds - 1
                print("##################################")
                print(deviceName + " Has Started")
                print("##################################")
            ####Device Not Done Building
            else:
                if Devices[dk]["DeviceStatus"] == "Rebooting Device":
                    print("Device Rebooting Skipping")
                    continue 
                Devices[dk]["DeviceStatus"] = "Started Building"
		Devices[dk]["OldDeviceStatus"] = Devices[dk]["DeviceStatus"]
                print("Device " + deviceName + " Attempting to start")
                ## Check for no process
                try:
                    id = (os.getpgid(pro.pid))
                ### Check for no Log Updates
                except:
                    id = None
                ######IF Devce IS starting and the the process Failed####
                if id == None:
                    if currentBuilds > 0:
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
                        if currentBuilds > 0:
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
                if DeviceLastUpdatedSeconds > DBLastUpdatedTimeMessageThreshold and (secondsSinceLastMessage > 3600 or Devices[dk]['RestartMessageSent'] <= 0) :
                    print("***********************")
                    print("Sending Discord Message")
                    messageText = deviceName + " has not been updated in the db in " + str(DeviceLastUpdatedSeconds) + " . You may have to restart the device"
                    webhook = DiscordWebhook(url=NotificationWebhookURL, content='@here ' + messageText)
                    try:
                        GetDeviceCapture(device)
                        with open("DeviceCapture" + dk+ ".png", "rb") as f:
                            webhook.add_file(file=f.read(), filename='Screenshot.png')
                    except:
                        print("Unable to Screenshot Device")
		    
                    
                    Devices[dk]["OldDeviceStatus"] = Devices[dk]["DeviceStatus"]
                    Devices[dk]["DeviceStatus"] = "Not Updated In a While"
                    Devices[dk]['RestartMessageSent'] = curTime
                    Devices[dk]["StartTime"] = 0
                    
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
@flask_login.login_required
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
@flask_login.login_required
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
    
    Devices[dk]["OldDeviceStatus"] = Devices[dk]["DeviceStatus"]
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
    if currentBuilds == maxBuilds:
	Devices[dk]["OldDeviceStatus"] = Devices[dk]["DeviceStatus"]
        Devices[dk]["DeviceStatus"] = "Queued"
        print("Max Builds Reached When attempting Restart")
        return
    currentBuilds = currentBuilds + 1
    Devices[dk]["StartTime"] = 0
    curTime = int(time.time())
    Devices[dk]["AttemptedStartTime"] = curTime
    startDeviceProcessArgument(deviceName)
    print("Restarting Process for " + deviceName)


@app.route("/DeviceManager/InstallAllIpa",methods=['GET'])
@flask_login.login_required
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

@app.route("/DeviceManager/SQLQuery",methods=['GET'])
@requires_auth
def performSqlQuery():

    query = request.args.get('Query')

    mydb = mysql.connector.connect(host= mySqlHost ,user= dbUser,passwd=dbPW, database="rdmdb", port=dbPort, connection_timeout = 15)
    mycursor = mydb.cursor(dictionary=True)
    mycursor.execute(query)
    try:
        
        myresult = mycursor.fetchall()
        print(myresult)
		
    except:
        myresult={}
        print("DB error")
    mydb.close()

    print(myresult)

    return jsonify(myresult)

@app.route("/DeviceManager/AssignDevice",methods=['GET'])
@requires_auth
def assignDevice():

    device = request.args.get('Device')
    instance = request.args.get('Instance')
    print(device)
    print(instance)
    session = requests.Session()
    CSRF = "YOURCSRF"
    SessionToken = "YOURTOKEN"
    dashboardURL  = "YourDashboardURL"


    headers1= {"Content-Type":"application/x-www-form-urlencoded", "Origin": dashboardURL, "Cookie":"SESSION-TOKEN="+ SessionToken+ ";CSRF-TOKEN="+CSRF}

    body = "instance="+ instance + "&_csrf="+ CSRF

    r = session.post(dashboardURL + "/dashboard/device/assign/"+device, headers=headers1, data = body)


    print(r.status_code)


    return jsonify(r.status_code)

@app.route("/DeviceManager/AutoAssignDevice",methods=['GET'])
@requires_auth
def AutoAssignDevice():

    device = request.args.get('Device')
    instance = request.args.get('Instance')
    time = request.args.get('Time')

    print(device)
    print(instance)
    session = requests.Session()
   

    headers1= {"Content-Type":"application/x-www-form-urlencoded", "Origin": dashboardURL, "Cookie":"SESSION-TOKEN="+ SessionToken+ ";CSRF-TOKEN="+CSRF}

    body = "device=" + device + "&instance="+ instance + "&time=" + str(time) +"&_csrf="+ CSRF

    r = session.post(dashboardURL + "/dashboard/assignment/add", headers=headers1, data = body)


    print(r.status_code)


    return jsonify(r.status_code)

@app.route("/DeviceManager/DeleteAutoAssignDevice",methods=['GET'])
@requires_auth
def DeleteAutoAssignDevice():

    device = request.args.get('Device')
    instance = request.args.get('Instance')
    time = request.args.get('Time')

    print(device)
    print(instance)
    session = requests.Session()
   

    headers1= {"Content-Type":"application/x-www-form-urlencoded", "Origin": dashboardURL, "Cookie":"SESSION-TOKEN="+ SessionToken+ ";CSRF-TOKEN="+CSRF}


    r = session.get(dashboardURL + "/dashboard/assignment/delete/" + instance + "\-" + device + "\-" + time , headers=headers1)


    print(r.status_code)


    return jsonify(r.status_code)


def signal_handler(sig, frame):
    stopAllDeviceManual()
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

