import os

from EOSS.aws.clients.SqsClient import SqsClient



""" EvaluationScaling

        1. Purpose
            The purpose of this class is to handle design-evaluator instance scaling on a per-user basis



"""




class EvaluationScaling:

    def __init__(self, user_info, num_instances):
        self.sqs_client = SqsClient(user_info)
        self.prod = os.environ['DEPLOYMENT_TYPE']  # Values: local | prod
        self.num_instances = num_instances

        # --> Get User Info
        self.user_info = user_info
        self.eoss_context = user_info.eosscontext

        self.user_id = user_info.user.id
        self.group_id = user_info.eosscontext.group_id
        self.problem_id = user_info.eosscontext.problem_id
        self.dataset_id = user_info.eosscontext.dataset_id

        # --> Get Queues
        self.eval_request_queue = self.eoss_context.eval_request_queue_url
        self.eval_response_queue = self.eoss_context.eval_response_queue_url


    async def initialize(self):

        # --> 1. Ensure user-specific queues exist
        await self.sqs_client.create_queue_url(self.eval_request_queue)
        await self.sqs_client.create_queue_url(self.eval_response_queue)


        return 0




