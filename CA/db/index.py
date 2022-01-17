from client.Client import Client

from client.Excel import Excel
from client.Topic import Topic
from client.LearningModule import LearningModule




def main():
    client = Client()

    # DROP / CREATE TABLES
    client.initialize()

    Excel(client).index()
    Topic(client).index()
    LearningModule(client).index()






if __name__ == "__main__":
    main()