# statsfeeder
###### simple python app that gets values or json from different modules and outputs them into graphite


 - you can create your own modules in any programing language. Just output to stdout either a value or a simple json. just look into stats.d

 
### Example outputs:
#### Single
```shell
[stats.d]# ./z.livingroom.temp1 
27.88
```
#### json
```shell
[stats.d]# ./home.apps.sickrage 
{
    "ep_downloaded": 8888, 
    "ep_snatched": 500, 
    "ep_total": 9999, 
    "shows_active": 100, 
    "shows_total": 200
}
```
  - the name of the file is the actual graphite path where the values will be saved. If the returned value is json, it will create a structure inside the name of the file with the json keys
   - For example in graphite you will have the following entries for home.apps.sickrage: 
     - home.apps.sickrage.ep_downloaded, home.apps.sickrage.ep_snatched, home.apps.sickrage.ep_total, home.apps.sickrage.shows_active, home.apps.sickrage.shows_total
