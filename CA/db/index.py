import os
import sys
import django

from client.Client import Client
from client.Excel import Excel
from client.Topic import Topic
from client.LearningModule import LearningModule
from client.Message import Message
from client.Questions import Questions


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

jennifer_account = {
    'username': 'jbowles',
    'email': 'jbowles@seaklab.com',
    'password': 'yzAhcenF3TdrCuve'
}

greg_account = {
    'username': 'ghogan',
    'email': 'ghogan@seaklab.com',
    'password': 'EP9fAq3PpFW6gKLc'
}

dani_account = {
    'username': 'dselva',
    'email': 'dselva@seaklab.com',
    'password': 'aYH8x9y9hPsghbK5'
}

demo_user_1 = {
    'username': 'duser1',
    'email': 'duser1@seaklab.com',
    'password': 'MDEdnqxs373gK8Um'
}
demo_user_2 = {
    'username': 'duser2',
    'email': 'duser2@seaklab.com',
    'password': 'qJ64ZPLaGum8XcDf'
}
demo_user_3 = {
    'username': 'duser3',
    'email': 'duser3@seaklab.com',
    'password': 'UY2TV8DUUfgzdGVr'
}
demo_user_4 = {
    'username': 'duser4',
    'email': 'duser4@seaklab.com',
    'password': '667Ayq9UJNz2U2Tb'
}
demo_user_5 = {
    'username': 'duser5',
    'email': 'duser5@seaklab.com',
    'password': 'U4VPbxK2Ch9PZ5NL'
}


demo_accounts = [dani_account, jennifer_account, bryan_account, greg_account, demo_user_1, demo_user_2, demo_user_3, demo_user_4, demo_user_5]





def main():

    client = Client()

    # DROP / CREATE TABLES
    client.initialize()

    # Index demo users
    index_demo_users(client)

    # Index learning content
    Excel(client).index()
    LearningModule(client).index()
    Questions(client).index()
    Topic(client).index()
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