container_engine/
├── README.md                  # 项目说明文档
├── requirements.txt           # 项目依赖的 Python 包
├── setup.py                   # 项目安装和打包配置
├── config/                    # 配置文件目录
│   ├── __init__.py
│   └── config.yaml            # 配置文件，使用 YAML 格式
├── container/                 # 容器管理模块
│   ├── __init__.py
│   ├── container.py
│   ├── container_manager.py    # 容器管理类（负责创建/删除容器）
│   ├── container_runtime.py    # 容器运行时类（与容器运行时交互，启动/停止容器）
│   └── image_handler.py        # 镜像处理类（下载/管理镜像）
├── orchestrator/              # 调度模块
│   ├── __init__.py
│   ├── scheduler_random.py           # 随机调度算法调度器
│   ├── kube_scheduler_plus.py  # k8s内置调度算法升级版资源调度器（选择合适的节点运行容器）支持cpu,gpu,i/o,net,mem等资源考虑
│   ├── DDQN_scheduler.py           # DDQN深度强化学习资源调度器（选择合适的节点运行容器）支持cpu,gpu,i/o,net,mem等资源考虑
│   ├── kube_scheduler.py           # k8s内置调度算法资源调度器（选择合适的节点运行容器）
│   └── workload_controller.py  # 工作负载控制器（管理调度的容器实例）
├── api/                       # API 接口模块
│   ├── __init__.py
│   ├── api_server.py          # API 服务器（REST API 入口）
│   └── routes.py              # API 路由定义
├── pod/                       # Pod 管理模块
│   ├── __init__.py
│   ├── pod.py                 # Pod 类（管理 Pod 的生命周期）
│   ├── pod_controller.py       # Pod 控制器（管理 Pod 的创建和删除）
├── node/                      # Pod 管理模块
│   ├── __init__.py
│   ├── node.py                 # node 类（管理 Pod 的生命周期）
│   ├── node_controller.py       # node 控制器（管理 Pod 的创建和删除）
├── kubernetes/                # Kubernetes 兼容性模块（可选）
│   ├── __init__.py
│   ├── k8s_client.py          # K8s 客户端类（与 K8s 兼容的接口）
│   └── k8s_resources.py       # K8s 资源定义（可选的 K8s API 资源兼容）
├── etcd/                      # etcd 管理模块
│   ├── __init__.py
│   ├── etcd_client.py         # etcd 客户端类（与 etcd 交互的接口）
│   ├── etcd_manager.py        # etcd 管理类（处理 etcd 数据的存储和检索）
│   └── etcd_config.py         # etcd 配置管理（加载和管理 etcd 配置）
├── exception/                 # 异常处理模块
│   ├── __init__.py
│   └── exception_handler.py    # 统一异常处理
├── logs/                      # 日志管理目录
│   ├── __init__.py
│   └── runtime.log            # 运行时日志文件
├── tests/                     # 单元测试目录
│   ├── __init__.py
│   ├── test_container.py      # 容器模块测试
│   ├── test_orchestrator.py   # 调度模块测试
│   ├── test_api.py            # API 模块测试
│   ├── test_pod.py            # Pod 模块测试
│   ├── test_etcd.py           # etcd 模块测试
└── docs/                      # 文档目录
    ├── architecture.md        # 系统架构文档
    └── usage.md               # 使用指南
