import dgl
import torch
import numpy as np
from .graph_builder_utils import *

class GraphBuilder:
    def __init__(self,
                 create_undirected_edges: bool = True,
                 add_self_edge: bool = True):
        self.create_undirected_edges = create_undirected_edges
        self.add_self_edge = add_self_edge

    def create_graph(self, batch_entity_pos, batch_sent_pos, batch_token_pos):
        batch_size = len(batch_entity_pos)

        num_mention = max([sum([len(ent_pos) for ent_pos in entity_pos]) for entity_pos in batch_entity_pos])
        num_entity = max([len(entity_pos) for entity_pos in batch_entity_pos])
        num_sent = max([len(sent_pos) for sent_pos in batch_sent_pos])
        # num_token = max([len(token_pos) for token_pos in batch_token_pos])

        mention_to_mention_edges = get_mention_to_mention_edges(num_mention, batch_entity_pos)
        sentence_to_sentence_edges = get_sentence_to_sentence_edges(num_sent, batch_sent_pos)
        mention_to_sentence_edges = get_mention_to_sentence_edges(num_mention, num_sent, batch_sent_pos, batch_entity_pos)
        mention_to_entity_edges = get_mention_to_entity_edges(num_mention, num_entity, batch_entity_pos)
        entity_to_sentence_edges = get_entity_to_sentence_edges(num_entity, num_sent, batch_sent_pos, batch_entity_pos)
        # token_to_sent_edges = get_token_to_sent_edges(num_token, num_sent, batch_token_pos, batch_sent_pos)
        # token_to_mention_edges = get_token_to_mention_edges(num_mention, num_token, batch_entity_pos, batch_token_pos)

        u = []
        v = []

        def get_new_entity_id(origin_entity_id):
            return num_mention * batch_size + origin_entity_id

        def get_new_sent_id(origin_sent_id):
            return num_mention * batch_size + num_entity * batch_size + origin_sent_id
        
        # def get_new_token_id(origin_token_id):
        #     return num_mention * batch_size + num_entity * batch_size + num_sent * batch_size + origin_token_id

        edge_u, edge_v = mention_to_mention_edges
        for edge_id in range(len(edge_u)):
            u.append(edge_u[edge_id])
            v.append(edge_v[edge_id])

        edge_u, edge_v = sentence_to_sentence_edges
        for edge_id in range(len(edge_u)):
            u.append(get_new_sent_id(edge_u[edge_id]))
            v.append(get_new_sent_id(edge_v[edge_id]))

        edge_u, edge_v = mention_to_sentence_edges
        for edge_id in range(len(edge_u)):
            u.append(edge_u[edge_id])
            v.append(get_new_sent_id(edge_v[edge_id]))
            if self.create_undirected_edges:
                v.append(edge_u[edge_id])
                u.append(get_new_sent_id(edge_v[edge_id]))

        edge_u, edge_v = mention_to_entity_edges
        for edge_id in range(len(edge_u)):
            u.append(edge_u[edge_id])
            v.append(get_new_entity_id(edge_v[edge_id]))
            if self.create_undirected_edges:
                u.append(get_new_entity_id(edge_v[edge_id]))
                v.append(edge_u[edge_id])

        edge_u, edge_v = entity_to_sentence_edges
        for edge_id in range(len(edge_u)):
            u.append(get_new_entity_id(edge_u[edge_id]))
            v.append(get_new_sent_id(edge_v[edge_id]))
            if self.create_undirected_edges:
                u.append(get_new_sent_id(edge_v[edge_id]))
                v.append(get_new_entity_id(edge_u[edge_id]))

        # edge_u, edge_v = token_to_mention_edges
        # for edge_id in range(len(edge_u)):
        #     u.append(get_new_token_id(edge_u[edge_id]))
        #     v.append(edge_v[edge_id])
            
        #     if self.create_undirected_edges:
        #         u.append(edge_v[edge_id])
        #         v.append(get_new_token_id(edge_u[edge_id]))

        # edge_u, edge_v = token_to_sent_edges
        # for edge_id in range(len(edge_u)):
        #     u.append(get_new_token_id(edge_u[edge_id]))
        #     v.append(get_new_sent_id(edge_v[edge_id]))
            
        #     if self.create_undirected_edges:
        #         u.append(get_new_sent_id(edge_v[edge_id]))
        #         v.append(get_new_token_id(edge_u[edge_id]))

        num_nodes = num_mention * batch_size  + num_entity * batch_size + num_sent * batch_size # + num_token * batch_size

        for edge_id in range(len(u)):
            assert u[edge_id] != v[edge_id], f"Exist self edge {u[edge_id]} to {v[edge_id]}"

        one_hot_encoding = np.zeros((num_nodes, num_nodes))
        
        for edge_u in u:
            for edge_v in v:
                one_hot_encoding[edge_u][edge_v] = 1

        graph = dgl.graph((torch.tensor(u), torch.tensor(v)), num_nodes=num_nodes)
        
        if self.add_self_edge:
            graph = dgl.add_self_loop(graph)
            
        return graph, num_mention, num_entity, num_sent, one_hot_encoding