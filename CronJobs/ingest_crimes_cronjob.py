from geopy.distance import vincenty
import json
from pymongo import MongoClient
import sodapy as sp
import datetime
from dateutil.relativedelta import relativedelta


date = datetime.datetime.now() - relativedelta(days=14)


date="'" + str(date)[0:10] + "T00:00:00.000'"


client = sp.Socrata("data.sfgov.org", "uWZNEv4tarYda0YNliMSOxHzk")
data=client.get("cuks-n6tp", content_type="json", where= "date>=%s" % date,limit=1000000)

client.close()

data_deduped=[]

#deduplicate
for item in data:
    if item["incidntnum"] not in incidnt_list:
            data_deduped.append(item)
            incidnt_list.append(item["incidntnum"])

#print(len(data), len(data_deduped))

cli_mongo = MongoClient()
db= cli_mongo["database"]

for i in data_deduped:
    db.sf_crimes.insert(i)

cli_mongo.close()


res_list=[]
mongo= MongoClient()
db = mongo["database"]
res_data =db.restaurants.find()
for res in res_data:
    res_list.append(res)
mongo.close()

def assoc_crime (res_id,res_cor):
        crimes =[]
        for i in data_deduped:
                record={}
                pt1=(float(i["y"]),float(i["x"]))
                pt2=(float(res_cor[0]), float(res_cor[1]))
                dist = vincenty(pt1,pt2).miles
                if dist < (.15):
                        record["restaurant"]=res_id
                        record["crime"]=i["incidntnum"]
                        crimes.append(record)
        return crimes
failed=[]
i=0
a=datetime.datetime.now()

mongo = MongoClient()
db= mongo["database"]
for restaurant in res_list:
    c=datetime.datetime.now()
    try:
        to_insert=assoc_crime(restaurant["id"],(restaurant["coordinates"]["latitude"],restaurant["coordinates"]["longitude"]))
        if len(to_insert)>0:
            db.crime_restaurant.insert(to_insert)
            b=datetime.datetime.now()
            i=i+1
            print("timeframe:", timeframe, "processed:",i,",time_batch:",b-c,",total time:", b-a)
    except:
        failed.append(restaurant["id"])
        continue
    mongo.close()

