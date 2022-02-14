import os
import sys
import django

from client.Client import Client
from client.Excel import Excel
from client.Topic import Topic
from client.LearningModule import LearningModule
from client.Message import Message


# --> Setup django for standalone use
sys.path.append('/app/daphne/daphne_brain')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'daphne_brain.settings')
django.setup()
from django.contrib.auth.models import User


# --> Define demo accounts
bryan_account = {
    'username': 'bcoots',
    'email': 'bcoots@seaklab.com',
    'password': 'Yq7s5GXZaQ8vH7k6'
}

dani_account = {
    'username': 'dselva',
    'email': 'dselva@seaklab.com',
    'password': 'aYH8x9y9hPsghbK5'
}

demo_accounts = [dani_account, bryan_account]





def main():



    client = Client()

    # DROP / CREATE TABLES
    client.initialize()

    # Index demo users
    index_demo_users(client)

    # Index learning content
    Excel(client).index()
    Topic(client).index()
    LearningModule(client).index()
    Message(client).index()



def index_demo_users(client):
    usernames = [x.username for x in client.get_users()]
    for account in demo_accounts:
        if account['username'] not in usernames:
            user = User.objects.create_user(account['username'], account['email'], account['password'])
            user.save()
            client.index_authuser_group(user.id, 1)






if __name__ == "__main__":
    main()