import socket
import threading
import pickle
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import gym
import myenv
from kubernetes import client, config
from sanic import Sanic
from sanic.response import json
from sanic.request import Request

# Sanic应用
app = Sanic("DDQN_Scheduler")

# 获取k8s集群中节点的IP和主机名
def get_node_ips():
    """从 Kubernetes 集群中获取所有 Node 的 IP 地址"""
    config.load_kube_config()
    v1 = client.CoreV1Api()
    
    node_ips = []
    nodes = v1.list_node()
    for node in nodes.items:
        node_name = node.metadata.name
        for address in node.status.addresses:
            if address.type == 'InternalIP':
                node_ips.append((node_name, address.address))
                break

    return node_ips

# 通过K8s获取节点IP并打印出来
node_ips = get_node_ips()
print(f"[INFO] Nodes and IPs: {node_ips}")

# 创建到节点的socket连接
def create_socket_connections(node_ips):
    """根据Node IPs创建Socket连接"""
    sockets = []
    for node_name, node_ip in node_ips:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.connect((node_ip, 9000))
            print(f"[INFO] Connected to {node_name} at {sock.getpeername()}")
            sockets.append(sock)
        except socket.error as e:
            print(f"[ERROR] Failed to connect to {node_name} at {node_ip}: {e}")
    return sockets

# 动态创建与所有节点的连接
sockets = create_socket_connections(node_ips)

# 环境初始化
env = gym.make('k8s-v0').unwrapped
env.setsocks(*sockets)  # 设置Socket连接到环境中

# hyper parameters
BATCH_SIZE = 32
LR = 0.01
EPSILON = 0.9
GAMMA = 0.9
TARGET_REPLACE_ITER = 100
MEMORY_CAPACITY = 100
N_ACTIONS = env.action_space.n
N_STATES = env.observation_space.shape[0]

class Net(nn.Module):
    def __init__(self):
        super(Net, self).__init__()
        self.fc1 = nn.Linear(N_STATES, 50)
        self.fc1.weight.data.normal_(0, 0.1)
        self.out = nn.Linear(50, N_ACTIONS)
        self.out.weight.data.normal_(0, 0.1)

    def forward(self, x):
        x = F.relu(self.fc1(x))
        actions_value = self.out(x)
        return actions_value

class DDQN(object):
    def __init__(self):
        self.eval_net, self.target_net = Net(), Net()
        self.learn_step_counter = 0
        self.memory_counter = 0
        self.memory = np.zeros((MEMORY_CAPACITY, N_STATES * 2 + 2))
        self.optimizer = torch.optim.Adam(self.eval_net.parameters(), lr=LR)
        self.loss_func = nn.MSELoss()

    def choose_action(self, x):
        """根据 ε-greedy 策略选择动作"""
        x = torch.unsqueeze(torch.FloatTensor(x), 0)
        if np.random.uniform() < EPSILON:
            actions_value = self.eval_net.forward(x)
            action = torch.max(actions_value, 1)[1].data.numpy()
            action = action[0]
        else:
            action = np.random.randint(0, N_ACTIONS)
        return action

    def store_transition(self, s, a, r, s_):
        """存储经验"""
        transition = np.hstack((s, [a, r], s_))
        index = self.memory_counter % MEMORY_CAPACITY
        self.memory[index, :] = transition
        self.memory_counter += 1

    def learn(self):
        """DDQN学习步骤"""
        if self.learn_step_counter % TARGET_REPLACE_ITER == 0:
            self.target_net.load_state_dict(self.eval_net.state_dict())
        self.learn_step_counter += 1

        sample_index = np.random.choice(MEMORY_CAPACITY, BATCH_SIZE)
        b_memory = self.memory[sample_index, :]
        b_s = torch.FloatTensor(b_memory[:, :N_STATES])
        b_a = torch.LongTensor(b_memory[:, N_STATES:N_STATES + 1].astype(int))
        b_r = torch.FloatTensor(b_memory[:, N_STATES + 1:N_STATES + 2])
        b_s_ = torch.FloatTensor(b_memory[:, -N_STATES:])

        # DDQN核心：拆分评估网络与目标网络，避免过估计
        q_eval = self.eval_net(b_s).gather(1, b_a)
        q_eval_next = self.eval_net(b_s_)
        q_next = self.target_net(b_s_).gather(1, torch.max(q_eval_next, 1)[1].unsqueeze(1))
        q_target = b_r + GAMMA * q_next.view(BATCH_SIZE, 1)

        loss = self.loss_func(q_eval, q_target)
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

class StepThread(threading.Thread):
    def __init__(self, func, dqn, env, state, action):
        threading.Thread.__init__(self)
        self.func = func
        self.dqn = dqn
        self.env = env
        self.state = state
        self.action = action

    def run(self):
        print('[INFO] Start the Step thread...')
        self.func(self.dqn, self.env, self.state, self.action)
        print('[INFO] Exit the Step thread!')

def makeStep(dqn, env, state, action):
    """执行一步调度"""
    s_, r, done, info = env.step(action)

    dqn.store_transition(state, action, r, s_)

    if env.count == 100:
        pod_action.clear()
        env.reset()

    if dqn.memory_counter > MEMORY_CAPACITY:
        t_file = open('transition.pkl', 'wb')
        pickle.dump(dqn.memory, t_file)
        t_file.close()

pod_action = {}  # 存储每个 Pod 的调度动作

@app.route('/choose', methods=['POST'])
async def choose(request: Request):
    """根据 Pod 名称选择调度节点"""
    podname = request.form.get("podname")
    print(f'[INFO] Get pod: {podname}')

    if podname in pod_action:
        print(f'[INFO] This pod has been scheduled, action: {pod_action[podname]}')
        return json({"action": pod_action[podname]})

    s = env.state

    # 简化Pod类型到状态映射逻辑
    pod_type = podname.split('-')[0]
    pod_states = {
        'video': [100.0, 23.0, 11.25, 2.49, 0.0, 1.54],
        'net': [54.0, 46.2, 80.04, 71.4, 0.0, 1.58],
        'disk': [100.0, 22.96, 12.6, 2.73, 0.0, 86.26]
    }
    s_pod = pod_states.get(pod_type, [0.0] * 6)

    if len(s) == 24:
        s = s + s_pod
    else:
        s[-6:] = s_pod

    # 选择动作
    action = ""
    a = dqn.choose_action(s)
    node_count = len(node_ips)
    if a < node_count:
        action = node_ips[a][0]  # 根据动作选择节点名

    pod_action[podname] = action

    # 启动一个独立线程执行步骤
    thread = StepThread(makeStep, dqn, env, s, a)
    thread.start()

    print(f'[INFO] Action for Pod {podname} is: {action}')
    return json({"action": action})

if __name__ == "__main__":
    dqn = DDQN()
    s = env.reset()

    print("[INFO] Environment initialize...")

    app.run(host="0.0.0.0", port=1234, debug=False, auto_reload=True)
