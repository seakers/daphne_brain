from flask import Flask, request
app = Flask(__name__)

@app.route('/')
def haura_auth():
    print("Check hasura status", request.data)

    response = {
        "X-Hasura-User-Id": "1",
        "X-Hasura-Role": "admin",
        "X-Hasura-Is-Owner": "true"
    }
    print("--> RESPONSE", response)
    return response