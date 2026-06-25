"""
Embedding-model selector endpoint.
GET  /api/embedding-model/  – returns current model + all available options
PUT  /api/embedding-model/  – switches the active model  { "model_key": "bert-large-uncased" }

Any authenticated user can read or switch.
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings

from api.embedding_service import EmbeddingService


@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def embedding_model_view(request):
    options = settings.EMBEDDING_MODEL_OPTIONS
    service = EmbeddingService()

    if request.method == 'GET':
        # Kick off lazy load so current_key is populated
        service._ensure_loaded()

        models_list = []
        for key, cfg in options.items():
            models_list.append({
                'key': key,
                'label': cfg['label'],
                'description': cfg['description'],
                'dimensions': cfg['dimensions'],
                'is_active': key == service.current_key,
            })

        return Response({
            'current_model': service.current_key,
            'dimensions': service.dimensions,
            'models': models_list,
        })

    # --- PUT ---
    model_key = request.data.get('model_key')
    if not model_key:
        return Response({'error': 'model_key is required'}, status=status.HTTP_400_BAD_REQUEST)

    if model_key not in options:
        return Response(
            {'error': f"Invalid model_key. Choose from: {list(options.keys())}"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if model_key == service.current_key:
        return Response({'message': 'Already using this model', 'current_model': model_key})

    try:
        # Switch model (persists to database via SystemSettings)
        EmbeddingService.switch_model(model_key)
        logger.info(f"Switched embedding model to: {model_key}")
    except Exception as e:
        logger.error(f"Error switching embedding model: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    cfg = options[model_key]
    return Response({
        'message': f'Switched to {cfg["label"]} (persisted to database)',
        'current_model': model_key,
        'dimensions': cfg['dimensions'],
    })
