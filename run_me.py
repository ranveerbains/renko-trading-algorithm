
from apscheduler.schedulers.blocking import BlockingScheduler 
import scheduled_job as sj
import sys

#executing scheduled job automatically using scheduler
## Interval time job, grace time for misfire = 5min, 
#if no order executed, program will wait for next candlestick in 5min
print('running')
sys.stdout.flush()
scheduler = BlockingScheduler(job_defaults={'misfire_grace_time': 2*60})
scheduler.add_job(sj.scheduled_job, 'cron', day_of_week='mon-fri', hour = '00-23', minute='*/5', second = 5)
#code above allows function to be executed every 5min, 5s after each 5min
# see if need start date for the scheduler
scheduler.start()
