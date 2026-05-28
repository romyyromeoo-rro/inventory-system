from services.task_queue import *
import time


#push_failed_job({
    #"username": "romeo",
    #"action": "CRASH_TEST"
#})


push_task({
     "username": "romeo",
     "action": "TEST_PROCESSING_QUEUE"
})
#push_low_priority({
    #"username": "romeo",
    #"action": "LOW_1"
#})

#push_low_priority({
    #"username": "romeo",
    #"action": "LOW_2",
#})

#push_high_priority({
    #"username": "romeo",
    #"action": "HIGH_1"
#})
