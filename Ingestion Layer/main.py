from pprint import pprint
import grequests
import io, json, time
from pymongo import MongoClient
from datetime import datetime
import csv
#db.sfdatagov.drop()
client = MongoClient()
db = client.database
def normalizeBusinessName(businessName):
    nameOfBusiness=str(businessName.replace(" ","-"))
    nameOfBusiness=nameOfBusiness.lower()
    nameOfBusiness=nameOfBusiness.replace(".","")
    nameOfBusiness=nameOfBusiness.replace("-&-","-and-")
    nameOfBusiness=nameOfBusiness.replace("'s","s")
    nameOfBusiness=nameOfBusiness.replace("-inc","-")
    nameOfBusiness=nameOfBusiness.replace("-llc","-")    
    return nameOfBusiness+"-san-francisco"
    
def ingest_sfdatagov():
    db.sfdatagov.drop()
    with open('restaurants.json') as data_file:    
        data = json.load(data_file)
    restaurants_json={}
    for each in data["data"]:
        nameOfBusiness=normalizeBusinessName(str(each[9]))
        db.sfdatagov.insert_one({"id":nameOfBusiness,"business_id":each[8],"business_name":each[9],"business_address":each[10],"business_city":each[11],"business_state":each[12],"business_postal_code":each[13],"business_latitude":each[14],"business_longitude":each[15],"business_location":each[16],"business_phone_number":each[17],"inspection_id":each[18],"inspection_date":each[19],"inspection_score":each[20],"inspection_type":each[21],"violation_id":each[22],"violation_description":each[23],"risk_category":each[24]})

def ingest_yelp_restaurants_from_sfdatagov():
    restaurants_file1 = open('Restaurant_Scores_-_LIVES_Standard.csv')
    db.restaurants_yelp.drop()
    db.restaurants_yelp_notfound.drop()
    restaurants1=csv.reader(restaurants_file1)
    rest_urls=[]
    start=time.time()
    counter=0
    sfdatagov_businesses={}
    for row in restaurants1:
        nameOfBusiness=normalizeBusinessName(str(row[1]))
        url = "https://api.yelp.com/v3/businesses/"+nameOfBusiness
        sfdatagov_businesses[url]=nameOfBusiness
        rest_urls.append(url)
        counter+=1
    end=time.time()
    print("Total time taken in seconds:",round(end-start,2))
    print("Total restaurants to be queried in yelp:",len(rest_urls))
    print()
    rest_urls=list(set(rest_urls))
    print("Total distinct restaurants to be queried in yelp:",len(rest_urls))
    print("Total distinct datasfgov_businesses restaurants ids stored:",len(sfdatagov_businesses))    
    restaurants_file1.close()
    
    start=time.time()
    print("Total yelp calls:",len(rest_urls))
    prev=0
    index=1
    count=0
    for i in range(0,len(rest_urls),2):
        print("prev:",prev)
        print("i:",i)
        rs = (grequests.get(u,headers={"Authorization":"Bearer jmJ29BYShLu4XglzpUvZwEKlfi3d8mHVFunVnbQFtUkZQFMhF5cgcKcSrTtscuP78TL_n3niYhNaIxtLQQT1HjHq0eUEEvafd-MHAd4852znbKRlA-mNXGm1fIlqWXYx"}) for u in rest_urls[prev:i])
        result=grequests.map(rs)
        data={}

        pos=0
        for each in result:
            if each is not None:
                if each.status_code and each.status_code == 200:
                    yelp_json=each.json()
                    yelp_json["sfdatagov_id"]=sfdatagov_businesses[each.url]
                    db.restaurants_yelp.insert_one(yelp_json)
                    count+=1
                else:
                    print("Not found",each.url)
                    db.restaurants_yelp_notfound.insert_one({"url":each.url})
            index+=1
        prev=i
        print()
    end=time.time()
    print("Total time taken in seconds:",round(end-start,2))
    print("Total entries found on yelp and stored in mongodb:",count)

    
ingest_sfdatagov()
ingest_yelp_restaurants_from_sfdatagov()
