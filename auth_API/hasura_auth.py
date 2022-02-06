from flask import Flask, request

app = Flask(__name__)

@app.route('/')
def hasura_auth():
    response = {
        "X-Hasura-User-Id": "1",
        "X-Hasura-Role": "admin",
        "X-Hasura-Is-Owner": "true"
    }
    return response