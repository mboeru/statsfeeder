# statsfeeder
##### simple, modular python app to send different values into Graphite


 - you can create your own modules in any programing language. Just output to stdout either a value or a simple json. Take a look into stats.d.examples

 
### Example outputs:
#### Single
```shell
[stats.d]# ./z.livingroom.temp1 
27.88
```
#### json
```shell
[stats.d]# ./z.apps.sickrage 
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

### Installing and Prerequisites
 - You will need a running carbon (graphite) server to wich you will feed the data
 - install from pip configparser and graphitesend
 - copy stats.d.examples to stats.d
 - copy config.ini.example to config.ini
 - adjust values in config.ini as per your needs
 - run ./statsfeeder.py

#### Running as a daemon
 - You can use the example supervisord script located in helpers. Just make sure to change the paths.
 - Using screen
  - screen -dm - S statsfeeder /root/statsfeeder/statsfeeder.py

#### Dynamically adding or removing modules
 - Every time it runs, statsfeeder checks the modules directory for new files. If there are new files with +x it will execute them. If an existing module is disabled by removing the execute attibute, that stat will no longer be collected. These things happen without the need to restart statsfeeder.
