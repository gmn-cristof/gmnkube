TODO 1：再次审查代码：添加失败回退，回滚机制。
TODO 2：修改调度逻辑，使schedule_pod_to_node相关逻辑能将pod调度到指定ip地址的node
TODO 3：优化更新container_runtime逻辑，添加监控容器运行情况逻辑
TODO 4：兼容pod和node类


状态计算： _get_state 中会将 Pod 的需求资源重复嵌入每个节点的特征，这可能导致模型难以学习区分哪些节点适合调度。建议独立计算 Pod 的需求特征。
节点动态变化： 
在更新 action_size 时，重建模型可能导致训练中断，建议使用模型的部分权重迁移（如 model.add(tf.keras.layers.Dense(..., weights=...))）。