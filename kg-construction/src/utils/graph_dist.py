from src.utils.file_operation import load_json


def floyd_warshall(graph, num_nodes):
    # 初始化距离矩阵
    dist = [[float("inf")] * num_nodes for _ in range(num_nodes)]

    # 自己到自己距离为0
    for i in range(num_nodes):
        dist[i][i] = 0

    # 填充初始边的信息，处理无向图：对每个边，两个方向都设为1
    for edge in graph:
        source, target = edge["source_id"], edge["target_id"]
        dist[source][target] = 1  # 设定source到target的边距离为1
        dist[target][source] = 1  # 设定target到source的边距离为1

    # Floyd-Warshall核心算法
    for k in range(num_nodes):
        for i in range(num_nodes):
            for j in range(num_nodes):
                if dist[i][j] > dist[i][k] + dist[k][j]:
                    dist[i][j] = dist[i][k] + dist[k][j]

    # 将不可达的路径设置为-1
    for i in range(num_nodes):
        for j in range(num_nodes):
            if dist[i][j] == float("inf"):
                dist[i][j] = -1

    return dist


def compute_shortest_paths(file_path, num_nodes):
    # 加载图数据
    graph = load_json(file_path)
    start_id = 0
    graph = [
        edge
        for edge in graph
        if edge["source_id"] >= start_id and edge["target_id"] >= start_id
    ]
    # 计算最短路径
    dist = floyd_warshall(graph, num_nodes)
    return dist
