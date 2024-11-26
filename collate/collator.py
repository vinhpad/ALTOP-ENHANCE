import torch
import random
import numpy as np
from .graph_builder import *


graph_builder = GraphBuilder()


def collate_fn(batch):
    max_len = max([len(f["input_ids"]) for f in batch])
    input_ids = [f["input_ids"] + [0] * (max_len - len(f["input_ids"])) for f in batch]
    input_mask = [[1.0] * len(f["input_ids"]) + [0.0] * (max_len - len(f["input_ids"])) for f in batch]
    labels = [f["labels"] for f in batch]
    batch_entity_pos = [f["entity_pos"] for f in batch]
    batch_sent_pos = [f['sent_pos'] for f in batch]
    batch_virtual_pos = create_virtual_node(batch_entity_pos)
    hts = [f["hts"] for f in batch]
    input_ids = torch.tensor(input_ids, dtype=torch.long)
    input_mask = torch.tensor(input_mask, dtype=torch.float)

    graph, num_mention, num_entity, num_sent, num_virtual = graph_builder.create_graph(batch_entity_pos, batch_sent_pos, batch_virtual_pos)

    output = (input_ids, input_mask,
              batch_entity_pos, 
              batch_sent_pos,
              batch_virtual_pos,
              graph, 
              num_mention, 
              num_entity, 
              num_sent, 
              num_virtual,
              labels,
              hts)
    return output