FROM python:3-alpine

WORKDIR /app/

ENV ZABBIX_SERVER= \
    FRITZBOX_HOSTNAME= \
    FRITZBOX_IP= \
    INTERVAL= \
    FRITZBOX_USER= \
    FRITZBOX_PASSWD= \
    ZABBIX_SENDER_DEBUG=

COPY app/* ./

RUN pip install --no-cache-dir -r ./requirements.txt

CMD [ "python", "./send.py" ]
