# api/hello.py
from sanic import Sanic
from sanic.response import json

app = Sanic("HelloWorldApp")

@app.route("/hello")
async def hello(request):
    return json({"message": "Hello, World!"})

if __name__ == "__main__":
    app.run()

{"name": "example-pod", 
 "namespace": "default", 
 "containers": [
     {"name": "nginx-container",
      "image": "nginx:latest",
      "command": [], 
      "resources": {
          "requests": {
              "cpu": "100m",
              "memory": "256Mi"
              }, 
          "limits": {
              "cpu": "200m", 
              "memory": "512Mi"}
          }, 
      "ports": [80]
      }
     , 
     {
          "name": "busybox-container", 
          "image": "busybox", 
          "command": ["sh", "-c", "sleep 3600"],
          "resources": {
              "requests": {
                  "cpu": "50m", 
                  "memory": "128Mi"
                  }, 
              "limits": {
                      "cpu": "100m", "memory": "256Mi"}
              }, 
          "ports": []}], "volumes": {}, "status": "Pending"}