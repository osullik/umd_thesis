import networkx as nx

# Create the graph from the given adjacency list
adj_list = {
    'a': {'b': 2, 'c': 3},
    'b': {},
    'c': {'d': 4},
    'd': {'e': 5},
    'e': {'f': 6, 'g': 7},
    'f': {},
    'g': {}
}
# Convert the nested dictionaries to tuple pairs with weights
adj_list_tuples = {node: [(neighbor, weight) for neighbor, weight in neighbors.items()] for node, neighbors in adj_list.items()}

G = nx.from_dict_of_lists(adj_list_tuples, create_using=nx.Graph)

# Identify and merge chain vertices
chain_vertices = [v for v, d in G.degree() if d == 1]  # Vertices with degree 1
for v in chain_vertices:
    neighbors = list(G.neighbors(v))
    if len(neighbors) == 1:  # Ensure it's still a chain vertex
        neighbor = neighbors[0]
        if G.degree(neighbor) == 2:  # Merge only if the neighbor has degree 2
            neighbor_neighbor = list(G.neighbors(neighbor))[0]
            # Update or compute new weights based on some criteria
            new_weight = G[v][neighbor]['weight'] + G[neighbor][neighbor_neighbor]['weight']
            # Add or update the edge with the merged vertices
            if G.has_edge(v, neighbor_neighbor):
                G[v][neighbor_neighbor]['weight'] = min(G[v][neighbor_neighbor]['weight'], new_weight)
            else:
                G.add_edge(v, neighbor_neighbor, weight=new_weight)
            G.remove_node(neighbor)

# Display the simplified graph with updated weights
print("Simplified graph with updated weights:")
print(G.edges(data=True))
