import { BrowserModule } from '@angular/platform-browser';
import { NgModule } from '@angular/core';
import {HttpModule} from "@angular/http"
import { FormsModule } from '@angular/forms';
import {RouterModule, Routes } from '@angular/router';
import { AppComponent } from './app.component';
import { HomePageComponent } from './home-page/home-page.component';
import {BrowserAnimationsModule} from '@angular/platform-browser/animations';
import { MatTabsModule } from '@angular/material';
import { DeviceGroupsComponent } from './device-groups/device-groups.component';
import {JsonPipe} from "../app/pipes/jsonPipe"
import {SafePipe} from "../app/pipes/safePipe"

const appRoutes: Routes = [
  { path: 'home-page', component: HomePageComponent },
  { path: 'device-groups', component: DeviceGroupsComponent },


];


@NgModule({
  declarations: [
    AppComponent,
    HomePageComponent,
    JsonPipe,
    SafePipe,
    DeviceGroupsComponent
  ],
  imports: [
    BrowserModule,
    HttpModule,
    MatTabsModule,
    FormsModule,
    BrowserAnimationsModule ,
    RouterModule.forRoot( appRoutes),
  ],
  providers: [],
  bootstrap: [AppComponent]
})
export class AppModule { }
