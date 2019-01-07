import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { Headers, Http, Response, RequestOptions } from "@angular/http"
import 'rxjs/add/operator/map'
import {interval} from "rxjs/observable/interval";
import {startWith, switchMap} from "rxjs/operators";
import { log } from 'util';

@Component({
  selector: 'app-home-page',
  templateUrl: './home-page.component.html',
  styleUrls: ['./home-page.component.css']
})
export class HomePageComponent implements OnInit {

 
  
  public devices: any[];
  ShowDevice = false
  selectedDevice = {}
  selectedDeviceIndex = 0
  deviceAssignments = {}
  instances = {}
  assignUrl = "/device/assign/"
  deviceGroups = {}
  DeviceOuputURL = "/DeviceManager/GetDeviceOutput"
  DeviceErrLogURL = "/DeviceManager/GetDeviceErrLog"
  DeviceErrLogBackupURL = "ErrLogBackup"
  DeviceOutputLogBackupURL = "OutputLogBackup"
  DeviceScreenshotURL = "/DeviceManager/GetDeviceScreenshot"
  DeviceRestartURL = "/DeviceManager/RestartDevice"
  DeviceUninstallUIControllerURL = "/DeviceManager/UninstallUIControl"
  DeviceRebuildDDFolderURL = "/DeviceManager/RebuildDDFolder"
  logOutputHTML = ""
  LastUpdatePercent = 0
  username = "yourApiUsername"
  pw = "PokemonIsAwesome"
  DeviceManagerAPIURL = "http://HOSTIP:8887"
  dashboardurl = "http://DAshboardIP:9000/dashboard"
  


  constructor(public http: Http) { }

  ngOnInit() {
      interval(10000)
        .pipe(startWith(0))
        .subscribe(() => this.loadDevices());
  }
  
  loadDevices() {
      console.log("loading...");
      this.getQueryResults("select * from DeviceManagerDevices").subscribe(data => {
      this.devices = JSON.parse(data["_body"])

    var LastSecondGoodCount = 0
    var disabledCount = 0
    for (let d in this.devices){
        var currentTime = Math.floor(Date.now() /1000)
        var SecondsSinceUpdate  = currentTime - this.devices[d]['last_seen']
        this.devices[d]["SecondsSinceUpdate"] = SecondsSinceUpdate
        if (this.devices[d]['enabled'] != 0){
            if (SecondsSinceUpdate < 180 ){
                //console.log("Enabled")
                //console.log(this.devices[d]['enabled'])
                LastSecondGoodCount = LastSecondGoodCount + 1
            }
        }else{
            console.log("Disabled")
            disabledCount = disabledCount + 1
        }
    }
    this.LastUpdatePercent = (LastSecondGoodCount  / (this.devices.length - disabledCount) ) * 100
    
  
      
        //console.log(this.devices)
      }, error => {
     
      });


      this.getQueryResults("select * from instance").subscribe(data => {
        this.instances = JSON.parse(data["_body"])
  
      
        //console.log(this.instances)
      }, error => {
     
      });
  
      this.getQueryResults("select device_uuid, instance_name, time from assignment").subscribe(data => {
        this.deviceAssignments = JSON.parse(data["_body"])
  
        for ( let i in this.deviceAssignments){
          var readableTime = this.sec2time(this.deviceAssignments[i]['time'])
          this.deviceAssignments[i]["AssignmentTime"] = readableTime
        }
  
      
        //console.log(this.deviceAssignments)
      }, error => {
     
      });
  
  
      this.getQueryResults("select distinct(deviceGroup) from DeviceManagerDevices").subscribe(data => {
        this.deviceGroups = JSON.parse(data["_body"])
  
      
        //console.log(this.deviceGroups)
    




      
    }, error => {
   
    });      
  }

  backToDevices(){

    this.ShowDevice = false
  }

  showDevice(device){
    this.ShowDevice = true
    this.selectedDevice = this.devices[device]
    this.selectedDeviceIndex = device

  }


  updateDeviceInstance(device,InstanceName){
    console.log(device + "Instance0 + " + InstanceName)

    this.assignDevice(device, InstanceName).subscribe(data => { 

    }, error => {

    });
  }

  deleteAssignment(name, instance, time){

    this.deleteAutoAssignDevice(name, instance, time).subscribe(data => { 

    }, error => {

    });

    this.ngOnInit()


  }

  OpenDeviceManagerURL(hostURL, device, URL){
    console.log(URL)
    if (URL == "OutputLogBackup" ){
      var openurl = hostURL + this.DeviceOuputURL + "?Device="+device + "&Latest=yes"
      window.open(openurl, '_blank')
      return
    }
     if (URL == "ErrLogBackup" ){
      var openurl = hostURL + this.DeviceErrLogURL + "?Device="+device + "&Latest=yes"
      window.open(openurl, '_blank')
      return
    }else{
      var openurl = hostURL + URL + "?Device="+device
      window.open(openurl, '_blank')
    }
   
    
    /* if hostURL{
      this.getDeviceOutputLog(hostURL, device).subscribe(data => { 

        console.log(data["_body"])
        this.logOutputHTML = data["_body"]
      }, error => {
  
      });

    }else{
      console.log("No Host URL")
    } */
    

  }




  saveDevice( ){

    let first = true
    var sqlUpdateString = "update DeviceManagerDevices set "
    for (let v in this.selectedDevice){
      console.log(v)
      console.log(typeof v)
      if (v != "last_seen" && v != "account_username" && v != "deviceStatus" && v != "SecondsSinceUpdate"){

        if (first){
          if (v != "")
          sqlUpdateString = sqlUpdateString + v + "= '" + this.selectedDevice[v] + "'"
          first = false
       }else{
         sqlUpdateString = sqlUpdateString + ", " + v + "= '" + this.selectedDevice[v] + "'"
 
       }
      }
      
    }
    sqlUpdateString = sqlUpdateString + " where uuid= '" + this.selectedDevice['uuid'] + "'"

    console.log(sqlUpdateString)

     this.getQueryResults(sqlUpdateString).subscribe(data => {

    
      console.log(this.instances)
    }, error => {
   
    }); 



  }






  login(username, pw) {

    var body = "email="+ username + "&password=" + pw + "&Submit=Submit"
    let header = new Headers({ 'Content-Type': 'application/x-www-form-urlencoded', 'withCredentials': true})
    return this.http.post(this.DeviceManagerAPIURL + "/login", body, { headers: header }).map(data => {
      return data;
    })

  }

  getQueryResults(query) {

    let header = new Headers({ "Authorization": "Basic " + btoa(this.username+":"+this.pw), 'Content-Type': 'application/x-www-form-urlencoded'})

    return this.http.get(this.DeviceManagerAPIURL + "/DeviceManager/SQLQuery?Query="+ query, { headers: header }).map(data => {
      return data;
    })
  }

  assignDevice(deviceName, InstanceName) {
    console.log(InstanceName)
    console.log("Updating Device")
    let header = new Headers({ "Authorization": "Basic " + btoa(this.username+":"+this.pw), 'Content-Type': 'application/x-www-form-urlencoded'})

    return this.http.get(this.DeviceManagerAPIURL + "/DeviceManager/AssignDevice?Device="+deviceName + "&Instance="+InstanceName, { headers: header } ).map(data => {
      return data;
    })
  }

 

  deleteAutoAssignDevice(deviceName, InstanceName, time) {
    console.log(InstanceName)
    console.log("Updating Device")
    let header = new Headers({ "Authorization": "Basic " + btoa(this.username+":"+this.pw), 'Content-Type': 'application/x-www-form-urlencoded'})

    return this.http.get(this.DeviceManagerAPIURL + "/DeviceManager/DeleteAutoAssignDevice?Device="+deviceName + "&Instance="+InstanceName+"&Time="+time, { headers: header } ).map(data => {
      return data;
    })
  }

  getDeviceOutputLog(backenURL, deviceName) {
    console.log("Updating Device")
    let header = new Headers({ "Authorization": "Basic " + btoa(this.username+":"+this.pw), 'Content-Type': 'application/x-www-form-urlencoded'})

    return this.http.get( backenURL + this.DeviceOuputURL + "?Device="+deviceName , { headers: header } ).map(data => {
      return data;
    })
  }


  pad(num, size) { return ('000' + num).slice(size * -1); }

  sec2time(timeInSeconds) {
  
  var time = +parseFloat(timeInSeconds).toFixed(3)
  var hours = +Math.floor(time / 60 / 60)
  var minutes = +Math.floor(time / 60) % 60
  var seconds = +Math.floor(time - minutes * 60)
  var milliseconds = time.toString().slice(-3);

  return this.pad(hours, 2) + ':' + this.pad(minutes, 2) + ':' + this.pad(seconds, 2);
}
  







}
