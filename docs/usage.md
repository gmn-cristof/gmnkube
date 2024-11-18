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
调度pod：

curl -X POST http://localhost:8001/DDQN_schedule \
  -H "Content-Type: application/json" \
  -d '{
    "apiVersion": "v1",
    "kind": "Pod",
    "metadata": {
      "name": "example-pod1",
      "namespace": "default",
      "status": "pending"
    }
  }'




停止并删除所有容器：
sudo ctr containers list --quiet | xargs -I {} sudo ctr containers delete {}
从etcd列出所有信息：
etcdctl get "" --prefix
清空etcd内信息：
etcdctl del "" --prefix
运行
python3 api/api_server_master.py

