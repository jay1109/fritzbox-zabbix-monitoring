from fritzconnection import FritzConnection
from fritzconnection.core.exceptions import FritzConnectionException
from fritzconnection.lib.fritzstatus import FritzStatus
from fritzconnection.lib.fritzhomeauto import FritzHomeAutomation
from zabbix_utils import ItemValue, Sender, ModuleBaseException
from datetime import datetime, timedelta
from time import sleep

import re
import os
import logging
import json


class FritzBoxMonitor:
    # =====================
    # constants
    #

    UNITS = {"s": "seconds", "m": "minutes", "h": "hours", "d": "days", "w": "weeks"}

    # Add more entries if you want, like: `y`, `yes`, `on`, ...
    TRUTHY_VALUES = (
        "true",
        "1",
        "t",
    )
    # Add more entries if you want, like: `n`, `no`, `off`, ...
    FALSY_VALUES = (
        "false",
        "0",
        "f",
    )
    VALID_VALUES = TRUTHY_VALUES + FALSY_VALUES

    def __init__(self):

        # =====================
        # get environment data
        #
        self.ZABBIX_SERVER = os.environ.get("ZABBIX_SERVER", "localhost")
        self.ZABBIX_SERVER_PORT = int(os.environ.get("ZABBIX_SERVER_PORT", "10051"))
        self.ZABBIX_TLS_PSK_IDENTITY = os.environ.get("TLS_PSK_IDENTITY", "")
        self.ZABBIX_TLS_PSK = os.environ.get("TLS_PSK", "")
        self.ZABBIX_SENDER_DEBUG = self.__getBoolEnvVariable("ZABBIX_SENDER_DEBUG", True)

        self.FRITZBOX_HOSTNAME = os.environ.get("FRITZBOX_HOSTNAME", "fritz.box")
        self.FRITZBOX_IP = os.environ.get("FRITZBOX_IP", "192.168.178.1")
        self.FRITZBOX_USER = os.environ.get("FRITZBOX_USER", "zabbixmonitor")
        self.FRITZBOX_PASSWD = os.environ.get("FRITZBOX_PASSWD", "changeme")

        self.INTERVAL = self.__convertToSeconds(os.environ.get("INTERVAL", "60s"))  # INTERVAL=30s

        self.LOGGING_FORMAT = "[%(asctime)s] %(levelname)s %(message)s"

        if os.name == "nt":
            self.PATHCACHE = "./"
        else:  #
            self.PATHCACHE = "./"

        if self.INTERVAL <= 0:
            self.INTERVAL = 60

        if self.ZABBIX_SENDER_DEBUG:
            logging.basicConfig(format=self.LOGGING_FORMAT, level=logging.DEBUG)
        else:
            logging.basicConfig(format=self.LOGGING_FORMAT)

        logging.info("ZABBIX_SERVER: %s", self.ZABBIX_SERVER)
        logging.info("ZABBIX_SERVER_PORT: %s", self.ZABBIX_SERVER_PORT)
        logging.info("ZABBIX_TLS_PSK_IDENTITY: %s", self.ZABBIX_TLS_PSK_IDENTITY)
        logging.info("ZABBIX_TLS_PSK: %s", self.ZABBIX_TLS_PSK)
        logging.info("ZABBIX_SENDER_DEBUG: %s", self.ZABBIX_SENDER_DEBUG)
        logging.info("FRITZBOX_HOSTNAME: %s", self.FRITZBOX_HOSTNAME)
        logging.info("FRITZBOX_IP: %s", self.FRITZBOX_IP)
        logging.info("FRITZBOX_USER: %s", self.FRITZBOX_USER)
        logging.info("FRITZBOX_PASSWD: %s", self.FRITZBOX_PASSWD)
        logging.info("INTERVAL: %s", self.INTERVAL)

    # =====================
    # internal functions
    #

    def __getBoolEnvVariable(self, name: str, default_value: bool | None = None) -> bool:
        value = os.getenv(name) or default_value
        if value is None:
            raise ValueError(f'Environment variable "{name}" is not set!')
        value = str(value).lower()
        if value not in self.VALID_VALUES:
            raise ValueError(f'Invalid value "{value}" for environment variable "{name}"!')
        return value in self.TRUTHY_VALUES

    def __convertToSeconds(self, text: str) -> int:
        return int(
            timedelta(
                **{
                    self.UNITS.get(m.group("unit").lower(), "seconds"): float(m.group("val"))
                    for m in re.finditer(
                        r"(?P<val>\d+(\.\d+)?)(?P<unit>[smhdw]?)",
                        text.replace(" ", ""),
                        flags=re.I,
                    )
                }
            ).total_seconds()
        )

    def __sleepToNextRun(self):
        t_abs_now = (datetime.now() - datetime.fromisocalendar(1970, 1, 1)).total_seconds()
        count = t_abs_now // self.INTERVAL  # integer division (division and floor)
        t_abs_next = (count + 1) * self.INTERVAL
        offset = t_abs_next - t_abs_now

        if offset <= 0:
            offset = self.INTERVAL

        logging.debug("next run in %fs", offset)
        sleep(offset)
    
    def __getConnectionStatus(self, state:bool) -> str:
        if state:
            return "Connected"
        else:
            return "Disconnected"
    
    def __getLinkStatus(self, state:bool) -> str:
        if state:
            return "Up"
        else:
            return "Down"

    # =====================
    def QueryAndSend(self):
        self.__sleepToNextRun()
        Values = []

        try:
            # =====================
            # query data
            #

            fc = FritzConnection(
                address=self.FRITZBOX_IP,
                user=self.FRITZBOX_USER,
                password=self.FRITZBOX_PASSWD,
                use_cache=True,
                cache_directory=self.PATHCACHE,
            )

            # print(fc)  # print router model information

            fritzStatus = FritzStatus(fc=fc)

            Values.append(ItemValue(self.FRITZBOX_HOSTNAME, "totalBytesReceived", fritzStatus.bytes_received))
            Values.append(ItemValue(self.FRITZBOX_HOSTNAME, "totalBytesSent", fritzStatus.bytes_sent))
            Values.append(ItemValue(self.FRITZBOX_HOSTNAME, "uptime", fritzStatus.connection_uptime))
            Values.append(ItemValue(self.FRITZBOX_HOSTNAME, "externalIPAddress", fritzStatus.external_ip))
            Values.append(ItemValue(self.FRITZBOX_HOSTNAME, "externalIPV6Address", fritzStatus.external_ipv6))
            Values.append(ItemValue(self.FRITZBOX_HOSTNAME, "externalIPV6Prefix", fritzStatus.ipv6_prefix))
            Values.append(ItemValue(self.FRITZBOX_HOSTNAME, "connectionStatus", self.__getConnectionStatus(fritzStatus.is_connected)))
            Values.append(ItemValue(self.FRITZBOX_HOSTNAME, "physicalLinkStatus", self.__getLinkStatus(fritzStatus.is_linked)))

            fritzStatusDeviceInfo = fritzStatus.get_device_info()
            Values.append(ItemValue(self.FRITZBOX_HOSTNAME, "softwareVersion", fritzStatusDeviceInfo["software_version"]))
           
            fritzHomeAutomation = FritzHomeAutomation(fc=fc)
            devices = fritzHomeAutomation.get_device_information_list()
            
            HomeDevices = []

            for device in devices:
                if device["NewProductName"] != "Template":  # ignore template devices
                    AIN = device["NewAIN"].replace(" ", "-")
                    
                    HomeDevices.append({"{#AIN}": AIN, "{#NAME}": device["NewDeviceName"]})

                    if device["NewTemperatureIsEnabled"] == "ENABLED":
                        Values.append(ItemValue(self.FRITZBOX_HOSTNAME, "homeDevice["+AIN + ",Temperature]", device["NewTemperatureCelsius"] * 0.1))

                    if device["NewHkrIsEnabled"] == "ENABLED":
                        Values.append(ItemValue(self.FRITZBOX_HOSTNAME,"homeDevice["+AIN + ",HkrSetTemperature]", device["NewHkrSetTemperature"] * 0.1))

            data = { "data": HomeDevices}

            Values.append(ItemValue(self.FRITZBOX_HOSTNAME, "associatedHomeDeviceDiscovery", json.dumps(data)))

            # for value in Values:
            #     print(value.host, value.key, value.value)

            # =====================
            # send data
            #
            sender = Sender(server=self.ZABBIX_SERVER, port=self.ZABBIX_SERVER_PORT)
            sender.send(Values)

            # response = sender.send(Values)
            # print(response)
            # {"processed": 5, "failed": 0, "total": 5, "time": "0.001661", "chunk": 1}
        except FritzConnectionException:
            pass
        except ModuleBaseException:
            pass
        except Exception as e:
            logging.error("An exception occurred: %s", repr(e))


def main():
    monitor = FritzBoxMonitor()

    while True:
        monitor.QueryAndSend()  # waits until next "interval" and then queries the information from the fritzbox and sends them to zabbix


if __name__ == "__main__":
    main()
