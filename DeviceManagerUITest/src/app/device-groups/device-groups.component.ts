import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { Headers, Http, Response, RequestOptions } from "@angular/http"
import 'rxjs/add/operator/map'



@Component({
  selector: 'app-device-groups',
  templateUrl: './device-groups.component.html',
  styleUrls: ['./device-groups.component.css']
})
export class DeviceGroupsComponent implements OnInit {

  GroupAutoAssignInstanceTZ = 0
  GroupAutoAssignInstanceType = ""
  devices = {}
  ShowDevice = false
  selectedDevice = {}
  selectedDeviceIndex = 0
  instances = {}
  selectedDeviceGroup = 1
  deviceAssignments = {}
  GroupAutoAssignInstance = ""
  GroupInstance = ""
  
  assignUrl = "/device/assign/"
  deviceGroups = {}
  AutoAssignTime = ""
  username = "yourApiUsername"
  pw = "PokemonIsAwesome"
  DeviceManagerAPIURL = "http://DEVICEMANGERHOSTIP:8887"
  dashboardurl = "http://dashboardIP:9000/dashboard"




  constructor(public http: Http) { }

  ngOnInit() {


  
      this.getQueryResults("select * from DeviceManagerDevices").subscribe(data => {
        this.devices = JSON.parse(data["_body"])


        console.log(this.devices)
      }, error => {

      });

      this.getQueryResults("select * from instance").subscribe(data => {
        this.instances = JSON.parse(data["_body"])


        console.log(this.instances)
      }, error => {

      });

      this.getQueryResults("select device_uuid, instance_name, time from assignment").subscribe(data => {
        this.deviceAssignments = JSON.parse(data["_body"])

        for (let i in this.deviceAssignments) {
          var readableTime = this.sec2time(this.deviceAssignments[i]['time'])
          this.deviceAssignments[i]["AssignmentTime"] = readableTime
        }


        console.log(this.deviceAssignments)
      }, error => {

      });


      this.getQueryResults("select distinct(deviceGroup) from DeviceManagerDevices").subscribe(data => {
        this.deviceGroups = JSON.parse(data["_body"])


        console.log(this.deviceGroups)
      }, error => {

      });


   



  }

  selectedAutoInstance() {

    for (let i in this.instances) {
      if (this.instances[i]['name'] == this.GroupAutoAssignInstance) {
        var InstanceJson = JSON.parse(this.instances[i]['data'])
        this.GroupAutoAssignInstanceTZ = InstanceJson['timezone_offset']
        this.GroupAutoAssignInstanceType = this.instances[i]['type']
      }
    }
    


  }


  updateDevicesInstance(group, Instance) {


    for (let i in this.devices) {
      if (this.devices[i].deviceGroup == group) {
        console.log("updating device " + this.devices[i].uuid)
        this.assignDevice(this.devices[i].uuid, Instance).subscribe(data => {

        }, error => {

        });

      }

    }
	this.ngOnInit()

  }

  deleteAssignment(name, instance, time) {

    this.deleteAutoAssignDevice(name, instance, time).subscribe(data => {

    }, error => {

    });

    this.ngOnInit()


  }

  updateDevicesAutoInstance(group, Instance) {

    var times = this.AutoAssignTime.split(":")


    var autoTime = (parseInt(times[0]) * 3600) + (parseInt(times[1]) * 60) + parseInt(times[2])
    console.log(autoTime)
    for (let i in this.devices) {
      if (this.devices[i].deviceGroup == group) {
        console.log("updating device " + this.devices[i].uuid)
        this.autoAssignDevice(this.devices[i].uuid, Instance, this.AutoAssignTime).subscribe(data => {

        }, error => {

        });

      }

    }

	this.ngOnInit()

  }


  updateDeviceGroup(group) {

    this.selectedDeviceGroup = group



  }



  getQueryResults(query) {

    let header = new Headers({ "Authorization": "Basic " + btoa(this.username+":"+this.pw), 'Content-Type': 'application/x-www-form-urlencoded'})

    return this.http.get(this.DeviceManagerAPIURL + "/DeviceManager/SQLQuery?Query=" + query, { headers: header }).map(data => {
      return data;
    })
  }

  assignDevice(deviceName, InstanceName) {
    console.log(InstanceName)
    let header = new Headers({ "Authorization": "Basic " + btoa(this.username+":"+this.pw), 'Content-Type': 'application/x-www-form-urlencoded'})
    console.log("Updating Device")
    return this.http.get(this.DeviceManagerAPIURL + "/DeviceManager/AssignDevice?Device=" + deviceName + "&Instance=" + InstanceName , { headers: header } ).map(data => {
      return data;
    })
  }

  autoAssignDevice(deviceName, InstanceName, time) {
    console.log(InstanceName)

    let header = new Headers({ "Authorization": "Basic " + btoa(this.username+":"+this.pw), 'Content-Type': 'application/x-www-form-urlencoded'})
    console.log("Updating Device")
    return this.http.get(this.DeviceManagerAPIURL + "/DeviceManager/AutoAssignDevice?Device=" + deviceName + "&Instance=" + InstanceName + "&Time=" + time , { headers: header }).map(data => {
      return data;
    })
  }

  deleteAutoAssignDevice(deviceName, InstanceName, time) {
    console.log(InstanceName)
    let header = new Headers({ "Authorization": "Basic " + btoa(this.username+":"+this.pw), 'Content-Type': 'application/x-www-form-urlencoded'})
    console.log("Updating Device")
    return this.http.get(this.DeviceManagerAPIURL + "/DeviceManager/DeleteAutoAssignDevice?Device=" + deviceName + "&Instance=" + InstanceName + "&Time=" + time , { headers: header }).map(data => {
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
