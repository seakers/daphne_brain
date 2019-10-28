import threading
from queue import Queue
from time import sleep

from asgiref.sync import async_to_sync


# --> This function will be the proactive teacher agent
def teacher_thread(thread_queue, session, user, channel_name):
    print('\n', '----- Teacher thread -----')
    print('----> session:', session)
    print('----> user:', user)
    print('----> channel name:', channel_name)
    print('--------------------------', '\n')

    # --> Here, the proactive teacher agent will do all of its functionality
    while thread_queue.empty():
        sleep(5)
        print('queue is still empty')



        # --> Objective Space Functionality




        # --> Design Space Functionality



        # --> Sensitivity Functionality



        # --> Feature Functionality








    print('--> Teacher thread has finished')
