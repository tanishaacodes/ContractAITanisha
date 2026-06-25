from bertopic import BERTopic
from sentence_transformers import SentenceTransformer
import os
import sys
import django

# ============================
# DJANGO BOOTSTRAP
# ============================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "contractai.settings")
django.setup()

# ============================
# LOAD CONTRACT DATA
# ============================
from core.models import Contract

docs = list(
    Contract.objects
    .exclude(full_text="")
    .values_list("full_text", flat=True)
)

print(f"📄 Training on {len(docs)} contracts")

if len(docs) < 5:
    raise RuntimeError("❌ Need at least 5 contracts to train BERTopic")

# ============================
# TRAIN MODEL
# ============================
embedding_model = SentenceTransformer("all-MiniLM-L6-v2", device='cpu')

topic_model = BERTopic(
    embedding_model=embedding_model,
    min_topic_size=5,
    calculate_probabilities=True
)

topic_model.fit(docs)

# ============================
# SAVE MODEL
# ============================
os.makedirs("models", exist_ok=True)
topic_model.save("models/bertopic_contracts")

print("✅ BERTopic model trained and saved successfully")
