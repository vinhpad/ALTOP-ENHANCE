import torch
from torch import nn
from .gcnii.air_gcnii import AIRGCNII

class GNN(nn.Module):
    def __init__(self, num_node_type, node_type_embedding, hidden_feat_dim: int, device: torch.device):
        
        super().__init__()
        self.node_type_embedding = nn.Embedding(num_node_type, node_type_embedding)

        self.gcn = AIRGCNII(
            num_hidden=hidden_feat_dim,
            num_layers=4,
            drop_out=0.2,
            drop_edge=0,
            lambda_=0.5
        )

        self.layer_norm = nn.LayerNorm(hidden_feat_dim)

        self.device = device

    def forward(self, inputs):
        (
            mention_hidden_state,
            entity_hidden_state,
            sent_hidden_state,
            virtual_hidden_state,
            graph,
        ) = inputs
        
        batch_size, num_mention, _ = mention_hidden_state.shape
        num_entity = int(entity_hidden_state.shape[1])
        num_sent = int(sent_hidden_state.shape[1])
        num_virtual = int(virtual_hidden_state.shape[1])
    
        mention_type_embedding = self.node_type_embedding(torch.tensor(0).to(self.device)).view(1, 1, -1)
        entity_type_embedding = self.node_type_embedding(torch.tensor(1).to(self.device)).view(1, 1, -1)
        sent_type_embedding = self.node_type_embedding(torch.tensor(2).to(self.device)).view(1, 1, -1)
        virtual_type_embedding = self.node_type_embedding(torch.tensor(3).to(self.device)).view(1, 1, -1)
        
        mention_type_embedding = torch.broadcast_to(mention_type_embedding, (batch_size, num_mention, -1))
        entity_type_embedding = torch.broadcast_to(entity_type_embedding, (batch_size, num_entity, -1))
        sent_type_embedding = torch.broadcast_to(sent_type_embedding, (batch_size, num_sent, -1))
        virtual_type_embedding = torch.broadcast_to(virtual_type_embedding, (batch_size, num_virtual, -1))
        
        mention_hidden_state = torch.concat((mention_hidden_state, mention_type_embedding), dim=2)
        entity_hidden_state = torch.concat((entity_hidden_state, entity_type_embedding), dim=2)
        sent_hidden_state = torch.concat((sent_hidden_state, sent_type_embedding), dim=2)
        virtual_hidden_state = torch.concat((virtual_hidden_state, virtual_type_embedding), dim=2)
        
        node_hidden_state = torch.concat((mention_hidden_state, entity_hidden_state, sent_hidden_state, virtual_hidden_state), dim=1)
        # node_hidden_state = self.layer_norm(node_hidden_state)  # Try out

        num_node = int(node_hidden_state.shape[1])
        node_hidden_state = torch.reshape(node_hidden_state, (batch_size * num_node, -1))

        output_node_hidden_state = self.gcn(graph, node_hidden_state)

        output_node_hidden_state = torch.reshape(output_node_hidden_state, (batch_size, num_node, -1))
        entity_hidden_state = output_node_hidden_state[:, num_mention:num_mention + num_entity]
        output_node_hidden_state = torch.reshape(output_node_hidden_state, (batch_size * num_node, -1))
        return entity_hidden_state, output_node_hidden_state