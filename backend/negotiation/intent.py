"""
Intent Classification for Negotiation
Uses Legal-BERT to detect counterparty negotiation tactics
"""
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import logging

logger = logging.getLogger(__name__)

# Intent taxonomy
INTENTS = [
    'LIABILITY_PUSH',
    'PRICE_PUSH',
    'PAYMENT_DELAY',
    'INDEMNITY_EXPANSION',
    'TERMINATION_FLEX',
    'GOVERNING_LAW',
    'GENERAL'
]

# Lazy loading of model
_tokenizer = None
_model = None


def get_intent_model():
    """Lazy load Legal-BERT model"""
    global _tokenizer, _model
    
    if _tokenizer is None or _model is None:
        try:
            logger.info("Loading Legal-BERT for intent classification...")
            _tokenizer = AutoTokenizer.from_pretrained("nlpaueb/legal-bert-base-uncased")
            # Using base model for now - can fine-tune on negotiation intents later
            _model = AutoModelForSequenceClassification.from_pretrained(
                "nlpaueb/legal-bert-base-uncased",
                num_labels=len(INTENTS, low_cpu_mem_usage=False),
                problem_type="single_label_classification"
            )
            _model.eval()
            logger.info("Legal-BERT loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load Legal-BERT: {e}")
            return None, None
    
    return _tokenizer, _model


def classify_intent(text):
    """
    Classify negotiation intent from text
    
    Args:
        text: Input text to classify
    
    Returns:
        str: Detected intent from INTENTS taxonomy
    """
    # Fallback to keyword matching if model not available
    tokenizer, model = get_intent_model()
    
    if tokenizer is None or model is None:
        return _classify_intent_keywords(text)
    
    try:
        # Tokenize
        inputs = tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=512,
            padding=True
        )
        
        # Predict
        with torch.no_grad():
            outputs = model(**inputs)
            logits = outputs.logits
        
        # Get intent
        predicted_idx = logits.argmax().item()
        intent = INTENTS[predicted_idx]
        confidence = torch.softmax(logits, dim=1)[0][predicted_idx].item()
        
        logger.debug(f"Intent: {intent}, Confidence: {confidence:.2f}")
        
        # If low confidence, fall back to keywords
        if confidence < 0.4:
            return _classify_intent_keywords(text)
        
        return intent
    
    except Exception as e:
        logger.error(f"Intent classification error: {e}")
        return _classify_intent_keywords(text)


def _classify_intent_keywords(text):
    """
    Keyword-based intent classification (fallback)
    """
    text_lower = text.lower()
    
    # Check for specific patterns
    if 'liabilit' in text_lower or 'indemnif' in text_lower:
        if 'indemnif' in text_lower:
            return 'INDEMNITY_EXPANSION'
        return 'LIABILITY_PUSH'
    
    if 'price' in text_lower or 'cost' in text_lower or 'payment' in text_lower:
        if 'payment' in text_lower and ('delay' in text_lower or 'net' in text_lower or 'term' in text_lower):
            return 'PAYMENT_DELAY'
        return 'PRICE_PUSH'
    
    if 'terminat' in text_lower or 'cancel' in text_lower:
        return 'TERMINATION_FLEX'
    
    if 'jurisdiction' in text_lower or 'governing law' in text_lower:
        return 'GOVERNING_LAW'
    
    return 'GENERAL'


def get_intent_description(intent):
    """Get human-readable description of intent"""
    descriptions = {
        'LIABILITY_PUSH': 'Counterparty seeking to expand or remove liability limits',
        'PRICE_PUSH': 'Counterparty negotiating price or cost terms',
        'PAYMENT_DELAY': 'Counterparty seeking extended payment terms',
        'INDEMNITY_EXPANSION': 'Counterparty expanding indemnification scope',
        'TERMINATION_FLEX': 'Counterparty seeking more flexible termination rights',
        'GOVERNING_LAW': 'Counterparty negotiating jurisdiction or governing law',
        'GENERAL': 'General negotiation discussion'
    }
    return descriptions.get(intent, 'Unknown intent')
