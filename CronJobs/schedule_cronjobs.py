from crontab import CronTab
import datetime 
import json 
my_cron = CronTab(user='w205')
job = my_cron.new(command='python3 /w205/home/w205_2017_project/ingest_crime_cronjob.py')
job.hour.on(5)
date = {"time complete": str(datetime.datetime.now())}
with open ('crime_log.json', 'wt') as  file :
    json.dumps(date,file)
    
    



