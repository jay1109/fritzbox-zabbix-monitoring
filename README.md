# Zabbix Monitoring for your AVM Fritz!Box Devices
## Requirements and successfully tested
- Zabbix Server Version: 7 (tested with 7.2.5)

## Setup
1. Create a user for monitoring (with settings permissions) in your FritzBox
2. Copy the content from the docker-compose.yml file to your local `docker-compose.yaml`` file and fillout the environment variables. You can leave some blank to use defaults (see below).
3. Download the Zabbix template file from [zbx_export_templates.yaml](https://github.com/jay1109/fritzbox-zabbix-monitoring/blob/master/templates) and import it to your Zabbix Monitoring system (if you update, delete the old template first)
4. Create a host in zabbix with the same hostname from docker-compose.yml (```FRITZBOX_HOSTNAME```)
5. Start your docker-compose file with ```docker-compose up -d```
6. You can check the container with ```docker-compose logs``` into the same directory

## Information
- Please make sure that your passwords do not contain a dollar sign.

### Environment Variables

|  Key  |  Default  |  Comment  |
| ----- | --------- | --------- |
|  ZABBIX_SERVER  |  -  |  IP address of your Zabbix server  |
|  ZABBIX_SERVER_PORT  |  10050  |  Custom port of your Zabbix server  |
|  TLS_PSK_IDENTITY  |  (not used)  |  ID of the pre-shared-key to be used  |
|  TLS_PSK_  |  (not used)  |  Secret of the pre-shared-key  |
|  INTERVAL  |  -  |  Check intervall  |
|  FRITZBOX_HOSTNAME  |  -  |  Hostname of your FritzBox at the Zabbix Server  |
|  FRITZBOX_IP  |  -  |  IP address of your FritzBox where it could be reached from this check service  |
|  FRITZBOX_USER  |  -  |  User in your FritzBox for this check service  |
|  FRITZBOX_PASSWD  |  -  |  Password in your FritzBox for this check service  |
|  ZABBIX_SENDER_DEBUG  |  False  |  Switch to enable verbose logging  |

## For builders and developers only
1. ```git clone XX```
2. ```cd container```
3. ```docker build --no-cache -t fritzbox-zabbix-monitoring```

For more information checkout the build file in this repo.

## Feature Requests and Bugs or Questions
- Please create a simple issue here https://github.com/jay1109/fritzbox-zabbix-monitoring/issues

## Known Errors
### 'Hostname' required
```
fritzbox-zabbix-monitoring-fritzbox-zabbix-monitoring-1  | zabbix_sender [8]: ERROR: [line 1] 'Hostname' required
fritzbox-zabbix-monitoring-fritzbox-zabbix-monitoring-1  | Sending failed.
```
- This error can be solved by removing the " chars in your environment section from docker-compose.yml

### Values are 0 in my Zabbix Server Host
- This error may comes up when you are using your AVM Device for a internal switch / access point instead for an normal internet router. I'm working on it to investigate this problem or create a fix. 

## DockerHub
https://hub.docker.com/r/jay110982/fritzbox-zabbix-monitoring

## Credits
Thanks to https://github.com/pthoelken/fritzbox-zabbix-monitoring/tree/main for his work.
I converted his code to python to use the FritzConnection library https://github.com/kbr/fritzconnection 
I tried to be as combatible as possible.

Changes to original code:
- switched to python instead of php
- using [python-zabbix-utils]https://github.com/zabbix/python-zabbix-utils instead of native zabbix_sender
- added SmartHomeDevices (tested with "FritzDect 302" Temperature)
- template: using rate() - function for data rate calculation
- template: using discovery for SmartHomeDevices
