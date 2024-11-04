import etcd3

# 连接到 Etcd 服务器
etcd_client = etcd3.client(host='localhost', port=2379)  # 根据实际情况修改主机和端口

# 存储键值对
def put_key(key, value):
    etcd_client.put(key, value)
    print(f"Stored key: {key}, value: {value}")

# 获取键值对
def get_key(key):
    value, metadata = etcd_client.get(key)
    if value is not None:
        print(f"Retrieved key: {key}, value: {value.decode()}")
    else:
        print(f"Key {key} not found.")

# 列出所有键值对
def list_keys():
    print("Listing all keys:")
    for value, metadata in etcd_client.get_all():
        print(f"Key: {metadata.key.decode()}, Value: {value.decode()}")

# 示例使用
if __name__ == "__main__":
    put_key("nodes/node1", "Node 1 info")
    put_key("nodes/node2", "Node 2 info")
    
    get_key("nodes/node1")
    
    list_keys()
