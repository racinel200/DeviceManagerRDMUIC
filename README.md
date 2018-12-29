# DeviceManagerRDMUIC
Device Manager

pip install flask
pip install flask_socketio
pip install requests
pip install mysql-connector
pip install discord_webhook

May Need
pip install mysql-connector-python

Put your Device UUID's and names in the RDM_Devices Folder 

Specify your UI Control Folder in the same directory as the script plug in your DB info and backend url info and run python DeviceManagerV6.py in a console. To exit out and stop all devices use control C in the same terminal window

Change the user in the DeviceConfigJson to something specific to you. 
You will need to log in for the first time on a browser using the username and password you specify in the config

Hit localhost:8887/DeviceManager/GetDeviceStatus to see your options of stuff to do for devices. 


