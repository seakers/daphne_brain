import asyncio
import aiohttp
import json





async def main(query, variables=None):
    json_body = {'query': query}
    if variables is not None:
        json_body['variables'] = variables

    async with aiohttp.ClientSession() as session:
        async with session.post('http://graphql:8080/v1/graphql', json=json_body) as response:

            text = await response.text()
            result = json.loads(text)
            print('--> RESULT:', result)
            return result


if __name__ == '__main__':
    query = """
        query dataset_id {
            Dataset(
                where: {id: {_eq: 1}}
            ) {
                group_id
                id
                name
                problem_id
                user_id
            }
        }
    """

    asyncio.run(main(query))


