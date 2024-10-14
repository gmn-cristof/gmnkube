# api/hello.py
from sanic import Sanic
from sanic.response import json

app = Sanic("HelloWorldApp")

@app.route("/hello")
async def hello(request):
    return json({"message": "Hello, World!"})

if __name__ == "__main__":
    app.run()
