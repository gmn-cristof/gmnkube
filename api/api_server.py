from sanic import Sanic
from routes import configure_routes

app = Sanic("ContainerAPI")

def main():
    configure_routes(app)
    app.run(host='0.0.0.0', port=5000)

if __name__ == "__main__":
    main()
