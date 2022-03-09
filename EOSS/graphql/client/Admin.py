import timeit

from EOSS.graphql.client.Abstract import AbstractGraphqlClient as GQLClient
from daphne_context.models import UserInformation
from asgiref.sync import async_to_sync, sync_to_async
from concurrent.futures import ProcessPoolExecutor
import asyncio





class AdminGraphqlClient(GQLClient):

    def __init__(self, user_info: UserInformation):
        super().__init__(user_info)

    ###########
    ### ADD ###
    ###########

    async def add_user_to_group(self, group_id, user_id=None):
        if user_id is None:
            user_id = self.user_id

        # --> 1. Check to see if the user is already part of the group
        if await self.check_user_in_group(group_id, user_id=user_id) is True:
            return None

        # --> 2. Add user to group
        mutation = """
            mutation insert_user_to_group {
                insert_Join__AuthUser_Group_one(
                    object: {user_id: %d, group_id: %d, admin: false}
                ) {
                    id
                }
            }
        """ % (int(self.user_id), int(group_id))

        result = await self._query(mutation)
        if 'insert_Join__AuthUser_Group_one' not in result:
            return None
        return result['insert_Join__AuthUser_Group_one']

    async def check_user_in_group(self, group_id, user_id=None):
        if user_id is None:
            user_id = self.user_id

        # --> 1. Check to see if the user is already part of the group
        query = """
                query add_to_group_check {
                    panel: Join__AuthUser_Group_aggregate(where: {group_id: {_eq: %d}, user_id: {_eq: %d}}) {
                        aggregate {
                            count
                        }
                    }
                }
            """ % (int(group_id), int(user_id))
        response = await self._query(query)

        if int(response['panel']['aggregate']['count']) > 0:
            return True
        return False
