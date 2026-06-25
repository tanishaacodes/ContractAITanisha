"""
Dispute Prediction Model Training Pipeline
===========================================
Trains neural network dispute predictor using historical contract data.

Features:
- PyTorch neural network with 3 hidden layers
- MiniLM + Legal-BERT embeddings as input features
- Binary classification: dispute (1) vs no dispute (0)
- Adam optimizer with learning rate scheduling
- Early stopping and model checkpointing
- Training metrics logging

Usage:
    python manage.py shell
    >>> from dispute_predictor.train_dispute_model import train_model
    >>> train_model()
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import numpy as np
from typing import List, Dict, Tuple
import logging
from pathlib import Path
import json
from datetime import datetime

logger = logging.getLogger(__name__)


class DisputeDataset(Dataset):
    """
    PyTorch Dataset for contract dispute prediction.
    Loads contracts with embeddings and dispute labels.
    """

    def __init__(self, embeddings: np.ndarray, labels: np.ndarray):
        """
        Args:
            embeddings: Contract embeddings (N, embedding_dim)
            labels: Dispute labels 0/1 (N,)
        """
        self.embeddings = torch.FloatTensor(embeddings)
        self.labels = torch.FloatTensor(labels)

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        return self.embeddings[idx], self.labels[idx]


class DisputePredictor(nn.Module):
    """
    Neural network for dispute probability prediction.

    Architecture:
        Input (embedding_dim) → 256 → ReLU → Dropout(0.3)
                              → 128 → ReLU → Dropout(0.3)
                              → 64  → ReLU → Dropout(0.2)
                              → 1   → Sigmoid
    """

    def __init__(self, input_dim: int = 768):
        """
        Args:
            input_dim: Embedding dimension (768 for Legal-BERT)
        """
        super().__init__()

        self.model = nn.Sequential(
            # Layer 1
            nn.Linear(input_dim, 256),
            nn.ReLU(),
            nn.Dropout(0.3),

            # Layer 2
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Dropout(0.3),

            # Layer 3
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Dropout(0.2),

            # Output
            nn.Linear(64, 1),
            nn.Sigmoid()
        )

    def forward(self, x):
        return self.model(x)


class EarlyStopping:
    """Early stopping to prevent overfitting."""

    def __init__(self, patience: int = 10, min_delta: float = 0.001):
        self.patience = patience
        self.min_delta = min_delta
        self.counter = 0
        self.best_loss = None
        self.early_stop = False

    def __call__(self, val_loss: float):
        if self.best_loss is None:
            self.best_loss = val_loss
        elif val_loss > self.best_loss - self.min_delta:
            self.counter += 1
            if self.counter >= self.patience:
                self.early_stop = True
        else:
            self.best_loss = val_loss
            self.counter = 0


def load_training_data() -> Tuple[np.ndarray, np.ndarray]:
    """
    Load contract embeddings and dispute labels from database.

    Returns:
        embeddings: (N, 768) array
        labels: (N,) array of 0/1
    """
    from core.models import Contract
    from arbitration.legalbert_service import LegalBERTEmbeddingService

    logger.info("Loading training data from database...")

    # Get contracts with known dispute outcomes
    contracts = Contract.objects.filter(
        dispute_occurred__isnull=False
    ).values_list('contract_text', 'dispute_occurred')

    if len(contracts) == 0:
        logger.warning("No labeled training data found. Using synthetic data.")
        return generate_synthetic_data()

    logger.info(f"Found {len(contracts)} labeled contracts")

    # Generate embeddings
    embedding_service = LegalBERTEmbeddingService()
    embeddings_list = []
    labels_list = []

    for contract_text, dispute_label in contracts:
        try:
            embedding = embedding_service.embed_text(contract_text)
            embeddings_list.append(embedding)
            labels_list.append(1.0 if dispute_label else 0.0)
        except Exception as e:
            logger.warning(f"Failed to embed contract: {e}")
            continue

    embeddings = np.array(embeddings_list)
    labels = np.array(labels_list)

    logger.info(f"Loaded {len(embeddings)} contract embeddings")
    logger.info(f"Dispute rate: {labels.mean():.1%}")

    return embeddings, labels


def generate_synthetic_data(n_samples: int = 1000) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate synthetic training data for testing.

    Args:
        n_samples: Number of samples to generate

    Returns:
        embeddings: (N, 768) random embeddings
        labels: (N,) synthetic labels
    """
    logger.info(f"Generating {n_samples} synthetic samples...")

    embeddings = np.random.randn(n_samples, 768).astype(np.float32)
    # Normalize
    embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)

    # Generate labels with some correlation to embedding features
    scores = embeddings[:, :10].sum(axis=1)
    probabilities = 1 / (1 + np.exp(-scores))
    labels = (probabilities > 0.5).astype(np.float32)

    logger.info(f"Synthetic dispute rate: {labels.mean():.1%}")

    return embeddings, labels


def train_model(
    epochs: int = 100,
    batch_size: int = 32,
    learning_rate: float = 0.001,
    val_split: float = 0.2,
    model_save_path: str = "models/dispute_predictor.pth"
) -> Dict:
    """
    Train dispute prediction model.

    Args:
        epochs: Number of training epochs
        batch_size: Batch size for training
        learning_rate: Initial learning rate
        val_split: Validation data split ratio
        model_save_path: Path to save trained model

    Returns:
        Training history dict with losses and metrics
    """
    logger.info("=" * 60)
    logger.info("DISPUTE PREDICTOR TRAINING PIPELINE")
    logger.info("=" * 60)

    # Load data
    embeddings, labels = load_training_data()

    # Train/val split
    n_val = int(len(embeddings) * val_split)
    indices = np.random.permutation(len(embeddings))

    train_embeddings = embeddings[indices[n_val:]]
    train_labels = labels[indices[n_val:]]
    val_embeddings = embeddings[indices[:n_val]]
    val_labels = labels[indices[:n_val]]

    logger.info(f"Training samples: {len(train_labels)}")
    logger.info(f"Validation samples: {len(val_labels)}")

    # Create datasets
    train_dataset = DisputeDataset(train_embeddings, train_labels)
    val_dataset = DisputeDataset(val_embeddings, val_labels)

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size)

    # Initialize model
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info(f"Using device: {device}")

    model = DisputePredictor(input_dim=embeddings.shape[1]).to(device)
    criterion = nn.BCELoss()
    optimizer = optim.Adam(model.parameters(), lr=learning_rate)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode='min', factor=0.5, patience=5, verbose=True
    )
    early_stopping = EarlyStopping(patience=15)

    # Training history
    history = {
        'train_loss': [],
        'val_loss': [],
        'train_acc': [],
        'val_acc': [],
    }

    best_val_loss = float('inf')

    # Training loop
    logger.info("\nStarting training...")
    for epoch in range(epochs):
        # Training phase
        model.train()
        train_loss = 0.0
        train_correct = 0
        train_total = 0

        for batch_embeddings, batch_labels in train_loader:
            batch_embeddings = batch_embeddings.to(device)
            batch_labels = batch_labels.to(device).unsqueeze(1)

            # Forward pass
            outputs = model(batch_embeddings)
            loss = criterion(outputs, batch_labels)

            # Backward pass
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            # Metrics
            train_loss += loss.item()
            predictions = (outputs > 0.5).float()
            train_correct += (predictions == batch_labels).sum().item()
            train_total += batch_labels.size(0)

        train_loss /= len(train_loader)
        train_acc = train_correct / train_total

        # Validation phase
        model.eval()
        val_loss = 0.0
        val_correct = 0
        val_total = 0

        with torch.no_grad():
            for batch_embeddings, batch_labels in val_loader:
                batch_embeddings = batch_embeddings.to(device)
                batch_labels = batch_labels.to(device).unsqueeze(1)

                outputs = model(batch_embeddings)
                loss = criterion(outputs, batch_labels)

                val_loss += loss.item()
                predictions = (outputs > 0.5).float()
                val_correct += (predictions == batch_labels).sum().item()
                val_total += batch_labels.size(0)

        val_loss /= len(val_loader)
        val_acc = val_correct / val_total

        # Update history
        history['train_loss'].append(train_loss)
        history['val_loss'].append(val_loss)
        history['train_acc'].append(train_acc)
        history['val_acc'].append(val_acc)

        # Learning rate scheduling
        scheduler.step(val_loss)

        # Logging
        if (epoch + 1) % 10 == 0 or epoch == 0:
            logger.info(
                f"Epoch {epoch+1}/{epochs} | "
                f"Train Loss: {train_loss:.4f} | Train Acc: {train_acc:.3f} | "
                f"Val Loss: {val_loss:.4f} | Val Acc: {val_acc:.3f}"
            )

        # Save best model
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            Path(model_save_path).parent.mkdir(parents=True, exist_ok=True)
            torch.save({
                'epoch': epoch,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'train_loss': train_loss,
                'val_loss': val_loss,
                'val_acc': val_acc,
            }, model_save_path)
            logger.info(f"💾 Saved best model (val_loss: {val_loss:.4f})")

        # Early stopping
        early_stopping(val_loss)
        if early_stopping.early_stop:
            logger.info(f"\n⏹️  Early stopping triggered at epoch {epoch+1}")
            break

    # Final results
    logger.info("\n" + "=" * 60)
    logger.info("TRAINING COMPLETE")
    logger.info("=" * 60)
    logger.info(f"Best validation loss: {best_val_loss:.4f}")
    logger.info(f"Final validation accuracy: {history['val_acc'][-1]:.3f}")
    logger.info(f"Model saved to: {model_save_path}")

    # Save training history
    history_path = model_save_path.replace('.pth', '_history.json')
    with open(history_path, 'w') as f:
        json.dump(history, f, indent=2)
    logger.info(f"Training history saved to: {history_path}")

    return history


def load_trained_model(model_path: str = "models/dispute_predictor.pth") -> DisputePredictor:
    """
    Load trained model from checkpoint.

    Args:
        model_path: Path to model checkpoint

    Returns:
        Loaded model in eval mode
    """
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    model = DisputePredictor()
    checkpoint = torch.load(model_path, map_location=device)
    model.load_state_dict(checkpoint['model_state_dict'])
    model.eval()
    model.to(device)

    logger.info(f"✅ Loaded model from {model_path}")
    logger.info(f"   Validation accuracy: {checkpoint.get('val_acc', 'N/A')}")

    return model


def predict_dispute_probability(model: DisputePredictor, embedding: np.ndarray) -> float:
    """
    Predict dispute probability for a contract.

    Args:
        model: Trained DisputePredictor model
        embedding: Contract embedding (768,)

    Returns:
        Dispute probability (0-1)
    """
    device = next(model.parameters()).device

    with torch.no_grad():
        embedding_tensor = torch.FloatTensor(embedding).unsqueeze(0).to(device)
        probability = model(embedding_tensor).item()

    return probability


if __name__ == '__main__':
    # Run training
    history = train_model(
        epochs=100,
        batch_size=32,
        learning_rate=0.001,
        val_split=0.2
    )

    print("\n✅ Training pipeline completed successfully!")
