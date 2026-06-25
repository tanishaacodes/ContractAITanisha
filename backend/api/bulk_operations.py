"""
Bulk Operations API Views
Handles bulk actions on contracts like bulk delete, bulk export, etc.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from core.models import Contract
from django.db import transaction


class BulkDeleteContractsView(APIView):
    """
    Bulk delete contracts
    Only deletes contracts that belong to the authenticated user
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        contract_ids = request.data.get('contract_ids', [])

        if not contract_ids:
            return Response(
                {'error': 'No contract IDs provided'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Verify all contracts belong to the user
        contracts = Contract.objects.filter(
            id__in=contract_ids,
            user=user
        )

        actual_count = contracts.count()
        requested_count = len(contract_ids)

        if actual_count != requested_count:
            return Response(
                {
                    'error': 'Some contracts do not exist or do not belong to you',
                    'requested': requested_count,
                    'found': actual_count
                },
                status=status.HTTP_403_FORBIDDEN
            )

        # Delete contracts
        with transaction.atomic():
            deleted_count, _ = contracts.delete()

        return Response({
            'success': True,
            'deleted_count': deleted_count,
            'message': f'Successfully deleted {deleted_count} contracts'
        })


class BulkDeleteAllContractsView(APIView):
    """
    Delete ALL contracts for the authenticated user
    USE WITH CAUTION - This is destructive!
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        # Require confirmation
        confirmation = request.data.get('confirm')
        if confirmation != 'DELETE_ALL_MY_CONTRACTS':
            return Response(
                {
                    'error': 'Confirmation required. Send confirm="DELETE_ALL_MY_CONTRACTS"'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Delete all user's contracts
        with transaction.atomic():
            deleted_count, _ = Contract.objects.filter(user=user).delete()

        return Response({
            'success': True,
            'deleted_count': deleted_count,
            'message': f'Successfully deleted all {deleted_count} contracts'
        })
