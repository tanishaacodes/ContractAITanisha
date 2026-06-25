"""
Initialize BERTopic Model for Contract Classification
======================================================
Run this script to train the BERTopic model on your existing contracts.
Requires at least 5 contracts with extracted text.

Usage:
    python initialize_bertopic.py
"""

import os
import sys
import django

# Fix encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Django setup
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "contractai.settings")
django.setup()

from core.models import Contract
from bertopic import BERTopic
from sentence_transformers import SentenceTransformer

def main():
    print("=" * 60)
    print("BERTopic Model Initialization")
    print("=" * 60)

    # Check existing contracts
    contracts = Contract.objects.exclude(full_text="").exclude(full_text__isnull=True)
    count = contracts.count()

    print(f"\n📊 Found {count} contracts with extracted text")

    if count < 10:
        print("\n⚠️  WARNING: You have fewer than 10 contracts.")
        print("   BERTopic works best with 20+ contracts for accurate clustering.")
        print("   Proceeding with simplified configuration...\n")

    print("⏳ Training BERTopic model (this may take a few minutes)...")

    # Extract texts
    docs = list(contracts.values_list("full_text", flat=True))

    # Initialize embedding model
    print("   Loading sentence transformer...")
    embedding_model = SentenceTransformer("all-mpnet-base-v2", device='cpu')

    # Train BERTopic with configuration based on dataset size
    print("   Training topic model...")

    if count < 15:
        # Small dataset: Use simpler configuration
        from umap import UMAP
        from hdbscan import HDBSCAN
        from sklearn.feature_extraction.text import CountVectorizer

        # Configure for small datasets
        umap_model = UMAP(
            n_neighbors=min(2, count - 1),  # Must be less than n_samples
            n_components=2,  # Reduce dimensions
            min_dist=0.0,
            metric='cosine',
            random_state=42
        )

        hdbscan_model = HDBSCAN(
            min_cluster_size=2,  # Minimum cluster size
            min_samples=1,
            metric='euclidean',
            cluster_selection_method='leaf',
            prediction_data=True
        )

        vectorizer_model = CountVectorizer(
            max_features=100,
            min_df=1,
            max_df=0.9,
            ngram_range=(1, 2),
            stop_words='english'
        )

        topic_model = BERTopic(
            embedding_model=embedding_model,
            umap_model=umap_model,
            hdbscan_model=hdbscan_model,
            vectorizer_model=vectorizer_model,
            calculate_probabilities=False,  # Faster for small datasets
            verbose=False
        )
    else:
        # Standard configuration for larger datasets
        topic_model = BERTopic(
            embedding_model=embedding_model,
            min_topic_size=3,
            calculate_probabilities=True,
            verbose=False
        )

    topic_model.fit(docs)

    # Create models directory
    models_dir = os.path.join(BASE_DIR, "models")
    os.makedirs(models_dir, exist_ok=True)

    # Save model
    model_path = os.path.join(models_dir, "bertopic_contracts")
    topic_model.save(model_path)

    print(f"\n✅ SUCCESS! BERTopic model trained and saved to:")
    print(f"   {model_path}")
    print(f"\n📈 Model Statistics:")
    print(f"   - Training documents: {count}")
    print(f"   - Topics discovered: {len(topic_model.get_topic_info()) - 1}")  # -1 for outlier topic
    print("\n🔄 Please restart your Django server to load the new model.")
    print("=" * 60)

if __name__ == "__main__":
    main()
