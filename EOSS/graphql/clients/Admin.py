import timeit

from EOSS.graphql.client import Client as GQLClient
from daphne_context.models import UserInformation
from asgiref.sync import async_to_sync, sync_to_async
from concurrent.futures import ProcessPoolExecutor
import asyncio





class Admin(GQLClient):

    def __init__(self, user_info: UserInformation):
        super().__init__(user_info)

    ##############
    ### INSERT ###
    ##############

    async def add_to_group(self, group_id):

        # --> 1. Check to see if the user is already part of the group
        query = """
            query add_to_group_check {
                panel: Join__AuthUser_Group_aggregate%s {
                    aggregate {
                        count
                    }
                }
            }
        """ % await GQLClient._where_wrapper([
            await GQLClient._where('group_id', '_eq', int(group_id), int),
            await GQLClient._where('user_id', '_eq', int(self.user_id), int)
        ])
        response = await self._query(query)

        if int(response['panel']['aggregate']['count']) > 0:
            print('--> USER ALREADY IN GROUP')
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

        result = await self._execute(query)
        if 'insert_Join__AuthUser_Group_one' not in result:
            return None
        return result['insert_Join__AuthUser_Group_one']



