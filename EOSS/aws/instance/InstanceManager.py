import os
import boto3
import asyncio

from EOSS.aws.instance.DesignEvaluatorInstance import DesignEvaluatorInstance
from EOSS.aws.clients.InstanceClient import InstanceClient
from EOSS.utils import call_boto3_client_async
from EOSS.aws.clients.SqsClient import SqsClient


""" InstanceManager
- Purpose of this class is to manage / regulate user ec2 instances for hosting containerized services

Services
- design-evaluator
- genetic-algorithm
    
AWS Functions
    1. run_instances()
    
    
    2. start_instances()
    3. stop_instances()
    
    SSM
    4. start_session()
    
    
    
"""


class InstanceManager:

    def __init__(self, user_info, resource_type='design-evaluator'):
        self.user_info = user_info
        self.user_id = self.user_info.user.id
        self.eosscontext = user_info.eosscontext
        self.resource_type = resource_type

        # --> List of (AbstractInstance) objects
        self.instances = []


    @property
    async def count(self):
        if self.resource_type == 'design-evaluator':
            return self.eosscontext.design_evaluator_task_count
        else:
            print('--> INSTANCE TYPE NOT RECOGNIZED')
        return 0



    async def initialize(self):

        # --> Gather the currently running ec2 instances
        await self.gather_instances()


    async def gather_instances(self):
        instance_list = await InstanceClient.get_instances(self.user_id, self.resource_type)

        # --> Create async init tasks
        async_tasks = []
        for instance in instance_list:
            if self.resource_type == 'design-evaluator':
                instance = DesignEvaluatorInstance(self.user_info, instance)
                self.instances.append(DesignEvaluatorInstance(self.user_info, instance))
                task = asyncio.create_task(instance.initialize())
                async_tasks.append(task)

        # --> Await all async tasks
        for task in async_tasks:
            await task

    """
      _____                  _       _         _____                                         
     |  __ \                | |     | |       |  __ \                                        
     | |__) |___  __ _ _   _| | __ _| |_ ___  | |__) |___  ___  ___  _   _ _ __ ___ ___  ___ 
     |  _  // _ \/ _` | | | | |/ _` | __/ _ \ |  _  // _ \/ __|/ _ \| | | | '__/ __/ _ \/ __|
     | | \ \  __/ (_| | |_| | | (_| | ||  __/ | | \ \  __/\__ \ (_) | |_| | | | (_|  __/\__ \
     |_|  \_\___|\__, |\__,_|_|\__,_|\__\___| |_|  \_\___||___/\___/ \__,_|_|  \___\___||___/
                  __/ |                                                                      
                 |___/ 
    """

    async def regulate_resources(self):
        async_tasks = []

        # --> Regulate instances concurrently in async tasks
        requested_num = await self.count
        current_num = len(self.instances)
        diff = abs(current_num - requested_num)
        if current_num < requested_num and requested_num <= 10:
            print('--> STARTING', diff, 'INSTANCES')
            for idx in range(diff):
                async_tasks.append(
                    asyncio.create_task(self.start_instance())
                )
        elif current_num > requested_num:
            print('--> STOPPING', diff, 'INSTANCES')
            for idx in range(diff):
                async_tasks.append(
                    asyncio.create_task(self.stop_instance(self.instances.pop()))
                )
        # --> Await all async tasks
        for task in async_tasks:
            await task

    async def start_instance(self, identifier=None):

        # --> 1. Check if there are any stopped instances that can be started



        return 0

    async def stop_instance(self, instance):
        return 0


















