from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from core.models import Contract

# ============================
# CONTRACT CLASSIFICATION LIST
# ============================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def contract_classify_list(request):
    contracts = Contract.objects.filter(user=request.user)

    data = []
    for c in contracts:
        data.append({
            "id": str(c.id),
            "file_name": c.original_filename,  # ✅ Fixed: was "name"
            "primary_class": c.contract_type or "Unclassified",  # ✅ Fixed: was "type"
            "confidence": c.confidence_score or 0
        })

    return Response(data)


# ============================
# CLASSIFY SINGLE CONTRACT
# ============================

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def classify_contract_view(request, contract_id):
    try:
        contract = Contract.objects.get(id=contract_id, user=request.user)

        # Check if contract has text
        if not contract.full_text or len(contract.full_text.strip()) < 50:
            return Response({
                "error": "Contract text is too short or missing",
                "contractType": "Error",
                "confidenceScore": 0
            }, status=400)

        # Use fast pattern-based classification with confidence scoring
        contract_type, confidence = _enhanced_classify(contract.full_text)

        contract.contract_type = contract_type
        contract.confidence_score = confidence
        contract.save()

        return Response({
            "contractType": contract_type,
            "confidenceScore": confidence,
            "classifier": "Pattern-Based (Fast)",
            "topics": [],
            "intents": {},
            "fusedScores": {},
            "explanation": f"Classified using fast pattern-based classifier"
        })

    except Contract.DoesNotExist:
        return Response({
            "error": "Contract not found",
            "contractType": "Error",
            "confidenceScore": 0
        }, status=404)

    except Exception as e:
        import traceback
        return Response({
            "error": str(e),
            "contractType": "Error",
            "confidenceScore": 0,
            "traceback": traceback.format_exc()
        }, status=500)


def _enhanced_classify(text):
    """Enhanced keyword-based classification with confidence scoring"""
    text_lower = text.lower()

    # Define contract types with weighted keywords
    contract_patterns = {
        'Master Service Agreement': {
            'primary': ['master service agreement', 'msa'],
            'secondary': ['statement of work', 'sow', 'deliverables', 'service provider'],
            'weight': 1.0
        },
        'Employment Agreement': {
            'primary': ['employment agreement', 'employment contract'],
            'secondary': ['employee', 'employer', 'salary', 'termination of employment', 'benefits'],
            'weight': 0.9
        },
        'Non-Disclosure Agreement (NDA)': {
            'primary': ['non-disclosure agreement', 'nda', 'confidentiality agreement'],
            'secondary': ['confidential information', 'proprietary information', 'trade secret'],
            'weight': 0.95
        },
        'Service Agreement': {
            'primary': ['service agreement', 'services agreement'],
            'secondary': ['services', 'service provider', 'deliverables', 'scope of work'],
            'weight': 0.85
        },
        'Vendor Agreement': {
            'primary': ['vendor agreement', 'purchase agreement'],
            'secondary': ['vendor', 'purchase', 'goods', 'supply', 'supplier'],
            'weight': 0.8
        },
        'Lease Agreement': {
            'primary': ['lease agreement', 'rental agreement'],
            'secondary': ['lease', 'tenant', 'landlord', 'rent', 'premises'],
            'weight': 0.9
        },
        'License Agreement': {
            'primary': ['license agreement', 'licensing agreement'],
            'secondary': ['license', 'intellectual property', 'software license', 'trademark'],
            'weight': 0.85
        }
    }

    # Score each contract type
    scores = {}
    for contract_type, patterns in contract_patterns.items():
        score = 0

        # Check primary keywords (high weight)
        for keyword in patterns['primary']:
            if keyword in text_lower:
                score += 50 * patterns['weight']
                break

        # Check secondary keywords (lower weight)
        secondary_matches = sum(1 for keyword in patterns['secondary'] if keyword in text_lower)
        score += (secondary_matches * 10) * patterns['weight']

        scores[contract_type] = min(score, 100)  # Cap at 100%

    # Find best match
    if scores:
        best_type = max(scores, key=scores.get)
        confidence = scores[best_type]

        if confidence >= 30:
            return best_type, round(confidence, 2)

    # Default to General Contract
    return 'General Contract', 50.0


# ============================
# CONTRACT CLUSTERS (BERTOPIC VISUALIZATION)
# ============================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def contract_clusters_view(request):
    """
    Generate BERTopic visualization HTML for all user's contracts
    """
    contracts = Contract.objects.filter(
        user=request.user,
        contract_type__isnull=False,
        full_text__isnull=False
    ).exclude(contract_type="Unclassified").exclude(contract_type="Outlier / Unknown")

    classified_count = contracts.count()

    if classified_count < 3:
        return Response({
            "html": "",
            "message": f"Need at least 3 classified contracts to generate visualization (currently have {classified_count})",
            "classified_count": classified_count
        })

    # ✅ Extract contract texts for BERTopic
    contract_texts = []
    contract_labels = []

    for c in contracts:
        if c.full_text and len(c.full_text.strip()) > 100:
            contract_texts.append(c.full_text)
            contract_labels.append(f"{c.original_filename} ({c.contract_type})")

    if len(contract_texts) < 3:
        return Response({
            "html": "",
            "message": f"Not enough contracts with sufficient text (need 3, have {len(contract_texts)})",
            "text_count": len(contract_texts)
        })

    try:
        # ✅ ENHANCED SYSTEMATIC CLUSTERING BY CONTRACT TYPE
        import plotly.graph_objects as go
        import math

        # Group contracts by type and calculate statistics
        type_groups = {}
        for c in contracts:
            ct = c.contract_type or "Unclassified"
            if ct not in type_groups:
                type_groups[ct] = {
                    'contracts': [],
                    'avg_confidence': 0,
                    'count': 0
                }
            type_groups[ct]['contracts'].append({
                "id": str(c.id),
                "filename": c.original_filename,
                "confidence": c.confidence_score or 0
            })
            type_groups[ct]['count'] += 1

        # Calculate average confidence for each type
        for ct, data in type_groups.items():
            if data['count'] > 0:
                data['avg_confidence'] = sum(c['confidence'] for c in data['contracts']) / data['count']

        # Sort types by count (largest first) for better visualization
        sorted_types = sorted(type_groups.items(), key=lambda x: x[1]['count'], reverse=True)

        # Generate visualization data with systematic positioning
        contract_data = []
        colors = ['#636EFA', '#EF553B', '#00CC96', '#AB63FA', '#FFA15A', '#19D3F3', '#FF6692', '#B6E880', '#FECB52', '#FF97FF']

        fig = go.Figure()

        # Calculate grid layout for cluster centers
        num_types = len(sorted_types)
        grid_cols = math.ceil(math.sqrt(num_types))
        grid_spacing = 5

        for idx, (contract_type, data) in enumerate(sorted_types):
            # Calculate grid position for this cluster center
            grid_row = idx // grid_cols
            grid_col = idx % grid_cols

            center_x = grid_col * grid_spacing
            center_y = grid_row * grid_spacing

            x_coords = []
            y_coords = []
            names = []
            confidences = []
            marker_sizes = []

            items = data['contracts']
            count = len(items)

            # Arrange contracts in circular pattern around center
            for i, item in enumerate(items):
                if count == 1:
                    # Single contract at center
                    x = center_x
                    y = center_y
                else:
                    # Multiple contracts in circular arrangement
                    angle = (2 * math.pi * i) / count
                    # Radius based on confidence (higher confidence closer to center)
                    radius = 1.5 - (item['confidence'] / 100) * 0.5
                    x = center_x + radius * math.cos(angle)
                    y = center_y + radius * math.sin(angle)

                x_coords.append(x)
                y_coords.append(y)

                # Truncate filename for display
                display_name = item['filename'][:20] + "..." if len(item['filename']) > 20 else item['filename']
                names.append(display_name if count <= 5 else "")  # Only show names if 5 or fewer contracts
                confidences.append(item['confidence'])

                # Marker size based on confidence
                marker_size = 12 + (item['confidence'] / 10)
                marker_sizes.append(marker_size)

                contract_data.append({
                    "filename": item['filename'],
                    "topic_name": contract_type,
                    "confidence": item['confidence'],
                    "x": x,
                    "y": y
                })

            # Add scatter trace for this contract type
            fig.add_trace(go.Scatter(
                x=x_coords,
                y=y_coords,
                mode='markers+text' if count <= 5 else 'markers',
                name=f"{contract_type} ({count})",
                text=names,
                textposition="top center",
                textfont=dict(size=9, color='white'),
                marker=dict(
                    size=marker_sizes,
                    color=colors[idx % len(colors)],
                    line=dict(width=2, color='rgba(255, 255, 255, 0.6)'),
                    opacity=0.8
                ),
                hovertemplate='<b>%{customdata[0]}</b><br>' +
                             f'Type: {contract_type}<br>' +
                             'Confidence: %{customdata[1]:.1f}%<br>' +
                             '<extra></extra>',
                customdata=[[item['filename'], item['confidence']] for item in items]
            ))

            # Add cluster label annotation
            fig.add_annotation(
                x=center_x,
                y=center_y - 2,
                text=f"<b>{contract_type}</b><br>{count} contract{'s' if count != 1 else ''}<br>Avg: {data['avg_confidence']:.1f}%",
                showarrow=False,
                font=dict(size=10, color=colors[idx % len(colors)]),
                bgcolor='rgba(0, 0, 0, 0.6)',
                bordercolor=colors[idx % len(colors)],
                borderwidth=1,
                borderpad=4,
                opacity=0.9
            )

        fig.update_layout(
            title=dict(
                text="<b>Contract Classification Clusters</b><br><sub>Organized by Type with Confidence-Based Positioning</sub>",
                font=dict(size=20)
            ),
            xaxis=dict(
                title="",
                showgrid=True,
                gridcolor='rgba(128, 128, 128, 0.1)',
                showticklabels=False,
                zeroline=False
            ),
            yaxis=dict(
                title="",
                showgrid=True,
                gridcolor='rgba(128, 128, 128, 0.1)',
                showticklabels=False,
                zeroline=False
            ),
            height=700,
            template="plotly_dark",
            showlegend=True,
            legend=dict(
                title="<b>Contract Types</b>",
                orientation="v",
                yanchor="top",
                y=1,
                xanchor="left",
                x=1.02,
                bgcolor='rgba(0, 0, 0, 0.5)',
                bordercolor='rgba(128, 128, 128, 0.3)',
                borderwidth=1
            ),
            hovermode='closest',
            plot_bgcolor='rgba(17, 24, 39, 1)',
            paper_bgcolor='rgba(17, 24, 39, 1)'
        )

        html = fig.to_html(include_plotlyjs='cdn', full_html=False)

        return Response({
            "html": html,
            "contract_count": len(contract_texts),
            "unique_topics": len(type_groups),
            "contracts": contract_data
        })

    except Exception as e:
        import traceback
        return Response({
            "html": "",
            "error": str(e),
            "traceback": traceback.format_exc(),
            "message": "Failed to generate visualization. Try classifying more contracts."
        })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def portfolio_risk_map(request):
    """
    Lightweight 2D portfolio map using confidence vs classification
    (NO embeddings required)
    """

    contracts = Contract.objects.filter(user=request.user)

    points = []
    for c in contracts:
        points.append({
            "id": str(c.id),
            "x": c.confidence_score or 0,
            "y": 1 if c.contract_type else 0,
            "label": c.contract_type or "Unclassified",
            "name": c.original_filename
        })

    return Response(points)
