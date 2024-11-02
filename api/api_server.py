from sanic import Sanic
from api.routes import configure_routes

# 初始化 Sanic 应用
app = Sanic("ContainerAPI")

# 主函数，配置路由并启动应用
def main():
    configure_routes(app)  # 调用路由配置函数
    app.run(host='0.0.0.0', port=5000)  # 监听 0.0.0.0，端口 5000

if __name__ == "__main__":
    main()
