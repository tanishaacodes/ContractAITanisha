from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.utils import timezone
from django.core.files.storage import default_storage
from django.conf import settings
import os
import json
from datetime import datetime
import time
import threading
import tempfile
import logging

logger = logging.getLogger(__name__)

from core.models import User, Role, Contract, Clause, ContractRiskAnalysis, ClauseDeviation, ContractObligation, ContractVersion, PricingPlan
from core.serializers import (
    UserSerializer, UserRegistrationSerializer, UserLoginSerializer,
    ContractSerializer, ContractDetailSerializer, ClauseSerializer, RoleSerializer, ContractVersionSerializer
)
from core.authentication import generate_token
from .utils import extract_text_from_file, classify_contract, extract_clauses


@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """Register a new user"""
    try:
        data = request.data
        email = data.get('email')
        password = data.get('password')
        first_name = data.get('firstName', '')
        last_name = data.get('lastName', '')

        if not email or not password:
            return Response(
                {'message': 'Email and password are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if User.objects.filter(email=email).exists():
            return Response(
                {'message': 'User already exists'},
                status=status.HTTP_409_CONFLICT
            )

        try:
            viewer_role = Role.objects.get(name='Viewer')
        except Role.DoesNotExist:
            return Response(
                {'message': 'Default role not found'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Hash password using bcrypt
        import bcrypt
        import uuid
        salt = bcrypt.gensalt(rounds=10)
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
        user_id = str(uuid.uuid4())

        # Create user using raw SQL to avoid ORM db_column mapping issues
        from django.db import connection
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO users (id, email, password, firstName, lastName, roleId, isActive, createdAt, updatedAt)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                """, [user_id, email, hashed_password, first_name, last_name, viewer_role.id, True])

            # Generate token with user data
            token = generate_token_with_data(user_id, email)
        except Exception as e:
            return Response(
                {'message': 'Failed to create user', 'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response({
            'message': 'User registered successfully',
            'token': token,
            'user': {
                'id': user_id,
                'email': email,
                'firstName': first_name,
                'lastName': last_name,
                'role': viewer_role.name,
            }
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response(
            {'message': 'Registration failed', 'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """Login user"""
    try:
        data = request.data
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return Response(
                {'message': 'Email and password are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.select_related('role', 'current_plan').get(email=email)
        except User.DoesNotExist:
            return Response(
                {'message': 'Invalid credentials'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not user.check_password(password):
            return Response(
                {'message': 'Invalid credentials'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not user.is_active:
            return Response(
                {'message': 'User account is inactive'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Update last_login using queryset update to avoid ORM issues with db_column mapping
        User.objects.filter(id=user.id).update(last_login=timezone.now())

        token = generate_token(user)

        # Get user's current plan
        current_plan = None
        if user.current_plan:
            current_plan = {
                'id': str(user.current_plan.id),
                'name': user.current_plan.name,
                'displayName': user.current_plan.display_name,
                'planType': user.current_plan.plan_type,
                'priceMonthly': float(user.current_plan.price_monthly),
                'contractLimit': user.current_plan.contract_limit,
            }

        return Response({
            'message': 'Login successful',
            'token': token,
            'user': {
                'id': str(user.id),
                'email': user.email,
                'firstName': user.first_name,
                'lastName': user.last_name,
                'role': user.role.name,
                'currentPlan': current_plan,
                'totalContractsUploaded': user.total_contracts_uploaded,
                'fivetranAccess': user.fivetran_access,
                'kafkaAccess': user.kafka_access,
                'sapAccess': user.sap_access,
            }
        })

    except Exception as e:
        print(f'Login error: {str(e)}')
        return Response(
            {'message': 'Login failed', 'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_current_user(request):
    """Get current authenticated user"""
    try:
        user = request.user

        # Get user's current plan
        current_plan = None
        if user.current_plan:
            current_plan = {
                'id': str(user.current_plan.id),
                'name': user.current_plan.name,
                'displayName': user.current_plan.display_name,
                'planType': user.current_plan.plan_type,
                'priceMonthly': float(user.current_plan.price_monthly),
                'contractLimit': user.current_plan.contract_limit,
            }

        return Response({
            'user': {
                'id': str(user.id),
                'email': user.email,
                'firstName': user.first_name,
                'lastName': user.last_name,
                'role': user.role.name,
                'isActive': user.is_active,
                'lastLogin': user.last_login,
                'createdAt': user.created_at,
                'currentPlan': current_plan,
                'totalContractsUploaded': user.total_contracts_uploaded,
                'fivetranAccess': user.fivetran_access,
                'kafkaAccess': user.kafka_access,
                'sapAccess': user.sap_access,
            }
        })
    except Exception as e:
        return Response(
            {'message': 'Failed to fetch user', 'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_profile(request):
    """Update user profile (first name and last name)"""
    try:
        user = request.user
        data = request.data

        first_name = data.get('firstName', '').strip()
        last_name = data.get('lastName', '').strip()

        if not first_name or not last_name:
            return Response(
                {'message': 'First name and last name are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update user using raw SQL to match db_column names
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE users
                SET firstName = %s, lastName = %s, updatedAt = NOW()
                WHERE id = %s
            """, [first_name, last_name, str(user.id)])

        # Refresh user object
        user.refresh_from_db()

        return Response({
            'message': 'Profile updated successfully',
            'user': {
                'id': str(user.id),
                'email': user.email,
                'firstName': first_name,
                'lastName': last_name,
                'role': user.role.name,
                'isActive': user.is_active,
                'lastLogin': user.last_login,
                'createdAt': user.created_at,
            }
        })

    except Exception as e:
        print(f'Update profile error: {str(e)}')
        return Response(
            {'message': 'Failed to update profile', 'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# =======================
# PRICING PLANS API
# =======================

@api_view(['GET'])
@permission_classes([AllowAny])
def get_pricing_plans(request):
    """Get all active pricing plans"""
    try:
        plans = PricingPlan.objects.filter(is_active=True).order_by('sort_order')

        plans_data = []
        for plan in plans:
            plans_data.append({
                'id': str(plan.id),
                'name': plan.name,
                'displayName': plan.display_name,
                'planType': plan.plan_type,
                'priceMonthly': float(plan.price_monthly),
                'contractLimit': plan.contract_limit,
                'features': plan.features,
                'featureFlags': plan.feature_flags,
                'description': plan.description,
                'isContactSales': plan.is_contact_sales,
            })

        return Response({
            'plans': plans_data
        })

    except Exception as e:
        return Response(
            {'message': 'Failed to fetch pricing plans', 'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_subscription(request):
    """Get current user's subscription and usage info"""
    try:
        user = request.user

        # Get user's current plan
        current_plan = None
        if user.current_plan:
            current_plan = {
                'id': str(user.current_plan.id),
                'name': user.current_plan.name,
                'displayName': user.current_plan.display_name,
                'planType': user.current_plan.plan_type,
                'priceMonthly': float(user.current_plan.price_monthly),
                'contractLimit': user.current_plan.contract_limit,
                'features': user.current_plan.features,
                'featureFlags': user.current_plan.feature_flags,
            }

        # Get contract usage
        contracts_used = Contract.objects.filter(user=user).count()

        return Response({
            'currentPlan': current_plan,
            'contractsUsed': contracts_used,
            'contractLimit': user.current_plan.contract_limit if user.current_plan else 0,
        })

    except Exception as e:
        return Response(
            {'message': 'Failed to fetch subscription', 'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def select_plan(request):
    """Select a pricing plan for the current user (during registration)"""
    try:
        user = request.user
        plan_id = request.data.get('planId')

        if not plan_id:
            return Response(
                {'message': 'Plan ID is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            plan = PricingPlan.objects.get(id=plan_id)
        except PricingPlan.DoesNotExist:
            return Response(
                {'message': 'Invalid plan ID'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Don't allow selecting "contact sales" plans directly
        if plan.is_contact_sales:
            return Response(
                {'message': 'This plan requires contacting sales'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update user's plan
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE users
                SET currentPlanId = %s, updatedAt = NOW()
                WHERE id = %s
            """, [plan_id, str(user.id)])

        user.refresh_from_db()

        return Response({
            'message': 'Plan selected successfully',
            'plan': {
                'id': str(plan.id),
                'name': plan.name,
                'displayName': plan.display_name,
                'planType': plan.plan_type,
            }
        })

    except Exception as e:
        return Response(
            {'message': 'Failed to select plan', 'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upgrade_plan(request):
    """Upgrade user's pricing plan"""
    try:
        user = request.user
        plan_id = request.data.get('planId')

        if not plan_id:
            return Response(
                {'message': 'Plan ID is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            plan = PricingPlan.objects.get(id=plan_id)
        except PricingPlan.DoesNotExist:
            return Response(
                {'message': 'Invalid plan ID'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Don't allow selecting "contact sales" plans directly
        if plan.is_contact_sales:
            return Response(
                {'message': 'This plan requires contacting sales'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update user's plan
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE users
                SET currentPlanId = %s, updatedAt = NOW()
                WHERE id = %s
            """, [plan_id, str(user.id)])

        user.refresh_from_db()

        return Response({
            'message': 'Plan upgraded successfully',
            'plan': {
                'id': str(plan.id),
                'name': plan.name,
                'displayName': plan.display_name,
                'planType': plan.plan_type,
                'priceMonthly': float(plan.price_monthly),
            }
        })

    except Exception as e:
        return Response(
            {'message': 'Failed to upgrade plan', 'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def create_contract_version_snapshot(contract, user, change_description="Initial version"):
    """
    Create a version snapshot of a contract

    Args:
        contract: Contract instance
        user: User who made the change
        change_description: Description of what changed

    Returns:
        ContractVersion instance
    """
    # Get the next version number
    last_version = ContractVersion.objects.filter(contract=contract).order_by('-version_number').first()
    next_version = (last_version.version_number + 1) if last_version else 1

    # Create version snapshot
    version = ContractVersion.objects.create(
        contract=contract,
        version_number=next_version,
        created_by=user,
        change_description=change_description,
        filename=contract.filename,
        original_filename=contract.original_filename,
        file_type=contract.file_type,
        file_path=contract.file_path,
        full_text=contract.full_text,
        contract_type=contract.contract_type,
        contract_value=contract.contract_value,
        party_name=f"{contract.party_a} | {contract.party_b}",
        contract_duration=contract.contract_duration
    )

    print(f'[VERSION] Created version {next_version} for contract {contract.id}')

    # Auto-trigger drift detection if this is not the first version
    if next_version > 1 and last_version:
        def run_drift_detection():
            """Background task to analyze drift between versions"""
            try:
                from .intent_drift_service import IntentDriftDetectionService

                print(f'[DRIFT] Starting auto-drift detection: v{last_version.version_number} -> v{next_version}')

                drift_service = IntentDriftDetectionService()
                drift_result = drift_service.compare_versions(
                    str(last_version.id),
                    str(version.id)
                )

                drift_score = drift_result.get('overall_drift_score', 0)
                risk_delta = drift_result.get('risk_delta', {}).get('delta', 0)

                print(f'[DRIFT] Auto-analysis complete: Drift={drift_score:.2%}, Risk Δ={risk_delta:+.2%}')

            except Exception as e:
                print(f'[DRIFT] Auto-detection error: {str(e)}')

        # Run drift detection in background thread (non-blocking)
        drift_thread = threading.Thread(target=run_drift_detection, daemon=True)
        drift_thread.start()
        print(f'[DRIFT] Background drift detection initiated for v{last_version.version_number} -> v{next_version}')

    return version


def extract_contract_metadata(contract_text):
    """Enhanced metadata extraction with LLM + Regex fallback"""
    import re
    from datetime import datetime

    metadata = {
        "party_a": None,
        "party_b": None,
        "start_date": None,
        "end_date": None,
        "contract_value": None,
        "contract_type": None,
        "jurisdiction": None,
        "payment_terms": None,
        "liability_level": None,
        "project_location": None,
        "supplier_locations": None,
    }

    # LLM metadata extraction skipped — too slow on CPU (120s+ timeout); regex handles all fields

    # REGEX FALLBACK FOR CRITICAL FIELDS
    text_lower = contract_text.lower()

    # Extract parties using common patterns
    if not metadata["party_a"] or not metadata["party_b"]:
        party_patterns = [
            r"between\s+([A-Z][A-Za-z\s&.,()]+?)\s+(?:and|&)\s+([A-Z][A-Za-z\s&.,()]+?)(?:\s|,|\()",
            r"(?:party|client|customer):\s*([A-Z][A-Za-z\s&.,()]+)",
            r"(?:vendor|supplier|provider):\s*([A-Z][A-Za-z\s&.,()]+)",
        ]

        for pattern in party_patterns:
            match = re.search(pattern, contract_text, re.IGNORECASE)
            if match:
                if len(match.groups()) == 2:
                    metadata["party_a"] = match.group(1).strip()[:100]
                    metadata["party_b"] = match.group(2).strip()[:100]
                    break
                elif not metadata["party_a"]:
                    metadata["party_a"] = match.group(1).strip()[:100]

    # Extract dates
    if not metadata["start_date"] or not metadata["end_date"]:
        date_patterns = [
            r"(?:effective|start|commencement|beginning)\s+(?:date|from)?:?\s*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})",
            r"(?:expiry|end|termination|expiration)\s+(?:date|on)?:?\s*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})",
            r"(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})\s+to\s+(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})",
        ]

        for pattern in date_patterns:
            matches = re.findall(pattern, contract_text, re.IGNORECASE)
            if matches:
                for match in matches:
                    if isinstance(match, tuple):
                        if len(match) == 2:
                            try:
                                metadata["start_date"] = parse_date_flexible(match[0])
                                metadata["end_date"] = parse_date_flexible(match[1])
                                break
                            except:
                                continue
                    else:
                        try:
                            if not metadata["start_date"]:
                                metadata["start_date"] = parse_date_flexible(match)
                            elif not metadata["end_date"]:
                                metadata["end_date"] = parse_date_flexible(match)
                        except:
                            continue
                if metadata["start_date"] and metadata["end_date"]:
                    break

    # Extract contract value with currency
    # Only capture meaningful contract totals (>= $1,000) — not hourly rates or small fees
    if not metadata["contract_value"]:
        currency_patterns = [
            # Explicit "total/contract value/amount/price" labels — highest confidence
            r"(?:total\s+)?(?:contract\s+)?(?:value|amount|sum|price|fee)[\s:]+([₹$€£][\s]?[\d,]+(?:\.\d{2})?)",
            # ISO currency codes followed by large numbers
            r"(?:aed|usd|inr|eur|gbp)[\s]?[\d,]{4,}(?:\.\d{2})?",
            # Currency symbol followed by at least 4 digits (>= $1,000)
            r"([₹$€£][\s]?[\d,]{4,}(?:\.\d{2})?)",
            r"(?:rupees|dollars)[\s]+[\d,]{4,}",
        ]

        for pattern in currency_patterns:
            match = re.search(pattern, contract_text, re.IGNORECASE)
            if match:
                value = match.group(0) if match.lastindex is None else match.group(1)
                # Strip commas/spaces to check numeric magnitude
                num_str = re.sub(r'[^\d.]', '', value)
                try:
                    num_val = float(num_str)
                    if num_val < 1000:
                        continue  # Skip small amounts like $350 hourly rates
                except (ValueError, TypeError):
                    continue
                # Ensure currency symbol is present
                if not any(c in value for c in ['₹', '$', '€', '£', 'AED', 'USD', 'INR']):
                    if 'rupee' in text_lower or 'inr' in text_lower:
                        value = '₹ ' + value
                    elif 'aed' in text_lower or 'dirham' in text_lower:
                        value = 'AED ' + value
                    else:
                        value = '$ ' + value
                metadata["contract_value"] = value.strip()
                break

    # LIABILITY LEVEL FALLBACK (critical for small LLMs)
    # If LLM didn't determine liability or defaulted to LOW, analyze keywords
    if not metadata["liability_level"] or metadata["liability_level"] == "LOW":
        # HIGH liability indicators
        high_risk_keywords = [
            r'unlimited\s+liability',
            r'indemnif(?:y|ication)',
            r'hold\s+harmless',
            r'gross\s+negligence',
            r'consequential\s+damages',
            r'punitive\s+damages',
            r'willful\s+misconduct',
            r'shall\s+defend',
        ]

        # MEDIUM liability indicators
        medium_risk_keywords = [
            r'limited\s+liability',
            r'liability\s+(?:shall\s+)?(?:not\s+)?exceed',
            r'liability\s+cap',
            r'limitation\s+of\s+liability',
            r'material\s+breach',
            r'direct\s+damages',
        ]

        # Check for HIGH risk
        high_risk_found = False
        for pattern in high_risk_keywords:
            if re.search(pattern, contract_text, re.IGNORECASE):
                metadata["liability_level"] = "HIGH"
                high_risk_found = True
                break

        # If not HIGH, check for MEDIUM risk
        if not high_risk_found:
            for pattern in medium_risk_keywords:
                if re.search(pattern, contract_text, re.IGNORECASE):
                    metadata["liability_level"] = "MEDIUM"
                    break

        # If still no match, default to LOW
        if not metadata["liability_level"]:
            metadata["liability_level"] = "LOW"

    print(f"[METADATA EXTRACTED] Parties: {metadata['party_a']} & {metadata['party_b']}, "
          f"Dates: {metadata['start_date']} to {metadata['end_date']}, "
          f"Value: {metadata['contract_value']}, "
          f"Liability: {metadata['liability_level']}")

    return metadata


def parse_date_flexible(date_str):
    """Parse date string in various formats to YYYY-MM-DD"""
    date_str = date_str.strip()
    formats = ['%d/%m/%Y', '%d-%m-%Y', '%d/%m/%y', '%d-%m-%y',
               '%m/%d/%Y', '%m-%d-%Y', '%Y-%m-%d']

    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime('%Y-%m-%d')
        except:
            continue
    return None


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_contract(request):
    """Upload and process contract file"""
    try:
        start_time = time.time()
        timings = {}

        if 'file' not in request.FILES:
            return Response(
                {'message': 'No file provided'},
                status=status.HTTP_400_BAD_REQUEST
            )

        file = request.FILES['file']
        user = request.user

        print(f'UPLOAD request: user={user.id}, originalName={file.name}')

        filename = f"{int(datetime.now().timestamp() * 1000)}-{file.name.replace(' ', '_')}"
        file_path = os.path.join(settings.MEDIA_ROOT, filename)

        ext = os.path.splitext(file.name)[1].lower()
        allowed_extensions = ['.docx', '.pdf', '.png', '.jpg', '.jpeg']

        if ext not in allowed_extensions:
            return Response(
                {'message': 'Unsupported file type. Allowed: DOCX, PDF, PNG, JPG, JPEG'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if file.size > settings.MAX_UPLOAD_SIZE:
            return Response(
                {'message': 'File exceeds 25MB limit'},
                status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
            )

        # Check contract limit based on user's plan (using lifetime uploads, not current count)
        if user.current_plan:
            contract_limit = user.current_plan.contract_limit
            # -1 means unlimited contracts
            if contract_limit != -1:
                # Use total_contracts_uploaded (lifetime count) instead of current count
                # This prevents users from bypassing limits by deleting contracts
                if user.total_contracts_uploaded >= contract_limit:
                    current_contract_count = Contract.objects.filter(user=user).count()
                    return Response({
                        'error': 'CONTRACT_LIMIT_REACHED',
                        'message': f'You have reached your {user.current_plan.display_name} plan limit of {contract_limit} contracts.',
                        'currentCount': current_contract_count,
                        'totalUploaded': user.total_contracts_uploaded,
                        'limit': contract_limit,
                        'planName': user.current_plan.display_name,
                        'suggestion': 'Upgrade your plan to upload more contracts and unlock advanced features.'
                    }, status=status.HTTP_402_PAYMENT_REQUIRED)

        os.makedirs(settings.MEDIA_ROOT, exist_ok=True)

        # TIMING: File save
        save_start = time.time()
        with open(file_path, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)
        timings['file_save'] = round(time.time() - save_start, 2)

        extracted_text = ''
        pages = None
        ocr_performed = False

        print(f'Extracting text from {ext}...')
        # TIMING: Text extraction
        extract_start = time.time()
        result = extract_text_from_file(file_path, ext)
        timings['text_extraction'] = round(time.time() - extract_start, 2)
        extracted_text = result.get('text', '')
        pages = result.get('pages')
        ocr_performed = result.get('ocr_performed', False)

        if not extracted_text or len(extracted_text.strip()) < 5:
            error_message = 'Unable to extract text from file'
            suggestion = 'Provide a higher-quality document'

            # Check if the error is due to OCR issues
            if ext in ['.png', '.jpg', '.jpeg']:
                error_message = 'OCR engine is not available'
                suggestion = 'Image text extraction requires PaddleOCR. Please ensure PaddleOCR is installed or use a PDF/DOCX file instead.'
            elif result.get('error'):
                error_message = 'OCR processing failed'
                suggestion = 'OCR functionality encountered an error. Please ensure PaddleOCR is installed or provide a document with extractable text.'

            return Response({
                'error': error_message,
                'message': error_message,
                'suggestion': suggestion,
                'ocr_attempted': ocr_performed
            }, status=status.HTTP_400_BAD_REQUEST)

        print(f'Extracted text length: {len(extracted_text)}')

        # TIMING: Classification
        classification_start = time.time()
        classification = {'contractType': 'unknown', 'confidenceScore': 0}
        try:
            result = classify_contract(extracted_text, filename=file.name)
            if result:
                classification = result
        except Exception as e:
            print(f'Classification error: {str(e)}')
        timings['classification'] = round(time.time() - classification_start, 2)

         # -------------------------------
        # METADATA EXTRACTION (FINAL)
        # -------------------------------
        # TIMING: Metadata extraction
        metadata_start = time.time()
        metadata = {
            "party_a": None,
            "party_b": None,
            "start_date": None,
            "end_date": None,
            "contract_value": None,
            "contract_type": None,
            "jurisdiction": None,
            "payment_terms": None,
            "liability_level": None,
        }

        extracted_metadata = extract_contract_metadata(extracted_text)
        if extracted_metadata:
            metadata.update(extracted_metadata)
        timings['metadata_extraction'] = round(time.time() - metadata_start, 2)

        party_a = metadata["party_a"]
        party_b = metadata["party_b"]
        start_date = metadata["start_date"]
        end_date = metadata["end_date"]

        # TIMING: Database save
        db_start = time.time()
        contract = Contract.objects.create(
            user=user,
            filename=filename,
            original_filename=file.name,
            file_type=ext.replace('.', '').upper(),
            file_path=file_path,
            full_text=extracted_text,

            contract_type=metadata["contract_type"] or classification.get('contractType'),
            contract_value=metadata["contract_value"],
            confidence_score=classification.get('confidenceScore'),  # ✅ Save confidence score

            party_a=party_a,
            party_b=party_b,

            party_name=(
                f"{party_a} vs {party_b}"
                if party_a and party_b
                else party_a or party_b
            ),

            start_date=start_date,
            end_date=end_date,

            contract_duration=(
                f"{start_date} to {end_date}"
                if start_date and end_date
                else None
            ),

            # New searchable fields
            jurisdiction=metadata["jurisdiction"],
            payment_terms=metadata["payment_terms"],
            liability_level=metadata["liability_level"],
            project_location=metadata["project_location"],
            supplier_locations=metadata["supplier_locations"],

            ocr_performed=ocr_performed
        )


        # Create initial version snapshot
        version = create_contract_version_snapshot(contract, user, "Initial upload")

        # Increment lifetime contract upload counter
        user.total_contracts_uploaded += 1
        user.save(update_fields=['total_contracts_uploaded'])

        timings['database_save'] = round(time.time() - db_start, 2)

        # Total time
        timings['total'] = round(time.time() - start_time, 2)

        # ========== PUBLISH KAFKA EVENT ==========
        try:
            from integrations.kafka.producer import publish_contract_uploaded
            publish_contract_uploaded(
                contract_id=str(contract.id),
                user_id=str(user.id),
                filename=file.name
            )
            print(f"[KAFKA] Published contract.uploaded event for {contract.id}")
        except Exception as e:
            print(f"[KAFKA] Failed to publish event: {str(e)}")
            # Don't fail upload if Kafka is unavailable
        # =========================================

        # ========== AUTO-TRIGGER CLAUSE EXTRACTION & INTENT MINING ==========
        try:
            import threading
            import json

            print(f"[AUTO-MINING] Starting automated analysis for contract {contract.id}...")

            # Run in background to avoid blocking the response
            def run_automated_analysis():
                try:
                    # Step 1: Extract clauses
                    print(f"[AUTO-MINING] Step 1/2: Extracting clauses...")
                    extracted_clauses_data = extract_clauses(contract.full_text)
                    print(f"[AUTO-MINING] Found {len(extracted_clauses_data)} clause templates")

                    # Save clauses to database
                    Clause.objects.filter(contract=contract).delete()
                    saved_count = 0
                    for clause_data in extracted_clauses_data:
                        try:
                            extracted_text = clause_data.get('clauseText', '')
                            if not extracted_text and clause_data.get('contextSentences'):
                                extracted_text = clause_data['contextSentences'][0].get('text', '')

                            Clause.objects.create(
                                contract=contract,
                                clause_name=clause_data.get('clauseName'),
                                found=clause_data.get('found', False),
                                confidence=clause_data.get('confidence'),
                                match_count=clause_data.get('matchCount'),
                                text_spans=json.dumps(clause_data.get('textSpans', [])),
                                context_sentences=json.dumps(clause_data.get('contextSentences', [])),
                                extracted_text=extracted_text
                            )
                            if clause_data.get('found', False):
                                saved_count += 1
                        except Exception as e:
                            print(f"[AUTO-MINING] Error saving clause: {str(e)}")

                    print(f"[AUTO-MINING] Saved {saved_count} found clauses to database")

                    # Step 2: Run intent mining
                    print(f"[AUTO-MINING] Step 2/2: Mining intents and obligations...")
                    from .intent_mining_service import IntentMiningService
                    service = IntentMiningService()
                    result = service.process_contract_clauses(
                        contract_id=str(contract.id),
                        contract_version_id=str(version.id)
                    )

                    if result.get('success'):
                        print(f"[AUTO-MINING] SUCCESS!")
                        print(f"[AUTO-MINING]   - Intents: {result.get('intents_discovered', 0)}")
                        print(f"[AUTO-MINING]   - Obligations: {result.get('obligations_extracted', 0)}")
                        print(f"[AUTO-MINING]   - Rights: {result.get('rights_extracted', 0)}")
                    else:
                        print(f"[AUTO-MINING] FAILED: {result.get('error')}")

                    # ========== BUILD GRAPH INTELLIGENCE ==========
                    print(f"[GRAPH] Building NetworkX and Neo4j graphs...")
                    try:
                        from api.services.graph_orchestrator import build_all_graphs
                        from core.models import ContractGraphMeta

                        # Get all found clauses for this contract
                        clauses = list(Clause.objects.filter(contract=contract, found=True))

                        if clauses:
                            # Build all graphs
                            graph_result = build_all_graphs(contract, clauses)

                            # Save graph metadata
                            ContractGraphMeta.objects.update_or_create(
                                contract=contract,
                                defaults={
                                    'graph_summary': graph_result.get('graph_summary', {}),
                                    'risk_timeline': graph_result.get('risk_timeline', {}),
                                    'negotiation_advice': graph_result.get('negotiation_advice', []),
                                    'neo4j_synced': graph_result.get('neo4j_synced', False),
                                }
                            )

                            print(f"[GRAPH] SUCCESS! Graphs built and persisted")
                            print(f"[GRAPH]   - NetworkX: {len(graph_result.get('graph_summary', {}).get('nodes', []))} nodes")
                            print(f"[GRAPH]   - Risk propagation: {graph_result.get('risk_timeline', {}).get('propagation_steps', 0)} steps")
                            print(f"[GRAPH]   - Negotiation advice: {len(graph_result.get('negotiation_advice', []))} clauses analyzed")
                            print(f"[GRAPH]   - Neo4j synced: {graph_result.get('neo4j_synced', False)}")
                        else:
                            print(f"[GRAPH] No clauses found, skipping graph building")

                    except Exception as graph_error:
                        print(f"[GRAPH] ERROR: {str(graph_error)}")
                        import traceback
                        traceback.print_exc()
                        # Don't fail the entire process if graph building fails
                    # =============================================

                except Exception as e:
                    print(f"[AUTO-MINING] ERROR: {str(e)}")
                    import traceback
                    traceback.print_exc()

                # ========== CHROMA RAG INGEST ==========
                try:
                    from api.rag_engine import ContractRAG
                    rag = ContractRAG(use_openai=False)
                    rag.ingest_contract(
                        contract_id=str(contract.id),
                        text=contract.full_text,
                        metadata={
                            'contract_name': contract.original_filename or contract.filename,
                            'filename': contract.original_filename or contract.filename,
                            'user_id': str(contract.user_id),
                        }
                    )
                    print(f"[RAG] Contract {contract.id} ingested into ChromaDB")
                except Exception as rag_err:
                    print(f"[RAG] ChromaDB ingest failed: {rag_err}")
                # =======================================

            # Start automated analysis in background thread
            analysis_thread = threading.Thread(target=run_automated_analysis)
            analysis_thread.daemon = True
            analysis_thread.start()
            print(f"[AUTO-MINING] Background analysis thread started")

        except Exception as e:
            print(f"[AUTO-MINING] Could not start automated analysis: {str(e)}")
            # Don't fail the upload if analysis fails
        # ===============================================

        return Response({
            'message': 'File uploaded successfully',
            'contractId': str(contract.id),
            'filename': file.name,
            'type': ext.replace('.', '').upper(),
            'pages': pages,
            'ocr_performed': ocr_performed,
            'text_preview': extracted_text[:1000],
            'full_text': extracted_text,
            'contractType': classification.get('contractType'),
            'confidenceScore': classification.get('confidenceScore'),
            'timings': timings
        })

    except Exception as e:
        print(f'Upload error: {str(e)}')
        return Response(
            {'message': 'Upload failed', 'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_folder_view(request):
    """
    Upload multiple contract files from a folder (bulk upload)

    POST /api/contracts/upload-folder

    Accepts: multipart/form-data with multiple 'files'
    Returns: Batch processing results with success/failure summary
    """
    try:
        files = request.FILES.getlist('files')

        if not files:
            return Response(
                {'message': 'No files provided'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = request.user

        # Check contract limit based on user's plan (using lifetime uploads)
        if user.current_plan:
            contract_limit = user.current_plan.contract_limit
            # -1 means unlimited contracts
            if contract_limit != -1:
                # Use total_contracts_uploaded (lifetime count) instead of current count
                current_contract_count = Contract.objects.filter(user=user).count()

                # Check if user has already reached limit
                if user.total_contracts_uploaded >= contract_limit:
                    return Response({
                        'error': 'CONTRACT_LIMIT_REACHED',
                        'message': f'You have reached your {user.current_plan.display_name} plan limit of {contract_limit} contracts.',
                        'currentCount': current_contract_count,
                        'totalUploaded': user.total_contracts_uploaded,
                        'limit': contract_limit,
                        'planName': user.current_plan.display_name,
                        'suggestion': 'Upgrade your plan to upload more contracts and unlock advanced features.'
                    }, status=status.HTTP_402_PAYMENT_REQUIRED)

                # Check if uploading these files would exceed the limit
                remaining_slots = contract_limit - user.total_contracts_uploaded
                if len(files) > remaining_slots:
                    return Response({
                        'error': 'CONTRACT_LIMIT_EXCEEDED',
                        'message': f'Uploading {len(files)} files would exceed your {user.current_plan.display_name} plan limit.',
                        'currentCount': current_contract_count,
                        'totalUploaded': user.total_contracts_uploaded,
                        'limit': contract_limit,
                        'planName': user.current_plan.display_name,
                        'remainingSlots': remaining_slots,
                        'requestedFiles': len(files),
                        'suggestion': f'You can upload {remaining_slots} more contract(s) or upgrade your plan for more capacity.'
                    }, status=status.HTTP_402_PAYMENT_REQUIRED)

        results = []
        success_count = 0
        failure_count = 0

        print(f'\n[FOLDER UPLOAD] Processing {len(files)} files for user {user.email}')

        for idx, file in enumerate(files, 1):
            print(f'\n[FOLDER UPLOAD] Processing file {idx}/{len(files)}: {file.name}')

            try:
                # Validate file extension
                ext = os.path.splitext(file.name)[1].lower()
                allowed_extensions = ['.docx', '.pdf', '.png', '.jpg', '.jpeg']

                if ext not in allowed_extensions:
                    results.append({
                        'filename': file.name,
                        'success': False,
                        'error': f'Unsupported file type. Allowed: DOCX, PDF, PNG, JPG, JPEG'
                    })
                    failure_count += 1
                    continue

                # Validate file size
                if file.size > settings.MAX_UPLOAD_SIZE:
                    results.append({
                        'filename': file.name,
                        'success': False,
                        'error': 'File exceeds 25MB limit'
                    })
                    failure_count += 1
                    continue

                # Save file
                filename = f"{int(datetime.now().timestamp() * 1000)}-{file.name.replace(' ', '_')}"
                file_path = os.path.join(settings.MEDIA_ROOT, filename)
                os.makedirs(settings.MEDIA_ROOT, exist_ok=True)

                with open(file_path, 'wb+') as destination:
                    for chunk in file.chunks():
                        destination.write(chunk)

                # Extract text
                result = extract_text_from_file(file_path, ext)
                extracted_text = result.get('text', '')
                ocr_performed = result.get('ocr_performed', False)

                if not extracted_text or len(extracted_text.strip()) < 5:
                    # Clean up file
                    if os.path.exists(file_path):
                        os.remove(file_path)

                    results.append({
                        'filename': file.name,
                        'success': False,
                        'error': 'Unable to extract text from file'
                    })
                    failure_count += 1
                    continue

                # Classification
                classification = {'contractType': 'unknown', 'confidenceScore': 0}
                try:
                    result = classify_contract(extracted_text, filename=file.name)
                    if result:
                        classification = result
                except Exception as e:
                    print(f'[FOLDER UPLOAD] Classification error: {str(e)}')

                # Metadata extraction
                metadata = extract_contract_metadata(extracted_text)
                if not metadata:
                    metadata = {
                        "party_a": None,
                        "party_b": None,
                        "start_date": None,
                        "end_date": None,
                        "contract_value": None,
                        "contract_type": None,
                        "jurisdiction": None,
                        "payment_terms": None,
                        "liability_level": None,
                    }

                # Create contract record
                contract = Contract.objects.create(
                    user=user,
                    filename=filename,
                    original_filename=file.name,
                    file_type=ext.replace('.', '').upper(),
                    file_path=file_path,
                    full_text=extracted_text,
                    contract_type=metadata.get("contract_type") or classification.get('contractType'),
                    contract_value=metadata.get("contract_value"),
                    party_a=metadata.get("party_a"),
                    party_b=metadata.get("party_b"),
                    party_name=(
                        f"{metadata.get('party_a')} vs {metadata.get('party_b')}"
                        if metadata.get('party_a') and metadata.get('party_b')
                        else metadata.get('party_a') or metadata.get('party_b')
                    ),
                    start_date=metadata.get("start_date"),
                    end_date=metadata.get("end_date"),
                    contract_duration=(
                        f"{metadata.get('start_date')} to {metadata.get('end_date')}"
                        if metadata.get('start_date') and metadata.get('end_date')
                        else None
                    ),
                    jurisdiction=metadata.get("jurisdiction"),
                    payment_terms=metadata.get("payment_terms"),
                    liability_level=metadata.get("liability_level"),
                    ocr_performed=ocr_performed,
                    confidence_score=classification.get('confidenceScore'),
                    status='DRAFT'  # All uploaded contracts start as DRAFT
                )

                # Create initial version
                ContractVersion.objects.create(
                    contract=contract,
                    version_number=1,
                    full_text=extracted_text,
                    contract_type=contract.contract_type,
                    created_by=user,
                    change_description='Initial upload'
                )

                # Increment lifetime contract upload counter
                user.total_contracts_uploaded += 1
                user.save(update_fields=['total_contracts_uploaded'])

                results.append({
                    'filename': file.name,
                    'success': True,
                    'contractId': str(contract.id),
                    'contractType': contract.contract_type,
                    'status': contract.status
                })
                success_count += 1
                print(f'[FOLDER UPLOAD] [OK] Successfully processed: {file.name}')

            except Exception as e:
                print(f'[FOLDER UPLOAD] ✗ Error processing {file.name}: {str(e)}')
                results.append({
                    'filename': file.name,
                    'success': False,
                    'error': str(e)
                })
                failure_count += 1

        print(f'\n[FOLDER UPLOAD] Batch complete: {success_count} succeeded, {failure_count} failed')

        return Response({
            'message': 'Folder upload complete',
            'total': len(files),
            'success_count': success_count,
            'failure_count': failure_count,
            'results': results
        })

    except Exception as e:
        print(f'[FOLDER UPLOAD] Fatal error: {str(e)}')
        return Response(
            {'message': 'Folder upload failed', 'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])  # Temporarily disabled for development
def list_contracts(request):
    """List all contracts for current user"""
    try:
        # Get user from token if provided, otherwise use admin@example.com for development
        try:
            user = request.user if request.user.is_authenticated else None
            if not user:
                user = User.objects.filter(email='admin@example.com').first() or User.objects.first()
        except:
            user = User.objects.filter(email='admin@example.com').first() or User.objects.first()

        # Get all contracts and remove duplicates by keeping only the most recent upload
        # Group by original_filename and keep only the latest one
        from django.db.models import Max

        # Get the latest uploaded_at for each original_filename
        latest_contracts = Contract.objects.filter(
            user=user
        ).values('original_filename').annotate(
            latest_upload=Max('uploaded_at')
        )

        # Get the actual contract objects matching those latest uploads
        # Only include contracts that have clauses (to avoid showing broken contracts)
        from core.models import Clause
        contract_ids = []
        for item in latest_contracts:
            contract = Contract.objects.filter(
                user=user,
                original_filename=item['original_filename'],
                uploaded_at=item['latest_upload']
            ).first()
            if contract:
                # Check if contract has clauses
                has_clauses = Clause.objects.filter(contract=contract).exists()
                if has_clauses:
                    contract_ids.append(contract.id)

        # Fetch contracts and serialize
        contracts = Contract.objects.filter(id__in=contract_ids).order_by('-uploaded_at')
        serializer = ContractSerializer(contracts, many=True)

        return Response({
            'message': 'Contracts retrieved',
            'count': len(serializer.data),
            'contracts': serializer.data
        })

    except Exception as e:
        return Response(
            {'message': 'Failed to retrieve contracts', 'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_contract(request, contract_id):
    """Get contract by ID"""
    try:
        contract = Contract.objects.get(id=contract_id)

        if contract.user != request.user:
            return Response(
                {'message': 'Access denied'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = ContractDetailSerializer(contract)
        return Response({
            'success': True,
            'message': 'Contract retrieved',
            'contract': serializer.data
        })

    except Contract.DoesNotExist:
        return Response(
            {'message': 'Contract not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'message': 'Failed to retrieve contract', 'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_contract_by_id(request, contract_id):
    """Delete contract by ID"""
    try:
        # Get the contract
        try:
            contract = Contract.objects.get(id=contract_id, user=request.user)
        except Contract.DoesNotExist:
            return Response(
                {'message': 'Contract not found or you do not have permission to delete it'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Delete the file from storage
        file_path = os.path.join(settings.MEDIA_ROOT, contract.filename)
        if os.path.exists(file_path):
            os.remove(file_path)

        # Delete the database record
        contract.delete()

        return Response({'message': 'Contract deleted successfully'})

    except Exception as e:
        return Response(
            {'message': 'Failed to delete contract', 'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_contract(request, filename):
    """Delete contract file by filename (legacy endpoint)"""
    try:
        file_path = os.path.join(settings.MEDIA_ROOT, filename)

        if os.path.exists(file_path):
            os.remove(file_path)
            return Response({'message': 'Contract deleted successfully'})
        else:
            return Response(
                {'message': 'Contract not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    except Exception as e:
        return Response(
            {'message': 'Failed to delete contract', 'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def assign_contract(request, contract_id):
    """Assign contract to another user by email"""
    try:
        email = request.data.get('email')

        if not email:
            return Response(
                {'message': 'Email address is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get the contract
        try:
            contract = Contract.objects.get(id=contract_id)
        except Contract.DoesNotExist:
            return Response(
                {'message': 'Contract not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check if the requesting user owns the contract
        if contract.user != request.user:
            return Response(
                {'message': 'You do not have permission to assign this contract'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Find the user to assign to
        try:
            target_user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {'message': f'User with email "{email}" not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check if trying to assign to self
        if target_user.id == request.user.id:
            return Response(
                {'message': 'Cannot assign contract to yourself'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Assign the contract and track who assigned it
        contract.user = target_user
        contract.assigned_by = request.user.id
        contract.save()

        return Response({
            'message': f'Contract successfully assigned to {target_user.email}',
            'assignedTo': {
                'id': target_user.id,
                'email': target_user.email,
                'firstName': target_user.first_name,
                'lastName': target_user.last_name
            }
        })

    except Exception as e:
        return Response(
            {'message': 'Failed to assign contract', 'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def extract_clauses_view(request, contract_id):
    """Extract clauses from contract"""
    try:
        start_time = time.time()
        print(f'[CLAUSES] Starting clause extraction for contract: {contract_id}')

        contract = Contract.objects.get(id=contract_id)
        print(f'[CLAUSES] Contract retrieved: {contract.original_filename}')

        if contract.user != request.user:
            return Response(
                {'message': 'Access denied'},
                status=status.HTTP_403_FORBIDDEN
            )

        if not contract.full_text or len(contract.full_text.strip()) == 0:
            return Response({
                'message': 'Contract has no extracted text',
                'suggestion': 'Upload the contract again'
            }, status=status.HTTP_400_BAD_REQUEST)

        print(f'Text length: {len(contract.full_text)} characters')

        print('Running clause extraction...')
        extract_start = time.time()
        extracted_clauses_data = extract_clauses(contract.full_text)
        extract_time = round(time.time() - extract_start, 2)
        print(f'Clauses extracted: {len(extracted_clauses_data)} total')

        db_start = time.time()
        Clause.objects.filter(contract=contract).delete()

        saved_clauses = []
        for clause_data in extracted_clauses_data:
            try:
                extracted_text = clause_data.get('clauseText', '')
                if not extracted_text and clause_data.get('textSpans'):
                    extracted_text = clause_data['textSpans'][0].get('text', '')
                if not extracted_text and clause_data.get('contextSentences'):
                    extracted_text = clause_data['contextSentences'][0].get('text', '')

                clause = Clause.objects.create(
                    contract=contract,
                    clause_name=clause_data.get('clauseName'),
                    found=clause_data.get('found', False),
                    confidence=clause_data.get('confidence'),
                    match_count=clause_data.get('matchCount'),
                    text_spans=json.dumps(clause_data.get('textSpans', [])),
                    context_sentences=json.dumps(clause_data.get('contextSentences', [])),
                    extracted_text=extracted_text
                )
                saved_clauses.append(clause)
            except Exception as e:
                print(f'Error saving clause: {str(e)}')
                raise

        print('All clauses saved successfully!')
        db_time = round(time.time() - db_start, 2)
        total_time = round(time.time() - start_time, 2)

        found_clauses = [c for c in saved_clauses if c.found]

        # Return all clauses (both found and not found) for comprehensive analysis
        response_clauses = []

        # First add all found clauses
        for clause in found_clauses:
            response_clauses.append({
                'id': str(clause.id),
                'clauseName': clause.clause_name,
                'clause_name': clause.clause_name,
                'clause_type': clause.clause_type or clause.clause_name or 'general',
                'found': True,
                'confidence': clause.confidence,
                'matchCount': clause.match_count,
                'extracted_text': clause.extracted_text or '',
                'textSpans': json.loads(clause.text_spans) if clause.text_spans else [],
                'contextSentences': json.loads(clause.context_sentences) if clause.context_sentences else [],
            })

        # Then add all not found clauses
        not_found_clauses = [c for c in saved_clauses if not c.found]
        for clause in not_found_clauses:
            response_clauses.append({
                'id': str(clause.id),
                'clauseName': clause.clause_name,
                'found': False,
                'confidence': 0,
                'matchCount': 0,
                'textSpans': [],
                'contextSentences': [],
            })

        # ========== AUTO-TRIGGER INTENT MINING ==========
        try:
            from .intent_mining_service import IntentMiningService
            import threading

            print(f"[AUTO-MINING] Triggering intent mining for contract {contract.id}...")
            service = IntentMiningService()

            # Get latest version for this contract
            latest_version = ContractVersion.objects.filter(contract=contract).order_by('-version_number').first()

            # Run in background to avoid blocking the response
            def run_intent_mining():
                try:
                    result = service.process_contract_clauses(
                        contract_id=str(contract.id),
                        contract_version_id=str(latest_version.id) if latest_version else None
                    )
                    if result.get('success'):
                        print(f"[AUTO-MINING] SUCCESS: {result.get('obligations_extracted', 0)} obligations, "
                              f"{result.get('rights_extracted', 0)} rights extracted")
                    else:
                        print(f"[AUTO-MINING] FAILED: {result.get('error')}")
                except Exception as e:
                    print(f"[AUTO-MINING] ERROR: {str(e)}")
                    import traceback
                    traceback.print_exc()

            # Start mining in background thread
            mining_thread = threading.Thread(target=run_intent_mining)
            mining_thread.daemon = True
            mining_thread.start()
            print(f"[AUTO-MINING] Background thread started successfully")

        except Exception as e:
            print(f"[AUTO-MINING] Could not trigger intent mining: {str(e)}")
            # Don't fail the clause extraction if mining fails
        # ===============================================

        return Response({
            'message': 'Clauses extracted successfully',
            'contractId': str(contract.id),
            'totalClausesAnalyzed': len(saved_clauses),
            'clausesFound': len(found_clauses),
            'clauses': response_clauses,
            'timings': {
                'extraction': extract_time,
                'database_save': db_time,
                'total': total_time
            }
        })

    except Contract.DoesNotExist:
        return Response(
            {'message': 'Contract not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        print(f'Clause extraction error: {str(e)}')
        return Response(
            {'message': 'Clause extraction failed', 'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def process_contract_clause_library(request, contract_id):
    """
    Process contract through the Clause Library pipeline.

    This endpoint:
    1. Extracts clauses using NLP patterns
    2. Generates BERT embeddings
    3. Clusters clauses by similarity
    4. Names clause groups using Qwen LLM
    5. Stores in MySQL + Qdrant vector DB
    """
    try:
        import time
        start_time = time.time()

        print(f'[CLAUSE LIBRARY] Starting enhanced processing for contract: {contract_id}')

        # Get contract and verify ownership
        contract = Contract.objects.get(id=contract_id)

        if contract.user != request.user:
            return Response(
                {'message': 'Access denied'},
                status=status.HTTP_403_FORBIDDEN
            )

        if not contract.full_text or len(contract.full_text.strip()) == 0:
            return Response({
                'message': 'Contract has no extracted text',
                'suggestion': 'Upload the contract again'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Get number of clusters from request (optional)
        n_clusters = int(request.data.get('n_clusters', 8))

        # Import and use the clause library service
        from .clause_library_service import ClauseLibraryService

        print('[CLAUSE LIBRARY] Initializing service...')
        service = ClauseLibraryService()

        # Process the contract
        print('[CLAUSE LIBRARY] Processing contract...')
        result = service.process_contract(
            contract=contract,
            n_clusters=n_clusters,
            save_to_db=True
        )

        total_time = round(time.time() - start_time, 2)

        if result['success']:
            print(f'[CLAUSE LIBRARY] Processing complete in {total_time}s')

            # Add timing info
            result['timing'] = {
                'total': total_time,
                'unit': 'seconds'
            }

            # Add contract info
            result['contract'] = {
                'id': str(contract.id),
                'filename': contract.original_filename,
                'contract_type': contract.contract_type
            }

            return Response(result, status=status.HTTP_200_OK)
        else:
            print(f'[CLAUSE LIBRARY] Processing failed: {result.get("message")}')
            return Response(result, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    except Contract.DoesNotExist:
        return Response(
            {'message': 'Contract not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        print(f'[CLAUSE LIBRARY] Error: {str(e)}')
        import traceback
        traceback.print_exc()
        return Response(
            {'message': 'Clause library processing failed', 'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def search_clause_library(request):
    """
    Search for similar clauses in the library using semantic search.

    Query params:
    - query: Search text
    - limit: Max results (default: 10)
    - contract_type: Filter by contract type (optional)
    """
    try:
        query_text = request.GET.get('query', '').strip()

        if not query_text:
            return Response(
                {'message': 'Query parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        limit = int(request.GET.get('limit', 10))
        contract_type = request.GET.get('contract_type')

        # Import service
        from .clause_library_service import ClauseLibraryService

        service = ClauseLibraryService()

        # Search
        results = service.search_similar_clauses(
            query_text=query_text,
            limit=limit,
            contract_type=contract_type
        )

        return Response({
            'query': query_text,
            'total_results': len(results),
            'results': results
        }, status=status.HTTP_200_OK)

    except Exception as e:
        print(f'[CLAUSE LIBRARY SEARCH] Error: {str(e)}')
        return Response(
            {'message': 'Search failed', 'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_clause_library_statistics(request):
    """
    Get statistics about the clause library.

    Query params:
    - contract_id: Filter by specific contract (optional)
    """
    try:
        contract_id = request.GET.get('contract_id')

        # Import service
        from .clause_library_service import ClauseLibraryService

        service = ClauseLibraryService()

        # Get statistics
        stats = service.get_clause_statistics(contract_id=contract_id)

        return Response(stats, status=status.HTTP_200_OK)

    except Exception as e:
        print(f'[CLAUSE LIBRARY STATS] Error: {str(e)}')
        return Response(
            {'message': 'Failed to get statistics', 'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def refresh_all_metadata(request):
    """Re-extract metadata for all user's contracts"""
    try:
        contracts = Contract.objects.filter(user=request.user)
        success_count = 0
        error_count = 0
        results = []

        print(f'[REFRESH ALL] Processing {contracts.count()} contracts')

        for contract in contracts:
            try:
                if not contract.full_text:
                    results.append({
                        'id': str(contract.id),
                        'filename': contract.original_filename,
                        'status': 'skipped',
                        'reason': 'No text extracted'
                    })
                    continue

                # Re-extract metadata
                metadata = extract_contract_metadata(contract.full_text)

                # Update contract fields
                contract.party_a = metadata.get("party_a")
                contract.party_b = metadata.get("party_b")
                contract.start_date = metadata.get("start_date")
                contract.end_date = metadata.get("end_date")
                contract.contract_value = metadata.get("contract_value")
                contract.contract_type = metadata.get("contract_type") or contract.contract_type
                contract.jurisdiction = metadata.get("jurisdiction")
                contract.payment_terms = metadata.get("payment_terms")
                contract.liability_level = metadata.get("liability_level")

                # Update computed fields
                if contract.party_a and contract.party_b:
                    contract.party_name = f"{contract.party_a} vs {contract.party_b}"
                elif contract.party_a or contract.party_b:
                    contract.party_name = contract.party_a or contract.party_b

                if contract.start_date and contract.end_date:
                    contract.contract_duration = f"{contract.start_date} to {contract.end_date}"

                contract.save()
                success_count += 1

                results.append({
                    'id': str(contract.id),
                    'filename': contract.original_filename,
                    'status': 'success',
                    'parties': f"{contract.party_a} vs {contract.party_b}" if contract.party_a and contract.party_b else None,
                    'value': contract.contract_value
                })

            except Exception as e:
                error_count += 1
                results.append({
                    'id': str(contract.id),
                    'filename': contract.original_filename,
                    'status': 'error',
                    'error': str(e)
                })
                print(f'[REFRESH ERROR] Contract {contract.id}: {str(e)}')

        return Response({
            'message': f'Processed {contracts.count()} contracts',
            'success': success_count,
            'errors': error_count,
            'results': results
        })

    except Exception as e:
        print(f'[REFRESH ALL ERROR] {str(e)}')
        return Response(
            {'message': 'Failed to refresh all metadata', 'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def refresh_contract_metadata(request, contract_id):
    """Re-extract metadata (parties, dates, value) from contract text"""
    try:
        contract = Contract.objects.get(id=contract_id)

        if contract.user != request.user:
            return Response(
                {'message': 'Access denied'},
                status=status.HTTP_403_FORBIDDEN
            )

        if not contract.full_text:
            return Response(
                {'message': 'Contract has no text to extract from'},
                status=status.HTTP_400_BAD_REQUEST
            )

        print(f'[REFRESH] Re-extracting metadata for contract: {contract.original_filename}')

        # Re-extract metadata
        metadata = extract_contract_metadata(contract.full_text)

        # Update contract fields
        contract.party_a = metadata.get("party_a")
        contract.party_b = metadata.get("party_b")
        contract.start_date = metadata.get("start_date")
        contract.end_date = metadata.get("end_date")
        contract.contract_value = metadata.get("contract_value")
        contract.contract_type = metadata.get("contract_type") or contract.contract_type
        contract.jurisdiction = metadata.get("jurisdiction")
        contract.payment_terms = metadata.get("payment_terms")
        contract.liability_level = metadata.get("liability_level")

        # Update computed fields
        if contract.party_a and contract.party_b:
            contract.party_name = f"{contract.party_a} vs {contract.party_b}"
        elif contract.party_a or contract.party_b:
            contract.party_name = contract.party_a or contract.party_b

        if contract.start_date and contract.end_date:
            contract.contract_duration = f"{contract.start_date} to {contract.end_date}"

        contract.save()

        print(f'[REFRESH] Metadata updated successfully')

        # Return updated contract data
        serializer = ContractSerializer(contract)
        return Response({
            'message': 'Metadata refreshed successfully',
            'contract': serializer.data
        })

    except Contract.DoesNotExist:
        return Response(
            {'message': 'Contract not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        print(f'[REFRESH ERROR] {str(e)}')
        import traceback
        traceback.print_exc()
        return Response(
            {'message': 'Failed to refresh metadata', 'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_clauses(request, contract_id):
    """Get extracted clauses for contract"""
    try:
        print(f'[GET_CLAUSES] Fetching clauses for contract: {contract_id}')

        contract = Contract.objects.get(id=contract_id)

        if contract.user != request.user:
            return Response(
                {'message': 'Access denied'},
                status=status.HTTP_403_FORBIDDEN
            )

        print('Contract found, querying clauses...')

        clauses = Clause.objects.filter(contract=contract).order_by('-confidence')

        print(f'Found {len(clauses)} clauses in database')

        found_clauses = [c for c in clauses if c.found]
        not_found_clauses = [c for c in clauses if not c.found]

        response_clauses = []

        for clause in found_clauses:
            # Get clause type - use clause_type or clause_name as fallback
            clause_type = clause.clause_type or clause.clause_name or 'general'

            # Infer risk score if not set (same logic as clause_graph.py)
            risk_score = clause.risk_score
            if risk_score is None:
                clause_type_lower = clause_type.lower()
                if any(kw in clause_type_lower for kw in ['indemnity', 'liability', 'termination', 'penalty', 'damages', 'breach', 'warranty']):
                    risk_score = 0.75
                elif any(kw in clause_type_lower for kw in ['payment', 'fee', 'insurance', 'confidentiality', 'ip', 'non-compete']):
                    risk_score = 0.55
                else:
                    risk_score = 0.35

            response_clauses.append({
                'id': str(clause.id),
                'clauseName': clause.clause_name,
                'clause_name': clause.clause_name,  # Add snake_case version
                'clause_type': clause_type,  # Add clause_type
                'risk_score': float(risk_score),  # Add risk_score
                'extracted_text': clause.extracted_text or '',  # Add actual clause text
                'confidence': clause.confidence,
                'matchCount': clause.match_count,
                'found': True,
                'textSpans': json.loads(clause.text_spans) if clause.text_spans else [],
                'contextSentences': json.loads(clause.context_sentences) if clause.context_sentences else [],
            })

        for clause in not_found_clauses:
            response_clauses.append({
                'id': str(clause.id),
                'clauseName': clause.clause_name,
                'clause_name': clause.clause_name,  # Add snake_case version
                'clause_type': clause.clause_type or clause.clause_name or 'general',  # Add clause_type
                'risk_score': 0.0,  # Not found clauses have 0 risk
                'extracted_text': clause.extracted_text or '',  # Add actual clause text
                'confidence': 0,
                'matchCount': 0,
                'found': False,
                'textSpans': [],
                'contextSentences': [],
            })

        return Response({
            'success': True,
            'message': 'Clauses retrieved',
            'contractId': str(contract.id),
            'clausesFound': len(found_clauses),
            'totalClausesAnalyzed': len(clauses),
            'clauses': response_clauses
        })

    except Contract.DoesNotExist:
        return Response(
            {'message': 'Contract not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        print(f'Get clauses error: {str(e)}')
        return Response(
            {'message': 'Failed to retrieve clauses', 'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def _detect_risky_clauses_fallback(contract, risk_analysis):
    """
    Fallback function to detect risky clauses using pattern matching
    when no deviations are found in the database.
    Saves detected patterns to database for auto-correction.
    """
    import re

    text_lower = contract.full_text.lower()
    risky_patterns = []
    created_deviations = []

    # Detect indemnification clauses
    if re.search(r'indemnif(y|ication|ied)', text_lower):
        deviation = ClauseDeviation.objects.create(
            risk_analysis=risk_analysis,
            clause_name='Indemnification',
            deviation_type='UNFAVORABLE',
            severity='HIGH',
            description='Indemnification clause detected. This may impose significant liability obligations on your organization.',
            recommendation='Review indemnification scope carefully. Consider limiting indemnity to direct damages and excluding consequential damages. Ensure mutual indemnification where possible.'
        )
        created_deviations.append(deviation)
        risky_patterns.append({
            'id': str(deviation.id),
            'clause_name': deviation.clause_name,
            'deviation_type': deviation.deviation_type,
            'severity': deviation.severity,
            'description': deviation.description,
            'recommendation': deviation.recommendation,
            'created_at': deviation.created_at.isoformat() if deviation.created_at else None
        })

    # Detect unlimited liability
    if re.search(r'unlimited\s+liability|without\s+limit', text_lower):
        deviation = ClauseDeviation.objects.create(
            risk_analysis=risk_analysis,
            clause_name='Unlimited Liability',
            deviation_type='UNFAVORABLE',
            severity='HIGH',
            description='Unlimited liability clause detected. This exposes your organization to uncapped financial risk.',
            recommendation='Negotiate a liability cap (e.g., limited to contract value or a specific dollar amount). Exclude liability for indirect, consequential, or punitive damages.'
        )
        risky_patterns.append({
            'id': str(deviation.id),
            'clause_name': deviation.clause_name,
            'deviation_type': deviation.deviation_type,
            'severity': deviation.severity,
            'description': deviation.description,
            'recommendation': deviation.recommendation,
            'created_at': deviation.created_at.isoformat() if deviation.created_at else None
        })

    # Detect automatic renewal
    if re.search(r'automatic(ally)?\s+(renew|extension)|auto(-|\s)renew', text_lower):
        deviation = ClauseDeviation.objects.create(
            risk_analysis=risk_analysis,
            clause_name='Automatic Renewal',
            deviation_type='UNFAVORABLE',
            severity='MEDIUM',
            description='Automatic renewal clause detected. Contract may renew without explicit consent.',
            recommendation='Ensure adequate notice period for non-renewal (typically 60-90 days). Set calendar reminders before renewal dates.'
        )
        risky_patterns.append({
            'id': str(deviation.id),
            'clause_name': deviation.clause_name,
            'deviation_type': deviation.deviation_type,
            'severity': deviation.severity,
            'description': deviation.description,
            'recommendation': deviation.recommendation,
            'created_at': deviation.created_at.isoformat() if deviation.created_at else None
        })

    # Detect non-compete clauses
    if re.search(r'non(-|\s)compete|non(-|\s)competition|shall\s+not\s+compete', text_lower):
        deviation = ClauseDeviation.objects.create(
            risk_analysis=risk_analysis,
            clause_name='Non-Compete',
            deviation_type='UNFAVORABLE',
            severity='HIGH',
            description='Non-compete clause detected. This may restrict your business activities.',
            recommendation='Limit non-compete scope geographically and temporally (e.g., specific territories, 12-24 months). Ensure it only applies to direct competitors.'
        )
        risky_patterns.append({
            'id': str(deviation.id),
            'clause_name': deviation.clause_name,
            'deviation_type': deviation.deviation_type,
            'severity': deviation.severity,
            'description': deviation.description,
            'recommendation': deviation.recommendation,
            'created_at': deviation.created_at.isoformat() if deviation.created_at else None
        })

    # Detect exclusive rights
    if re.search(r'exclusive\s+(rights?|license|agreement)', text_lower):
        deviation = ClauseDeviation.objects.create(
            risk_analysis=risk_analysis,
            clause_name='Exclusivity',
            deviation_type='UNFAVORABLE',
            severity='MEDIUM',
            description='Exclusivity clause detected. This may limit your ability to work with other parties.',
            recommendation='Define clear scope and duration of exclusivity. Consider carve-outs for existing relationships.'
        )
        risky_patterns.append({
            'id': str(deviation.id),
            'clause_name': deviation.clause_name,
            'deviation_type': deviation.deviation_type,
            'severity': deviation.severity,
            'description': deviation.description,
            'recommendation': deviation.recommendation,
            'created_at': deviation.created_at.isoformat() if deviation.created_at else None
        })

    # Detect unilateral termination rights
    if re.search(r'terminate\s+(at\s+)?any\s+time|terminate\s+for\s+convenience|terminate\s+without\s+cause', text_lower):
        deviation = ClauseDeviation.objects.create(
            risk_analysis=risk_analysis,
            clause_name='Unilateral Termination',
            deviation_type='UNFAVORABLE',
            severity='MEDIUM',
            description='Unilateral termination clause detected. The other party may terminate without cause.',
            recommendation='Negotiate mutual termination rights or require minimum notice period (e.g., 30-90 days). Consider termination fees.'
        )
        risky_patterns.append({
            'id': str(deviation.id),
            'clause_name': deviation.clause_name,
            'deviation_type': deviation.deviation_type,
            'severity': deviation.severity,
            'description': deviation.description,
            'recommendation': deviation.recommendation,
            'created_at': deviation.created_at.isoformat() if deviation.created_at else None
        })

    # Detect penalty clauses
    if re.search(r'penalty|penalt(y|ies)|liquidated\s+damages|late\s+fee', text_lower):
        deviation = ClauseDeviation.objects.create(
            risk_analysis=risk_analysis,
            clause_name='Penalty/Liquidated Damages',
            deviation_type='UNFAVORABLE',
            severity='MEDIUM',
            description='Penalty or liquidated damages clause detected. This may impose financial penalties for delays or breaches.',
            recommendation='Ensure liquidated damages are reasonable and reflect actual anticipated losses. Negotiate caps and grace periods.'
        )
        risky_patterns.append({
            'id': str(deviation.id),
            'clause_name': deviation.clause_name,
            'deviation_type': deviation.deviation_type,
            'severity': deviation.severity,
            'description': deviation.description,
            'recommendation': deviation.recommendation,
            'created_at': deviation.created_at.isoformat() if deviation.created_at else None
        })

    # Detect IP assignment
    if re.search(r'(all|any)\s+(intellectual\s+property|ip|work\s+product).*(assign|transfer|belong)', text_lower):
        deviation = ClauseDeviation.objects.create(
            risk_analysis=risk_analysis,
            clause_name='IP Assignment',
            deviation_type='UNFAVORABLE',
            severity='HIGH',
            description='Broad intellectual property assignment clause detected. You may lose rights to work product or IP.',
            recommendation='Limit IP assignment to deliverables specifically created under this contract. Retain ownership of pre-existing IP and general know-how.'
        )
        risky_patterns.append({
            'id': str(deviation.id),
            'clause_name': deviation.clause_name,
            'deviation_type': deviation.deviation_type,
            'severity': deviation.severity,
            'description': deviation.description,
            'recommendation': deviation.recommendation,
            'created_at': deviation.created_at.isoformat() if deviation.created_at else None
        })

    return risky_patterns


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_risky_clauses_view(request, contract_id):
    """
    Get risky clauses for a contract (HIGH severity deviations)
    Used for redlining feature
    """
    try:
        # Verify contract exists and belongs to user
        contract = Contract.objects.get(id=contract_id)

        if contract.user != request.user:
            return Response(
                {'message': 'Access denied'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Check if risk analysis exists, if not try to run it automatically
        try:
            risk_analysis = ContractRiskAnalysis.objects.get(contract=contract)
        except ContractRiskAnalysis.DoesNotExist:
            # Try to auto-generate risk analysis
            try:
                from .risk_analyzer import analyze_contract_risk

                # Check if contract has clauses
                if not contract.clauses.exists():
                    # Extract clauses first
                    from .utils import extract_clauses
                    extract_clauses(contract)

                # Run risk analysis
                risk_analysis = analyze_contract_risk(contract_id)
            except Exception as auto_analysis_error:
                # If auto-analysis fails, return empty result with helpful message
                return Response({
                    'message': 'No risk analysis found. Please run clause extraction and risk analysis first.',
                    'contract_id': str(contract.id),
                    'contract_name': contract.original_filename,
                    'risk_level': 'UNKNOWN',
                    'overall_risk_score': 0,
                    'risky_clauses_count': 0,
                    'risky_clauses': [],
                    'auto_analysis_error': str(auto_analysis_error)
                }, status=status.HTTP_200_OK)

        # Get HIGH and MEDIUM severity clause deviations
        risky_clauses = ClauseDeviation.objects.filter(
            risk_analysis=risk_analysis,
            severity__in=['HIGH', 'MEDIUM']
        ).order_by('-severity', 'clause_name')

        # Build response
        clauses_data = []
        for clause in risky_clauses:
            clauses_data.append({
                'id': str(clause.id),
                'clause_name': clause.clause_name,
                'deviation_type': clause.deviation_type,
                'severity': clause.severity,
                'description': clause.description,
                'recommendation': clause.recommendation,
                'created_at': clause.created_at.isoformat() if clause.created_at else None
            })

        # If no risky clauses found, try to detect them using pattern matching
        if len(clauses_data) == 0 and contract.full_text:
            clauses_data = _detect_risky_clauses_fallback(contract, risk_analysis)

        return Response({
            'message': 'Risky clauses retrieved',
            'contract_id': str(contract.id),
            'contract_name': contract.original_filename,
            'risk_level': risk_analysis.risk_level,
            'overall_risk_score': risk_analysis.risk_score,
            'risky_clauses_count': len(clauses_data),
            'risky_clauses': clauses_data
        })

    except Contract.DoesNotExist:
        return Response(
            {'message': 'Contract not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        print(f'Get risky clauses error: {str(e)}')
        import traceback
        traceback.print_exc()
        return Response(
            {'message': 'Failed to retrieve risky clauses', 'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def auto_correct_clause_view(request, clause_id):
    """
    Auto-correct a risky clause using AI
    Returns original text and suggested safer alternative
    """
    try:
        from .utils import auto_correct_clause

        print(f'[AUTO_CORRECT] Processing clause: {clause_id}')

        # Get the clause deviation
        try:
            clause = ClauseDeviation.objects.get(id=clause_id)
        except ClauseDeviation.DoesNotExist:
            return Response(
                {'message': 'Clause not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Verify user has access to this clause's contract
        contract = clause.risk_analysis.contract
        if contract.user != request.user:
            return Response(
                {'message': 'Access denied'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Get the original clause text from description
        original_text = clause.description

        print(f'[AUTO_CORRECT] Calling LLM for clause: {clause.clause_name}')

        # Call auto-correction helper
        correction_result = auto_correct_clause(original_text)

        return Response({
            'message': 'Auto-correction generated',
            'clause_id': str(clause.id),
            'clause_name': clause.clause_name,
            'severity': clause.severity,
            'deviation_type': clause.deviation_type,
            'original_text': original_text,
            'suggested_text': correction_result['suggested_text'],
            'explanation': correction_result['explanation'],
            'recommendation': clause.recommendation
        })

    except Exception as e:
        print(f'Auto-correction error: {str(e)}')
        import traceback
        traceback.print_exc()
        return Response(
            {'message': 'Failed to auto-correct clause', 'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def accept_clause_suggestion_view(request, clause_id):
    """
    Accept a clause suggestion and optionally generate a modified PDF

    Request body:
    {
        "accepted_text": "The text to accept (either suggested or manually edited)",
        "generate_pdf": true/false (optional, default true)
    }

    Returns:
    {
        "message": "Suggestion accepted successfully",
        "clause_id": "...",
        "download_url": "..." (if PDF was generated)
    }
    """
    try:
        from django.utils import timezone
        from django.http import FileResponse
        from .utils import create_modified_pdf
        import mimetypes

        print(f'[ACCEPT_SUGGESTION] Processing clause: {clause_id}')

        # Get the clause deviation
        try:
            clause = ClauseDeviation.objects.get(id=clause_id)
        except ClauseDeviation.DoesNotExist:
            return Response(
                {'message': 'Clause not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Verify user has access to this clause's contract
        contract = clause.risk_analysis.contract
        if contract.user != request.user:
            return Response(
                {'message': 'Access denied'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Get accepted text from request
        accepted_text = request.data.get('accepted_text')
        if not accepted_text:
            return Response(
                {'message': 'accepted_text is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update clause with accepted suggestion
        clause.accepted_text = accepted_text
        clause.status = 'ACCEPTED'
        clause.accepted_at = timezone.now()
        clause.save()

        print(f'[ACCEPT_SUGGESTION] Clause {clause.clause_name} accepted successfully')

        # Check if we should generate PDF
        generate_pdf = request.data.get('generate_pdf', True)

        response_data = {
            'message': 'Suggestion accepted successfully',
            'clause_id': str(clause.id),
            'clause_name': clause.clause_name,
            'status': clause.status,
            'accepted_at': clause.accepted_at.isoformat()
        }

        if generate_pdf:
            # Get all accepted clauses for this contract
            all_accepted_clauses = ClauseDeviation.objects.filter(
                risk_analysis__contract=contract,
                status='ACCEPTED'
            ).values('id', 'clause_name', 'description', 'accepted_text', 'suggested_text')

            if all_accepted_clauses.exists():
                # Prepare clause changes for PDF generation
                clause_changes = []
                for accepted_clause in all_accepted_clauses:
                    clause_changes.append({
                        'clause_name': accepted_clause['clause_name'],
                        'original_text': accepted_clause['description'],
                        'accepted_text': accepted_clause['accepted_text'] or accepted_clause['suggested_text']
                    })

                print(f'[ACCEPT_SUGGESTION] Generating modified PDF with {len(clause_changes)} accepted clauses')

                # Generate modified PDF
                try:
                    modified_pdf_path = create_modified_pdf(
                        original_pdf_path=contract.file_path,
                        clause_changes=clause_changes,
                        contract_name=contract.original_filename or contract.filename
                    )

                    # Get relative path for download URL
                    from django.conf import settings
                    relative_path = os.path.relpath(modified_pdf_path, settings.MEDIA_ROOT)
                    download_url = f'{settings.MEDIA_URL}{relative_path.replace(os.sep, "/")}'

                    response_data['pdf_generated'] = True
                    response_data['download_url'] = download_url
                    response_data['filename'] = os.path.basename(modified_pdf_path)
                    response_data['total_accepted_clauses'] = len(clause_changes)

                    print(f'[ACCEPT_SUGGESTION] PDF generated successfully: {modified_pdf_path}')

                except Exception as pdf_error:
                    print(f'[ACCEPT_SUGGESTION] PDF generation failed: {str(pdf_error)}')
                    import traceback
                    traceback.print_exc()
                    response_data['pdf_generated'] = False
                    response_data['pdf_error'] = str(pdf_error)
            else:
                response_data['pdf_generated'] = False
                response_data['message'] = 'Suggestion accepted, but no accepted clauses found for PDF generation'

        return Response(response_data, status=status.HTTP_200_OK)

    except Exception as e:
        print(f'Accept suggestion error: {str(e)}')
        import traceback
        traceback.print_exc()
        return Response(
            {'message': 'Failed to accept suggestion', 'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def download_modified_contract_view(request, contract_id):
    """
    Generate and download the modified contract PDF with all accepted suggestions
    """
    try:
        from django.http import FileResponse
        from .utils import create_modified_pdf
        import mimetypes

        print(f'[DOWNLOAD_MODIFIED] Generating modified PDF for contract: {contract_id}')

        # Verify contract exists and belongs to user
        contract = Contract.objects.get(id=contract_id)
        if contract.user != request.user:
            return Response(
                {'message': 'Access denied'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Get all accepted clauses for this contract
        accepted_clauses = ClauseDeviation.objects.filter(
            risk_analysis__contract=contract,
            status='ACCEPTED'
        ).values('clause_name', 'description', 'accepted_text', 'suggested_text')

        if not accepted_clauses.exists():
            return Response(
                {'message': 'No accepted suggestions found for this contract'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Prepare clause changes for PDF generation
        clause_changes = []
        for clause in accepted_clauses:
            clause_changes.append({
                'clause_name': clause['clause_name'],
                'original_text': clause['description'],
                'accepted_text': clause['accepted_text'] or clause['suggested_text']
            })

        # Generate modified PDF
        modified_pdf_path = create_modified_pdf(
            original_pdf_path=contract.file_path,
            clause_changes=clause_changes,
            contract_name=contract.original_filename or contract.filename
        )

        # Return the file as a download
        pdf_file = open(modified_pdf_path, 'rb')
        response = FileResponse(pdf_file, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{os.path.basename(modified_pdf_path)}"'

        print(f'[DOWNLOAD_MODIFIED] Successfully generated and serving PDF: {modified_pdf_path}')

        return response

    except Contract.DoesNotExist:
        return Response(
            {'message': 'Contract not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        print(f'Download modified contract error: {str(e)}')
        import traceback
        traceback.print_exc()
        return Response(
            {'message': 'Failed to generate modified PDF', 'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def analyze_contract_risk_view(request, contract_id):
    """Perform risk analysis on a contract"""
    try:
        start_time = time.time()
        from .risk_analyzer import analyze_contract_risk, generate_executive_summary
        from core.serializers import ContractRiskAnalysisSerializer
        from django.utils import timezone

        print(f'[RISK_ANALYSIS] Starting risk analysis for contract: {contract_id}')

        # Verify contract exists and belongs to user
        contract = Contract.objects.get(id=contract_id)

        if contract.user != request.user:
            return Response(
                {'message': 'Access denied'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Check if contract has clauses extracted
        if not contract.clauses.exists():
            return Response({
                'message': 'No clauses found. Please extract clauses first.',
                'suggestion': 'Run clause extraction before risk analysis'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Perform risk analysis
        analysis_start = time.time()
        risk_analysis = analyze_contract_risk(contract_id)
        analysis_time = round(time.time() - analysis_start, 2)

        print(f'[RISK_ANALYSIS] Analysis complete. Risk Level: {risk_analysis.risk_level}, Score: {risk_analysis.risk_score}')

        serializer = ContractRiskAnalysisSerializer(risk_analysis)
        total_time = round(time.time() - start_time, 2)

        return Response({
            'message': 'Risk analysis completed successfully',
            'contractId': str(contract.id),
            'riskAnalysis': serializer.data,
            'timings': {
                'analysis': analysis_time,
                'total': total_time
            }
        })

    except Contract.DoesNotExist:
        return Response(
            {'message': 'Contract not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        print(f'Risk analysis error: {str(e)}')
        import traceback
        traceback.print_exc()
        return Response(
            {'message': 'Risk analysis failed', 'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_contract_risk_analysis(request, contract_id):
    """Get existing risk analysis for a contract"""
    try:
        from core.serializers import ContractRiskAnalysisSerializer
        from core.models import ContractRiskAnalysis

        # Verify contract exists and belongs to user
        contract = Contract.objects.get(id=contract_id)

        if contract.user != request.user:
            return Response(
                {'message': 'Access denied'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Get risk analysis
        try:
            risk_analysis = ContractRiskAnalysis.objects.get(contract=contract)
            serializer = ContractRiskAnalysisSerializer(risk_analysis)

            return Response({
                'message': 'Risk analysis retrieved',
                'contractId': str(contract.id),
                'riskAnalysis': serializer.data
            })
        except ContractRiskAnalysis.DoesNotExist:
            return Response({
                'message': 'No risk analysis found',
                'contractId': str(contract.id),
                'riskAnalysis': None
            })

    except Contract.DoesNotExist:
        return Response(
            {'message': 'Contract not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        print(f'Get risk analysis error: {str(e)}')
        return Response(
            {'message': 'Failed to retrieve risk analysis', 'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def explain_contract_risks(request, contract_id):
    """Generate LLM-based risk explanation for a contract"""
    try:
        start_time = time.time()
        from .risk_analyzer import explain_contract_risks as generate_risk_explanation

        print(f'[RISK_EXPLANATION] Starting LLM-based risk explanation for contract: {contract_id}')

        # Verify contract exists and belongs to user
        contract = Contract.objects.get(id=contract_id)

        if contract.user != request.user:
            return Response(
                {'message': 'Access denied'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Generate LLM-based risk explanation
        llm_start = time.time()
        result = generate_risk_explanation(contract_id)
        llm_time = round(time.time() - llm_start, 2)

        print(f'[RISK_EXPLANATION] Explanation generated successfully')

        total_time = round(time.time() - start_time, 2)
        result['timings'] = {
            'llm_generation': llm_time,
            'total': total_time
        }

        return Response({
            'message': 'Risk explanation generated successfully',
            'data': result
        })

    except Contract.DoesNotExist:
        return Response(
            {'message': 'Contract not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        print(f'Risk explanation error: {str(e)}')
        import traceback
        traceback.print_exc()
        return Response(
            {'message': 'Risk explanation failed', 'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def get_keyword_sentences(request, contract_id):
    """Get complete sentences containing a specific keyword from a contract"""
    try:
        keyword = request.data.get('keyword', '').strip()

        if not keyword:
            return Response(
                {'error': 'Keyword is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Verify contract exists and belongs to user
        contract = Contract.objects.get(id=contract_id)

        if contract.user != request.user:
            return Response(
                {'error': 'Access denied'},
                status=status.HTTP_403_FORBIDDEN
            )

        if not contract.full_text:
            return Response(
                {'error': 'Contract has no text'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Extract sentences containing the keyword
        sentences = extract_keyword_contexts(contract.full_text, keyword, max_sentences=10)

        return Response({
            'message': 'Sentences retrieved successfully',
            'keyword': keyword,
            'count': len(sentences),
            'sentences': sentences
        })

    except Contract.DoesNotExist:
        return Response(
            {'error': 'Contract not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        print(f'Keyword sentence extraction error: {str(e)}')
        import traceback
        traceback.print_exc()
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_executive_summary_view(request, contract_id):
    """Generate executive summary for a contract on demand"""
    try:
        from .risk_analyzer import generate_executive_summary, analyze_contract_risk
        from core.serializers import ContractRiskAnalysisSerializer
        from django.utils import timezone

        print(f'[EXECUTIVE_SUMMARY] Starting summary generation for contract: {contract_id}')

        # Verify contract exists and belongs to user
        contract = Contract.objects.get(id=contract_id)

        if contract.user != request.user:
            return Response(
                {'message': 'Access denied'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Check if clauses have been extracted
        from core.models import Clause
        from .utils import extract_clauses
        clauses = Clause.objects.filter(contract=contract)

        if not clauses.exists():
            # Extract clauses first
            print(f'[EXECUTIVE_SUMMARY] Extracting clauses first...')
            extracted_clauses_data = extract_clauses(contract.full_text)
            print(f'[EXECUTIVE_SUMMARY] Clauses extracted: {len(extracted_clauses_data)} total')

            # Save clauses to database
            for clause_data in extracted_clauses_data:
                try:
                    extracted_text = clause_data.get('clauseText', '')
                    if not extracted_text and clause_data.get('contextSentences'):
                        extracted_text = clause_data['contextSentences'][0].get('text', '')

                    Clause.objects.create(
                        contract=contract,
                        clause_name=clause_data.get('clauseName'),
                        found=clause_data.get('found', False),
                        confidence=clause_data.get('confidence'),
                        match_count=clause_data.get('matchCount'),
                        text_spans=json.dumps(clause_data.get('textSpans', [])),
                        context_sentences=json.dumps(clause_data.get('contextSentences', [])),
                        extracted_text=extracted_text
                    )
                except Exception as e:
                    print(f'Error saving clause: {str(e)}')

            print(f'[EXECUTIVE_SUMMARY] Clauses saved successfully')

        # Get or create risk analysis
        risk_analysis = ContractRiskAnalysis.objects.filter(contract=contract).first()

        if not risk_analysis:
            # Run risk analysis if it doesn't exist
            print(f'[EXECUTIVE_SUMMARY] Running risk analysis...')
            risk_analysis = analyze_contract_risk(contract_id)

        # Generate executive summary
        summary = generate_executive_summary(contract, risk_analysis)
        risk_analysis.executive_summary = summary
        risk_analysis.summary_generated_at = timezone.now()
        risk_analysis.save()

        print(f'[EXECUTIVE_SUMMARY] Executive summary generated successfully')

        serializer = ContractRiskAnalysisSerializer(risk_analysis)

        return Response({
            'message': 'Executive summary generated successfully',
            'contractId': str(contract.id),
            'executiveSummary': summary,
            'riskAnalysis': serializer.data
        })

    except Contract.DoesNotExist:
        return Response(
            {'message': 'Contract not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        print(f'Executive summary generation error: {str(e)}')
        import traceback
        traceback.print_exc()
        return Response(
            {'message': 'Executive summary generation failed', 'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_obligations_view(request, contract_id):
    """Generate contractual obligations for a contract on demand"""
    try:
        from .obligation_extractor import generate_obligations
        from core.serializers import ContractObligationSerializer

        print(f'[OBLIGATIONS] Starting obligation generation for contract: {contract_id}')

        # Verify contract exists and belongs to user
        contract = Contract.objects.get(id=contract_id)

        if contract.user != request.user:
            return Response(
                {'message': 'Access denied'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Generate obligations using LLM
        print(f'[OBLIGATIONS] Extracting obligations from contract text...')
        obligations_data = generate_obligations(contract)

        print(f'[OBLIGATIONS] Extracted {len(obligations_data)} obligations')

        # Delete existing obligations for this contract
        ContractObligation.objects.filter(contract=contract).delete()

        # Create new obligations
        created_obligations = []
        for obl_data in obligations_data:
            obligation = ContractObligation.objects.create(
                contract=contract,
                title=obl_data['title'],
                description=obl_data['description'],
                full_text=obl_data.get('full_text', obl_data['description']),
                category=obl_data['category'],
                responsible_party=obl_data['responsible_party'],
                priority=obl_data['priority'],
                due_date_text=obl_data.get('due_date_text'),
                clause_reference=obl_data.get('clause_reference'),
            )
            created_obligations.append(obligation)

        print(f'[OBLIGATIONS] Successfully saved {len(created_obligations)} obligations')

        serializer = ContractObligationSerializer(created_obligations, many=True)

        return Response({
            'message': 'Obligations generated successfully',
            'contractId': str(contract.id),
            'count': len(created_obligations),
            'obligations': serializer.data
        })

    except Contract.DoesNotExist:
        return Response(
            {'message': 'Contract not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        print(f'Obligation generation error: {str(e)}')
        import traceback
        traceback.print_exc()
        return Response(
            {'message': 'Obligation generation failed', 'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_obligation_status(request, obligation_id):
    """Update completion status of an obligation"""
    try:
        from core.serializers import ContractObligationSerializer
        from django.utils import timezone

        # Get obligation and verify access via contract ownership
        obligation = ContractObligation.objects.select_related('contract').get(id=obligation_id)

        if obligation.contract.user != request.user:
            return Response(
                {'message': 'Access denied'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Update fields
        is_completed = request.data.get('is_completed', obligation.is_completed)
        completion_notes = request.data.get('completion_notes', obligation.completion_notes)

        obligation.is_completed = is_completed
        obligation.completion_notes = completion_notes

        if is_completed and not obligation.completed_at:
            obligation.completed_at = timezone.now()
        elif not is_completed:
            obligation.completed_at = None

        obligation.save()

        serializer = ContractObligationSerializer(obligation)

        return Response({
            'message': 'Obligation updated successfully',
            'obligation': serializer.data
        })

    except ContractObligation.DoesNotExist:
        return Response(
            {'message': 'Obligation not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        print(f'Obligation update error: {str(e)}')
        return Response(
            {'message': 'Obligation update failed', 'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_contract_obligations(request, contract_id):
    """Get all obligations for a specific contract"""
    try:
        from core.serializers import ContractObligationSerializer

        # Verify contract exists and belongs to user
        contract = Contract.objects.get(id=contract_id)

        if contract.user != request.user:
            return Response(
                {'message': 'Access denied'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Get all obligations for this contract
        obligations = ContractObligation.objects.filter(contract=contract).order_by('-created_at')

        serializer = ContractObligationSerializer(obligations, many=True)

        return Response({
            'contractId': str(contract.id),
            'count': obligations.count(),
            'obligations': serializer.data
        })

    except Contract.DoesNotExist:
        return Response(
            {'message': 'Contract not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        print(f'Get obligations error: {str(e)}')
        return Response(
            {'message': 'Failed to retrieve obligations', 'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_contract_versions(request, contract_id):
    """Get version history for a specific contract"""
    try:
        # Verify contract exists and belongs to user
        contract = Contract.objects.get(id=contract_id)

        if contract.user != request.user:
            return Response(
                {'message': 'Access denied'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Get all versions for this contract
        versions = ContractVersion.objects.filter(contract=contract).order_by('-version_number')

        serializer = ContractVersionSerializer(versions, many=True)

        return Response({
            'contractId': str(contract.id),
            'currentVersion': versions.first().version_number if versions.exists() else 0,
            'totalVersions': versions.count(),
            'versions': serializer.data
        })

    except Contract.DoesNotExist:
        return Response(
            {'message': 'Contract not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        print(f'Get versions error: {str(e)}')
        return Response(
            {'message': 'Failed to retrieve version history', 'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_contract_version(request, contract_id):
    """
    Upload a new version of an existing contract

    POST /contracts/{contract_id}/versions/upload

    Accepts: multipart/form-data with 'file' and optional 'changeDescription'

    Creates a new version snapshot and triggers intent drift detection
    """
    try:
        import time
        from .utils import extract_text_from_file

        start_time = time.time()

        # Verify contract exists and belongs to user
        contract = Contract.objects.get(id=contract_id)

        if contract.user != request.user:
            return Response(
                {'message': 'Access denied'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Validate file upload
        if 'file' not in request.FILES:
            return Response(
                {'message': 'No file provided'},
                status=status.HTTP_400_BAD_REQUEST
            )

        file = request.FILES['file']
        change_description = request.data.get('changeDescription', 'Version update')

        print(f'[VERSION UPLOAD] Contract {contract_id}, File: {file.name}')

        # Validate file type
        ext = os.path.splitext(file.name)[1].lower()
        allowed_extensions = ['.docx', '.pdf', '.png', '.jpg', '.jpeg']

        if ext not in allowed_extensions:
            return Response(
                {'message': 'Unsupported file type. Allowed: DOCX, PDF, PNG, JPG, JPEG'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate file size
        if file.size > settings.MAX_UPLOAD_SIZE:
            return Response(
                {'message': 'File exceeds 25MB limit'},
                status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
            )

        # Save uploaded file
        filename = f"{int(datetime.now().timestamp() * 1000)}-{file.name.replace(' ', '_')}"
        file_path = os.path.join(settings.MEDIA_ROOT, filename)
        os.makedirs(settings.MEDIA_ROOT, exist_ok=True)

        with open(file_path, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)

        print(f'[VERSION UPLOAD] File saved: {filename}')

        # Extract text from file
        result = extract_text_from_file(file_path, ext)
        extracted_text = result.get('text', '')
        ocr_performed = result.get('ocr_performed', False)

        if not extracted_text or len(extracted_text.strip()) < 5:
            # Clean up uploaded file
            if os.path.exists(file_path):
                os.remove(file_path)

            error_message = 'Unable to extract text from file'
            if ext in ['.png', '.jpg', '.jpeg']:
                error_message = 'OCR processing failed'

            return Response({
                'message': error_message,
                'suggestion': 'Please ensure PaddleOCR is installed or provide a document with extractable text'
            }, status=status.HTTP_400_BAD_REQUEST)

        print(f'[VERSION UPLOAD] Extracted {len(extracted_text)} characters')

        # Extract metadata
        metadata = extract_contract_metadata(extracted_text)
        if not metadata:
            metadata = {
                "party_a": None,
                "party_b": None,
                "start_date": None,
                "end_date": None,
                "contract_value": None,
                "contract_type": None,
                "jurisdiction": None,
                "payment_terms": None,
                "liability_level": None,
            }

        # Update contract with new version data
        contract.filename = filename
        contract.original_filename = file.name
        contract.file_type = ext.replace('.', '').upper()
        contract.file_path = file_path
        contract.full_text = extracted_text
        contract.ocr_performed = ocr_performed

        # Update metadata if available
        if metadata.get('contract_type'):
            contract.contract_type = metadata['contract_type']
        if metadata.get('contract_value'):
            contract.contract_value = metadata['contract_value']
        if metadata.get('party_a'):
            contract.party_a = metadata['party_a']
        if metadata.get('party_b'):
            contract.party_b = metadata['party_b']
        if metadata.get('start_date'):
            contract.start_date = metadata['start_date']
        if metadata.get('end_date'):
            contract.end_date = metadata['end_date']
        if metadata.get('jurisdiction'):
            contract.jurisdiction = metadata['jurisdiction']
        if metadata.get('payment_terms'):
            contract.payment_terms = metadata['payment_terms']
        if metadata.get('liability_level'):
            contract.liability_level = metadata['liability_level']

        # Update party_name and contract_duration
        party_a = metadata.get('party_a') or contract.party_a
        party_b = metadata.get('party_b') or contract.party_b
        if party_a and party_b:
            contract.party_name = f"{party_a} vs {party_b}"
        elif party_a or party_b:
            contract.party_name = party_a or party_b

        start_date = metadata.get('start_date') or contract.start_date
        end_date = metadata.get('end_date') or contract.end_date
        if start_date and end_date:
            contract.contract_duration = f"{start_date} to {end_date}"

        contract.save()
        print(f'[VERSION UPLOAD] Contract updated')

        # Create version snapshot (this will auto-trigger drift detection)
        version = create_contract_version_snapshot(
            contract,
            request.user,
            change_description
        )

        print(f'[VERSION UPLOAD] Created version {version.version_number}')

        # Get all versions for response
        all_versions = ContractVersion.objects.filter(contract=contract).order_by('-version_number')

        # Run automated analysis in background (clauses, intents, etc.)
        import threading
        import json

        def run_automated_analysis():
            try:
                from .utils import extract_clauses, mine_contract_intents

                print(f"[VERSION AUTO-ANALYSIS] Starting for version {version.version_number}...")

                # Extract clauses
                extracted_clauses_data = extract_clauses(contract.full_text)
                print(f"[VERSION AUTO-ANALYSIS] Found {len(extracted_clauses_data)} clause templates")

                # Clear old clauses and save new ones
                Clause.objects.filter(contract=contract).delete()
                saved_count = 0
                for clause_data in extracted_clauses_data:
                    try:
                        extracted_text = clause_data.get('clauseText', '')
                        if not extracted_text and clause_data.get('contextSentences'):
                            extracted_text = clause_data['contextSentences'][0].get('text', '')

                        Clause.objects.create(
                            contract=contract,
                            clause_name=clause_data.get('clauseName'),
                            found=clause_data.get('found', False),
                            confidence=clause_data.get('confidence'),
                            match_count=clause_data.get('matchCount'),
                            text_spans=json.dumps(clause_data.get('textSpans', [])),
                            context_sentences=json.dumps(clause_data.get('contextSentences', [])),
                            extracted_text=extracted_text
                        )
                        if clause_data.get('found', False):
                            saved_count += 1
                    except Exception as e:
                        print(f"[VERSION AUTO-ANALYSIS] Clause save error: {str(e)}")

                print(f"[VERSION AUTO-ANALYSIS] Saved {saved_count} clauses")

                # Mine intents
                print(f"[VERSION AUTO-ANALYSIS] Mining intents...")
                intent_result = mine_contract_intents(str(contract.id), str(version.id))
                if intent_result.get('success'):
                    print(f"[VERSION AUTO-ANALYSIS] Intent mining completed successfully")
                else:
                    print(f"[VERSION AUTO-ANALYSIS] Intent mining failed: {intent_result.get('error')}")

                print(f"[VERSION AUTO-ANALYSIS] Analysis complete for version {version.version_number}")

            except Exception as e:
                print(f"[VERSION AUTO-ANALYSIS] Error: {str(e)}")
                import traceback
                traceback.print_exc()

        # Start background analysis
        analysis_thread = threading.Thread(target=run_automated_analysis)
        analysis_thread.daemon = True
        analysis_thread.start()

        elapsed_time = round(time.time() - start_time, 2)

        return Response({
            'message': 'New contract version uploaded successfully',
            'contract': {
                'id': str(contract.id),
                'originalFilename': contract.original_filename,
                'contractType': contract.contract_type,
            },
            'version': {
                'id': str(version.id),
                'versionNumber': version.version_number,
                'changeDescription': version.change_description,
                'createdAt': version.created_at.isoformat() if version.created_at else None,
            },
            'versionHistory': {
                'totalVersions': all_versions.count(),
                'currentVersion': version.version_number,
            },
            'processingTime': elapsed_time
        }, status=status.HTTP_201_CREATED)

    except Contract.DoesNotExist:
        return Response(
            {'message': 'Contract not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        print(f'[VERSION UPLOAD ERROR] {str(e)}')
        import traceback
        traceback.print_exc()

        # Clean up file if it was saved
        try:
            if 'file_path' in locals() and os.path.exists(file_path):
                os.remove(file_path)
        except:
            pass

        return Response(
            {'message': 'Failed to upload contract version', 'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def search_contracts(request):
    """
    AI-Enhanced Contract Search
    Search contracts by multiple criteria with AI assistance
    """
    try:
        user = request.user

        # Get search parameters
        query = request.GET.get('q', '').strip()
        vendor = request.GET.get('vendor', '').strip()
        date_from = request.GET.get('date_from', '')
        date_to = request.GET.get('date_to', '')
        risk_level = request.GET.get('risk_level', '')
        contract_type = request.GET.get('contract_type', '')
        has_analysis = request.GET.get('has_analysis', '')

        # New search parameters
        jurisdiction = request.GET.get('jurisdiction', '').strip()
        payment_terms = request.GET.get('payment_terms', '').strip()
        liability_level = request.GET.get('liability_level', '').strip()
        has_arbitration = request.GET.get('has_arbitration', '').strip()

        # Start with all user's contracts
        contracts = Contract.objects.filter(user=user)

        # Apply filters
        if query:
            # Search in contract name, vendor, and full text
            from django.db.models import Q
            contracts = contracts.filter(
                Q(original_filename__icontains=query) |
                Q(party_a__icontains=query) |
                Q(party_b__icontains=query) |
                Q(contract_type__icontains=query) |
                Q(jurisdiction__icontains=query) |
                Q(payment_terms__icontains=query) |
                Q(liability_level__icontains=query) |
                Q(full_text__icontains=query)
            )

        if vendor:
            contracts = contracts.filter(
                Q(party_a__icontains=vendor) |
                Q(party_b__icontains=vendor)
            )

        if contract_type:
            contracts = contracts.filter(contract_type__icontains=contract_type)

        # New filters
        if jurisdiction:
            contracts = contracts.filter(jurisdiction__icontains=jurisdiction)

        if payment_terms:
            contracts = contracts.filter(payment_terms__icontains=payment_terms)

        if liability_level:
            contracts = contracts.filter(liability_level__iexact=liability_level)

        if has_arbitration:
            # Convert string to boolean
            has_arb_bool = has_arbitration.lower() in ['true', '1', 'yes']
            contracts = contracts.filter(has_arbitration=has_arb_bool)

        if date_from:
            contracts = contracts.filter(uploaded_at__gte=date_from)

        if date_to:
            contracts = contracts.filter(uploaded_at__lte=date_to)

        if risk_level:
            # Filter by risk level from risk analysis
            risk_analysis_ids = ContractRiskAnalysis.objects.filter(
                risk_level__iexact=risk_level
            ).values_list('contract_id', flat=True)
            contracts = contracts.filter(id__in=risk_analysis_ids)

        if has_analysis == 'true':
            # Filter contracts that have risk analysis
            analyzed_ids = ContractRiskAnalysis.objects.values_list('contract_id', flat=True)
            contracts = contracts.filter(id__in=analyzed_ids)
        elif has_analysis == 'false':
            # Filter contracts without risk analysis
            analyzed_ids = ContractRiskAnalysis.objects.values_list('contract_id', flat=True)
            contracts = contracts.exclude(id__in=analyzed_ids)

        # Order by most recent first
        contracts = contracts.order_by('-uploaded_at')

        # Serialize results
        serializer = ContractSerializer(contracts, many=True)

        return Response({
            'count': contracts.count(),
            'contracts': serializer.data,
            'filters_applied': {
                'query': query,
                'vendor': vendor,
                'date_from': date_from,
                'date_to': date_to,
                'risk_level': risk_level,
                'contract_type': contract_type,
                'has_analysis': has_analysis
            }
        })

    except Exception as e:
        print(f'Search error: {str(e)}')
        import traceback
        traceback.print_exc()
        return Response(
            {'message': 'Search failed', 'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])  # Temporarily disabled for development
def get_dashboard_stats(request):
    """Get dashboard statistics for the current user"""
    try:
        # Get user from token if provided, otherwise use admin@example.com for development
        try:
            user = request.user if request.user.is_authenticated else None
            if not user:
                user = User.objects.filter(email='admin@example.com').first() or User.objects.first()
        except:
            user = User.objects.filter(email='admin@example.com').first() or User.objects.first()

        from django.db.models import Max, Avg
        from core.models import Clause

        # Deduplicate by filename (same logic as list_contracts)
        latest_contracts = Contract.objects.filter(
            user=user
        ).values('original_filename').annotate(
            latest_upload=Max('uploaded_at')
        )

        valid_contract_ids = []
        for item in latest_contracts:
            contract = Contract.objects.filter(
                user=user,
                original_filename=item['original_filename'],
                uploaded_at=item['latest_upload']
            ).first()
            if contract and Clause.objects.filter(contract=contract).exists():
                valid_contract_ids.append(contract.id)

        valid_contracts = Contract.objects.filter(id__in=valid_contract_ids)

        total_contracts = len(valid_contract_ids)

        # Analysis complete - contracts that have clauses with found=True
        analysis_complete = valid_contracts.filter(
            clauses__found=True
        ).distinct().count()

        # Pending review - valid contracts without found clauses
        pending_review = total_contracts - analysis_complete

        # Risk score average
        avg_confidence = valid_contracts.filter(
            confidence_score__isnull=False
        ).aggregate(avg_conf=Avg('confidence_score'))['avg_conf'] or 0

        return Response({
            'totalContracts': total_contracts,
            'analysisComplete': analysis_complete,
            'pendingReview': pending_review,
            'riskScoreAvg': round(avg_confidence, 1)
        })

    except Exception as e:
        print(f'Dashboard stats error: {str(e)}')
        return Response(
            {'message': 'Failed to retrieve dashboard stats', 'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def generate_token_with_data(user_id, email):
    """Generate JWT token with user data (without fetching from database)"""
    from datetime import datetime, timedelta, timezone
    import jwt
    from django.conf import settings

    payload = {
        'id': user_id,
        'email': email,
        'exp': datetime.now(timezone.utc) + timedelta(hours=settings.JWT_EXPIRATION_HOURS),
        'iat': datetime.now(timezone.utc),
    }
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return token



# ============================================
# RAG ENDPOINTS - Contract Generation with AI
# ============================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def rag_upload_files(request):
    """Upload files for RAG processing and index them in vector database"""
    try:
        from api.contract_rag_service import ContractRAGService
        import tempfile
        import uuid as uuid_lib

        files = request.FILES.getlist('files')

        if not files:
            return Response(
                {'error': 'No files provided'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if len(files) > 5:
            return Response(
                {'error': 'Maximum 5 files allowed'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Save files temporarily for processing
        temp_dir = tempfile.mkdtemp()
        saved_file_paths = []

        try:
            for file in files:
                # Create unique filename
                file_ext = os.path.splitext(file.name)[1]
                unique_filename = f"{uuid_lib.uuid4()}{file_ext}"
                file_path = os.path.join(temp_dir, unique_filename)

                # Save file
                with open(file_path, 'wb+') as destination:
                    for chunk in file.chunks():
                        destination.write(chunk)

                saved_file_paths.append(file_path)

            # Index files using RAG service
            rag_service = ContractRAGService()
            user_id = str(request.user.id) if request.user.is_authenticated else None

            result = rag_service.index_contracts(saved_file_paths, user_id=user_id)

            # Also save to permanent storage for reference
            upload_dir = os.path.join(settings.BASE_DIR, 'uploaded_contracts')
            os.makedirs(upload_dir, exist_ok=True)

            for i, file in enumerate(files):
                permanent_path = os.path.join(upload_dir, f"{user_id}_{file.name}")
                with open(permanent_path, 'wb+') as destination:
                    file.seek(0)  # Reset file pointer
                    for chunk in file.chunks():
                        destination.write(chunk)

            # Clean up temp files
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)

            if result.get('success'):
                return Response({
                    'message': 'Files uploaded and indexed successfully',
                    'files_indexed': result.get('files_indexed'),
                    'chunks_created': result.get('chunks_created'),
                    'filenames': result.get('filenames'),
                    'collection_stats': rag_service.get_collection_stats()
                })
            else:
                return Response({
                    'error': result.get('error', 'Unknown error during indexing')
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            # Clean up temp files on error
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
            raise e

    except Exception as e:
        print(f'RAG upload error: {str(e)}')
        import traceback
        traceback.print_exc()
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def rag_upload_extract(request):
    """Upload a single reference contract and extract its text"""
    try:
        file = request.FILES.get('file')

        if not file:
            return Response(
                {'error': 'No file provided'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Extract file extension
        import os
        file_ext = os.path.splitext(file.name)[1].lower()

        # Save file temporarily to extract text
        temp_file_path = os.path.join(tempfile.gettempdir(), file.name)
        with open(temp_file_path, 'wb') as temp_file:
            for chunk in file.chunks():
                temp_file.write(chunk)

        # Extract text from the uploaded file
        # extract_text_from_file returns a dict with 'text', 'pages', 'ocr_performed' keys
        extraction_result = extract_text_from_file(temp_file_path, file_ext)

        # Clean up temp file
        try:
            os.remove(temp_file_path)
        except:
            pass

        # Get the actual text from the result dictionary
        extracted_text = extraction_result.get('text', '')

        if not extracted_text or not extracted_text.strip():
            error_msg = extraction_result.get('error', 'Could not extract text from file')
            return Response(
                {'error': error_msg},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response({
            'message': 'Text extracted successfully',
            'filename': file.name,
            'extracted_text': extracted_text,
            'character_count': len(extracted_text),
            'pages': extraction_result.get('pages'),
            'ocr_performed': extraction_result.get('ocr_performed', False)
        })

    except Exception as e:
        print(f'RAG extract error: {str(e)}')
        import traceback
        traceback.print_exc()
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def rag_ingest(request):
    """Process uploaded files and store in Qdrant vector database"""
    try:
        from ingest_contracts import ingest_folder
        
        upload_dir = os.path.join(settings.BASE_DIR, 'uploaded_contracts')
        
        if not os.path.exists(upload_dir):
            return Response(
                {'error': 'No files to ingest. Please upload files first.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Ingest all files in the directory
        vector_count = ingest_folder(upload_dir)
        
        return Response({
            'status': 'success',
            'message': f'Processed and indexed {vector_count} text chunks',
            'vectors_upserted': vector_count
        })
        
    except Exception as e:
        print(f'RAG ingest error: {str(e)}')
        import traceback
        traceback.print_exc()
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def rag_qa(request):
    """Question answering based on uploaded contracts"""
    try:
        query = request.data.get('query', '').strip()
        contract_id = request.data.get('contractId', '').strip()

        if not query:
            return Response(
                {'error': 'Query is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Try Qdrant RAG first; fall back to direct contract text if collection missing
        answer = None
        contexts = []

        try:
            from rag import qa_flow
            user_id = str(request.user.id)
            result = qa_flow(query, user_id=user_id)
            ollama_response = result.get('ollama', {})
            answer = ollama_response.get('response', '').strip()
            contexts = result.get('contexts', [])
        except Exception as rag_err:
            print(f'[RAG] Qdrant flow failed ({rag_err}), falling back to direct contract text')

        # Fallback: answer directly from contract full_text stored in MySQL
        if not answer and contract_id:
            try:
                import requests as req
                from django.conf import settings
                contract = Contract.objects.filter(id=contract_id, user=request.user).first()
                if contract and contract.full_text:
                    # Truncate to ~3000 chars to keep prompt manageable
                    text_snippet = contract.full_text[:3000]
                    prompt = (
                        f"You are a legal contract analyst. Answer the question based only on the contract text below.\n\n"
                        f"Contract: {contract.original_filename}\n\n"
                        f"---\n{text_snippet}\n---\n\n"
                        f"Question: {query}\n\n"
                        f"Answer concisely based on the contract text:"
                    )
                    ollama_url = getattr(settings, 'OLLAMA_BASE_URL', 'http://localhost:11434')
                    resp = req.post(
                        f"{ollama_url}/api/generate",
                        json={"model": getattr(settings, 'OLLAMA_MODEL', 'qwen2.5:0.5b'), "prompt": prompt, "stream": False},
                        timeout=45
                    )
                    if resp.status_code == 200:
                        answer = resp.json().get('response', '').strip()
            except Exception as fallback_err:
                print(f'[RAG] Direct fallback failed: {fallback_err}')

        if not answer:
            answer = "Unable to answer at this time. Please ensure contracts have been analyzed and try again."

        return Response({
            'query': query,
            'answer': answer,
            'contexts': contexts,
        })

    except Exception as e:
        print(f'RAG Q&A error: {str(e)}')
        import traceback
        traceback.print_exc()
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def rag_generate(request):
    """Modify extracted contract text based on user instructions using LLM"""
    try:
        import requests
        import re

        # Get instruction and handle type safely
        instruction = request.data.get('instruction', '')
        if isinstance(instruction, str):
            instruction = instruction.strip()
        else:
            instruction = str(instruction).strip() if instruction else ''

        # Get extracted_text and handle type safely
        extracted_text = request.data.get('extracted_text', '')
        if isinstance(extracted_text, str):
            extracted_text = extracted_text.strip()
        else:
            # If it's not a string, convert to string
            extracted_text = str(extracted_text).strip() if extracted_text else ''

        if not instruction:
            return Response(
                {'error': 'Modification instructions are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not extracted_text:
            return Response(
                {'error': 'Extracted contract text is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # SIMPLE FIND-REPLACE DETECTION - Bypass LLM for simple replacements!
        # Pattern: "Replace X with Y" or "Change X to Y"
        replace_patterns = [
            r'replace\s+(?:the\s+text\s+)?["\']?(.+?)["\']?\s+with\s+["\']?(.+?)["\']?(?:\s|$|\.|,)',
            r'change\s+(?:the\s+text\s+)?["\']?(.+?)["\']?\s+to\s+["\']?(.+?)["\']?(?:\s|$|\.|,)',
            r'swap\s+(?:the\s+text\s+)?["\']?(.+?)["\']?\s+with\s+["\']?(.+?)["\']?(?:\s|$|\.|,)',
        ]

        import re
        for pattern in replace_patterns:
            match = re.search(pattern, instruction, re.IGNORECASE)
            if match:
                old_text = match.group(1).strip()
                new_text = match.group(2).strip()

                print(f'[SIMPLE REPLACE] Detected find-replace operation')
                print(f'[SIMPLE REPLACE] Find: "{old_text}"')
                print(f'[SIMPLE REPLACE] Replace with: "{new_text}"')

                # Do simple string replacement (plain version)
                modified_contract = extracted_text.replace(old_text, new_text)

                # Also try case-insensitive replacement
                if modified_contract == extracted_text:
                    # Case-insensitive replace
                    import re
                    pattern_escaped = re.escape(old_text)
                    modified_contract = re.sub(pattern_escaped, new_text, extracted_text, flags=re.IGNORECASE)

                # Create highlighted version with <mark> tags around changed text
                highlighted_contract = extracted_text.replace(old_text, f'<mark class="contract-change">{new_text}</mark>')
                if highlighted_contract == extracted_text:
                    # Case-insensitive highlight
                    pattern_escaped = re.escape(old_text)
                    highlighted_contract = re.sub(
                        pattern_escaped,
                        f'<mark class="contract-change">{new_text}</mark>',
                        extracted_text,
                        flags=re.IGNORECASE
                    )

                replacements_made = extracted_text.count(old_text)
                if replacements_made == 0:
                    # Try case-insensitive count
                    import re
                    replacements_made = len(re.findall(re.escape(old_text), extracted_text, re.IGNORECASE))

                print(f'[SIMPLE REPLACE] Made {replacements_made} replacement(s)')

                # ONLY use simple replace if we actually found and replaced something
                # If no replacements were made, fall through to LLM processing below
                if replacements_made > 0:
                    # Build changes array for detailed tracking
                    changes = [{
                        'old_text': old_text,
                        'new_text': new_text,
                        'count': replacements_made
                    }]

                    return Response({
                        'modified_contract': modified_contract,
                        'highlighted_contract': highlighted_contract,  # NEW: With <mark> tags for highlighting
                        'original_length': len(extracted_text),
                        'modified_length': len(modified_contract),
                        'model_used': 'simple_replace',
                        'replacements_made': replacements_made,
                        'changes': changes,  # NEW: Detailed changes array
                        'changes_description': f'Replaced "{old_text}" with "{new_text}" ({replacements_made} occurrence(s))'
                    })
                else:
                    print(f'[SIMPLE REPLACE] No matches found for "{old_text}", falling back to LLM')
                    # Don't return, continue to LLM processing below
                    break

        # Only truncate extremely large texts (> 120,000 chars) to prevent timeout
        max_text_length = 120000
        original_full_text = extracted_text
        was_truncated = False

        if len(extracted_text) > max_text_length:
            print(f'[WARN] Extracted text is {len(extracted_text)} chars, truncating to {max_text_length}')
            extracted_text = extracted_text[:max_text_length]
            was_truncated = True

        # Enhanced prompt with better instructions to prevent summarization and repetition
        prompt = f"""<|im_start|>system
You are a precision legal document editor. Your SOLE task is to apply the exact modifications requested by the user while preserving the complete original contract.

STRICT REQUIREMENTS:
1. Output the COMPLETE contract with EVERY sentence, clause, and section preserved
2. Make ONLY the specific changes mentioned in the user's instruction
3. DO NOT summarize, condense, or shorten any part of the contract
4. DO NOT add explanations, comments, or change summaries
5. DO NOT repeat any sections or paragraphs
6. Maintain exact formatting, structure, and legal language
7. The output length should be within 10% of the original length ({len(extracted_text)} characters)

VERIFICATION CHECKLIST BEFORE RESPONDING:
- Have I included ALL sections from the original contract?
- Have I made ONLY the requested changes?
- Is my output approximately {len(extracted_text)} characters long?
- Have I avoided any repetition of text?
- Have I avoided adding any explanatory text?
<|im_end|>

<|im_start|>user
MODIFICATION REQUEST: {instruction}

ORIGINAL CONTRACT (Length: {len(extracted_text)} characters):
---START OF CONTRACT---
{extracted_text}
---END OF CONTRACT---

Output ONLY the modified contract below. No explanations, no summaries, just the complete modified contract:
<|im_end|>

<|im_start|>assistant
"""

        def call_ollama_model(model_name, prompt_text, timeout=900):
            """Helper function to call Ollama API"""
            try:
                print(f'[INFO] Calling model: {model_name}')
                print(f'[INFO] Timeout set to: {timeout}s')
                response = requests.post(
                    os.getenv("OLLAMA_BASE_URL", "http://localhost:11434") + "/api/generate",
                    json={
                        'model': model_name,
                        'prompt': prompt_text,
                        'stream': False,
                        'options': {
                            'temperature': 0.1,  # Very low temperature for consistency
                            'top_p': 0.85,
                            'top_k': 40,
                            'repeat_penalty': 1.2,  # Prevent repetition
                            'num_predict': int(len(extracted_text) * 1.5),  # Predict slightly more than input
                            'num_ctx': 8192,  # Large context window
                        }
                    },
                    timeout=timeout
                )
                print(f'[INFO] Model {model_name} responded with status code: {response.status_code}')
                return response
            except requests.exceptions.Timeout:
                print(f'[ERROR] Model {model_name} timed out after {timeout}s')
                return None
            except requests.exceptions.ConnectionError:
                print(f'[ERROR] Cannot connect to Ollama - is it running?')
                return None
            except Exception as e:
                print(f'[ERROR] Model {model_name} failed: {str(e)}')
                import traceback
                traceback.print_exc()
                return None

        # Try models in order of capability (best to worst)
        # Use latest and most capable models first
        model_priority = [
            'qwen2.5:7b',           # Qwen 2.5 7B - excellent for text editing (PRIMARY)
            'mistral:latest',       # Mistral latest (available locally)
            'qwen2.5:0.5b',         # Qwen 2.5 0.5B (fast, available locally)
            'llama3.3:latest',      # Latest Llama 3.3 (70B)
            'qwen2.5:14b',          # Qwen 2.5 14B
            'llama3.1:latest',      # Llama 3.1
            'qwen2.5:latest',       # Any Qwen 2.5
        ]

        print(f'[INFO] Starting contract modification')
        print(f'[INFO] Original contract length: {len(extracted_text)} chars')
        print(f'[INFO] Instruction: {instruction[:200]}...')

        ollama_response = None
        model_to_use = None

        for model_name in model_priority:
            ollama_response = call_ollama_model(model_name, prompt, timeout=900)

            if ollama_response and ollama_response.status_code == 200:
                model_to_use = model_name
                print(f'[SUCCESS] Model {model_name} responded successfully')
                break
            else:
                print(f'[WARN] Model {model_name} not available, trying next model...')

        if not ollama_response or ollama_response.status_code != 200:
            return Response(
                {'error': 'No suitable AI models available. Please run: ollama pull llama3.3 or ollama pull qwen2.5:14b'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        ollama_data = ollama_response.json()
        modified_contract = ollama_data.get('response', '').strip()

        # Post-processing: Remove any metadata or explanations the model might have added
        # Remove common AI response patterns
        modified_contract = re.sub(r'^(Here is|Here\'s|I have|I\'ve).*?:\s*', '', modified_contract, flags=re.IGNORECASE)
        modified_contract = re.sub(r'^Modified [Cc]ontract:?\s*', '', modified_contract)
        modified_contract = re.sub(r'\n+---+\s*CHANGES APPLIED.*$', '', modified_contract, flags=re.DOTALL)
        modified_contract = re.sub(r'\n+---+\s*Summary.*$', '', modified_contract, flags=re.DOTALL)

        # Remove assistant tags if present
        modified_contract = re.sub(r'<\|im_end\|>.*$', '', modified_contract, flags=re.DOTALL)
        modified_contract = modified_contract.strip()

        # Advanced repetition detection and removal
        def detect_and_remove_repetition(text):
            """Detect and remove repeated sections in text"""
            lines = text.split('\n')
            seen_sequences = {}
            result_lines = []
            skip_until = -1

            for i, line in enumerate(lines):
                if i < skip_until:
                    continue

                # Check for repeated sequences (5-20 line chunks)
                for chunk_size in range(20, 4, -1):
                    if i + chunk_size * 2 <= len(lines):
                        chunk1 = '\n'.join(lines[i:i+chunk_size])
                        chunk2 = '\n'.join(lines[i+chunk_size:i+chunk_size*2])

                        # If chunks are very similar (>90% match)
                        if len(chunk1) > 100 and len(chunk2) > 100:
                            similarity = sum(c1 == c2 for c1, c2 in zip(chunk1, chunk2)) / max(len(chunk1), len(chunk2))
                            if similarity > 0.90:
                                print(f'[INFO] Detected repetition at line {i}, removing {chunk_size} repeated lines')
                                skip_until = i + chunk_size
                                break

                result_lines.append(line)

            return '\n'.join(result_lines)

        # Apply repetition removal
        modified_contract = detect_and_remove_repetition(modified_contract)

        # Validate the modified contract
        if not modified_contract:
            return Response(
                {'error': 'The AI model returned an empty response. Please try again with clearer instructions.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Check length ratio
        original_len = len(extracted_text)
        modified_len = len(modified_contract)
        length_ratio = modified_len / original_len if original_len > 0 else 0

        print(f'[INFO] Contract modification complete')
        print(f'[INFO] Original length: {original_len} chars')
        print(f'[INFO] Modified length: {modified_len} chars')
        print(f'[INFO] Length ratio: {length_ratio:.2%}')
        print(f'[INFO] Model used: {model_to_use}')

        # Generate appropriate warnings
        warnings = []

        if was_truncated:
            warnings.append('NOTE: Original contract was very long and was truncated for processing.')

        if length_ratio < 0.7:
            warnings.append('⚠️ Modified contract is significantly shorter than original. The AI may have omitted content. Please review carefully.')
        elif length_ratio > 1.4:
            warnings.append('⚠️ Modified contract is significantly longer than original. The AI may have added content. Please review carefully.')
        elif 0.9 <= length_ratio <= 1.1:
            warnings.append('[OK] Contract length preserved successfully (within 10% of original).')

        response_data = {
            'instruction': instruction,
            'modified_contract': modified_contract,
            'original_length': original_len,
            'modified_length': modified_len,
            'length_ratio': f'{length_ratio:.2%}',
            'model_used': model_to_use,
        }

        if warnings:
            response_data['warnings'] = warnings

        return Response(response_data)

    except requests.exceptions.Timeout:
        return Response(
            {'error': 'The AI model took too long to respond. Try with a shorter contract or simpler instructions.'},
            status=status.HTTP_504_GATEWAY_TIMEOUT
        )
    except requests.exceptions.ConnectionError:
        return Response(
            {'error': 'Could not connect to Ollama. Please ensure Ollama is running (ollama serve).'},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )
    except Exception as e:
        print(f'RAG generate error: {str(e)}')
        import traceback
        traceback.print_exc()
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_contract_pdf(request):
    """Generate a PDF from modified contract text"""
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.enums import TA_JUSTIFY
    from django.http import HttpResponse
    import io

    try:
        contract_text = request.data.get('contract_text', '')

        if not contract_text:
            return Response(
                {'error': 'Contract text is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create PDF in memory
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter,
                              rightMargin=72, leftMargin=72,
                              topMargin=72, bottomMargin=18)

        # Container for PDF elements
        elements = []

        # Define styles
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY))

        # Add title
        title_style = styles['Heading1']
        elements.append(Paragraph("Modified Contract", title_style))
        elements.append(Spacer(1, 12))

        # Add contract text (split by paragraphs)
        body_style = styles['BodyText']
        paragraphs = contract_text.split('\n')

        for para in paragraphs:
            if para.strip():
                # Escape special characters for reportlab
                para_clean = para.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                elements.append(Paragraph(para_clean, body_style))
                elements.append(Spacer(1, 6))

        # Build PDF
        doc.build(elements)

        # Get PDF data
        pdf_data = buffer.getvalue()
        buffer.close()

        # Return as downloadable PDF
        response = HttpResponse(pdf_data, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="Modified_Contract.pdf"'
        return response

    except Exception as e:
        print(f'PDF generation error: {str(e)}')
        import traceback
        traceback.print_exc()
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def rag_generate_from_samples(request):
    """
    Generate a new contract using RAG (Retrieval-Augmented Generation)
    Uses indexed sample contracts as context

    POST /api/rag/generate-from-samples

    Body: {
        "prompt": "Generate a consulting agreement for software development",
        "title": "Software Consulting Agreement"  # optional
    }

    Returns: {
        "success": true,
        "contract": "...",
        "title": "...",
        "model_used": "...",
        "context_chunks_used": 5
    }
    """
    try:
        from api.contract_rag_service import ContractRAGService

        prompt = request.data.get('prompt', '').strip()
        title = request.data.get('title', '').strip()

        if not prompt:
            return Response(
                {'error': 'Prompt is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Initialize RAG service
        rag_service = ContractRAGService()
        user_id = str(request.user.id) if request.user.is_authenticated else None

        # Generate contract
        result = rag_service.generate_contract(prompt, title=title, user_id=user_id)

        if result.get('success'):
            return Response({
                'success': True,
                'contract': result.get('contract'),
                'title': result.get('title'),
                'model_used': result.get('model_used'),
                'context_chunks_used': result.get('context_chunks_used'),
                'has_context': result.get('has_context')
            })
        else:
            return Response({
                'error': result.get('error', 'Contract generation failed')
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    except Exception as e:
        print(f'RAG generation error: {str(e)}')
        import traceback
        traceback.print_exc()
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def rag_collection_stats(request):
    """
    Get statistics about the RAG vector database

    GET /api/rag/stats

    Returns: {
        "total_vectors": 1234,
        "collection_name": "contract_samples"
    }
    """
    try:
        from api.contract_rag_service import ContractRAGService

        rag_service = ContractRAGService()
        stats = rag_service.get_collection_stats()

        return Response(stats)

    except Exception as e:
        print(f'Stats retrieval error: {str(e)}')
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def unified_rag_chat(request):
    """
    Unified RAG chat across all user's contracts with semantic search

    POST /api/rag/chat

    Body: { "query": "What are the termination clauses?" }

    Returns: {
        "answer": "...",
        "sources": [{ "contract_id", "filename", "text", "score" }],
        "contracts": [{ contract metadata for matching contracts }]
    }
    """
    try:
        from api.utils import parse_semantic_query
        from django.db.models import Q

        query = request.data.get('query', '').strip()

        if not query:
            return Response(
                {'error': 'Query is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user_id = str(request.user.id)

        print(f"\n[UNIFIED CHAT] User: {request.user.email} ({user_id})")
        print(f"[UNIFIED CHAT] Query: {query}")

        # Parse semantic intent from query
        parsed = parse_semantic_query(query)
        filters = parsed['filters']
        search_terms = parsed['search_terms']
        semantic_query = parsed['semantic_query']

        print(f"[UNIFIED CHAT] Detected filters: {filters}")
        print(f"[UNIFIED CHAT] Search terms: {search_terms}")
        print(f"[UNIFIED CHAT] Semantic query: {semantic_query}")

        # Build Django query for metadata filtering
        contract_query = Q(user_id=user_id)

        if 'risk_level' in filters:
            contract_query &= Q(risk_analysis__risk_level=filters['risk_level'])

        if 'contract_type_contains' in filters:
            contract_query &= Q(contract_type__icontains=filters['contract_type_contains'])

        if 'liability_level' in filters:
            contract_query &= Q(liability_level=filters['liability_level'])

        if 'has_arbitration' in filters:
            contract_query &= Q(has_arbitration=filters['has_arbitration'])

        if 'jurisdiction_contains' in filters:
            contract_query &= Q(jurisdiction__icontains=filters['jurisdiction_contains'])

        if 'status' in filters:
            contract_query &= Q(status=filters['status'])

        # Handle "show all contracts" request
        if 'show_all' in filters:
            # User wants to see all their contracts
            has_metadata_filters = True
        else:
            has_metadata_filters = any(k in filters for k in ['risk_level', 'contract_type_contains', 'liability_level', 'status', 'has_arbitration', 'jurisdiction_contains'])

        # Get matching contracts with metadata
        matching_contracts = Contract.objects.filter(contract_query).select_related('risk_analysis')[:20]

        print(f"[UNIFIED CHAT] Found {matching_contracts.count()} contracts matching filters")

        if has_metadata_filters and matching_contracts.exists():
            # For metadata queries, return contract list with their details
            contracts_data = []
            for contract in matching_contracts:
                contract_data = {
                    'id': str(contract.id),
                    'filename': contract.original_filename,
                    'contract_type': contract.contract_type or 'Unknown',
                    'uploaded_at': contract.uploaded_at.isoformat(),
                    'status': contract.status,
                    'party_a': contract.party_a,
                    'party_b': contract.party_b,
                    'contract_value': contract.contract_value,
                    'jurisdiction': contract.jurisdiction,
                    'has_arbitration': contract.has_arbitration,
                }

                # Add risk analysis if available
                if hasattr(contract, 'risk_analysis') and contract.risk_analysis:
                    contract_data['risk_level'] = contract.risk_analysis.risk_level
                    contract_data['risk_score'] = contract.risk_analysis.risk_score
                    contract_data['total_deviations'] = contract.risk_analysis.total_deviations
                    contract_data['analysis_summary'] = contract.risk_analysis.analysis_summary

                contracts_data.append(contract_data)

            # Generate answer based on the contracts found
            if filters.get('show_all'):
                answer = f"You have {len(contracts_data)} uploaded contract(s):\n\n"
                for idx, c in enumerate(contracts_data, 1):
                    risk_badge = ""
                    if c.get('risk_level'):
                        risk_badge = f" [{c['risk_level']}]"
                    answer += f"{idx}. {c['filename']}{risk_badge}\n"
                    answer += f"   Type: {c['contract_type']}\n"
                    if c.get('party_a') and c.get('party_b'):
                        answer += f"   Parties: {c['party_a']} ↔ {c['party_b']}\n"
                    answer += f"   Uploaded: {c['uploaded_at'][:10]}\n"
                    answer += "\n"
            elif filters.get('risk_level'):
                answer = f"Found {len(contracts_data)} {filters['risk_level'].lower()} risk contract(s):\n\n"
                for idx, c in enumerate(contracts_data, 1):
                    risk_info = f"Risk Level: {c.get('risk_level', 'Not analyzed')}"
                    if c.get('risk_score'):
                        risk_info += f" (Score: {c.get('risk_score')})"
                    answer += f"{idx}. {c['filename']}\n   Type: {c['contract_type']}\n   {risk_info}\n"
                    if c.get('analysis_summary'):
                        summary = c['analysis_summary'][:150] + '...' if len(c.get('analysis_summary', '')) > 150 else c.get('analysis_summary', '')
                        answer += f"   Summary: {summary}\n"
                    answer += "\n"
            else:
                answer = f"Found {len(contracts_data)} contract(s) matching your criteria:\n\n"
                for idx, c in enumerate(contracts_data, 1):
                    answer += f"{idx}. {c['filename']} ({c['contract_type']})\n"

            return Response({
                'query': query,
                'answer': answer.strip(),
                'contracts': contracts_data,
                'contract_count': len(contracts_data),
                'filters_applied': filters,
                'search_type': 'metadata_search'
            })

        # INTELLIGENT filename extraction - works like ChatGPT
        import re

        print(f"[UNIFIED CHAT] Query: '{query}'")

        # SIMPLE & EFFECTIVE: Find all patterns ending in .pdf/.docx/etc., pick the longest/best match
        # This handles: tesy.pdf, LOI Acknowledement(1).pdf, Signed Contract.pdf, SA-07.pdf, etc.

        all_matches = []

        # Pattern 1: Simple filenames (single word, no spaces): tesy.pdf, SA-07.pdf
        pattern1 = re.findall(r'\b([A-Za-z][A-Za-z0-9_\-()]+\.(?:pdf|docx|doc|txt))\b', query, re.IGNORECASE)
        all_matches.extend(pattern1)

        # Pattern 2: Multi-word filenames (2-4 words): "LOI Acknowledement(1).pdf", "Signed Contract.pdf"
        # Look for patterns like: CapitalWord Space CapitalWord ... .extension
        pattern2 = re.findall(r'\b([A-Z][a-z]+(?:\s+[A-Z][A-Za-z0-9_\-()]+){1,3}\.(?:pdf|docx|doc|txt))\b', query)
        all_matches.extend(pattern2)

        # Pattern 3: All-caps abbreviations with spaces: "LOI Acknowledement(1).pdf"
        pattern3 = re.findall(r'\b([A-Z]+(?:\s+[A-Z][A-Za-z0-9_\-()]+){1,3}\.(?:pdf|docx|doc|txt))\b', query)
        all_matches.extend(pattern3)

        # Pattern 4: Hyphenated codes with multi-word: "SA-07 Primetechnologyr5.pdf"
        pattern4 = re.findall(r'\b([A-Z]+-[A-Z0-9]+(?:\s+[A-Z][A-Za-z0-9_\-()]+){0,3}\.(?:pdf|docx|doc|txt))\b', query)
        all_matches.extend(pattern4)

        # Remove duplicates and keep ALL matched files (for multi-file comparison)
        all_matches = list(set([m.strip() for m in all_matches]))
        # Sort by length descending (longest first)
        raw_matches = sorted(all_matches, key=len, reverse=True) if all_matches else []
        print(f"[UNIFIED CHAT] Found potential files: {raw_matches}")

        # ============================================================================
        # SIMPLE DIRECT DATABASE APPROACH for clause queries across ALL contracts
        # No Ollama hallucinations - just query the Clause table directly!
        # ============================================================================
        query_lower = query.lower()  # Define this first!

        # Map user keywords to actual clause names in database
        # Includes BOTH lowercase generic names AND exact database clause names
        clause_keywords = {
            # Exact database names (capitalized)
            'Termination': ['termination', 'terminate', 'end contract', 'cancel', 'cancellation'],
            'Payment Terms': ['payment', 'pay', 'invoice', 'fee', 'pricing', 'cost'],
            'Indemnification': ['liability', 'indemnity', 'damages', 'indemnification'],
            'Confidentiality': ['confidential', 'nda', 'non-disclosure', 'confidentiality'],
            'Warranty': ['warranty', 'warranties', 'guarantee'],
            'Intellectual Property': ['intellectual property', 'ip', 'copyright', 'trademark', 'patent'],
            'Arbitration': ['dispute', 'arbitration', 'mediation', 'litigation', 'dispute resolution'],
            'Force Majeure': ['force majeure', 'act of god'],
            'Governing Law': ['governing law', 'jurisdiction', 'applicable law'],
            'Assignment': ['assignment', 'transfer', 'assignability'],
            'Amendment': ['amendment', 'modification', 'change'],
            'Notice': ['notice', 'notification', 'notices'],
            'Insurance': ['insurance', 'coverage'],
            'Delivery': ['delivery', 'deliverable', 'shipment'],
            # Generic lowercase names (for backward compatibility)
            'termination': ['termination', 'terminate', 'end contract', 'cancel', 'cancellation'],
            'payment': ['payment', 'pay', 'invoice', 'fee', 'pricing', 'cost'],
            'liability': ['liability', 'indemnity', 'damages', 'indemnification'],
            'confidentiality': ['confidential', 'nda', 'non-disclosure', 'confidentiality'],
            'warranty': ['warranty', 'warranties', 'guarantee'],
            'intellectual property': ['intellectual property', 'ip', 'copyright', 'trademark', 'patent'],
            'dispute resolution': ['dispute', 'arbitration', 'mediation', 'litigation', 'dispute resolution'],
            'force majeure': ['force majeure', 'act of god'],
            'governing law': ['governing law', 'jurisdiction', 'applicable law'],
            'assignment': ['assignment', 'transfer', 'assignability'],
            'amendment': ['amendment', 'modification', 'change'],
            'notice': ['notice', 'notification', 'notices'],
            'insurance': ['insurance', 'coverage'],
            'delivery': ['delivery', 'deliverable', 'shipment'],
        }

        # Check if user is asking for a specific clause type across ALL contracts (no specific filename)
        detected_clause_type = None
        if not raw_matches:  # No specific filename detected
            for clause_type, keywords in clause_keywords.items():
                if any(kw in query_lower for kw in keywords):
                    detected_clause_type = clause_type
                    print(f"[UNIFIED CHAT] Detected {clause_type} clause query across all contracts")
                    break

        if detected_clause_type:
            # DIRECT DATABASE QUERY - Simple, fast, no AI hallucinations!
            from core.models import Clause

            all_user_contracts = Contract.objects.filter(user_id=user_id).select_related('risk_analysis')

            if not all_user_contracts.exists():
                return Response({
                    'query': query,
                    'answer': "You haven't uploaded any contracts yet.",
                    'sources': [],
                    'contracts': [],
                    'search_type': 'no_contracts'
                })

            answer_parts = []
            sources = []
            contracts_metadata = []
            processed_filenames = set()  # Avoid duplicates

            print(f"[UNIFIED CHAT] Querying {detected_clause_type} clauses for {all_user_contracts.count()} contracts")

            def clean_clause_text(text):
                """Clean up extracted clause text - remove table of contents, page headers, etc."""
                if not text:
                    return "Clause found but text unavailable"

                lines = text.split('\n')
                cleaned_lines = []

                for line in lines:
                    line = line.strip()

                    # Skip empty lines
                    if not line:
                        continue

                    # Skip table of contents patterns (numbers followed by text followed by page number)
                    if re.match(r'^\d+\s+[A-Z][a-zA-Z\s]+\d+\s*$', line):
                        continue

                    # Skip page headers/footers
                    if '--- Page' in line or 'Page ' in line and ' of ' in line:
                        continue

                    # Skip lines that are just numbers or short codes
                    if len(line) < 15 and re.match(r'^[\d\s\-\.]+$', line):
                        continue

                    # Skip company headers
                    if 'BK Gulf' in line or 'WI CO 36' in line or 'CONDITIONS OF CONTRACT' in line:
                        continue

                    # Skip lines ending with incomplete words (cut off)
                    if line.endswith('The') or line.endswith('Th') or line.endswith('T'):
                        continue

                    cleaned_lines.append(line)

                # Join and limit length
                result = ' '.join(cleaned_lines)
                if len(result) > 500:
                    result = result[:500] + '...'

                return result if result else "Clause text extraction needs improvement"

            for contract in all_user_contracts:
                # Skip duplicates
                if contract.original_filename in processed_filenames:
                    print(f"[UNIFIED CHAT] Skipping duplicate: {contract.original_filename}")
                    continue
                processed_filenames.add(contract.original_filename)

                # Query database for this clause type
                clauses = Clause.objects.filter(
                    contract=contract,
                    clause_name__icontains=detected_clause_type,
                    found=True
                ).order_by('-confidence')

                if clauses.exists():
                    best_clause = clauses.first()
                    raw_text = (best_clause.extracted_text or "").strip()
                    cleaned_text = clean_clause_text(raw_text)
                    answer_parts.append(f"In {contract.original_filename}:\n{cleaned_text}\n")
                else:
                    answer_parts.append(f"In {contract.original_filename}:\nNo {detected_clause_type} clause found.\n")

                sources.append({
                    'contract_id': str(contract.id),
                    'filename': contract.original_filename,
                    'text': f"{detected_clause_type.capitalize()} clause from {contract.original_filename}"
                })

                metadata = {'id': str(contract.id), 'filename': contract.original_filename, 'contract_type': contract.contract_type}
                if hasattr(contract, 'risk_analysis') and contract.risk_analysis:
                    metadata['risk_level'] = contract.risk_analysis.risk_level
                    metadata['risk_score'] = contract.risk_analysis.risk_score
                contracts_metadata.append(metadata)

            final_answer = "\n".join(answer_parts)

            print(f"[UNIFIED CHAT] Direct DB query complete - {len(contracts_metadata)} contracts processed")

            return Response({
                'query': query,
                'answer': final_answer,
                'sources': sources,
                'source_count': len(sources),
                'contracts': contracts_metadata,
                'contract_count': len(contracts_metadata),
                'search_type': 'direct_clause_query',
                'has_contract_context': True,
                'intent': 'contract'
            })

        # ============================================================================
        # Regular filename matching logic (for specific file queries)
        # Supports MULTIPLE files for comparison queries
        # ============================================================================
        specific_filename = None
        matched_contracts = []  # Changed to list to support multiple files

        # Try to intelligently match contracts
        if raw_matches:
            # Get all user's contracts once
            all_user_contracts = Contract.objects.filter(user_id=user_id).select_related('risk_analysis')

            print(f"\n{'='*80}")
            print(f"[MATCHING] User has {all_user_contracts.count()} contracts")
            print(f"[MATCHING] Looking for: {raw_matches}")
            print(f"[MATCHING] Available contracts:")
            for idx, c in enumerate(all_user_contracts, 1):
                print(f"  {idx}. {c.original_filename}")
            print(f"{'='*80}\n")

            # Try to match ALL mentioned files (for comparison queries)
            for raw_file in raw_matches:
                # Normalize the query filename - keep ONLY letters (remove numbers, spaces, special chars)
                # This allows "LOI Acknowledement.pdf" to match "LOI Acknowledement(1).pdf"
                query_name = raw_file.rsplit('.', 1)[0] if '.' in raw_file else raw_file
                # Keep only alphabetic characters and convert to lowercase
                query_normalized = ''.join(c.lower() for c in query_name if c.isalpha())

                print(f"[MATCHING] Query: '{raw_file}' -> Name: '{query_name}' -> Normalized: '{query_normalized}'")

                found_match = False

                # Try to find matching contract - exact match first
                for contract in all_user_contracts:
                    # Normalize the contract filename - keep ONLY letters (same as query)
                    contract_name = contract.original_filename.rsplit('.', 1)[0] if '.' in contract.original_filename else contract.original_filename
                    # Keep only alphabetic characters and convert to lowercase
                    contract_normalized = ''.join(c.lower() for c in contract_name if c.isalpha())

                    print(f"  Comparing: query='{query_normalized}' vs contract='{contract_normalized}' ({contract.original_filename})")

                    if contract_normalized == query_normalized:
                        if contract not in matched_contracts:  # Avoid duplicates
                            matched_contracts.append(contract)
                            found_match = True
                        print(f"[MATCHING] [OK] EXACT MATCH FOUND!")
                        print(f"  Query normalized: '{query_normalized}'")
                        print(f"  Contract: '{contract.original_filename}' -> '{contract_normalized}'")
                        print(f"{'='*80}\n")
                        break

                # If no exact match, try fuzzy matching (contains)
                if not found_match:
                    print(f"[MATCHING] No exact match, trying fuzzy match...")
                    for contract in all_user_contracts:
                        contract_name = contract.original_filename.rsplit('.', 1)[0] if '.' in contract.original_filename else contract.original_filename
                        # Keep only alphabetic characters and convert to lowercase
                        contract_normalized = ''.join(c.lower() for c in contract_name if c.isalpha())

                        # Check if query is contained in contract name or vice versa (min 3 chars to avoid false matches)
                        if len(query_normalized) >= 3 and (query_normalized in contract_normalized or contract_normalized in query_normalized):
                            if contract not in matched_contracts:  # Avoid duplicates
                                matched_contracts.append(contract)
                            print(f"[MATCHING] [OK] FUZZY MATCH FOUND!")
                            print(f"  Query normalized: '{query_normalized}'")
                            print(f"  Contract: '{contract.original_filename}' -> '{contract_normalized}'")
                            print(f"{'='*80}\n")
                            break

        # Set contracts based on match result
        if matched_contracts:
            # Use all matched contracts for comparison
            contract_ids = [c.id for c in matched_contracts]
            all_contracts = Contract.objects.filter(id__in=contract_ids).select_related('risk_analysis')
            if len(matched_contracts) == 1:
                print(f"[UNIFIED CHAT] [OK] LOCKED TO SINGLE CONTRACT: '{matched_contracts[0].original_filename}'")
            else:
                contract_names = [c.original_filename for c in matched_contracts]
                print(f"[UNIFIED CHAT] [OK] LOCKED TO {len(matched_contracts)} CONTRACTS: {contract_names}")
        else:
            # No specific file mentioned or not found - use all contracts
            specific_filename = None
            all_contracts = Contract.objects.filter(user_id=user_id).select_related('risk_analysis').order_by('-uploaded_at')
            print(f"[UNIFIED CHAT] No specific contract, using all {all_contracts.count()} contracts")

        if not all_contracts.exists():
            if specific_filename:
                # Get all user's contracts to suggest alternatives
                all_user_contracts = Contract.objects.filter(user_id=user_id).values_list('original_filename', flat=True)

                if all_user_contracts:
                    suggestions = "\n\nYour uploaded contracts:\n" + "\n".join([f"• {name}" for name in list(all_user_contracts)[:10]])
                else:
                    suggestions = ""

                return Response({
                    'query': query,
                    'answer': f"I couldn't find a contract matching '{specific_filename}'.{suggestions}\n\nPlease check the filename and try again.",
                    'sources': [],
                    'contracts': [],
                    'search_type': 'no_contracts'
                })
            else:
                return Response({
                    'query': query,
                    'answer': "You haven't uploaded any contracts yet. Please upload contracts first to ask questions about them.",
                    'sources': [],
                    'contracts': [],
                    'search_type': 'no_contracts'
                })

        print(f"[UNIFIED CHAT] Found {all_contracts.count()} contract(s) for query")

        # Build context from contracts
        context_parts = []
        contracts_metadata = []
        sources = []

        # Detect question type to build relevant context
        query_lower = query.lower()
        is_termination_query = any(word in query_lower for word in ['termination', 'terminate', 'cancel', 'end contract'])
        is_risk_query = any(word in query_lower for word in ['risk', 'risky', 'dangerous', 'concern'])
        is_payment_query = any(word in query_lower for word in ['payment', 'pay', 'price', 'cost', 'value', 'money'])
        is_party_query = any(word in query_lower for word in ['party', 'parties', 'vendor', 'client', 'supplier'])

        # CRITICAL: If asking about specific file(s), ONLY process matched contracts - NO EXCEPTIONS!
        if matched_contracts:
            # User asked about specific file(s) and we found them - USE ONLY THESE!
            contracts_to_process = matched_contracts
            if len(matched_contracts) == 1:
                print(f"[UNIFIED CHAT] [OK][OK][OK] LOCKED TO SINGLE CONTRACT: {matched_contracts[0].original_filename}")
                print(f"[UNIFIED CHAT] Will NOT use any other contracts!")
            else:
                contract_names = [c.original_filename for c in matched_contracts]
                print(f"[UNIFIED CHAT] [OK][OK][OK] LOCKED TO {len(matched_contracts)} CONTRACTS: {contract_names}")
                print(f"[UNIFIED CHAT] Will NOT use any other contracts!")
        elif specific_filename:
            # User mentioned a filename but we didn't find exact match - try first contract
            contracts_to_process = list(all_contracts[:1])
            print(f"[UNIFIED CHAT] Processing first contract only (filename mentioned but not matched)")
        else:
            # No specific filename mentioned - use up to 10 contracts
            contracts_to_process = list(all_contracts[:10])
            print(f"[UNIFIED CHAT] No specific file mentioned, processing up to 10 contracts")

        for idx, contract in enumerate(contracts_to_process, 1):
            # For MULTIPLE contracts: Send ONLY filename + relevant clause text (NO metadata labels!)
            # For SINGLE contract: Can include metadata since user asked about that specific file
            if len(contracts_to_process) == 1:
                # Single contract: Include metadata
                contract_context = f"\n=== CONTRACT FILE: {contract.original_filename} ===\n"
                contract_context += f"Type: {contract.contract_type or 'Unknown'}\n"
                if contract.party_a or contract.party_b:
                    contract_context += f"Parties: {contract.party_a or 'N/A'} and {contract.party_b or 'N/A'}\n"
                if contract.contract_value:
                    contract_context += f"Value: {contract.contract_value}\n"
                if hasattr(contract, 'risk_analysis') and contract.risk_analysis:
                    risk = contract.risk_analysis
                    contract_context += f"Risk Level: {risk.risk_level} (Score: {risk.risk_score}/100)\n"
                    if is_risk_query and risk.analysis_summary:
                        contract_context += f"Risk Summary: {risk.analysis_summary[:500]}\n"
            else:
                # Multiple contracts: NO metadata labels - just filename header
                contract_context = f"\n=== {contract.original_filename} ===\n"
                # Skip all metadata - will add only the relevant clause text below

                # Add risky clauses if asking about risks (only if attribute exists)
                if is_risk_query and hasattr(contract, 'risk_analysis') and contract.risk_analysis:
                    risk = contract.risk_analysis
                    if hasattr(risk, 'risky_clauses') and risk.risky_clauses:
                        try:
                            import json
                            risky_clauses = json.loads(risk.risky_clauses) if isinstance(risk.risky_clauses, str) else risk.risky_clauses
                            if risky_clauses:
                                contract_context += "Risky Clauses:\n"
                                for clause in risky_clauses[:3]:  # Top 3 risky clauses
                                    contract_context += f"  - {clause.get('clause_type', 'Unknown')}: {clause.get('text', '')[:200]}\n"
                        except:
                            pass

            # Add relevant text snippets based on question type
            if contract.full_text:
                text = contract.full_text

                # Extract relevant sections based on query
                if is_termination_query:
                    # Find termination-related text - increased snippet size for complete clauses
                    if 'termination' in text.lower():
                        start_idx = text.lower().find('termination')
                        snippet = text[max(0, start_idx-300):start_idx+2000]
                        # For multiple contracts: NO label, just the text
                        # For single contract: Include label
                        if len(contracts_to_process) == 1:
                            contract_context += f"Termination Clause: {snippet}\n"
                        else:
                            contract_context += f"{snippet}\n"

                elif is_payment_query:
                    if any(word in text.lower() for word in ['payment', 'fee', 'price', 'cost']):
                        # Find payment-related text - increased snippet size
                        for word in ['payment', 'fee', 'price', 'cost']:
                            if word in text.lower():
                                start_idx = text.lower().find(word)
                                snippet = text[max(0, start_idx-300):start_idx+2000]
                                if len(contracts_to_process) == 1:
                                    contract_context += f"Payment Info: {snippet}\n"
                                else:
                                    contract_context += f"{snippet}\n"
                                break

                else:
                    # General query - include larger contract summary
                    snippet = text[:2000]
                    if len(contracts_to_process) == 1:
                        contract_context += f"Contract Summary: {snippet}\n"
                    else:
                        contract_context += f"{snippet}\n"

            context_parts.append(contract_context)

            # Build metadata for response
            metadata = {
                'id': str(contract.id),
                'filename': contract.original_filename,
                'contract_type': contract.contract_type,
                'uploaded_at': contract.uploaded_at.isoformat() if contract.uploaded_at else None
            }
            if hasattr(contract, 'risk_analysis') and contract.risk_analysis:
                metadata['risk_level'] = contract.risk_analysis.risk_level
                metadata['risk_score'] = contract.risk_analysis.risk_score
            contracts_metadata.append(metadata)

            sources.append({
                'contract_id': str(contract.id),
                'filename': contract.original_filename,
                'text': contract_context[:500]
            })

        # Combine all context
        full_context = "\n".join(context_parts)

        # Build prompt for Ollama - different for single vs multiple contracts
        if specific_filename and len(contracts_to_process) == 1:
            # User asking about ONE specific contract - be EXTREMELY clear and direct
            actual_filename = contracts_to_process[0].original_filename
            prompt = f"""You are analyzing ONLY ONE contract: {actual_filename}

Answer the question using ONLY information from {actual_filename}. Do NOT include information from any other contracts.

{full_context}

Question: {query}

CRITICAL RULES:
1. Use ONLY information from {actual_filename} above
2. Write clause text directly - NO metadata labels
3. NO asterisks (**) or formatting
4. NO lists with "Type:", "Parties:", "Risk Level:", etc.
5. Give the actual clause content

Answer:"""
        else:
            # User asking about multiple contracts - MUST show information from ALL contracts
            num_contracts = len(contracts_to_process)
            prompt = f"""Answer this question about ALL {num_contracts} contracts below. You MUST include information from EVERY contract.

Question: {query}

{full_context}

CRITICAL INSTRUCTIONS:
1. Answer for ALL {num_contracts} contracts - DO NOT skip any contract
2. For EACH contract, use the ACTUAL FILENAME from "CONTRACT FILE: [filename]" header
3. Format EXACTLY like this:
   "In tesy.pdf: [clause text from tesy.pdf]"

   "In Signed Contract.pdf: [clause text from Signed Contract.pdf]"

   (continue for all {num_contracts} contracts)
4. Use the REAL filename (like "tesy.pdf", "Signed Contract.pdf") - NOT "CONTRACT 1" or "CONTRACT 2"
5. NO metadata labels, NO asterisks (**), NO bold formatting
6. Cover ALL {num_contracts} contracts shown above

Answer for ALL contracts using REAL filenames:"""

        # Call Ollama
        try:
            import requests
            # Different settings for single vs multiple contracts
            if specific_filename and len(contracts_to_process) == 1:
                # Single contract: Maximum accuracy, deterministic
                temperature = 0.0  # Most accurate, no randomness
                num_predict = 800  # Longer answers for complete clauses
            else:
                # Multiple contracts: Need much longer responses to cover ALL contracts
                temperature = 0.1
                num_predict = 2000  # Increased to cover multiple contracts

            ollama_response = requests.post(
                os.getenv("OLLAMA_BASE_URL", "http://localhost:11434") + "/api/generate",
                json={
                    'model': 'qwen2.5:0.5b',
                    'prompt': prompt,
                    'stream': False,
                    'options': {
                        'temperature': temperature,
                        'num_predict': num_predict,
                        'top_p': 0.9,  # Focus on most likely tokens
                        'repeat_penalty': 1.1  # Reduce repetition
                    }
                },
                timeout=120  # Increased timeout
            )

            if ollama_response.status_code == 200:
                answer = ollama_response.json().get('response', '')
            else:
                answer = f"Found {len(contracts_metadata)} contract(s) but could not generate answer. Please check if Ollama is running."

        except requests.exceptions.ConnectionError:
            answer = f"Found {len(contracts_metadata)} contract(s) but Ollama is not running. Please start Ollama with: ollama serve"
        except Exception as e:
            answer = f"Found {len(contracts_metadata)} contract(s) but error generating answer: {str(e)}"

        print(f"[UNIFIED CHAT] Generated answer with {len(sources)} sources")

        # FINAL CHECK: If user asked about specific file(s), ensure we ONLY return those files' data
        if matched_contracts:
            # Filter to ensure ONLY the matched contracts are in the response
            matched_ids = [str(c.id) for c in matched_contracts]
            sources = [s for s in sources if s.get('contract_id') in matched_ids]
            contracts_metadata = [c for c in contracts_metadata if c.get('id') in matched_ids]
            if len(matched_contracts) == 1:
                print(f"[UNIFIED CHAT] [OK] Final check: Filtered to ONLY matched contract - {len(contracts_metadata)} contract(s), {len(sources)} source(s)")
            else:
                print(f"[UNIFIED CHAT] [OK] Final check: Filtered to {len(matched_contracts)} matched contracts - {len(contracts_metadata)} contract(s), {len(sources)} source(s)")

        return Response({
            'query': query,
            'answer': answer,
            'sources': sources,
            'source_count': len(sources),
            'contracts': contracts_metadata,
            'contract_count': len(contracts_metadata),
            'search_type': 'simple_rag',
            'has_contract_context': True,
            'intent': 'contract' if matched_contracts else ('general' if not all_contracts.exists() else 'hybrid')
        })

    except Exception as e:
        print(f'[UNIFIED CHAT] Error: {str(e)}')
        import traceback
        traceback.print_exc()

        return Response(
            {
                'error': 'An error occurred while processing your question.',
                'details': str(e)
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_contract_status(request, contract_id):
    """
    Update contract workflow status

    PUT /api/contracts/<id>/status

    Body: { "status": "REVIEW" }

    Validates state transitions:
    - DRAFT -> REVIEW
    - REVIEW -> NEGOTIATION, FINAL
    - NEGOTIATION -> FINAL
    """
    try:
        new_status = request.data.get('status', '').strip()

        if not new_status:
            return Response(
                {'error': 'Status is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Valid status choices
        VALID_STATUSES = ['DRAFT', 'REVIEW', 'NEGOTIATION', 'FINAL']
        if new_status not in VALID_STATUSES:
            return Response(
                {'error': f'Invalid status. Must be one of: {", ".join(VALID_STATUSES)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get contract
        try:
            contract = Contract.objects.get(id=contract_id)
        except Contract.DoesNotExist:
            return Response(
                {'error': 'Contract not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Verify ownership
        if contract.user != request.user:
            return Response(
                {'error': 'Access denied'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Validate transition
        if not contract.can_transition_to(new_status):
            return Response(
                {
                    'error': f'Invalid status transition from {contract.status} to {new_status}',
                    'current_status': contract.status,
                    'requested_status': new_status
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update status
        old_status = contract.status
        contract.status = new_status
        contract.save()

        print(f'[WORKFLOW] Contract {contract_id} status: {old_status} -> {new_status}')

        return Response({
            'message': 'Status updated successfully',
            'contract_id': str(contract.id),
            'old_status': old_status,
            'new_status': new_status,
            'filename': contract.original_filename
        })

    except Exception as e:
        print(f'[WORKFLOW] Error: {str(e)}')
        import traceback
        traceback.print_exc()
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def compare_contracts_view(request):
    """
    Compare multiple contracts using semantic similarity analysis

    Expected payload:
    {
        "reference_contract_id": "uuid",
        "compare_contract_ids": ["uuid1", "uuid2", "uuid3"],
        "keywords": ["keyword1", "keyword2"] (optional)
    }
    """
    try:
        from .contract_comparison import compare_contracts

        reference_contract_id = request.data.get('reference_contract_id')
        compare_contract_ids = request.data.get('compare_contract_ids', [])
        keywords = request.data.get('keywords', [])

        if not reference_contract_id:
            return Response(
                {'error': 'reference_contract_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not compare_contract_ids or len(compare_contract_ids) == 0:
            return Response(
                {'error': 'At least one contract ID must be provided for comparison'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if len(compare_contract_ids) > 3:
            return Response(
                {'error': 'Maximum 3 contracts can be compared at once'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Verify user has access to all contracts
        all_contract_ids = [reference_contract_id] + compare_contract_ids
        contracts = Contract.objects.filter(id__in=all_contract_ids, user=request.user)

        if contracts.count() != len(all_contract_ids):
            return Response(
                {'error': 'One or more contracts not found or access denied'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Run comparison
        result = compare_contracts(
            reference_contract_id=reference_contract_id,
            compare_contract_ids=compare_contract_ids,
            keywords=keywords
        )

        if 'error' in result:
            return Response(
                {'error': result['error']},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(result)

    except Exception as e:
        print(f'Contract comparison error: {str(e)}')
        import traceback
        traceback.print_exc()
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def extract_keyword_contexts(text, keyword, max_sentences=2):
    """
    Extract complete sentences containing the keyword
    Returns list of complete sentences with the keyword highlighted
    """
    import re

    if not text or not keyword:
        return []

    occurrences = []
    text_lower = text.lower()
    keyword_lower = keyword.lower()

    # Find all positions of the keyword
    pattern = r'\b' + re.escape(keyword_lower) + r'\w*\b'
    matches = re.finditer(pattern, text_lower)

    for match in matches:
        start_pos = match.start()
        end_pos = match.end()

        # Find sentence boundaries (., ?, !, or start/end of text)
        # Look backwards to find sentence start
        sentence_start = 0
        for i in range(start_pos - 1, -1, -1):
            if text[i] in '.!?\n':
                # Check if it's truly end of sentence (not abbreviation like "Mr.")
                if i + 1 < len(text) and (text[i + 1].isspace() or text[i] == '\n'):
                    sentence_start = i + 1
                    break

        # Look forwards to find sentence end
        sentence_end = len(text)
        for i in range(end_pos, len(text)):
            if text[i] in '.!?':
                # Include the punctuation mark
                sentence_end = i + 1
                break

        # Extract complete sentence(s)
        # Optionally include surrounding sentences for more context
        context_start = sentence_start
        context_end = sentence_end

        # Try to include one sentence before if available
        if sentence_start > 0:
            for i in range(sentence_start - 2, -1, -1):
                if text[i] in '.!?\n':
                    if i + 1 < len(text) and (text[i + 1].isspace() or text[i] == '\n'):
                        context_start = i + 1
                        break

        # Try to include one sentence after if available
        if sentence_end < len(text):
            for i in range(sentence_end, min(sentence_end + 500, len(text))):
                if text[i] in '.!?':
                    if i + 1 < len(text) and (text[i + 1].isspace() or text[i] == '\n'):
                        context_end = i + 1
                        break

        # Get the full context
        context = text[context_start:context_end].strip()

        # Get the actual matched keyword from original text
        matched_keyword = text[start_pos:end_pos]

        occurrences.append({
            'context': context,
            'matched_text': matched_keyword,
            'position': start_pos
        })

    return occurrences[:10]  # Limit to 10 occurrences per contract


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def compare_contracts_upload(request):
    """
    Compare multiple uploaded contract files using semantic similarity analysis

    Expected files:
    - reference_file: The baseline contract (PDF or DOCX)
    - compare_files: 1-3 contracts to compare against reference
    - keywords: Optional comma-separated keywords
    """
    try:
        from .contract_comparison import compute_clause_similarity
        from .utils import extract_text_from_file, extract_clauses as extract_clauses_util

        reference_file = request.FILES.get('reference_file')
        compare_files = request.FILES.getlist('compare_files')
        keywords_str = request.data.get('keywords', '')

        if not reference_file:
            return Response(
                {'error': 'reference_file is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not compare_files or len(compare_files) == 0:
            return Response(
                {'error': 'At least one comparison file must be provided'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if len(compare_files) > 3:
            return Response(
                {'error': 'Maximum 3 contracts can be compared at once'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Parse keywords
        keywords = [k.strip() for k in keywords_str.split(',') if k.strip()] if keywords_str else []

        # Save uploaded files temporarily
        import tempfile
        temp_files = []

        try:
            # Extract text from reference file
            print('Extracting text from reference file...')
            ref_ext = os.path.splitext(reference_file.name)[1].lower()

            # Save reference file temporarily
            with tempfile.NamedTemporaryFile(suffix=ref_ext, delete=False) as temp_ref:
                for chunk in reference_file.chunks():
                    temp_ref.write(chunk)
                temp_ref_path = temp_ref.name
                temp_files.append(temp_ref_path)

            ref_result = extract_text_from_file(temp_ref_path, ref_ext)
            ref_text = ref_result.get('text', '') if isinstance(ref_result, dict) else ref_result
            ref_name = reference_file.name

            # Extract text from comparison files
            compare_texts = []
            for comp_file in compare_files:
                print(f'Extracting text from {comp_file.name}...')
                comp_ext = os.path.splitext(comp_file.name)[1].lower()

                # Save comparison file temporarily
                with tempfile.NamedTemporaryFile(suffix=comp_ext, delete=False) as temp_comp:
                    for chunk in comp_file.chunks():
                        temp_comp.write(chunk)
                    temp_comp_path = temp_comp.name
                    temp_files.append(temp_comp_path)

                result = extract_text_from_file(temp_comp_path, comp_ext)
                text = result.get('text', '') if isinstance(result, dict) else result
                compare_texts.append({
                    'name': comp_file.name,
                    'text': text
                })

            # Extract clauses
            print('Extracting clauses from reference...')
            ref_clauses_data = extract_clauses_util(ref_text)

            # Build risk comparison (simplified - keyword-based scoring)
            risk_comparison = []

            # Reference file risk assessment
            ref_keywords_found = 0
            if keywords:
                for kw in keywords:
                    if kw.lower() in ref_text.lower():
                        ref_keywords_found += 1

            ref_risk_score = min(ref_keywords_found * 10, 100)
            ref_risk_level = 'LOW' if ref_risk_score <= 30 else 'MEDIUM' if ref_risk_score <= 60 else 'HIGH' if ref_risk_score <= 80 else 'CRITICAL'

            risk_comparison.append({
                'contract_name': ref_name,
                'is_reference': True,
                'risk_level': ref_risk_level,
                'risk_score': ref_risk_score,
                'total_deviations': 0,
                'critical_issues': 0,
                'medium_issues': 0,
                'low_issues': 0
            })

            # Compare files risk assessment
            for comp_data in compare_texts:
                comp_keywords_found = 0
                if keywords:
                    for kw in keywords:
                        if kw.lower() in comp_data['text'].lower():
                            comp_keywords_found += 1

                comp_risk_score = min(comp_keywords_found * 10, 100)
                comp_risk_level = 'LOW' if comp_risk_score <= 30 else 'MEDIUM' if comp_risk_score <= 60 else 'HIGH' if comp_risk_score <= 80 else 'CRITICAL'

                risk_comparison.append({
                    'contract_name': comp_data['name'],
                    'is_reference': False,
                    'risk_level': comp_risk_level,
                    'risk_score': comp_risk_score,
                    'total_deviations': 0,
                    'critical_issues': 0,
                    'medium_issues': 0,
                    'low_issues': 0
                })

            # Clause comparison
            aligned_clauses = []

            for i, ref_clause in enumerate(ref_clauses_data[:15]):  # Limit for performance
                if not ref_clause.get('found'):
                    continue

                ref_clause_text = ref_clause.get('extractedText', '')
                if not ref_clause_text:
                    continue

                for comp_data in compare_texts:
                    comp_clauses = extract_clauses_util(comp_data['text'])

                    for comp_clause in comp_clauses[:15]:
                        if not comp_clause.get('found'):
                            continue

                        comp_clause_text = comp_clause.get('extractedText', '')
                        if not comp_clause_text:
                            continue

                        similarity = compute_clause_similarity(ref_clause_text, comp_clause_text)

                        if similarity > 0.5:  # Only show if > 50% similar
                            aligned_clauses.append({
                                'clause_type': ref_clause.get('clauseName', 'General'),
                                'similarity_score': similarity,
                                'clauses': [
                                    {
                                        'contract_name': ref_name,
                                        'is_reference': True,
                                        'text': ref_clause_text[:300]
                                    },
                                    {
                                        'contract_name': comp_data['name'],
                                        'is_reference': False,
                                        'text': comp_clause_text[:300]
                                    }
                                ]
                            })
                            break

            # Keyword matching with context extraction
            keyword_matches = {}
            if keywords:
                for keyword in keywords:
                    keyword_matches[keyword] = []

                    # Reference file
                    ref_occurrences = extract_keyword_contexts(ref_text, keyword)
                    keyword_matches[keyword].append({
                        'contract_name': ref_name,
                        'is_reference': True,
                        'count': len(ref_occurrences),
                        'occurrences': ref_occurrences
                    })

                    # Compare files
                    for comp_data in compare_texts:
                        comp_occurrences = extract_keyword_contexts(comp_data['text'], keyword)
                        keyword_matches[keyword].append({
                            'contract_name': comp_data['name'],
                            'is_reference': False,
                            'count': len(comp_occurrences),
                            'occurrences': comp_occurrences
                        })

            return Response({
                'risk_comparison': risk_comparison,
                'clause_comparison': {
                    'aligned_clauses': aligned_clauses[:30],
                    'total_aligned': len(aligned_clauses)
                },
                'missing_clauses': [],
                'keyword_matches': keyword_matches
            })

        finally:
            # Clean up temporary files
            for temp_file in temp_files:
                try:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                        print(f'Cleaned up temp file: {temp_file}')
                except Exception as e:
                    print(f'Failed to clean up temp file {temp_file}: {e}')

    except Exception as e:
        print(f'Contract comparison upload error: {str(e)}')
        import traceback
        traceback.print_exc()
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# =========================
# INTENT MINING ENDPOINTS
# =========================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def analyze_contract_intents(request, contract_id):
    """
    Analyze a contract to discover legal intents, obligations, and rights.

    This endpoint:
    1. Discovers legal intents from all contract clauses using LLM
    2. Normalizes and deduplicates similar intents
    3. Extracts obligations and rights for each intent
    4. Stores results in the database for later retrieval
    5. Auto-triggers compliance analysis after intent mining
    """
    try:
        from .intent_mining_service import IntentMiningService
        from .compliance_service import ComplianceDetectionService
        from core.models import Contract, ContractVersion
        import logging

        logger = logging.getLogger(__name__)

        # Get the latest version for this contract
        contract = Contract.objects.get(id=contract_id)
        latest_version = ContractVersion.objects.filter(contract=contract).order_by('-version_number').first()

        service = IntentMiningService()
        result = service.process_contract_clauses(
            contract_id=contract_id,
            contract_version_id=str(latest_version.id) if latest_version else None
        )

        if result.get('success'):
            return Response(result, status=status.HTTP_200_OK)
        else:
            return Response(
                {'error': result.get('error', 'Unknown error')},
                status=status.HTTP_400_BAD_REQUEST
            )

    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ========== INTENT DRIFT DETECTION ENDPOINTS ==========

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def compare_intent_versions(request, contract_id, version1_id, version2_id):
    """
    Compare intents, obligations, and rights between two contract versions.

    POST /contracts/{contract_id}/versions/{version1_id}/compare/{version2_id}

    Returns drift analysis with added/removed/modified items and risk delta.
    """
    try:
        # Verify contract access
        contract = Contract.objects.get(id=contract_id)
        if contract.user != request.user:
            return Response({'message': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)

        # Verify versions belong to this contract
        version1 = ContractVersion.objects.get(id=version1_id, contract=contract)
        version2 = ContractVersion.objects.get(id=version2_id, contract=contract)

        # Run drift analysis
        from .intent_drift_service import IntentDriftDetectionService
        service = IntentDriftDetectionService()

        result = service.compare_versions(str(version1_id), str(version2_id))

        if not result.get('success'):
            return Response(
                {'message': result.get('error', 'Drift analysis failed')},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response({
            'message': 'Drift analysis completed',
            'contractId': str(contract_id),
            'drift': result
        })

    except ContractVersion.DoesNotExist:
        return Response({'message': 'Version not found'}, status=status.HTTP_404_NOT_FOUND)
    except Contract.DoesNotExist:
        return Response({'message': 'Contract not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Version comparison error: {str(e)}")
        return Response(
            {'message': 'Comparison failed', 'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_drift_timeline(request, contract_id):
    """
    Get drift history for all sequential version comparisons.

    GET /contracts/{contract_id}/drift-timeline

    Returns array of drift comparisons: v1->v2, v2->v3, etc.
    """
    try:
        contract = Contract.objects.get(id=contract_id)
        if contract.user != request.user:
            return Response({'message': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)

        # Get all versions ordered by version number
        versions = ContractVersion.objects.filter(contract=contract).order_by('version_number')

        if versions.count() < 2:
            return Response({
                'contractId': str(contract_id),
                'timeline': [],
                'totalVersions': versions.count(),
                'totalComparisons': 0,
                'message': 'Need at least 2 versions for drift timeline'
            })

        from .intent_drift_service import IntentDriftDetectionService
        service = IntentDriftDetectionService()

        timeline = []
        version_list = list(versions)

        for i in range(len(version_list) - 1):
            v1 = version_list[i]
            v2 = version_list[i + 1]

            try:
                result = service.compare_versions(str(v1.id), str(v2.id))

                if result.get('success'):
                    timeline.append({
                        'from_version': v1.version_number,
                        'to_version': v2.version_number,
                        'from_version_id': str(v1.id),
                        'to_version_id': str(v2.id),
                        'drift_score': result.get('overall_drift_score', 0),
                        'risk_delta': result.get('risk_delta', {}).get('delta', 0),
                        'intent_changes': result.get('intent_drift', {}).get('change_count', 0),
                        'obligation_changes': result.get('obligation_drift', {}).get('change_count', 0),
                        'right_changes': result.get('right_drift', {}).get('change_count', 0),
                        'comparison_date': v2.created_at.isoformat() if v2.created_at else None
                    })
            except Exception as e:
                logger.error(f"Error comparing versions {v1.id} and {v2.id}: {str(e)}")
                continue

        return Response({
            'contractId': str(contract_id),
            'totalVersions': versions.count(),
            'totalComparisons': len(timeline),
            'timeline': timeline
        })

    except Contract.DoesNotExist:
        return Response({'message': 'Contract not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        import traceback
        logger.error(f"Drift timeline error: {str(e)}")
        traceback.print_exc()
        return Response(
            {'message': 'Failed to generate timeline', 'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def compare_contract_versions(request, contract_id, version1_id, version2_id):
    """
    Compare two specific contract versions to detect intent drift.

    GET /contracts/{contract_id}/versions/{version1_id}/compare/{version2_id}

    Returns detailed drift analysis between the two versions.
    """
    try:
        # Verify contract exists and belongs to user
        contract = Contract.objects.get(id=contract_id)
        if contract.user != request.user:
            return Response({'message': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)

        # Verify both versions exist and belong to the contract
        try:
            version1 = ContractVersion.objects.get(id=version1_id, contract=contract)
            version2 = ContractVersion.objects.get(id=version2_id, contract=contract)
        except ContractVersion.DoesNotExist:
            return Response(
                {'message': 'One or both versions not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Perform drift detection
        from .intent_drift_service import IntentDriftDetectionService
        service = IntentDriftDetectionService()

        result = service.compare_versions(str(version1_id), str(version2_id))

        if not result.get('success'):
            return Response(
                {'message': 'Failed to analyze drift', 'error': result.get('error')},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Return comprehensive drift analysis
        return Response({
            'success': True,
            'contractId': str(contract_id),
            'drift': {
                'version1': {
                    'id': str(version1.id),
                    'version_number': version1.version_number,
                    'created_at': version1.created_at.isoformat() if version1.created_at else None
                },
                'version2': {
                    'id': str(version2.id),
                    'version_number': version2.version_number,
                    'created_at': version2.created_at.isoformat() if version2.created_at else None
                },
                'overall_drift_score': result.get('overall_drift_score', 0),
                'intent_drift': result.get('intent_drift', {}),
                'obligation_drift': result.get('obligation_drift', {}),
                'right_drift': result.get('right_drift', {}),
                'risk_delta': result.get('risk_delta', {}),
                'summary': result.get('summary', '')
            }
        })

    except Contract.DoesNotExist:
        return Response({'message': 'Contract not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Version comparison error: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response(
            {'message': 'Failed to compare versions', 'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_version_intents(request, contract_id, version_id):
    """
    Get all intents, obligations, and rights for a specific version.

    GET /contracts/{contract_id}/versions/{version_id}/intents

    Returns complete intent data for version comparison UI.
    """
    try:
        contract = Contract.objects.get(id=contract_id)
        if contract.user != request.user:
            return Response({'message': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)

        version = ContractVersion.objects.get(id=version_id, contract=contract)

        # Get version-specific data
        clause_intents = ClauseIntent.objects.filter(contract_version=version).select_related('intent', 'clause')
        obligations = IntentObligation.objects.filter(contract_version=version).select_related('intent', 'clause')
        rights = IntentRight.objects.filter(contract_version=version).select_related('intent', 'clause')

        # Serialize
        from core.serializers import ClauseIntentSerializer, IntentObligationSerializer, IntentRightSerializer

        return Response({
            'contractId': str(contract_id),
            'versionId': str(version_id),
            'versionNumber': version.version_number,
            'intents': ClauseIntentSerializer(clause_intents, many=True).data,
            'obligations': IntentObligationSerializer(obligations, many=True).data,
            'rights': IntentRightSerializer(rights, many=True).data,
            'summary': {
                'total_intents': clause_intents.count(),
                'total_obligations': obligations.count(),
                'total_rights': rights.count()
            }
        })

    except ContractVersion.DoesNotExist:
        return Response({'message': 'Version not found'}, status=status.HTTP_404_NOT_FOUND)
    except Contract.DoesNotExist:
        return Response({'message': 'Contract not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Version intents error: {str(e)}")
        return Response(
            {'message': 'Failed to retrieve version intents', 'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_contract_intents(request, contract_id):
    """
    Get all discovered intents for a contract with their obligations and rights.
    """
    try:
        from core.models import Contract, Intent, ClauseIntent, IntentObligation, IntentRight
        from core.serializers import IntentSerializer, ClauseIntentSerializer, IntentObligationSerializer, IntentRightSerializer

        contract = Contract.objects.get(id=contract_id)

        # Get all intents discovered for this contract's clauses
        clause_ids = contract.clauses.filter(found=True).values_list('id', flat=True)
        clause_intents = ClauseIntent.objects.filter(clause_id__in=clause_ids).select_related('intent', 'clause')

        # Get unique intents
        intent_ids = clause_intents.values_list('intent_id', flat=True).distinct()
        intents = Intent.objects.filter(id__in=intent_ids)

        # For each intent, get obligations and rights
        intent_data = []
        for intent in intents:
            obligations = IntentObligation.objects.filter(
                intent=intent,
                clause_id__in=clause_ids
            )
            rights = IntentRight.objects.filter(
                intent=intent,
                clause_id__in=clause_ids
            )

            intent_data.append({
                'intent': IntentSerializer(intent).data,
                'clauses': ClauseIntentSerializer(
                    clause_intents.filter(intent=intent),
                    many=True
                ).data,
                'obligations': IntentObligationSerializer(obligations, many=True).data,
                'rights': IntentRightSerializer(rights, many=True).data,
                'obligation_count': obligations.count(),
                'rights_count': rights.count(),
            })

        return Response({
            'contract_id': contract_id,
            'total_intents': len(intent_data),
            'intents': intent_data
        }, status=status.HTTP_200_OK)

    except Contract.DoesNotExist:
        return Response(
            {'error': 'Contract not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_intents(request):
    """
    Get all discovered intents across all contracts.
    Used for portfolio analytics and visualization.
    """
    try:
        from core.models import Intent
        from core.serializers import IntentSerializer

        # Get query parameters
        min_occurrence = int(request.GET.get('min_occurrence', 1))
        limit = int(request.GET.get('limit', 50))

        # Get intents ordered by occurrence count
        intents = Intent.objects.filter(
            occurrence_count__gte=min_occurrence
        ).order_by('-occurrence_count')[:limit]

        serializer = IntentSerializer(intents, many=True)

        return Response({
            'total_intents': Intent.objects.count(),
            'filtered_intents': intents.count(),
            'intents': serializer.data
        }, status=status.HTTP_200_OK)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_intent_analytics(request):
    """
    Get analytics data for Intent Mining visualization.
    Returns data for pie charts, heatmaps, and portfolio insights.
    """
    try:
        from core.models import Intent, IntentObligation, IntentRight
        from django.db.models import Count, Avg, Q

        # Intent distribution by occurrence
        intent_distribution = list(Intent.objects.values(
            'name', 'occurrence_count', 'confidence'
        ).order_by('-occurrence_count')[:20])

        # Obligation priority distribution
        obligation_priority = list(IntentObligation.objects.values('priority').annotate(
            count=Count('id')
        ).order_by('priority'))

        # Obligation party distribution
        obligation_party = list(IntentObligation.objects.values('party').annotate(
            count=Count('id')
        ).order_by('party'))

        # Rights party distribution
        rights_party = list(IntentRight.objects.values('party').annotate(
            count=Count('id')
        ).order_by('party'))

        # High-risk obligations and rights
        high_risk_obligations = IntentObligation.objects.filter(
            risk_score__gte=0.7
        ).select_related('intent', 'clause').order_by('-risk_score')[:10]

        high_risk_rights = IntentRight.objects.filter(
            risk_score__gte=0.7
        ).select_related('intent', 'clause').order_by('-risk_score')[:10]

        # Average risk scores by intent
        intent_risk_scores = list(Intent.objects.annotate(
            avg_obligation_risk=Avg('obligations__risk_score'),
            avg_right_risk=Avg('rights__risk_score'),
            total_obligations=Count('obligations'),
            total_rights=Count('rights')
        ).filter(
            Q(total_obligations__gt=0) | Q(total_rights__gt=0)
        ).values(
            'name', 'avg_obligation_risk', 'avg_right_risk',
            'total_obligations', 'total_rights'
        ).order_by('-avg_obligation_risk')[:15])

        from core.serializers import IntentObligationSerializer, IntentRightSerializer

        return Response({
            'summary': {
                'total_intents': Intent.objects.count(),
                'total_obligations': IntentObligation.objects.count(),
                'total_rights': IntentRight.objects.count(),
                'high_risk_obligations_count': IntentObligation.objects.filter(risk_score__gte=0.7).count(),
                'high_risk_rights_count': IntentRight.objects.filter(risk_score__gte=0.7).count(),
            },
            'visualizations': {
                'intent_distribution': intent_distribution,
                'obligation_priority': obligation_priority,
                'obligation_party': obligation_party,
                'rights_party': rights_party,
                'intent_risk_scores': intent_risk_scores,
            },
            'high_risk_items': {
                'obligations': IntentObligationSerializer(high_risk_obligations, many=True).data,
                'rights': IntentRightSerializer(high_risk_rights, many=True).data,
            }
        }, status=status.HTTP_200_OK)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_portfolio_risk_score(request):
    """
    Calculate portfolio-wide risk score aggregation.

    Returns:
        - Overall portfolio risk score (0-1)
        - Risk by party (YOUR_COMPANY vs COUNTERPARTY exposure)
        - Risk by intent category
        - Top risk contributors (contracts, obligations, rights)
        - Party exposure analysis across all contracts

    GET /api/portfolio/risk
    """
    try:
        from core.models import Contract, IntentObligation, IntentRight, Intent, ClauseIntent
        from django.db.models import Avg, Count, Q, Max, Min, Sum

        # Get all user's contracts
        user_contracts = Contract.objects.filter(user=request.user)

        if not user_contracts.exists():
            return Response({
                'portfolio_risk_score': 0,
                'message': 'No contracts found'
            }, status=status.HTTP_200_OK)

        # ===== OVERALL PORTFOLIO RISK =====
        # Weighted average of obligation risk (60%) + rights risk (40%)
        obligation_stats = IntentObligation.objects.filter(
            clause__contract__in=user_contracts
        ).aggregate(
            avg_risk=Avg('risk_score'),
            total=Count('id'),
            high_risk_count=Count('id', filter=Q(risk_score__gte=0.7))
        )

        rights_stats = IntentRight.objects.filter(
            clause__contract__in=user_contracts
        ).aggregate(
            avg_risk=Avg('risk_score'),
            total=Count('id'),
            high_risk_count=Count('id', filter=Q(risk_score__gte=0.7))
        )

        obl_avg = obligation_stats['avg_risk'] or 0
        right_avg = rights_stats['avg_risk'] or 0

        portfolio_risk_score = (obl_avg * 0.6) + (right_avg * 0.4)

        # ===== PARTY EXPOSURE ANALYSIS =====
        # Aggregate obligations by party across all contracts
        party_obligations = IntentObligation.objects.filter(
            clause__contract__in=user_contracts
        ).values('party').annotate(
            count=Count('id'),
            avg_risk=Avg('risk_score'),
            high_risk_count=Count('id', filter=Q(risk_score__gte=0.7)),
            critical_count=Count('id', filter=Q(risk_score__gte=0.85))
        ).order_by('-avg_risk')

        party_rights = IntentRight.objects.filter(
            clause__contract__in=user_contracts
        ).values('party').annotate(
            count=Count('id'),
            avg_risk=Avg('risk_score'),
            high_risk_count=Count('id', filter=Q(risk_score__gte=0.7))
        ).order_by('-avg_risk')

        # ===== INTENT CATEGORY RISK =====
        # Risk breakdown by intent type
        intent_risk_breakdown = Intent.objects.annotate(
            obligation_count=Count('obligations', filter=Q(obligations__clause__contract__in=user_contracts)),
            rights_count=Count('rights', filter=Q(rights__clause__contract__in=user_contracts)),
            avg_obligation_risk=Avg('obligations__risk_score', filter=Q(obligations__clause__contract__in=user_contracts)),
            avg_rights_risk=Avg('rights__risk_score', filter=Q(rights__clause__contract__in=user_contracts))
        ).filter(
            Q(obligation_count__gt=0) | Q(rights_count__gt=0)
        ).values(
            'name',
            'obligation_count',
            'rights_count',
            'avg_obligation_risk',
            'avg_rights_risk'
        ).order_by('-avg_obligation_risk')[:15]

        # Calculate combined risk per intent
        for item in intent_risk_breakdown:
            obl_risk = item['avg_obligation_risk'] or 0
            right_risk = item['avg_rights_risk'] or 0
            item['combined_risk'] = (obl_risk * 0.6) + (right_risk * 0.4) if (obl_risk or right_risk) else 0

        # ===== TOP RISK CONTRIBUTORS =====
        # Top 10 high-risk obligations across portfolio
        high_risk_obligations = IntentObligation.objects.filter(
            clause__contract__in=user_contracts,
            risk_score__gte=0.7
        ).select_related('intent', 'clause__contract').order_by('-risk_score')[:10]

        # Top 10 high-risk rights
        high_risk_rights = IntentRight.objects.filter(
            clause__contract__in=user_contracts,
            risk_score__gte=0.7
        ).select_related('intent', 'clause__contract').order_by('-risk_score')[:10]

        # Top 5 riskiest contracts
        contract_risks = []
        for contract in user_contracts:
            obl_avg = IntentObligation.objects.filter(
                clause__contract=contract
            ).aggregate(avg=Avg('risk_score'))['avg'] or 0

            right_avg = IntentRight.objects.filter(
                clause__contract=contract
            ).aggregate(avg=Avg('risk_score'))['avg'] or 0

            combined = (obl_avg * 0.6) + (right_avg * 0.4)

            if combined > 0:
                contract_risks.append({
                    'contract_id': str(contract.id),
                    'filename': contract.original_filename,
                    'risk_score': round(combined, 3),
                    'obligation_avg_risk': round(obl_avg, 3),
                    'rights_avg_risk': round(right_avg, 3)
                })

        contract_risks.sort(key=lambda x: x['risk_score'], reverse=True)

        # ===== RISK SEVERITY DISTRIBUTION =====
        total_items = (obligation_stats['total'] or 0) + (rights_stats['total'] or 0)
        high_risk_items = (obligation_stats['high_risk_count'] or 0) + (rights_stats['high_risk_count'] or 0)

        return Response({
            'portfolio_risk_score': round(portfolio_risk_score, 3),
            'severity': 'HIGH' if portfolio_risk_score >= 0.7 else 'MEDIUM' if portfolio_risk_score >= 0.4 else 'LOW',
            'summary': {
                'total_contracts': user_contracts.count(),
                'total_obligations': obligation_stats['total'] or 0,
                'total_rights': rights_stats['total'] or 0,
                'high_risk_items': high_risk_items,
                'avg_obligation_risk': round(obl_avg, 3),
                'avg_rights_risk': round(right_avg, 3),
            },
            'party_exposure': {
                'obligations': list(party_obligations),
                'rights': list(party_rights),
            },
            'intent_risk_breakdown': list(intent_risk_breakdown),
            'top_risk_contributors': {
                'contracts': contract_risks[:5],
                'obligations': [
                    {
                        'id': str(obl.id),
                        'contract': obl.clause.contract.original_filename,
                        'intent': obl.intent.name,
                        'party': obl.party,
                        'action': obl.action[:100],
                        'risk_score': float(obl.risk_score),
                        'priority': obl.priority
                    }
                    for obl in high_risk_obligations
                ],
                'rights': [
                    {
                        'id': str(right.id),
                        'contract': right.clause.contract.original_filename,
                        'intent': right.intent.name,
                        'party': right.party,
                        'entitlement': right.entitlement[:100],
                        'risk_score': float(right.risk_score)
                    }
                    for right in high_risk_rights
                ]
            }
        }, status=status.HTTP_200_OK)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ==================== COMPLIANCE MAPPING ENDPOINTS ====================


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def analyze_contract_compliance(request, contract_id):
    """
    Analyze contract for compliance with all active frameworks.
    Auto-triggered after intent mining.

    POST /api/contracts/<contract_id>/compliance/analyze
    """
    try:
        from api.compliance_service import ComplianceDetectionService

        service = ComplianceDetectionService()
        result = service.analyze_contract_compliance(str(contract_id))

        if result['success']:
            return Response(result, status=status.HTTP_200_OK)
        else:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_contract_compliance(request, contract_id):
    """
    Get detailed compliance results for a contract.

    GET /api/contracts/<contract_id>/compliance
    """
    try:
        from core.models import ContractComplianceAnalysis, IntentComplianceMapping
        from core.serializers import IntentComplianceMappingSerializer

        contract = Contract.objects.get(id=contract_id)

        # Get or create analysis
        analysis, created = ContractComplianceAnalysis.objects.get_or_create(
            contract=contract,
            defaults={
                'overall_compliance_score': 0.0,
                'analysis_completed_at': timezone.now()
            }
        )

        # Get all mappings
        mappings = IntentComplianceMapping.objects.filter(
            contract=contract
        ).select_related('intent', 'requirement', 'requirement__framework')

        return Response({
            'contract': {
                'id': str(contract.id),
                'filename': contract.original_filename,
                'contract_type': contract.contract_type
            },
            'analysis': {
                'overall_compliance_score': analysis.overall_compliance_score,
                'total_requirements_checked': analysis.total_requirements_checked,
                'compliant_count': analysis.compliant_count,
                'partial_count': analysis.partial_count,
                'non_compliant_count': analysis.non_compliant_count,
                'compliance_risk_score': analysis.compliance_risk_score,
                'critical_violations': analysis.critical_violations,
                'high_violations': analysis.high_violations,
                'medium_violations': analysis.medium_violations,
                'low_violations': analysis.low_violations,
                'analysis_completed_at': analysis.analysis_completed_at.isoformat() if analysis.analysis_completed_at else None
            },
            'framework_scores': analysis.framework_scores,
            'mappings': IntentComplianceMappingSerializer(mappings, many=True).data
        }, status=status.HTTP_200_OK)

    except Contract.DoesNotExist:
        return Response(
            {'error': 'Contract not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_compliance_dashboard(request):
    """
    Portfolio-wide compliance analytics.

    GET /api/compliance/dashboard
    """
    try:
        from core.models import ContractComplianceAnalysis

        analyses = ContractComplianceAnalysis.objects.all()

        if not analyses.exists():
            return Response({
                'summary': {
                    'total_contracts_analyzed': 0,
                    'avg_compliance_score': 0,
                    'total_violations': 0,
                    'critical_violations': 0
                }
            }, status=status.HTTP_200_OK)

        total_contracts = analyses.count()
        avg_score = analyses.aggregate(Avg('overall_compliance_score'))['overall_compliance_score__avg'] or 0
        total_violations = analyses.aggregate(Count('id'))['id__count'] or 0

        return Response({
            'summary': {
                'total_contracts_analyzed': total_contracts,
                'avg_compliance_score': round(avg_score, 1),
                'total_violations': total_violations,
                'critical_violations': sum(a.critical_violations for a in analyses)
            },
            'visualizations': {
                'framework_distribution': [
                    {'framework': 'GDPR', 'avg_score': 75.0},
                    {'framework': 'SOX', 'avg_score': 85.0},
                    {'framework': 'HIPAA', 'avg_score': 70.0},
                    {'framework': 'GST', 'avg_score': 80.0}
                ]
            }
        }, status=status.HTTP_200_OK)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_compliance_frameworks(request):
    """
    Get all compliance frameworks and their requirements.

    GET /api/compliance/frameworks
    """
    try:
        from core.models import ComplianceFramework, ComplianceRequirement

        frameworks = ComplianceFramework.objects.filter(is_active=True)

        data = []
        for fw in frameworks:
            reqs = ComplianceRequirement.objects.filter(
                framework=fw,
                is_active=True
            )
            data.append({
                'code': fw.code,
                'name': fw.name,
                'description': fw.description,
                'jurisdiction': fw.jurisdiction,
                'requirements_count': reqs.count(),
                'requirements': [
                    {
                        'code': r.requirement_code,
                        'name': r.requirement_name,
                        'type': r.requirement_type,
                        'criticality': r.criticality
                    }
                    for r in reqs
                ]
            })

        return Response({'frameworks': data}, status=status.HTTP_200_OK)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ======================
# NEGOTIATION AGENT ENDPOINTS
# ======================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def analyze_clause_for_negotiation(request, contract_id, clause_id):
    """
    Generate AI-powered rewrite suggestions for a clause.

    POST /contracts/<id>/clauses/<id>/analyze-negotiation
    Body: {
        "perspective": "BUYER" | "SELLER"  (optional, defaults to BUYER)
    }
    """
    try:
        from .negotiation_service import NegotiationAgentService
        from core.models import Clause
        from core.serializers import ClauseRewriteSuggestionSerializer

        clause = Clause.objects.select_related('contract').get(
            id=clause_id,
            contract_id=contract_id
        )

        perspective = request.data.get('perspective', 'BUYER')
        if perspective not in ['BUYER', 'SELLER']:
            perspective = 'BUYER'

        service = NegotiationAgentService()
        suggestions = service.analyze_clause_for_negotiation(
            clause=clause,
            user=request.user,
            perspective=perspective
        )

        serializer = ClauseRewriteSuggestionSerializer(suggestions, many=True)
        return Response({
            'success': True,
            'clause_id': clause_id,
            'clause_name': clause.clause_name,
            'perspective': perspective,
            'suggestions_count': len(suggestions),
            'suggestions': serializer.data
        }, status=status.HTTP_200_OK)

    except Clause.DoesNotExist:
        return Response(
            {'success': False, 'error': 'Clause not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response(
            {'success': False, 'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_contract_suggestions(request, contract_id):
    """
    Get all rewrite suggestions for a contract.

    GET /contracts/<id>/negotiation-suggestions?status=PENDING
    """
    try:
        from core.models import ClauseRewriteSuggestion
        from core.serializers import ClauseRewriteSuggestionSerializer

        filters = {'contract_id': contract_id}

        # Optional status filter
        req_status = request.query_params.get('status')
        if req_status:
            filters['status'] = req_status

        suggestions = ClauseRewriteSuggestion.objects.filter(**filters).select_related(
            'clause', 'contract', 'created_by', 'reviewed_by'
        ).order_by('-priority', '-created_at')

        serializer = ClauseRewriteSuggestionSerializer(suggestions, many=True)
        return Response({
            'success': True,
            'count': suggestions.count(),
            'suggestions': serializer.data
        }, status=status.HTTP_200_OK)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response(
            {'success': False, 'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_suggestion_status(request, suggestion_id):
    """
    Accept or reject a suggestion.

    POST /negotiation-suggestions/<id>/update-status
    Body: {
        "action": "ACCEPT" | "REJECT",
        "modified_text": "..."  (optional, for ACCEPT with modifications)
    }
    """
    try:
        from .negotiation_service import NegotiationAgentService
        from core.serializers import ClauseRewriteSuggestionSerializer

        action = request.data.get('action')
        modified_text = request.data.get('modified_text')

        if action not in ['ACCEPT', 'REJECT']:
            return Response(
                {'success': False, 'error': 'Invalid action. Must be ACCEPT or REJECT'},
                status=status.HTTP_400_BAD_REQUEST
            )

        service = NegotiationAgentService()

        if action == 'ACCEPT':
            suggestion = service.accept_suggestion(
                suggestion_id=suggestion_id,
                user=request.user,
                modified_text=modified_text
            )
        else:  # REJECT
            suggestion = service.reject_suggestion(
                suggestion_id=suggestion_id,
                user=request.user
            )

        serializer = ClauseRewriteSuggestionSerializer(suggestion)
        return Response({
            'success': True,
            'action': action,
            'suggestion': serializer.data
        }, status=status.HTTP_200_OK)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response(
            {'success': False, 'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ======================
# KNOWLEDGE GRAPH ENDPOINTS
# ======================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def sync_contract_to_graph(request, contract_id):
    """
    Sync a contract to Neo4j knowledge graph.

    POST /contracts/<id>/sync-to-graph
    """
    try:
        from .knowledge_graph_service import KnowledgeGraphService

        service = KnowledgeGraphService()
        result = service.sync_contract_to_graph(str(contract_id))
        service.close()

        if result['success']:
            return Response(result, status=status.HTTP_200_OK)
        else:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response(
            {'success': False, 'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_contract_graph(request, contract_id):
    """
    Get the knowledge graph visualization data for a contract.

    GET /contracts/<id>/graph
    Returns nodes and edges for visualization.
    """
    try:
        from .knowledge_graph_service import KnowledgeGraphService

        service = KnowledgeGraphService()
        graph_data = service.get_contract_subgraph(str(contract_id))
        service.close()

        return Response({
            'success': True,
            'contract_id': contract_id,
            'graph': graph_data
        }, status=status.HTTP_200_OK)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response(
            {'success': False, 'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def find_similar_contracts_graph(request, contract_id):
    """
    Find contracts similar to this one based on knowledge graph analysis.

    GET /contracts/<id>/similar?limit=5
    """
    try:
        from .knowledge_graph_service import KnowledgeGraphService

        limit = int(request.query_params.get('limit', 5))

        service = KnowledgeGraphService()
        similar = service.find_similar_contracts(str(contract_id), limit=limit)
        service.close()

        return Response({
            'success': True,
            'contract_id': contract_id,
            'similar_contracts': similar
        }, status=status.HTTP_200_OK)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response(
            {'success': False, 'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def query_knowledge_graph(request):
    """
    Execute a custom Cypher query on the knowledge graph.

    POST /knowledge-graph/query
    Body: {
        "query": "MATCH (c:Contract) WHERE c.riskLevel = 'HIGH' RETURN c",
        "parameters": {}
    }
    """
    try:
        from .knowledge_graph_service import KnowledgeGraphService

        cypher_query = request.data.get('query')
        parameters = request.data.get('parameters', {})

        if not cypher_query:
            return Response(
                {'success': False, 'error': 'Query is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        service = KnowledgeGraphService()
        results = service.query_graph(cypher_query, parameters)
        service.close()

        return Response({
            'success': True,
            'results': results
        }, status=status.HTTP_200_OK)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response(
            {'success': False, 'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# =======================
# Clause Heatmap Endpoints
# =======================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_clause_heatmap(request):
    """
    GET /api/clause-heatmap/portfolio

    Returns portfolio-wide clause risk heatmap with:
    - Risk matrix (likelihood vs impact)
    - Key metrics
    - Top risky clauses
    - Breakdown by clause type
    """
    try:
        from .clause_heatmap_service import clause_heatmap_service

        user_id = request.user.id
        heatmap_data = clause_heatmap_service.get_portfolio_heatmap(user_id)

        return Response({
            'success': True,
            'data': heatmap_data
        }, status=status.HTTP_200_OK)

    except Exception as e:
        import traceback
        logger.error(f"Clause heatmap error: {str(e)}")
        traceback.print_exc()
        return Response({
            'success': False,
            'error': 'Failed to generate clause heatmap',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def enrich_contract_clauses(request, contract_id):
    """
    POST /api/contracts/<contract_id>/clauses/enrich

    Trigger risk enrichment for all clauses in a contract.
    """
    try:
        from .clause_heatmap_service import clause_heatmap_service

        contract = Contract.objects.get(id=contract_id, user=request.user)
        clauses = Clause.objects.filter(contract=contract, found=True)

        enriched_count = 0
        for clause in clauses:
            try:
                clause_heatmap_service.enrich_clause_risk(clause)
                enriched_count += 1
            except Exception as e:
                logger.error(f"Failed to enrich clause {clause.id}: {str(e)}")

        return Response({
            'success': True,
            'message': f'Enriched {enriched_count} clauses',
            'contract_id': str(contract_id),
            'enriched_count': enriched_count
        }, status=status.HTTP_200_OK)

    except Contract.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Contract not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        import traceback
        logger.error(f"Clause enrichment error: {str(e)}")
        traceback.print_exc()
        return Response({
            'success': False,
            'error': 'Failed to enrich clauses',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# =======================
# URL Aliases for Frontend Compatibility
# =======================

# Alias for negotiation suggestions endpoint
get_negotiation_suggestions = get_contract_suggestions

# Alias for update suggestion status endpoint
update_negotiation_suggestion_status = update_suggestion_status


# =======================
# AI CHAT IMPROVEMENTS
# Features: Conversation History, Caching, Page Numbers, Streaming
# =======================

import hashlib
import uuid
from django.db import connection
from django.http import StreamingHttpResponse
import PyPDF2
import io

# ============ HELPER FUNCTIONS ============

def get_db_connection():
    """Get raw database connection for direct SQL queries"""
    return connection

def create_conversation(user_id):
    """Create a new conversation"""
    conversation_id = str(uuid.uuid4())
    with get_db_connection().cursor() as cursor:
        cursor.execute("""
            INSERT INTO chat_conversations (id, userId, title, lastMessageAt, createdAt, updatedAt)
            VALUES (%s, %s, %s, NOW(), NOW(), NOW())
        """, [conversation_id, user_id, 'New Conversation'])
    return conversation_id

def save_message(conversation_id, role, content, sources=None, page_numbers=None, contract_ids=None):
    """Save a chat message"""
    message_id = str(uuid.uuid4())
    with get_db_connection().cursor() as cursor:
        cursor.execute("""
            INSERT INTO chat_messages
            (id, conversationId, role, content, sources, pageNumbers, contractIds, createdAt)
            VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
        """, [
            message_id, conversation_id, role, content,
            json.dumps(sources) if sources else None,
            json.dumps(page_numbers) if page_numbers else None,
            json.dumps(contract_ids) if contract_ids else None
        ])

        # Update conversation's lastMessageAt
        cursor.execute("""
            UPDATE chat_conversations
            SET lastMessageAt = NOW(), updatedAt = NOW()
            WHERE id = %s
        """, [conversation_id])

    return message_id

def get_conversation_history(conversation_id, limit=10):
    """Get recent messages from a conversation"""
    with get_db_connection().cursor() as cursor:
        cursor.execute("""
            SELECT role, content, sources, pageNumbers, contractIds, createdAt
            FROM chat_messages
            WHERE conversationId = %s
            ORDER BY createdAt DESC
            LIMIT %s
        """, [conversation_id, limit])

        columns = [col[0] for col in cursor.description]
        messages = []
        for row in cursor.fetchall():
            msg = dict(zip(columns, row))
            # Parse JSON fields
            if msg['sources']:
                msg['sources'] = json.loads(msg['sources']) if isinstance(msg['sources'], str) else msg['sources']
            if msg['pageNumbers']:
                msg['pageNumbers'] = json.loads(msg['pageNumbers']) if isinstance(msg['pageNumbers'], str) else msg['pageNumbers']
            if msg['contractIds']:
                msg['contractIds'] = json.loads(msg['contractIds']) if isinstance(msg['contractIds'], str) else msg['contractIds']
            messages.append(msg)

        return list(reversed(messages))  # Return in chronological order

def generate_cache_key(query, contract_ids=None):
    """Generate cache key for a query"""
    cache_string = query.lower().strip()
    if contract_ids:
        cache_string += '|' + '|'.join(sorted(contract_ids))
    return hashlib.sha256(cache_string.encode()).hexdigest()

def get_cached_response(query_hash):
    """Get cached response if exists and not expired"""
    with get_db_connection().cursor() as cursor:
        cursor.execute("""
            SELECT response, sources, pageNumbers, contractIds
            FROM chat_cache
            WHERE queryHash = %s AND (expiresAt IS NULL OR expiresAt > NOW())
        """, [query_hash])

        row = cursor.fetchone()
        if row:
            # Update hit count and last accessed
            cursor.execute("""
                UPDATE chat_cache
                SET hitCount = hitCount + 1, lastAccessedAt = NOW()
                WHERE queryHash = %s
            """, [query_hash])

            return {
                'response': row[0],
                'sources': json.loads(row[1]) if row[1] else [],
                'pageNumbers': json.loads(row[2]) if row[2] else {},
                'contractIds': json.loads(row[3]) if row[3] else []
            }
    return None

def save_to_cache(query, query_hash, response, sources=None, page_numbers=None, contract_ids=None, ttl_hours=24):
    """Save response to cache"""
    cache_id = str(uuid.uuid4())
    with get_db_connection().cursor() as cursor:
        cursor.execute("""
            INSERT INTO chat_cache
            (id, queryHash, query, response, sources, pageNumbers, contractIds, createdAt, expiresAt, lastAccessedAt)
            VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), DATE_ADD(NOW(), INTERVAL %s HOUR), NOW())
            ON DUPLICATE KEY UPDATE
                response = VALUES(response),
                sources = VALUES(sources),
                pageNumbers = VALUES(pageNumbers),
                contractIds = VALUES(contractIds),
                hitCount = hitCount + 1,
                lastAccessedAt = NOW()
        """, [
            cache_id, query_hash, query, response,
            json.dumps(sources) if sources else None,
            json.dumps(page_numbers) if page_numbers else None,
            json.dumps(contract_ids) if contract_ids else None,
            ttl_hours
        ])

def extract_page_numbers_from_pdf(file_path, search_text):
    """Extract page numbers where text appears in PDF"""
    page_numbers = []
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            search_text_lower = search_text.lower()[:200]  # First 200 chars

            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                page_text = page.extract_text().lower()

                if search_text_lower in page_text:
                    page_numbers.append(page_num + 1)  # 1-indexed

                if len(page_numbers) >= 3:  # Limit to first 3 pages
                    break
    except Exception as e:
        print(f"[PAGE EXTRACTION ERROR] {str(e)}")

    return page_numbers

def log_analytics(user_id, query, contract_id=None, response_time=None, was_cached=False):
    """Log analytics for chat queries"""
    analytics_id = str(uuid.uuid4())
    with get_db_connection().cursor() as cursor:
        cursor.execute("""
            INSERT INTO chat_analytics
            (id, userId, query, contractId, responseTime, wasCached, timestamp)
            VALUES (%s, %s, %s, %s, %s, %s, NOW())
        """, [analytics_id, user_id, query, contract_id, response_time, 1 if was_cached else 0])

# ============ API ENDPOINTS ============

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_conversations(request):
    """Get all conversations for the current user"""
    try:
        user_id = request.user.id

        with get_db_connection().cursor() as cursor:
            cursor.execute("""
                SELECT c.id, c.title, c.lastMessageAt, c.createdAt,
                       (SELECT COUNT(*) FROM chat_messages WHERE conversationId = c.id) as messageCount
                FROM chat_conversations c
                WHERE c.userId = %s
                ORDER BY c.lastMessageAt DESC
                LIMIT 50
            """, [user_id])

            columns = [col[0] for col in cursor.description]
            conversations = [dict(zip(columns, row)) for row in cursor.fetchall()]

        return Response({
            'conversations': conversations
        })
    except Exception as e:
        print(f"[GET CONVERSATIONS ERROR] {str(e)}")
        return Response({'error': str(e)}, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_conversation_messages(request, conversation_id):
    """Get messages for a specific conversation"""
    try:
        user_id = request.user.id

        # Verify conversation belongs to user
        with get_db_connection().cursor() as cursor:
            cursor.execute("""
                SELECT id FROM chat_conversations
                WHERE id = %s AND userId = %s
            """, [conversation_id, user_id])

            if not cursor.fetchone():
                return Response({'error': 'Conversation not found'}, status=404)

        messages = get_conversation_history(conversation_id, limit=100)

        return Response({
            'conversation_id': conversation_id,
            'messages': messages
        })
    except Exception as e:
        print(f"[GET MESSAGES ERROR] {str(e)}")
        return Response({'error': str(e)}, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_suggested_questions(request):
    """Get suggested questions based on contract type"""
    try:
        contract_type = request.GET.get('contractType', 'General')

        with get_db_connection().cursor() as cursor:
            cursor.execute("""
                SELECT id, question, category, priority
                FROM suggested_questions
                WHERE contractType = %s AND isActive = 1
                ORDER BY priority DESC
                LIMIT 10
            """, [contract_type])

            columns = [col[0] for col in cursor.description]
            questions = [dict(zip(columns, row)) for row in cursor.fetchall()]

        return Response({
            'questions': questions
        })
    except Exception as e:
        print(f"[GET SUGGESTED QUESTIONS ERROR] {str(e)}")
        return Response({'error': str(e)}, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_chat_analytics(request):
    """Get chat analytics for the current user"""
    try:
        user_id = request.user.id
        days = int(request.GET.get('days', 7))

        with get_db_connection().cursor() as cursor:
            # Most asked questions
            cursor.execute("""
                SELECT query, COUNT(*) as count
                FROM chat_analytics
                WHERE userId = %s AND timestamp >= DATE_SUB(NOW(), INTERVAL %s DAY)
                GROUP BY query
                ORDER BY count DESC
                LIMIT 10
            """, [user_id, days])

            top_questions = [{'query': row[0], 'count': row[1]} for row in cursor.fetchall()]

            # Most queried contracts
            cursor.execute("""
                SELECT c.originalFilename, COUNT(*) as count
                FROM chat_analytics ca
                JOIN contracts c ON ca.contractId = c.id
                WHERE ca.userId = %s AND ca.timestamp >= DATE_SUB(NOW(), INTERVAL %s DAY)
                GROUP BY c.id
                ORDER BY count DESC
                LIMIT 10
            """, [user_id, days])

            top_contracts = [{'filename': row[0], 'count': row[1]} for row in cursor.fetchall()]

            # Average response time
            cursor.execute("""
                SELECT AVG(responseTime) as avg_time,
                       SUM(CASE WHEN wasCached = 1 THEN 1 ELSE 0 END) as cached_count,
                       COUNT(*) as total_count
                FROM chat_analytics
                WHERE userId = %s AND timestamp >= DATE_SUB(NOW(), INTERVAL %s DAY)
            """, [user_id, days])

            row = cursor.fetchone()
            stats = {
                'avg_response_time': round(row[0]) if row[0] else 0,
                'cached_responses': row[1],
                'total_queries': row[2],
                'cache_hit_rate': round((row[1] / row[2] * 100) if row[2] > 0 else 0, 1)
            }

        return Response({
            'top_questions': top_questions,
            'top_contracts': top_contracts,
            'stats': stats
        })
    except Exception as e:
        print(f"[GET ANALYTICS ERROR] {str(e)}")
        return Response({'error': str(e)}, status=500)




# =========================
# CLAUSE EDITING ENDPOINTS
# =========================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_contract_clauses_for_editing(request, contract_id):
    """
    Get all clauses from a contract for editing

    GET /api/contracts/<contract_id>/clauses/edit

    Returns:
        - contract info (filename, status, can_edit)
        - list of all clauses with current text and risk scores
        - version history count for each clause
    """
    from .clause_edit_service import clause_edit_service

    try:
        result = clause_edit_service.get_contract_clauses_for_editing(contract_id)
        return Response(result)
    except Exception as e:
        logger.error(f"Error getting clauses for editing: {str(e)}")
        return Response({'success': False, 'error': str(e)}, status=500)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_clause_text(request, clause_id):
    """
    Update a clause with new text

    PUT /api/clauses/<clause_id>/edit

    Body:
        {
            "modified_text": "New clause text",
            "change_description": "Explanation of what changed"
        }

    Returns:
        - new clause version info
        - original vs new risk scores
        - risk improvement indicator
    """
    from .clause_edit_service import clause_edit_service

    try:
        modified_text = request.data.get('modified_text')
        change_description = request.data.get('change_description', '')

        if not modified_text:
            return Response(
                {'success': False, 'error': 'modified_text is required'},
                status=400
            )

        result = clause_edit_service.update_clause(
            clause_id=clause_id,
            modified_text=modified_text,
            change_description=change_description,
            user_id=str(request.user.id)
        )

        if result['success']:
            return Response(result)
        else:
            return Response(result, status=400)

    except Exception as e:
        logger.error(f"Error updating clause: {str(e)}")
        return Response({'success': False, 'error': str(e)}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_clause_version_history(request, clause_id):
    """
    Get version history for a clause

    GET /api/clauses/<clause_id>/versions

    Returns:
        - clause info
        - list of all versions with changes and risk scores
    """
    from .clause_edit_service import clause_edit_service

    try:
        result = clause_edit_service.get_clause_version_history(clause_id)
        return Response(result)
    except Exception as e:
        logger.error(f"Error getting version history: {str(e)}")
        return Response({'success': False, 'error': str(e)}, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def regenerate_modified_contract(request, contract_id):
    """
    Regenerate contract with all modified clauses

    POST /api/contracts/<contract_id>/regenerate

    Body (optional):
        {
            "output_format": "pdf" | "docx"  (default: "pdf")
        }

    Returns:
        - new contract version info
        - download path
        - file size
        - change summary
    """
    from .clause_edit_service import clause_edit_service

    try:
        output_format = request.data.get('output_format', 'pdf')

        result = clause_edit_service.regenerate_contract(
            contract_id=contract_id,
            user_id=str(request.user.id),
            output_format=output_format
        )

        if result['success']:
            return Response(result)
        else:
            return Response(result, status=400)

    except Exception as e:
        logger.error(f"Error regenerating contract: {str(e)}")
        return Response({'success': False, 'error': str(e)}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def download_modified_contract(request, version_id):
    """
    Download a specific contract version

    GET /api/contract-versions/<version_id>/download

    Returns:
        File download response
    """
    from core.models import ContractVersion
    from django.http import FileResponse
    import os

    try:
        contract_version = ContractVersion.objects.get(id=version_id)

        # Check if file exists
        if not os.path.exists(contract_version.file_path):
            return Response(
                {'success': False, 'error': 'Contract file not found'},
                status=404
            )

        # Return file
        response = FileResponse(
            open(contract_version.file_path, 'rb'),
            content_type='application/pdf'
        )
        response['Content-Disposition'] = f'attachment; filename="{contract_version.filename}"'

        return response

    except ContractVersion.DoesNotExist:
        return Response(
            {'success': False, 'error': 'Contract version not found'},
            status=404
        )
    except Exception as e:
        logger.error(f"Error downloading contract version: {str(e)}")
        return Response({'success': False, 'error': str(e)}, status=500)


# =========================
# AI SUGGESTION ENDPOINTS
# =========================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def get_ai_suggestion(request):
    """
    Get AI suggestion for selected contract text

    POST /api/ai/suggest-improvement

    Body:
        {
            "selected_text": "The text user selected",
            "context": "Optional surrounding context for better suggestions"
        }

    Returns:
        {
            "success": true,
            "original_text": "...",
            "suggested_text": "Improved version",
            "improvements": ["List of changes made"],
            "reasoning": "Why these changes help"
        }
    """
    from .ai_suggestion_service import ai_suggestion_service

    try:
        selected_text = request.data.get('selected_text')
        context = request.data.get('context', '')

        if not selected_text or not selected_text.strip():
            return Response(
                {'success': False, 'error': 'selected_text is required'},
                status=400
            )

        result = ai_suggestion_service.suggest_improvement(selected_text, context)

        if result['success']:
            return Response(result)
        else:
            return Response(result, status=500)

    except Exception as e:
        logger.error(f"Error getting AI suggestion: {str(e)}")
        return Response({'success': False, 'error': str(e)}, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def get_ai_alternatives(request):
    """
    Get multiple alternative phrasings for selected text

    POST /api/ai/suggest-alternatives

    Body:
        {
            "selected_text": "The text to generate alternatives for",
            "num_alternatives": 3
        }

    Returns:
        {
            "success": true,
            "original_text": "...",
            "alternatives": [
                {
                    "text": "Alternative version",
                    "risk_level": "LOW/MEDIUM/HIGH",
                    "reason": "Why this version works"
                },
                ...
            ]
        }
    """
    from .ai_suggestion_service import ai_suggestion_service

    try:
        selected_text = request.data.get('selected_text')
        num_alternatives = request.data.get('num_alternatives', 3)

        if not selected_text or not selected_text.strip():
            return Response(
                {'success': False, 'error': 'selected_text is required'},
                status=400
            )

        result = ai_suggestion_service.suggest_alternatives(selected_text, num_alternatives)

        if result['success']:
            return Response(result)
        else:
            return Response(result, status=500)

    except Exception as e:
        logger.error(f"Error getting AI alternatives: {str(e)}")
        return Response({'success': False, 'error': str(e)}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_counterparty_portfolio_heatmap(request):
    """
    Get portfolio-level counterparty risk heatmap for CFO/CRO dashboard.

    Returns aggregated counterparty risk metrics:
    - Reliability scores (behavior-based from negotiation history)
    - Financial exposure (contract value + liabilities + silent risks)
    - Failure probability (Bayesian inference)
    - Risk quadrants (immediate action / monitor / safe)
    """
    try:
        from .counterparty_portfolio_service import counterparty_portfolio_service

        user_id = str(request.user.id)
        result = counterparty_portfolio_service.get_portfolio_heatmap(user_id)

        return Response({
            'success': True,
            'data': result
        }, status=200)

    except Exception as e:
        logger.error(f"Error generating counterparty portfolio heatmap: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_contract_portfolio_risk_detail(request, contract_id):
    """
    Get detailed portfolio-level risk intelligence for a specific contract.

    This provides CFO/CRO-level insights including:
    - Counterparty profile & reliability breakdown (acceptance, stall, redline, deviation)
    - Financial exposure decomposition (contract value + liability + silent risks)
    - Bayesian failure probability with explanation
    - Portfolio context (% of total exposure, related contracts)
    - Risk quadrant classification
    - Recommended actions based on risk profile

    This transforms contract detail view from legal document viewer
    to executive risk intelligence surface.
    """
    try:
        from .counterparty_portfolio_service import counterparty_portfolio_service

        result = counterparty_portfolio_service.get_contract_risk_detail(str(contract_id))

        return Response({
            'success': True,
            'data': result
        }, status=200)

    except Contract.DoesNotExist:
        return Response({
            'success': False,
            'error': f'Contract {contract_id} not found'
        }, status=404)

    except Exception as e:
        logger.error(f"Error fetching contract portfolio risk detail: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def contract_graph_dashboard(request, contract_id):
    """
    Contract Graph Intelligence Dashboard Data
    ===========================================

    GET /api/contracts/<contract_id>/graph-dashboard

    Returns pre-computed graph analysis for immediate dashboard rendering:
    - NetworkX clause interaction graph (nodes/edges)
    - Risk propagation timeline
    - Negotiation priority advice
    - Graph metrics and hotspots

    This endpoint serves the Graph Intelligence Dashboard (Phase 1)
    Data is pre-computed during contract upload, so this is very fast.
    """
    try:
        from core.models import Contract, ContractGraphMeta, Clause

        # Verify contract exists and user has access
        contract = Contract.objects.get(id=contract_id, user=request.user)

        # Try to get pre-computed graph metadata
        try:
            graph_meta = ContractGraphMeta.objects.get(contract=contract)

            response_data = {
                'success': True,
                'contract_id': str(contract.id),
                'contract_name': contract.filename,
                'graph_summary': graph_meta.graph_summary,
                'risk_timeline': graph_meta.risk_timeline,
                'negotiation_advice': graph_meta.negotiation_advice,
                'neo4j_synced': graph_meta.neo4j_synced,
                'created_at': graph_meta.created_at.isoformat(),
                'updated_at': graph_meta.updated_at.isoformat(),
            }

            return Response(response_data)

        except ContractGraphMeta.DoesNotExist:
            # Graph not built yet - trigger rebuild
            logger.warning(f"Graph metadata not found for contract {contract_id}, triggering rebuild")

            from api.services.graph_orchestrator import build_all_graphs

            # Get clauses - try found=True first, then all clauses
            clauses = list(Clause.objects.filter(contract=contract, found=True))

            # If no found clauses, try getting all clauses (some may have found=False but still be useful)
            if not clauses:
                clauses = list(Clause.objects.filter(contract=contract))
                logger.info(f"No found=True clauses, using all {len(clauses)} clauses for contract {contract_id}")

            if not clauses:
                # Return empty graph state instead of error
                logger.warning(f"No clauses at all for contract {contract_id}")

                # Create empty graph metadata
                empty_graph_meta = ContractGraphMeta.objects.create(
                    contract=contract,
                    graph_summary={"nodes": [], "edges": [], "metrics": {"total_nodes": 0, "total_edges": 0, "density": 0}},
                    risk_timeline={"timeline": [], "total_risk": 0, "hotspots": [], "risk_map": {}, "propagation_steps": 0},
                    negotiation_advice=[],
                    neo4j_synced=False,
                )

                return Response({
                    'success': True,
                    'contract_id': str(contract.id),
                    'contract_name': contract.filename,
                    'graph_summary': empty_graph_meta.graph_summary,
                    'risk_timeline': empty_graph_meta.risk_timeline,
                    'negotiation_advice': empty_graph_meta.negotiation_advice,
                    'neo4j_synced': False,
                    'created_at': empty_graph_meta.created_at.isoformat(),
                    'updated_at': empty_graph_meta.updated_at.isoformat(),
                    'warning': 'No clauses found for this contract. Please extract clauses first.',
                    'rebuilt': True,
                })

            # Build graphs now
            try:
                graph_result = build_all_graphs(contract, clauses)
            except Exception as graph_error:
                logger.error(f"Error building graphs for contract {contract_id}: {graph_error}", exc_info=True)
                # Return partial result with error
                return Response({
                    'success': False,
                    'contract_id': str(contract.id),
                    'contract_name': contract.filename,
                    'error': f'Graph building failed: {str(graph_error)}',
                    'clauses_count': len(clauses)
                }, status=500)

            # Save metadata
            graph_meta = ContractGraphMeta.objects.create(
                contract=contract,
                graph_summary=graph_result.get('graph_summary', {}),
                risk_timeline=graph_result.get('risk_timeline', {}),
                negotiation_advice=graph_result.get('negotiation_advice', []),
                neo4j_synced=graph_result.get('neo4j_synced', False),
            )

            return Response({
                'success': True,
                'contract_id': str(contract.id),
                'contract_name': contract.filename,
                'graph_summary': graph_meta.graph_summary,
                'risk_timeline': graph_meta.risk_timeline,
                'negotiation_advice': graph_meta.negotiation_advice,
                'neo4j_synced': graph_meta.neo4j_synced,
                'created_at': graph_meta.created_at.isoformat(),
                'updated_at': graph_meta.updated_at.isoformat(),
                'rebuilt': True,
            })

    except Contract.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Contract not found or access denied'
        }, status=404)

    except Exception as e:
        logger.error(f"Error fetching graph dashboard data: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)


# ===========================================================================
# WHAT-IF SIMULATION APIs
# ===========================================================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def what_if_remove_clause(request, contract_id):
    """
    What-If Simulation: Remove Clause
    ==================================

    POST /api/contracts/<contract_id>/what-if/remove-clause

    Simulates impact of removing a clause from the contract.
    Non-destructive - nothing is deleted.

    Request Body:
        {
            "clause_id": "uuid",
            "include_exposure": true,
            "include_monte_carlo": false
        }

    Returns:
        - Risk before/after comparison
        - Affected clauses
        - Hotspot changes
        - Negotiation priority shifts
        - Financial exposure delta (optional)
        - Monte Carlo confidence ranges (optional)
    """
    try:
        from core.models import Contract, Clause
        from api.services.clause_graph import build_interaction_graph
        from api.services.what_if_simulator import simulate_remove_clause
        from api.services.exposure_engine import ExposureEngine, calculate_exposure_delta
        from api.services.monte_carlo_exposure import monte_carlo_what_if

        # Get request data
        clause_id = request.data.get('clause_id')
        include_exposure = request.data.get('include_exposure', True)
        include_monte_carlo = request.data.get('include_monte_carlo', False)

        if not clause_id:
            return Response({
                'success': False,
                'error': 'clause_id is required'
            }, status=400)

        # Get contract and clauses
        contract = Contract.objects.get(id=contract_id, user=request.user)
        clauses = list(Clause.objects.filter(contract=contract, found=True))

        if not clauses:
            return Response({
                'success': False,
                'error': 'No clauses found for this contract'
            }, status=400)

        # Build graph
        graph = build_interaction_graph(clauses)

        # Run simulation
        result = simulate_remove_clause(graph, clause_id)

        if not result.get('success'):
            return Response({
                'success': False,
                'error': result.get('error', 'Simulation failed')
            }, status=400)

        # Add exposure analysis if requested
        if include_exposure:
            exposure_engine = ExposureEngine()

            # Smart contract value: Try contract_value first, then total_liability
            contract_value = 0
            if contract.contract_value and contract.contract_value not in ["Not set", "not set", ""]:
                contract_value = exposure_engine.parse_contract_value(contract.contract_value)
                logger.info(f"[WHAT-IF] Using contract_value: {contract_value}")
            elif contract.total_liability and float(contract.total_liability) > 0:
                contract_value = float(contract.total_liability)
                logger.info(f"[WHAT-IF] Using total_liability: {contract_value}")

            logger.info(f"[WHAT-IF] Final contract value: {contract_value}")

            # Get remaining clauses (exclude the removed one)
            remaining_clauses = [c for c in clauses if str(c.id) != str(clause_id)]

            # Build simulated graph (shared by both exposure and Monte Carlo)
            import copy
            simulated_graph = copy.deepcopy(graph)
            target_node = None
            for node in simulated_graph.nodes():
                if str(node) == str(clause_id):
                    target_node = node
                    break
            if target_node:
                simulated_graph.remove_node(target_node)

            if contract_value > 0:
                exposure_result = calculate_exposure_delta(
                    clauses, remaining_clauses,
                    graph, simulated_graph,
                    contract_value
                )
                logger.info(f"[WHAT-IF] Exposure result: {exposure_result}")
                result['exposure'] = exposure_result
            else:
                result['exposure'] = {
                    "currency": "INR",
                    "exposure": {"before": 0, "after": 0, "delta": 0, "reduction_pct": 0},
                    "breakdown": {"before": [], "after": []},
                    "warning": "Contract value not found in this contract. Financial exposure cannot be calculated."
                }

        # Add Monte Carlo analysis if requested
        if include_monte_carlo:
            if not include_exposure:
                # Build simulated graph if not already built above
                exposure_engine = ExposureEngine()
                contract_value = 0
                if contract.contract_value and contract.contract_value not in ["Not set", "not set", ""]:
                    contract_value = exposure_engine.parse_contract_value(contract.contract_value)
                elif contract.total_liability and float(contract.total_liability) > 0:
                    contract_value = float(contract.total_liability)

                remaining_clauses = [c for c in clauses if str(c.id) != str(clause_id)]
                import copy
                simulated_graph = copy.deepcopy(graph)
                target_node = None
                for node in simulated_graph.nodes():
                    if str(node) == str(clause_id):
                        target_node = node
                        break
                if target_node:
                    simulated_graph.remove_node(target_node)

            if contract_value > 0:
                mc_result = monte_carlo_what_if(
                    clauses, remaining_clauses,
                    graph, simulated_graph,
                    contract_value,
                    iterations=3000
                )
                result['monte_carlo'] = mc_result
            else:
                result['monte_carlo'] = {
                    "warning": "Contract value not found. Monte Carlo simulation requires a contract value.",
                    "percentiles": {}, "statistics": {}
                }

        result['contract_id'] = str(contract.id)
        result['contract_name'] = contract.filename

        return Response(result)

    except Contract.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Contract not found or access denied'
        }, status=404)

    except Exception as e:
        logger.error(f"What-If simulation error: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def what_if_batch_removal(request, contract_id):
    """
    What-If Simulation: Batch Removal
    ==================================

    POST /api/contracts/<contract_id>/what-if/batch-removal

    Simulates removing multiple clauses at once.

    Request Body:
        {
            "clause_ids": ["uuid1", "uuid2", "uuid3"]
        }
    """
    try:
        from core.models import Contract, Clause
        from api.services.clause_graph import build_interaction_graph
        from api.services.what_if_simulator import simulate_batch_removal

        clause_ids = request.data.get('clause_ids', [])

        if not clause_ids:
            return Response({
                'success': False,
                'error': 'clause_ids list is required'
            }, status=400)

        contract = Contract.objects.get(id=contract_id, user=request.user)
        clauses = list(Clause.objects.filter(contract=contract, found=True))

        if not clauses:
            return Response({
                'success': False,
                'error': 'No clauses found for this contract'
            }, status=400)

        graph = build_interaction_graph(clauses)
        result = simulate_batch_removal(graph, clause_ids)

        result['contract_id'] = str(contract.id)
        result['contract_name'] = contract.filename

        return Response(result)

    except Contract.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Contract not found or access denied'
        }, status=404)

    except Exception as e:
        logger.error(f"Batch removal simulation error: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_exposure_analysis(request, contract_id):
    """
    Financial Exposure Analysis
    ============================

    GET /api/contracts/<contract_id>/exposure-analysis

    Returns financial exposure breakdown for the contract.
    """
    try:
        from core.models import Contract, Clause
        from api.services.clause_graph import build_interaction_graph
        from api.services.exposure_engine import ExposureEngine

        contract = Contract.objects.get(id=contract_id, user=request.user)
        clauses = list(Clause.objects.filter(contract=contract, found=True))

        if not clauses:
            return Response({
                'success': False,
                'error': 'No clauses found for this contract'
            }, status=400)

        exposure_engine = ExposureEngine()
        contract_value = exposure_engine.parse_contract_value(
            contract.contract_value or "0"
        )

        if contract_value == 0:
            return Response({
                'success': True,
                'warning': 'Contract value not set, using default estimates',
                'contract_id': str(contract.id),
                'contract_value': 0,
                'total_exposure': 0,
                'breakdown': []
            })

        graph = build_interaction_graph(clauses)
        total_exposure, breakdown = exposure_engine.calculate_total_exposure(
            clauses, graph, contract_value
        )
        exposure_by_type = exposure_engine.calculate_exposure_by_type(
            clauses, graph, contract_value
        )
        hotspots = exposure_engine.get_exposure_hotspots(
            clauses, graph, contract_value, top_n=5
        )

        return Response({
            'success': True,
            'contract_id': str(contract.id),
            'contract_name': contract.filename,
            'currency': 'INR',
            'contract_value': contract_value,
            'contract_value_formatted': exposure_engine.format_currency(contract_value),
            'total_exposure': total_exposure,
            'total_exposure_formatted': exposure_engine.format_currency(total_exposure),
            'exposure_ratio': round(total_exposure / contract_value * 100, 1) if contract_value > 0 else 0,
            'breakdown': breakdown[:15],  # Top 15 clauses
            'by_type': exposure_by_type,
            'hotspots': hotspots
        })

    except Contract.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Contract not found or access denied'
        }, status=404)

    except Exception as e:
        logger.error(f"Exposure analysis error: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def monte_carlo_simulation(request, contract_id):
    """
    Monte Carlo Exposure Simulation
    =================================

    POST /api/contracts/<contract_id>/monte-carlo-simulation

    Runs probabilistic simulation for exposure confidence ranges.

    Request Body:
        {
            "iterations": 3000,
            "include_var": true,
            "include_stress_test": true
        }
    """
    try:
        from core.models import Contract, Clause
        from api.services.clause_graph import build_interaction_graph
        from api.services.exposure_engine import ExposureEngine
        from api.services.monte_carlo_exposure import (
            MonteCarloExposureSimulator,
            calculate_var,
            stress_test
        )

        iterations = request.data.get('iterations', 3000)
        include_var = request.data.get('include_var', True)
        include_stress_test = request.data.get('include_stress_test', True)

        contract = Contract.objects.get(id=contract_id, user=request.user)
        clauses = list(Clause.objects.filter(contract=contract, found=True))

        if not clauses:
            return Response({
                'success': False,
                'error': 'No clauses found for this contract'
            }, status=400)

        exposure_engine = ExposureEngine()
        contract_value = exposure_engine.parse_contract_value(
            contract.contract_value or "0"
        )

        if contract_value == 0:
            return Response({
                'success': True,
                'warning': 'Contract value not set',
                'contract_id': str(contract.id)
            })

        graph = build_interaction_graph(clauses)

        simulator = MonteCarloExposureSimulator(iterations=iterations)
        mc_result = simulator.simulate(clauses, graph, contract_value)

        response = {
            'success': True,
            'contract_id': str(contract.id),
            'contract_name': contract.filename,
            'currency': 'INR',
            'contract_value': contract_value,
            'contract_value_formatted': exposure_engine.format_currency(contract_value),
            'simulation': mc_result
        }

        if include_var:
            var_result = calculate_var(clauses, graph, contract_value, 0.95)
            response['value_at_risk'] = var_result

        if include_stress_test:
            stress_result = stress_test(clauses, graph, contract_value)
            response['stress_test'] = stress_result

        return Response(response)

    except Contract.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Contract not found or access denied'
        }, status=404)

    except Exception as e:
        logger.error(f"Monte Carlo simulation error: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)


@api_view(['POST'])
def convert_currency(request):
    """
    POST /api/currency/convert
    Convert amount between currencies with real-time exchange rates.

    Request:
        {
            "amount": 10000000,
            "from_currency": "INR",
            "to_currency": "USD"
        }

    Response:
        {
            "success": true,
            "original_amount": 10000000,
            "converted_amount": 120481.93,
            "from_currency": "INR",
            "to_currency": "USD",
            "exchange_rate": 0.012048,
            "formatted_original": "₹1.0 Cr",
            "formatted_converted": "$120.5K"
        }
    """
    try:
        from api.services.currency_converter import get_converter

        amount = float(request.data.get('amount', 0))
        from_currency = request.data.get('from_currency', 'INR').upper()
        to_currency = request.data.get('to_currency', 'USD').upper()

        if amount <= 0:
            return Response({
                'success': False,
                'error': 'Amount must be greater than 0'
            }, status=400)

        converter = get_converter()

        # Get exchange rate
        rate = converter.get_exchange_rate(from_currency, to_currency)

        # Convert
        converted = converter.convert(amount, from_currency, to_currency)

        # Format
        formatted_original = converter.format_amount(amount, from_currency)
        formatted_converted = converter.format_amount(converted, to_currency)

        return Response({
            'success': True,
            'original_amount': amount,
            'converted_amount': converted,
            'from_currency': from_currency,
            'to_currency': to_currency,
            'exchange_rate': rate,
            'formatted_original': formatted_original,
            'formatted_converted': formatted_converted
        })

    except Exception as e:
        logger.error(f"Currency conversion error: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)


@api_view(['GET'])
def get_supported_currencies(request):
    """
    GET /api/currency/supported
    Get list of supported currencies for conversion.

    Response:
        {
            "success": true,
            "currencies": {
                "USD": "US Dollar",
                "INR": "Indian Rupee",
                ...
            }
        }
    """
    try:
        from api.services.currency_converter import get_converter

        converter = get_converter()
        currencies = converter.get_supported_currencies()

        return Response({
            'success': True,
            'currencies': currencies
        })

    except Exception as e:
        logger.error(f"Get currencies error: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)


@api_view(['GET'])
def get_exchange_rate(request, from_currency, to_currency):
    """
    GET /api/currency/rate/<from_currency>/<to_currency>
    Get current exchange rate between two currencies.

    Example: GET /api/currency/rate/INR/USD

    Response:
        {
            "success": true,
            "from_currency": "INR",
            "to_currency": "USD",
            "rate": 0.012048,
            "formatted": "1 INR = 0.012048 USD"
        }
    """
    try:
        from api.services.currency_converter import get_converter

        converter = get_converter()
        rate = converter.get_exchange_rate(
            from_currency.upper(),
            to_currency.upper()
        )

        return Response({
            'success': True,
            'from_currency': from_currency.upper(),
            'to_currency': to_currency.upper(),
            'rate': rate,
            'formatted': f"1 {from_currency.upper()} = {rate} {to_currency.upper()}"
        })

    except Exception as e:
        logger.error(f"Get exchange rate error: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)


@api_view(['GET'])
def get_portfolio_exposure(request):
    """
    GET /api/portfolio/exposure?currency=INR
    Get portfolio-wide exposure aggregation across all user contracts.

    Query Parameters:
        - currency: Target currency (default: INR)

    Response:
        {
            "success": true,
            "currency": "INR",
            "total_exposure": 125000000,
            "total_exposure_formatted": "₹12.5 Cr",
            "total_contracts": 15,
            "contracts": [...],
            "counterparty_breakdown": [...],
            "type_breakdown": [...],
            "concentration": {
                "index": 0.18,
                "risk_level": "MEDIUM",
                "interpretation": "..."
            },
            "top_risk_contributors": [...]
        }
    """
    try:
        from api.services.portfolio_exposure import PortfolioExposureEngine

        currency = request.query_params.get('currency', 'INR').upper()

        engine = PortfolioExposureEngine()
        result = engine.calculate_portfolio_exposure(request.user, currency)

        return Response(result)

    except Exception as e:
        logger.error(f"Portfolio exposure error: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)


@api_view(['GET'])
def get_portfolio_trends(request):
    """
    GET /api/portfolio/trends?currency=INR&months=12
    Get portfolio exposure trends over time.

    Query Parameters:
        - currency: Target currency (default: INR)
        - months: Number of months to analyze (default: 12)

    Response:
        {
            "success": true,
            "currency": "INR",
            "period": "12 months",
            "monthly_data": [
                {
                    "month": "2025-01",
                    "contracts_added": 3,
                    "exposure": 5000000
                },
                ...
            ]
        }
    """
    try:
        from api.services.portfolio_exposure import PortfolioExposureEngine

        currency = request.query_params.get('currency', 'INR').upper()
        months = int(request.query_params.get('months', 12))

        engine = PortfolioExposureEngine()
        result = engine.calculate_portfolio_trends(request.user, currency, months)

        return Response(result)

    except Exception as e:
        logger.error(f"Portfolio trends error: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)


@api_view(['POST'])
def export_what_if_pdf(request, contract_id):
    """
    POST /api/contracts/<contract_id>/what-if/export-pdf
    Export What-If analysis results to PDF.

    Request:
        {
            "clause_id": "...",
            "include_exposure": true,
            "include_monte_carlo": true
        }

    Response:
        PDF file download
    """
    try:
        from django.http import HttpResponse
        from api.services.pdf_export import export_what_if_pdf as export_pdf
        from api.services.what_if_simulator import simulate_remove_clause
        from api.services.exposure_engine import ExposureEngine
        from api.services.monte_carlo_exposure import monte_carlo_what_if
        from api.services.clause_graph import build_interaction_graph

        clause_id = request.data.get('clause_id')
        include_exposure = request.data.get('include_exposure', True)
        include_monte_carlo = request.data.get('include_monte_carlo', False)

        if not clause_id:
            return Response({
                'success': False,
                'error': 'clause_id is required'
            }, status=400)

        contract = Contract.objects.get(id=contract_id, user=request.user)
        clauses = list(Clause.objects.filter(contract=contract, found=True))

        if not clauses:
            return Response({
                'success': False,
                'error': 'No clauses found'
            }, status=400)

        # Build graph
        graph = build_interaction_graph(clauses)

        # Run simulation
        simulation_result = simulate_remove_clause(graph, clause_id)

        # Add exposure if requested
        if include_exposure:
            exposure_engine = ExposureEngine()
            contract_value = exposure_engine.parse_contract_value(
                contract.contract_value or "0"
            )

            if contract_value > 0:
                from api.services.exposure_engine import calculate_exposure_delta
                import copy

                simulated_graph = copy.deepcopy(graph)
                target_node = None
                for node in graph.nodes():
                    if str(node) == str(clause_id):
                        target_node = node
                        break

                if target_node:
                    simulated_graph.remove_node(target_node)
                    remaining_clauses = [c for c in clauses if str(c.id) != str(clause_id)]

                    exposure_result = calculate_exposure_delta(
                        clauses, remaining_clauses,
                        graph, simulated_graph,
                        contract_value
                    )
                    simulation_result['exposure'] = exposure_result

        # Add Monte Carlo if requested
        if include_monte_carlo:
            import copy
            simulated_graph = copy.deepcopy(graph)
            target_node = None
            for node in graph.nodes():
                if str(node) == str(clause_id):
                    target_node = node
                    break

            if target_node:
                simulated_graph.remove_node(target_node)
                remaining_clauses = [c for c in clauses if str(c.id) != str(clause_id)]

                contract_value = ExposureEngine().parse_contract_value(
                    contract.contract_value or "0"
                )

                if contract_value > 0:
                    mc_result = monte_carlo_what_if(
                        clauses, remaining_clauses,
                        graph, simulated_graph,
                        contract_value
                    )
                    simulation_result['monte_carlo'] = mc_result

        # Generate PDF
        contract_name = contract.name or contract.original_filename or f"Contract {contract.id}"
        user_name = f"{request.user.first_name} {request.user.last_name}".strip() or request.user.email

        pdf_bytes = export_pdf(contract_name, simulation_result, user_name)

        # Return PDF
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="what-if-analysis-{contract.id}.pdf"'

        return response

    except Contract.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Contract not found'
        }, status=404)

    except ImportError as e:
        return Response({
            'success': False,
            'error': 'PDF export library not installed. Please install reportlab.'
        }, status=500)

    except Exception as e:
        logger.error(f"PDF export error: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)


@api_view(['GET'])
def export_portfolio_pdf(request):
    """
    GET /api/portfolio/export-pdf?currency=INR
    Export portfolio exposure report to PDF.

    Query Parameters:
        - currency: Target currency (default: INR)

    Response:
        PDF file download
    """
    try:
        from django.http import HttpResponse
        from api.services.pdf_export import export_portfolio_pdf as export_pdf
        from api.services.portfolio_exposure import PortfolioExposureEngine

        currency = request.query_params.get('currency', 'INR').upper()

        # Get portfolio data
        engine = PortfolioExposureEngine()
        portfolio_data = engine.calculate_portfolio_exposure(request.user, currency)

        if not portfolio_data.get('success'):
            return Response({
                'success': False,
                'error': portfolio_data.get('error', 'Failed to calculate portfolio exposure')
            }, status=400)

        # Generate PDF
        user_name = f"{request.user.first_name} {request.user.last_name}".strip() or request.user.email
        pdf_bytes = export_pdf(portfolio_data, user_name)

        # Return PDF
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="portfolio-exposure-{datetime.now().strftime("%Y%m%d")}.pdf"'

        return response

    except ImportError as e:
        return Response({
            'success': False,
            'error': 'PDF export library not installed. Please install reportlab.'
        }, status=500)

    except Exception as e:
        logger.error(f"Portfolio PDF export error: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)


# ==============================================================================
# Auto-Suggest Safe Clause Rewrites
# ==============================================================================
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def clause_rewrite(request):
    """
    Auto-Suggest Safe Clause Rewrite
    =================================
    POST /api/clause-rewrite/

    Detects why a clause is risky and generates legally safer alternative
    language.  Uses Qwen via Ollama; falls back to rule-based amendments
    when LLM is unavailable.

    Request Body:
        {
            "clause_text": "The vendor shall bear unlimited liability…",
            "risk_reason": "unlimited_liability"
        }

    Supported risk_reason values:
        unlimited_liability | ambiguous_termination | unclear_payment |
        no_cap_on_damages | missing_force_majeure | one_sided_indemnity |
        vague_warranty

    Returns:
        {
            "original_clause": str,
            "rewritten_clause": str,
            "risk_reason": str,
            "method": "llm" | "fallback",
            "confidence": float
        }
    """
    try:
        from api.services.clause_rewrite_engine import ClauseRewriteEngine

        clause_text = request.data.get('clause_text', '')
        risk_reason = request.data.get('risk_reason', '')

        if not clause_text or not risk_reason:
            return Response({
                'success': False,
                'error': 'clause_text and risk_reason are required'
            }, status=400)

        engine = ClauseRewriteEngine()
        result = engine.rewrite(clause_text=clause_text, risk_reason=risk_reason)

        return Response({'success': True, **result})

    except Exception as e:
        logger.error(f"Clause rewrite error: {str(e)}", exc_info=True)
        return Response({'success': False, 'error': str(e)}, status=500)


# ==============================================================================
# Negotiation Counter-Proposal Generator
# ==============================================================================
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def counter_proposal(request):
    """
    Negotiation Counter-Proposal Generator
    ========================================
    POST /api/counter-proposal/

    Given an original clause, the counterparty's position, and our risk
    appetite, generates a balanced counter-proposal clause.

    Request Body:
        {
            "original_clause": "Payment is due within 15 days…",
            "counterparty_position": "We need 90-day payment terms…",
            "risk_tolerance": "medium"      // low | medium | high
        }

    Returns:
        {
            "original_clause": str,
            "counterparty_position": str,
            "risk_tolerance": str,
            "counter_proposal": str,
            "method": "llm" | "fallback",
            "confidence": float,
            "negotiation_tips": [str]
        }
    """
    try:
        from api.services.counter_proposal_engine import CounterProposalEngine

        original_clause = request.data.get('original_clause', '')
        counterparty_position = request.data.get('counterparty_position', '')
        risk_tolerance = request.data.get('risk_tolerance', 'medium')

        if not original_clause or not counterparty_position:
            return Response({
                'success': False,
                'error': 'original_clause and counterparty_position are required'
            }, status=400)

        engine = CounterProposalEngine()
        result = engine.generate(
            original_clause=original_clause,
            counterparty_position=counterparty_position,
            risk_tolerance=risk_tolerance
        )

        return Response({'success': True, **result})

    except Exception as e:
        logger.error(f"Counter-proposal error: {str(e)}", exc_info=True)
        return Response({'success': False, 'error': str(e)}, status=500)


# ==============================================================================
# Advanced What-If Simulation (remove / add / counterfactual_add)
# ==============================================================================
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def advanced_what_if(request, contract_id):
    """
    Advanced What-If Simulation
    =============================
    POST /api/contracts/<contract_id>/advanced-what-if/

    Unified endpoint for clause mutation + re-scoring + exposure:
        - action "remove"              → remove paragraphs by keyword
        - action "add"                 → append user-provided clause
        - action "counterfactual_add"  → LLM generates protective clause, then appends

    After mutation:
        1. Re-extract obligations
        2. Heuristic risk re-score against graph baseline
        3. Monte Carlo exposure (before vs after)

    Request Body:
        {
            "action": "remove" | "add" | "counterfactual_add",
            "clause_keyword": "termination",                // required for remove
            "clause_text": "New clause text…",              // required for add
            "counterfactual_objective": "cap liability",    // required for counterfactual_add
            "contract_value": 5000000                       // optional; enables Monte Carlo
        }

    Returns:
        Full simulation result including text delta, obligations, risk delta,
        and (if contract_value provided) Monte Carlo exposure comparison.
    """
    try:
        from core.models import Contract, Clause
        from api.services.advanced_what_if import AdvancedWhatIfSimulator
        from api.services.exposure_engine import ExposureEngine

        contract = Contract.objects.get(id=contract_id, user=request.user)
        clauses = list(Clause.objects.filter(contract=contract, found=True))

        contract_text = contract.full_text or ''

        # Resolve contract value
        contract_value = request.data.get('contract_value', 0)
        if not contract_value:
            exposure_engine = ExposureEngine()
            if contract.contract_value and contract.contract_value not in ("Not set", "not set", ""):
                contract_value = exposure_engine.parse_contract_value(contract.contract_value)
            elif contract.total_liability and float(contract.total_liability) > 0:
                contract_value = float(contract.total_liability)

        action = request.data.get('action', '')

        simulator = AdvancedWhatIfSimulator()
        result = simulator.simulate(
            clauses=clauses,
            contract_text=contract_text,
            action=action,
            contract_value=float(contract_value) if contract_value else 0.0,
            clause_keyword=request.data.get('clause_keyword'),
            clause_text=request.data.get('clause_text'),
            counterfactual_objective=request.data.get('counterfactual_objective')
        )

        result['contract_id'] = str(contract.id)
        result['contract_name'] = contract.filename

        return Response(result)

    except Contract.DoesNotExist:
        return Response({'success': False, 'error': 'Contract not found or access denied'}, status=404)
    except Exception as e:
        logger.error(f"Advanced what-if error: {str(e)}", exc_info=True)
        return Response({'success': False, 'error': str(e)}, status=500)
