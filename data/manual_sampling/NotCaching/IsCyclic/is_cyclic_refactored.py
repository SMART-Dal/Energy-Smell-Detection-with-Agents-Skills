from enum import Enum


class NodeState(Enum):
    UNVISITED = 0
    VISITING = 1
    VISITED = 2

def dfs(node: int, visited: list, graph: list[list[int]]) -> bool:
    if visited[node] == NodeState.VISITING:
        return True
    visited[node] = NodeState.VISITING
    for neighbor in graph[node]:
        if visited[neighbor] != NodeState.VISITED:
            if dfs(neighbor, visited, graph):
                return True
    visited[node] = NodeState.VISITED
    return False


def is_cyclic(graph: list[list[int]]):
    visited = [NodeState.UNVISITED for i in range(len(graph))]
    for i in range(len(graph)):
        if visited[i] == NodeState.UNVISITED:
            if dfs(i, visited, graph):
                return True
    return False




count = 100
k = 30
graph = {}
for i in range(count):
    graph[i] = [i+1]
graph[count] = []
for i in range(count+1, count + k):
    graph[i] = [1]
    graph[0].append(i)
graph[0].append(count + k)
graph[count + k] = [count + k + 1]
graph[count + k + 1] = [0]


for i in range(10_000):
    a = is_cyclic(graph)

