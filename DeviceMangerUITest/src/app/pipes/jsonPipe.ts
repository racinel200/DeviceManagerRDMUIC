import {Injectable, Pipe, PipeTransform} from '@angular/core';
import {DomSanitizer, SafeHtml, SafeStyle, SafeScript, SafeUrl, SafeResourceUrl} from '@angular/platform-browser'

@Pipe({name: 'keys'})
export class JsonPipe implements PipeTransform{
    transform(value,args:string[]) : any{
        let keys=[];
        for(let key in value){
            keys.push({key:key, value:value[key]});
        }
        return keys;
    }
}



