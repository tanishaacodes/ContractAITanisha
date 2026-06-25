"""
Intent Drift Detection Service
================================
Detects and quantifies semantic drift in legal intents, obligations, and rights
across contract versions using:
- Semantic similarity (embedding-based comparison)
- Structural changes (added/removed/modified)
- Risk delta tracking
"""

import numpy as np
from typing import Dict, List, Tuple
from sklearn.metrics.pairwise import cosine_similarity
from core.models import ContractVersion, ClauseIntent, IntentObligation, IntentRight, Intent
from django.db import transaction
import logging

# Import embedding service singleton
from api.embedding_service import embedding_service

logger = logging.getLogger(__name__)


class IntentDriftDetectionService:
    """Service for detecting drift between contract versions"""

    def __init__(self):
        self.embedding_service = embedding_service
        self.similarity_threshold = 0.80  # 80% similarity = "modified", <80% = "removed/added"

    def compare_versions(self, version1_id: str, version2_id: str) -> Dict:
        """
        Compare two contract versions and detect intent drift.

        Args:
            version1_id: Baseline version UUID
            version2_id: Comparison version UUID

        Returns:
            {
                'success': True/False,
                'version1': {...metadata...},
                'version2': {...metadata...},
                'overall_drift_score': 0.45,  # 0-1, higher = more drift
                'intent_drift': {
                    'added': [...],
                    'removed': [...],
                    'modified': [...],
                    'unchanged': [...]
                },
                'obligation_drift': {...},
                'right_drift': {...},
                'risk_delta': {
                    'previous_risk': 0.6,
                    'current_risk': 0.75,
                    'delta': +0.15,
                    'direction': 'INCREASED'
                },
                'summary': "High drift detected..."
            }
        """
        try:
            # Load versions
            version1 = ContractVersion.objects.get(id=version1_id)
            version2 = ContractVersion.objects.get(id=version2_id)

            # Validate same contract
            if version1.contract_id != version2.contract_id:
                return {
                    'success': False,
                    'error': 'Versions must belong to same contract'
                }

            # Load version-specific intents, obligations, rights
            v1_clause_intents = ClauseIntent.objects.filter(contract_version=version1).select_related('intent', 'clause')
            v2_clause_intents = ClauseIntent.objects.filter(contract_version=version2).select_related('intent', 'clause')

            v1_obligations = IntentObligation.objects.filter(contract_version=version1).select_related('intent', 'clause')
            v2_obligations = IntentObligation.objects.filter(contract_version=version2).select_related('intent', 'clause')

            v1_rights = IntentRight.objects.filter(contract_version=version1).select_related('intent', 'clause')
            v2_rights = IntentRight.objects.filter(contract_version=version2).select_related('intent', 'clause')

            # Detect drift
            intent_drift = self._detect_intent_drift(v1_clause_intents, v2_clause_intents)
            obligation_drift = self._detect_obligation_drift(v1_obligations, v2_obligations)
            right_drift = self._detect_right_drift(v1_rights, v2_rights)

            # Calculate overall drift score
            overall_score = self._calculate_overall_drift_score(intent_drift, obligation_drift, right_drift)

            # Calculate risk delta
            risk_delta = self._calculate_risk_delta(v1_obligations, v2_obligations, v1_rights, v2_rights)

            # Generate summary
            summary = self._generate_drift_summary(overall_score, intent_drift, obligation_drift, right_drift, risk_delta)

            return {
                'success': True,
                'version1': {
                    'id': str(version1.id),
                    'version_number': version1.version_number,
                    'created_at': version1.created_at.isoformat() if version1.created_at else None,
                    'change_description': version1.change_description
                },
                'version2': {
                    'id': str(version2.id),
                    'version_number': version2.version_number,
                    'created_at': version2.created_at.isoformat() if version2.created_at else None,
                    'change_description': version2.change_description
                },
                'overall_drift_score': overall_score,
                'intent_drift': intent_drift,
                'obligation_drift': obligation_drift,
                'right_drift': right_drift,
                'risk_delta': risk_delta,
                'summary': summary
            }

        except ContractVersion.DoesNotExist:
            return {'success': False, 'error': 'Version not found'}
        except Exception as e:
            logger.error(f"Drift comparison error: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': str(e)}

    def _detect_intent_drift(self, v1_intents, v2_intents) -> Dict:
        """
        Uses semantic similarity to match intents across versions.

        Algorithm:
        1. Create embeddings for all intent names from both versions
        2. Compute similarity matrix
        3. For each v1 intent:
           - Find best match in v2 (highest cosine similarity)
           - If similarity >= 0.80 and confidence changed: MODIFIED
           - If similarity < 0.80: REMOVED
        4. Any v2 intents not matched: ADDED
        """

        # Build intent maps
        v1_map = {ci.intent.name: ci for ci in v1_intents}
        v2_map = {ci.intent.name: ci for ci in v2_intents}

        added = []
        removed = []
        modified = []
        unchanged = []

        # Create embeddings
        if v1_map and v2_map:
            v1_names = list(v1_map.keys())
            v2_names = list(v2_map.keys())

            v1_embeddings = np.array(self.embedding_service.embed_batch(v1_names))
            v2_embeddings = np.array(self.embedding_service.embed_batch(v2_names))

            # Compute similarity matrix: v1 x v2
            sim_matrix = cosine_similarity(v1_embeddings, v2_embeddings)

            matched_v2_indices = set()

            for i, v1_name in enumerate(v1_names):
                v1_ci = v1_map[v1_name]

                # Find best match in v2
                best_v2_idx = np.argmax(sim_matrix[i])
                best_similarity = sim_matrix[i][best_v2_idx]
                v2_name = v2_names[best_v2_idx]
                v2_ci = v2_map[v2_name]

                if best_similarity >= self.similarity_threshold:
                    # MATCHED: Check if modified
                    matched_v2_indices.add(best_v2_idx)

                    if abs(v1_ci.confidence - v2_ci.confidence) > 0.1:
                        modified.append({
                            'intent_name': v1_name,
                            'matched_to': v2_name,
                            'similarity': float(best_similarity),
                            'confidence_change': float(v2_ci.confidence - v1_ci.confidence),
                            'v1_confidence': float(v1_ci.confidence),
                            'v2_confidence': float(v2_ci.confidence),
                            'clause_v1': v1_ci.clause.clause_name,
                            'clause_v2': v2_ci.clause.clause_name
                        })
                    else:
                        unchanged.append({
                            'intent_name': v1_name,
                            'confidence': float(v1_ci.confidence),
                            'similarity': float(best_similarity)
                        })
                else:
                    # REMOVED (no good match)
                    removed.append({
                        'intent_name': v1_name,
                        'confidence': float(v1_ci.confidence),
                        'clause': v1_ci.clause.clause_name
                    })

            # Find ADDED intents (v2 intents not matched)
            for j, v2_name in enumerate(v2_names):
                if j not in matched_v2_indices:
                    v2_ci = v2_map[v2_name]
                    added.append({
                        'intent_name': v2_name,
                        'confidence': float(v2_ci.confidence),
                        'clause': v2_ci.clause.clause_name
                    })

        elif v2_map:
            # No v1 intents, all v2 are added
            added = [{'intent_name': name, 'confidence': float(ci.confidence), 'clause': ci.clause.clause_name}
                    for name, ci in v2_map.items()]
        elif v1_map:
            # No v2 intents, all v1 are removed
            removed = [{'intent_name': name, 'confidence': float(ci.confidence), 'clause': ci.clause.clause_name}
                      for name, ci in v1_map.items()]

        return {
            'added': added,
            'removed': removed,
            'modified': modified,
            'unchanged': unchanged,
            'total_v1': len(v1_map),
            'total_v2': len(v2_map),
            'change_count': len(added) + len(removed) + len(modified)
        }

    def _detect_obligation_drift(self, v1_obligations, v2_obligations) -> Dict:
        """
        Detect changes in obligations.
        Match by: (intent_name, party, action_similarity)
        Track changes in: action, condition, deadline, priority, risk_score
        """

        added = []
        removed = []
        modified = []
        unchanged = []

        # Group by intent and party for matching
        v1_groups = {}
        for obl in v1_obligations:
            key = (obl.intent.name, obl.party)
            if key not in v1_groups:
                v1_groups[key] = []
            v1_groups[key].append(obl)

        v2_groups = {}
        for obl in v2_obligations:
            key = (obl.intent.name, obl.party)
            if key not in v2_groups:
                v2_groups[key] = []
            v2_groups[key].append(obl)

        # Compare groups
        all_keys = set(v1_groups.keys()) | set(v2_groups.keys())

        for key in all_keys:
            intent_name, party = key
            v1_obls = v1_groups.get(key, [])
            v2_obls = v2_groups.get(key, [])

            if not v1_obls:
                # All v2 obligations in this group are ADDED
                for obl in v2_obls:
                    added.append({
                        'intent': intent_name,
                        'party': party,
                        'action': obl.action,
                        'deadline': obl.deadline,
                        'priority': obl.priority,
                        'risk_score': float(obl.risk_score)
                    })

            elif not v2_obls:
                # All v1 obligations in this group are REMOVED
                for obl in v1_obls:
                    removed.append({
                        'intent': intent_name,
                        'party': party,
                        'action': obl.action,
                        'deadline': obl.deadline,
                        'priority': obl.priority,
                        'risk_score': float(obl.risk_score)
                    })

            else:
                # Match obligations by action similarity
                v1_actions = [obl.action for obl in v1_obls]
                v2_actions = [obl.action for obl in v2_obls]

                v1_action_embeddings = np.array(self.embedding_service.embed_batch(v1_actions))
                v2_action_embeddings = np.array(self.embedding_service.embed_batch(v2_actions))

                sim_matrix = cosine_similarity(v1_action_embeddings, v2_action_embeddings)

                matched_v2_indices = set()

                for i, v1_obl in enumerate(v1_obls):
                    best_j = np.argmax(sim_matrix[i])
                    best_sim = sim_matrix[i][best_j]
                    v2_obl = v2_obls[best_j]

                    if best_sim >= self.similarity_threshold:
                        matched_v2_indices.add(best_j)

                        # Check for modifications
                        has_changes = (
                            v1_obl.deadline != v2_obl.deadline or
                            v1_obl.condition != v2_obl.condition or
                            v1_obl.priority != v2_obl.priority or
                            abs(v1_obl.risk_score - v2_obl.risk_score) > 0.1
                        )

                        if has_changes:
                            changes = {}
                            if v1_obl.deadline != v2_obl.deadline:
                                changes['deadline'] = {'old': v1_obl.deadline, 'new': v2_obl.deadline}
                            if v1_obl.condition != v2_obl.condition:
                                changes['condition'] = {'old': v1_obl.condition, 'new': v2_obl.condition}
                            if v1_obl.priority != v2_obl.priority:
                                changes['priority'] = {'old': v1_obl.priority, 'new': v2_obl.priority}
                            if abs(v1_obl.risk_score - v2_obl.risk_score) > 0.1:
                                changes['risk_score'] = {'old': float(v1_obl.risk_score), 'new': float(v2_obl.risk_score)}

                            modified.append({
                                'intent': intent_name,
                                'party': party,
                                'action': v1_obl.action,
                                'changes': changes,
                                'similarity': float(best_sim)
                            })
                        else:
                            unchanged.append({
                                'intent': intent_name,
                                'party': party,
                                'action': v1_obl.action
                            })
                    else:
                        removed.append({
                            'intent': intent_name,
                            'party': party,
                            'action': v1_obl.action,
                            'risk_score': float(v1_obl.risk_score)
                        })

                # Unmatched v2 obligations are ADDED
                for j, v2_obl in enumerate(v2_obls):
                    if j not in matched_v2_indices:
                        added.append({
                            'intent': intent_name,
                            'party': party,
                            'action': v2_obl.action,
                            'risk_score': float(v2_obl.risk_score)
                        })

        return {
            'added': added,
            'removed': removed,
            'modified': modified,
            'unchanged': unchanged,
            'total_v1': len(list(v1_obligations)),
            'total_v2': len(list(v2_obligations)),
            'change_count': len(added) + len(removed) + len(modified)
        }

    def _detect_right_drift(self, v1_rights, v2_rights) -> Dict:
        """
        Detect changes in rights.
        Similar to obligations but tracks: entitlement, trigger changes
        """

        added = []
        removed = []
        modified = []
        unchanged = []

        # Group by intent and party for matching
        v1_groups = {}
        for right in v1_rights:
            key = (right.intent.name, right.party)
            if key not in v1_groups:
                v1_groups[key] = []
            v1_groups[key].append(right)

        v2_groups = {}
        for right in v2_rights:
            key = (right.intent.name, right.party)
            if key not in v2_groups:
                v2_groups[key] = []
            v2_groups[key].append(right)

        # Compare groups
        all_keys = set(v1_groups.keys()) | set(v2_groups.keys())

        for key in all_keys:
            intent_name, party = key
            v1_rights_list = v1_groups.get(key, [])
            v2_rights_list = v2_groups.get(key, [])

            if not v1_rights_list:
                # All v2 rights in this group are ADDED
                for right in v2_rights_list:
                    added.append({
                        'intent': intent_name,
                        'party': party,
                        'entitlement': right.entitlement,
                        'trigger': right.trigger,
                        'risk_score': float(right.risk_score)
                    })

            elif not v2_rights_list:
                # All v1 rights in this group are REMOVED
                for right in v1_rights_list:
                    removed.append({
                        'intent': intent_name,
                        'party': party,
                        'entitlement': right.entitlement,
                        'trigger': right.trigger,
                        'risk_score': float(right.risk_score)
                    })

            else:
                # Match rights by entitlement similarity
                v1_entitlements = [right.entitlement for right in v1_rights_list]
                v2_entitlements = [right.entitlement for right in v2_rights_list]

                v1_entitlement_embeddings = np.array(self.embedding_service.embed_batch(v1_entitlements))
                v2_entitlement_embeddings = np.array(self.embedding_service.embed_batch(v2_entitlements))

                sim_matrix = cosine_similarity(v1_entitlement_embeddings, v2_entitlement_embeddings)

                matched_v2_indices = set()

                for i, v1_right in enumerate(v1_rights_list):
                    best_j = np.argmax(sim_matrix[i])
                    best_sim = sim_matrix[i][best_j]
                    v2_right = v2_rights_list[best_j]

                    if best_sim >= self.similarity_threshold:
                        matched_v2_indices.add(best_j)

                        # Check for modifications
                        has_changes = (
                            v1_right.trigger != v2_right.trigger or
                            abs(v1_right.risk_score - v2_right.risk_score) > 0.1
                        )

                        if has_changes:
                            changes = {}
                            if v1_right.trigger != v2_right.trigger:
                                changes['trigger'] = {'old': v1_right.trigger, 'new': v2_right.trigger}
                            if abs(v1_right.risk_score - v2_right.risk_score) > 0.1:
                                changes['risk_score'] = {'old': float(v1_right.risk_score), 'new': float(v2_right.risk_score)}

                            modified.append({
                                'intent': intent_name,
                                'party': party,
                                'entitlement': v1_right.entitlement,
                                'changes': changes,
                                'similarity': float(best_sim)
                            })
                        else:
                            unchanged.append({
                                'intent': intent_name,
                                'party': party,
                                'entitlement': v1_right.entitlement
                            })
                    else:
                        removed.append({
                            'intent': intent_name,
                            'party': party,
                            'entitlement': v1_right.entitlement,
                            'risk_score': float(v1_right.risk_score)
                        })

                # Unmatched v2 rights are ADDED
                for j, v2_right in enumerate(v2_rights_list):
                    if j not in matched_v2_indices:
                        added.append({
                            'intent': intent_name,
                            'party': party,
                            'entitlement': v2_right.entitlement,
                            'risk_score': float(v2_right.risk_score)
                        })

        return {
            'added': added,
            'removed': removed,
            'modified': modified,
            'unchanged': unchanged,
            'total_v1': len(list(v1_rights)),
            'total_v2': len(list(v2_rights)),
            'change_count': len(added) + len(removed) + len(modified)
        }

    def _calculate_overall_drift_score(self, intent_drift, obligation_drift, right_drift) -> float:
        """
        Weighted drift score calculation.

        Formula:
        - Intent change ratio = (added + removed + modified) / max(total_v1, total_v2, 1)
        - Obligation change ratio = same calculation
        - Rights change ratio = same calculation

        Overall = (intent_ratio * 0.3) + (obligation_ratio * 0.4) + (rights_ratio * 0.3)

        Returns: 0.0 to 1.0 (0 = no drift, 1 = complete drift)
        """

        def change_ratio(drift_data):
            total = max(drift_data.get('total_v1', 0), drift_data.get('total_v2', 0), 1)
            changes = drift_data.get('change_count', 0)
            return changes / total

        intent_ratio = change_ratio(intent_drift)
        obligation_ratio = change_ratio(obligation_drift)
        right_ratio = change_ratio(right_drift)

        overall = (intent_ratio * 0.3) + (obligation_ratio * 0.4) + (right_ratio * 0.3)

        return min(overall, 1.0)  # Cap at 1.0

    def _calculate_risk_delta(self, v1_obligations, v2_obligations, v1_rights, v2_rights) -> Dict:
        """
        Calculate change in overall risk exposure.

        Risk calculation:
        - Average obligation risk score (weighted by priority: HIGH=1.5, MEDIUM=1.0, LOW=0.5)
        - Average rights risk score
        - Combined risk = (obligations * 0.6) + (rights * 0.4)
        """

        def weighted_obligation_risk(obligations):
            obligations_list = list(obligations)
            if not obligations_list:
                return 0.0

            priority_weights = {'HIGH': 1.5, 'MEDIUM': 1.0, 'LOW': 0.5}
            weighted_sum = sum(
                obl.risk_score * priority_weights.get(obl.priority, 1.0)
                for obl in obligations_list
            )
            total_weight = sum(priority_weights.get(obl.priority, 1.0) for obl in obligations_list)

            return weighted_sum / total_weight if total_weight > 0 else 0.0

        def avg_rights_risk(rights):
            rights_list = list(rights)
            if not rights_list:
                return 0.0
            return sum(r.risk_score for r in rights_list) / len(rights_list)

        v1_obl_risk = weighted_obligation_risk(v1_obligations)
        v2_obl_risk = weighted_obligation_risk(v2_obligations)

        v1_right_risk = avg_rights_risk(v1_rights)
        v2_right_risk = avg_rights_risk(v2_rights)

        v1_combined = (v1_obl_risk * 0.6) + (v1_right_risk * 0.4)
        v2_combined = (v2_obl_risk * 0.6) + (v2_right_risk * 0.4)

        delta = v2_combined - v1_combined

        return {
            'previous_risk': round(v1_combined, 3),
            'current_risk': round(v2_combined, 3),
            'delta': round(delta, 3),
            'delta_percent': round((delta / v1_combined * 100) if v1_combined > 0 else 0, 2),
            'direction': 'INCREASED' if delta > 0 else 'DECREASED' if delta < 0 else 'UNCHANGED',
            'breakdown': {
                'obligations': {
                    'previous': round(v1_obl_risk, 3),
                    'current': round(v2_obl_risk, 3),
                    'delta': round(v2_obl_risk - v1_obl_risk, 3)
                },
                'rights': {
                    'previous': round(v1_right_risk, 3),
                    'current': round(v2_right_risk, 3),
                    'delta': round(v2_right_risk - v1_right_risk, 3)
                }
            }
        }

    def _generate_drift_summary(self, overall_score, intent_drift, obligation_drift, right_drift, risk_delta) -> str:
        """Generate human-readable summary of drift analysis"""

        if overall_score > 0.7:
            drift_level = "High"
        elif overall_score > 0.3:
            drift_level = "Moderate"
        else:
            drift_level = "Low"

        total_changes = (
            intent_drift.get('change_count', 0) +
            obligation_drift.get('change_count', 0) +
            right_drift.get('change_count', 0)
        )

        risk_direction = risk_delta.get('direction', 'UNCHANGED')
        risk_change = risk_delta.get('delta_percent', 0)

        summary = f"{drift_level} drift detected ({int(overall_score * 100)}%). "
        summary += f"Total changes: {total_changes} "
        summary += f"({intent_drift.get('change_count', 0)} intents, "
        summary += f"{obligation_drift.get('change_count', 0)} obligations, "
        summary += f"{right_drift.get('change_count', 0)} rights). "
        summary += f"Risk {risk_direction.lower()} by {abs(risk_change):.1f}%."

        return summary
