"""
Graph Neural Network for Arbitration Dispute Prediction
========================================================
Uses PyTorch Geometric to build a GNN that predicts arbitration outcomes
based on contract clause graph structure and risk features.

Model: Graph Convolutional Network (GCN) + Multi-Head Attention (GAT)
Input: Clause graph with 8-dimensional risk vectors
Output: Dispute probability + outcome distribution

Training Data: Historical arbitration cases with outcomes
"""

import logging
import os
import pickle
from typing import List, Dict, Optional, Tuple
import numpy as np

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    from torch_geometric.data import Data, Dataset
    from torch_geometric.nn import GCNConv, GATConv, global_mean_pool
    _TORCH_GEO_AVAILABLE = True
except ImportError:
    _TORCH_GEO_AVAILABLE = False
    # Create dummy classes for type hints
    class Data: pass
    class Dataset: pass
    class nn:
        class Module: pass

# Dummy ArbitrationGNN for when PyTorch Geometric is not available
# (overridden below if _TORCH_GEO_AVAILABLE is True)
class ArbitrationGNN:
    pass

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════
# 1. GNN ARCHITECTURE
# ═══════════════════════════════════════════════════════════

if _TORCH_GEO_AVAILABLE:
    class ArbitrationGNN(nn.Module):
        """
        Graph Neural Network for arbitration dispute prediction.

        Architecture:
        - 2× GCN layers (graph convolution)
        - 1× GAT layer (multi-head attention)
        - Global pooling (graph-level representation)
        - 2× FC layers (classification head)

        Input: Node features (8-dim risk vector)
        Output: [dispute_prob, buyer_win, supplier_win, partial, settlement]
        """

        def __init__(
            self,
            input_dim: int = 8,
            hidden_dim: int = 64,
            output_dim: int = 5,
            num_heads: int = 4,
            dropout: float = 0.3,
        ):
            super().__init__()

            self.input_dim = input_dim
            self.hidden_dim = hidden_dim
            self.output_dim = output_dim

            # GCN layers
            self.conv1 = GCNConv(input_dim, hidden_dim)
            self.conv2 = GCNConv(hidden_dim, hidden_dim)

            # Multi-head attention layer
            self.gat = GATConv(
                hidden_dim,
                hidden_dim // num_heads,
                heads=num_heads,
                concat=True,
                dropout=dropout,
            )

            # Classification head
            self.fc1 = nn.Linear(hidden_dim, hidden_dim // 2)
            self.fc2 = nn.Linear(hidden_dim // 2, output_dim)

            self.dropout = nn.Dropout(dropout)
            self.batch_norm1 = nn.BatchNorm1d(hidden_dim)
            self.batch_norm2 = nn.BatchNorm1d(hidden_dim)

        def forward(self, data: Data) -> torch.Tensor:
            """
            Forward pass.

            Args:
                data: PyG Data object with x (node features) and edge_index

            Returns:
                Tensor of shape (batch_size, 5) with [dispute_prob, buyer, supplier, partial, settlement]
            """
            x, edge_index, batch = data.x, data.edge_index, data.batch

            # GCN layer 1
            x = self.conv1(x, edge_index)
            x = self.batch_norm1(x)
            x = F.relu(x)
            x = self.dropout(x)

            # GCN layer 2
            x = self.conv2(x, edge_index)
            x = self.batch_norm2(x)
            x = F.relu(x)
            x = self.dropout(x)

            # Multi-head attention
            x = self.gat(x, edge_index)
            x = F.elu(x)

            # Global pooling (graph-level)
            x = global_mean_pool(x, batch)

            # Classification head
            x = self.fc1(x)
            x = F.relu(x)
            x = self.dropout(x)

            x = self.fc2(x)

            # Sigmoid for dispute probability (first output)
            # Softmax for outcome distribution (last 4 outputs)
            dispute_prob = torch.sigmoid(x[:, 0:1])
            outcomes = F.softmax(x[:, 1:], dim=1)

            return torch.cat([dispute_prob, outcomes], dim=1)


# ═══════════════════════════════════════════════════════════
# 2. DATASET CLASS
# ═══════════════════════════════════════════════════════════

if _TORCH_GEO_AVAILABLE:
    class ArbitrationGraphDataset(Dataset):
        """
        PyTorch Geometric Dataset for arbitration graphs.
        Loads historical cases and converts to graph format.
        """

        def __init__(
            self,
            historical_cases: List[Dict],
            transform=None,
            pre_transform=None,
        ):
            super().__init__(None, transform, pre_transform)
            self.cases = historical_cases

        def len(self) -> int:
            return len(self.cases)

        def get(self, idx: int) -> Data:
            """
            Convert a historical case to PyG Data object.

            Returns:
                Data with:
                - x: Node features (N × 8) - risk scores
                - edge_index: Graph connectivity (2 × E)
                - y: Target labels (5,) - [has_dispute, buyer, supplier, partial, settlement]
            """
            case = self.cases[idx]

            # Extract graph features (stored as JSON during case creation)
            graph_features = case.get("graph_features", {})
            node_features = graph_features.get("node_features", [[0.5] * 8])  # N × 8
            edges = graph_features.get("edges", [[0, 1]])  # E × 2

            # Convert to tensors
            x = torch.tensor(node_features, dtype=torch.float)

            # Edge index format: (2, E) - [source_nodes, target_nodes]
            edge_index = torch.tensor(edges, dtype=torch.long).t().contiguous()

            # Labels
            outcome = case.get("outcome", "SETTLEMENT")
            has_dispute = 1.0 if outcome != "DISMISSED" else 0.0
            buyer_win = 1.0 if outcome == "BUYER_WIN" else 0.0
            supplier_win = 1.0 if outcome == "SUPPLIER_WIN" else 0.0
            partial = 1.0 if outcome == "PARTIAL_AWARD" else 0.0
            settlement = 1.0 if outcome == "SETTLEMENT" else 0.0

            y = torch.tensor(
                [has_dispute, buyer_win, supplier_win, partial, settlement],
                dtype=torch.float,
            )

            return Data(x=x, edge_index=edge_index, y=y)


# ═══════════════════════════════════════════════════════════
# 3. TRAINING SERVICE
# ═══════════════════════════════════════════════════════════

class GNNTrainingService:
    """
    Service for training and managing the arbitration GNN model.
    """

    def __init__(self, model_dir: str = "models/arbitration_gnn"):
        self.model_dir = model_dir
        os.makedirs(model_dir, exist_ok=True)

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model: Optional[ArbitrationGNN] = None
        self.optimizer = None

        logger.info(f"GNN Training Service initialized on device: {self.device}")

    def create_model(
        self,
        input_dim: int = 8,
        hidden_dim: int = 64,
        output_dim: int = 5,
        learning_rate: float = 0.001,
    ) -> ArbitrationGNN:
        """
        Create and initialize a new GNN model.

        Args:
            input_dim: Input feature dimensionality (8 risk scores)
            hidden_dim: Hidden layer size
            output_dim: Output dimension (5: dispute + 4 outcomes)
            learning_rate: Learning rate

        Returns:
            Initialized model
        """
        if not _TORCH_GEO_AVAILABLE:
            raise RuntimeError("PyTorch Geometric not available")

        self.model = ArbitrationGNN(
            input_dim=input_dim,
            hidden_dim=hidden_dim,
            output_dim=output_dim,
        )
        self.model.to(self.device)

        self.optimizer = torch.optim.Adam(self.model.parameters(), lr=learning_rate)

        logger.info(f"Created GNN model with {sum(p.numel() for p in self.model.parameters())} parameters")

        return self.model

    def train_epoch(
        self, train_loader, criterion_dispute, criterion_outcome
    ) -> Tuple[float, float]:
        """
        Train model for one epoch.

        Args:
            train_loader: PyG DataLoader
            criterion_dispute: Loss function for dispute prediction (BCE)
            criterion_outcome: Loss function for outcome prediction (CrossEntropy)

        Returns:
            (avg_loss, accuracy)
        """
        if not self.model:
            raise RuntimeError("Model not created")

        self.model.train()
        total_loss = 0
        correct = 0
        total = 0

        for data in train_loader:
            data = data.to(self.device)

            self.optimizer.zero_grad()

            # Forward pass
            out = self.model(data)

            # Split outputs
            dispute_pred = out[:, 0]
            outcome_pred = out[:, 1:]

            # Split targets
            dispute_target = data.y[:, 0]
            outcome_target = data.y[:, 1:]

            # Compute losses
            loss_dispute = criterion_dispute(dispute_pred, dispute_target)
            loss_outcome = criterion_outcome(outcome_pred, outcome_target)

            loss = loss_dispute + loss_outcome

            # Backward pass
            loss.backward()
            self.optimizer.step()

            total_loss += loss.item()

            # Accuracy (for dispute prediction)
            predicted = (dispute_pred > 0.5).float()
            correct += (predicted == dispute_target).sum().item()
            total += dispute_target.size(0)

        avg_loss = total_loss / len(train_loader)
        accuracy = correct / total if total > 0 else 0

        return avg_loss, accuracy

    def evaluate(self, test_loader, criterion_dispute, criterion_outcome) -> Dict:
        """
        Evaluate model on test set.

        Args:
            test_loader: PyG DataLoader
            criterion_dispute: BCE loss
            criterion_outcome: CrossEntropy loss

        Returns:
            Dict with metrics
        """
        if not self.model:
            raise RuntimeError("Model not created")

        self.model.eval()
        total_loss = 0
        correct = 0
        total = 0

        with torch.no_grad():
            for data in test_loader:
                data = data.to(self.device)

                out = self.model(data)
                dispute_pred = out[:, 0]
                outcome_pred = out[:, 1:]

                dispute_target = data.y[:, 0]
                outcome_target = data.y[:, 1:]

                loss_dispute = criterion_dispute(dispute_pred, dispute_target)
                loss_outcome = criterion_outcome(outcome_pred, outcome_target)
                loss = loss_dispute + loss_outcome

                total_loss += loss.item()

                predicted = (dispute_pred > 0.5).float()
                correct += (predicted == dispute_target).sum().item()
                total += dispute_target.size(0)

        return {
            "test_loss": total_loss / len(test_loader),
            "test_accuracy": correct / total if total > 0 else 0,
        }

    def save_model(self, checkpoint_name: str = "best_model.pt"):
        """
        Save model weights and optimizer state.

        Args:
            checkpoint_name: Filename for checkpoint
        """
        if not self.model:
            raise RuntimeError("Model not created")

        checkpoint_path = os.path.join(self.model_dir, checkpoint_name)

        torch.save({
            "model_state_dict": self.model.state_dict(),
            "optimizer_state_dict": self.optimizer.state_dict(),
            "model_config": {
                "input_dim": self.model.input_dim,
                "hidden_dim": self.model.hidden_dim,
                "output_dim": self.model.output_dim,
            },
        }, checkpoint_path)

        logger.info(f"Model saved to {checkpoint_path}")

    def load_model(self, checkpoint_name: str = "best_model.pt"):
        """
        Load model weights from checkpoint.

        Args:
            checkpoint_name: Filename for checkpoint

        Returns:
            Loaded model
        """
        checkpoint_path = os.path.join(self.model_dir, checkpoint_name)

        if not os.path.exists(checkpoint_path):
            logger.warning(f"Checkpoint not found: {checkpoint_path}")
            return None

        checkpoint = torch.load(checkpoint_path, map_location=self.device)

        # Recreate model with saved config
        config = checkpoint["model_config"]
        self.model = ArbitrationGNN(**config)
        self.model.load_state_dict(checkpoint["model_state_dict"])
        self.model.to(self.device)
        self.model.eval()

        logger.info(f"Model loaded from {checkpoint_path}")

        return self.model


# ═══════════════════════════════════════════════════════════
# 4. INFERENCE SERVICE
# ═══════════════════════════════════════════════════════════

class GNNInferenceService:
    """
    Service for making predictions with trained GNN model.
    """

    def __init__(self, model_path: str = "models/arbitration_gnn/best_model.pt"):
        self.model_path = model_path
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model: Optional[ArbitrationGNN] = None

        # Auto-load model if exists
        self._load_model()

    def _load_model(self):
        """Load model from disk."""
        if not _TORCH_GEO_AVAILABLE:
            logger.warning("PyTorch Geometric not available. GNN predictions disabled.")
            return

        if os.path.exists(self.model_path):
            try:
                checkpoint = torch.load(self.model_path, map_location=self.device)
                config = checkpoint["model_config"]
                self.model = ArbitrationGNN(**config)
                self.model.load_state_dict(checkpoint["model_state_dict"])
                self.model.to(self.device)
                self.model.eval()
                logger.info(f"GNN model loaded from {self.model_path}")
            except Exception as e:
                logger.error(f"Failed to load GNN model: {e}")
                self.model = None
        else:
            logger.info("No trained GNN model found. Predictions will use heuristics.")

    def is_available(self) -> bool:
        """Check if GNN model is loaded."""
        return self.model is not None

    def predict(
        self,
        node_features: List[List[float]],
        edges: List[List[int]],
    ) -> Dict:
        """
        Predict arbitration outcome for a contract graph.

        Args:
            node_features: List of 8-dim risk vectors (N × 8)
            edges: List of [source, target] pairs (E × 2)

        Returns:
            Dict with predictions:
            {
                "dispute_probability": float,
                "buyer_win_probability": float,
                "supplier_win_probability": float,
                "partial_award_probability": float,
                "settlement_probability": float,
                "confidence": float,
            }
        """
        if not self.is_available():
            # Fallback to heuristic if model not available
            return self._heuristic_prediction(node_features)

        try:
            # Convert to PyG Data
            x = torch.tensor(node_features, dtype=torch.float).to(self.device)
            edge_index = torch.tensor(edges, dtype=torch.long).t().contiguous().to(self.device)

            batch = torch.zeros(x.size(0), dtype=torch.long).to(self.device)

            data = Data(x=x, edge_index=edge_index, batch=batch)

            # Predict
            with torch.no_grad():
                out = self.model(data)

            # Extract predictions
            pred = out.cpu().numpy()[0]

            return {
                "dispute_probability": round(float(pred[0]), 4),
                "buyer_win_probability": round(float(pred[1]), 4),
                "supplier_win_probability": round(float(pred[2]), 4),
                "partial_award_probability": round(float(pred[3]), 4),
                "settlement_probability": round(float(pred[4]), 4),
                "confidence": round(float(np.max(pred[1:])), 4),  # Confidence = highest outcome prob
            }

        except Exception as e:
            logger.error(f"GNN prediction failed: {e}")
            return self._heuristic_prediction(node_features)

    def _heuristic_prediction(self, node_features: List[List[float]]) -> Dict:
        """
        Fallback heuristic prediction when GNN model is unavailable.
        Uses average risk scores as proxy.
        """
        if not node_features:
            return {
                "dispute_probability": 0.50,
                "buyer_win_probability": 0.25,
                "supplier_win_probability": 0.25,
                "partial_award_probability": 0.25,
                "settlement_probability": 0.25,
                "confidence": 0.30,
            }

        # Average composite risk
        avg_risk = np.mean([np.mean(features) for features in node_features])

        # Simple heuristic: higher risk → higher dispute probability
        dispute_prob = min(0.40 + avg_risk * 0.50, 0.90)

        return {
            "dispute_probability": round(float(dispute_prob), 4),
            "buyer_win_probability": 0.30,
            "supplier_win_probability": 0.20,
            "partial_award_probability": 0.25,
            "settlement_probability": 0.25,
            "confidence": 0.35,  # Low confidence for heuristic
        }


# Global singleton
_gnn_inference = None


def get_gnn_inference_service() -> GNNInferenceService:
    """Get or create the global GNN inference service."""
    global _gnn_inference
    if _gnn_inference is None:
        _gnn_inference = GNNInferenceService()
    return _gnn_inference
