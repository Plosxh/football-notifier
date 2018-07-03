import json
import requests
import json
import os
import datetime
import threading
from win10toast import ToastNotifier


def main():
    STATUS = ""
    SCORE_HOME = ""
    SCORE_AWAY = ""
    SAVED_MATCH = {}
    startLoop(SAVED_MATCH)


def startLoop(SAVED_MATCH):
    conf =""
    with open('conf.json') as f:
        conf = json.load(f)
    threading.Timer(10.0, startLoop, [SAVED_MATCH]).start()
    matchs = getMatchInfos(conf)
    date = datetime.datetime.strptime("2018-07-15T17:00:00", '%Y-%m-%dT%H:%M:%S')
    now = datetime.datetime.now()
    approxDate = now - datetime.timedelta(days=2)
    for match in matchs:
        if match["status"] == "IN_PLAY" or match["status"] == "PAUSED" or match["status"] == "SCHEDULED" :
            print(match)
            toAdd = {}
            toAdd["home"] = match["score"]["fullTime"]["homeTeam"]
            toAdd["away"] = match["score"]["fullTime"]["awayTeam"]
            toAdd["status"] = match["status"]
            if match["id"] not in SAVED_MATCH:
                SAVED_MATCH[match["id"]]=  toAdd
                data = formatSlackData(match)
                toaster = ToastNotifier()
                print("first passage")
                toaster.show_toast(match["status"],
                                   match["homeTeam"]["name"]+" : "+str(match["score"]["fullTime"]["homeTeam"])+"\n"+match["awayTeam"]["name"]+" : "+str(match["score"]["fullTime"]["awayTeam"]),
                                   icon_path="./Soccer-icon.png",
                                   duration=5)
            else:
                if match["score"]["fullTime"]["homeTeam"] != SAVED_MATCH["id"]["home"] or match["score"]["fullTime"]["awayTeam"] != SAVED_MATCH["id"]["away"] or SAVED_MATCH["id"]["status"] != match["status"]:
                    SAVED_MATCH[match["id"]]=  toAdd
                    data = formatSlackData(match)
                    print("changed")
                    toaster = ToastNotifier()
                    toaster.show_toast(match["status"],
                                       match["homeTeam"]["name"]+" : "+str(match["score"]["fullTime"]["homeTeam"])+"\n"+match["awayTeam"]["name"]+" : "+str(match["score"]["fullTime"]["awayTeam"]),
                                       icon_path="./Soccer-icon.png",
                                       duration=5)


def formatSlackData(data):
    format = ""
    format = "["+data["status"]+"] : "+data["competition"]["name"]+" | Date : "+ str(datetime.datetime.strptime(data["utcDate"][:-1], '%Y-%m-%dT%H:%M:%S'))+" | " + " " + data["homeTeam"]["name"] + " ( Home Team ) VS "+ data["awayTeam"]["name"]
    format += " ( Away Team ) | Result : "+str(data["score"]["fullTime"]["homeTeam"])+" / "+str(data["score"]["fullTime"]["awayTeam"])

    return format

def sendToSlack(webhook, data):
    slack_data = {}
    slack_data['text']=data
    resp = requests.post(webhook, data=json.dumps(slack_data), headers={'Content-Type': 'application/json'})


def sendToES(es_client, indexName, docType, data):
    es_client = Elasticsearch(
                    host="localhost",
                    port=9200,
                )
    create_index(es_client,conf["elasticsearch"]["index"])
    es_client.index(index=indexName,
                    doc_type=docType,
                    body=data,
                    id=data["id"])
def getMatchInfos(conf):
    """
        Get match data from football-data.org and return an array of match
    """
    req = requests.get(conf["football"]["endpoint"], headers={"X-Auth-Token":conf["football"]["apiKey"]})
    match = json.loads(req.content)
    for m in match["matches"]:
        if m["status"] != "FINISHED" and m["status"] != "SCHEDULED":
    return match["matches"]


def create_index(es_client, index):
    """
        Create the ElasticSearch Index if it doesn't exist
    """
    try:
        res = es_client.indices.exists(index)
        if res is False:
            es_client.indices.create(index, body=INDEX_MAPPING)
            return 1
    except (ConnectionError, ConnectionRefusedError, RequestError):
        logger.info("Check ElasticSearch instances, must not be viable or healthy")

if __name__ == '__main__':
    main()
