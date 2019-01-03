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

For Device Manage UI


CREATE TABLE rdmdb.DeviceManagerDevices (

    uuid varchar(255) Primary Key ,
    device_id varchar(255) ,
    last_seen int(11) unsigned,
    instance_name varchar(255),
    account_username varchar(255),
    fastIV tinyint(1) unsigned Default 0,
    enableAccountManager tinyint(1) Default 1,
    enabled tinyint(1) Default 0,
    workspace_folder varchar(255),
    backendURL varchar(255),
    deviceStatus varchar(255),
    IpaPath varchar(255),
    deviceGroup varchar(255) Default '1',
    DeviceManagerHost varchar(255)
    

);

DELIMITER $$         

CREATE TRIGGER `updateDeviceManagerTable` AFTER UPDATE ON `device` FOR EACH ROW
BEGIN
    UPDATE  DeviceManagerDevices
    SET  uuid = NEW.uuid
       , last_seen = NEW.last_seen
       , instance_name = NEW.instance_name
       , account_username = NEW.account_username
       
    WHERE uuid = NEW.uuid;    
END $$

DELIMITER ;

INSERT INTO DeviceManagerDevices ( 
      uuid, 
      account_username,
      instance_name
       ) 
SELECT uuid, 
       account_username, 
       instance_name
FROM rdmdb.device


Unzip the DeviceManagerUI folder and edit the username and password in the home-page.compoenents.ts and the device-group.components.ts

run npm install to install dependencies and then run ng serve --open 

