import os
import sys
import django
import json


from client.Client import Client
from client.Message import Message





def main():
    print('--> INDEXING MESSAGES')

    client = Client()

    msg_text = 'Here is an example of how daphne will help you traverse learning modules'

    more_info = {
        'modules': [
            {'name': 'Spacecraft Bus', 'slides': [1, 3]}
        ]
    }


    for user in client.get_users():
        client.index_message(user.id, msg_text, 'Daphne', json.dumps(more_info))













if __name__ == "__main__":
    main()