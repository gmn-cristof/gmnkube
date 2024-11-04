代码运行之前需输入
export PYTHONPATH=/mnt/d/gmnkube:$PYTHONPATH
export TF_ENABLE_ONEDNN_OPTS=0
启动虚拟环境：
source myenv/bin/activate
列出所有节点：
curl -X GET http://localhost:8001/nodes
获取特定节点信息
curl -X GET http://localhost:8001/nodes/node1
删除节点
curl -X DELETE http://localhost:8001/nodes/node1
列出所有pod：
curl -X GET http://localhost:8001/pods
删除pod：
curl -X DELETE http://localhost:8001/pods/pod1

