"""
Django management command to seed embedding-based AI data
Populates Risk Playbooks, Intent Templates, and Approved Clauses
"""

from django.core.management.base import BaseCommand
from core.models import RiskPlaybook, IntentTemplate, ApprovedClause
from api.embedding_service import embedding_service
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Seed database with risk playbooks, intent templates, and approved clauses'

    def handle(self, *args, **kwargs):
        self.stdout.write('Starting seed process...')

        # Seed Risk Playbooks
        self.seed_risk_playbooks()

        # Seed Intent Templates
        self.seed_intent_templates()

        # Seed Approved Clauses
        self.seed_approved_clauses()

        self.stdout.write(self.style.SUCCESS('Seed process completed!'))

    def seed_risk_playbooks(self):
        """Seed risk playbooks with common risky patterns"""
        self.stdout.write('Seeding risk playbooks...')

        risk_playbooks_data = [
            {
                'risk_name': 'Unlimited Liability Clause',
                'risk_type': 'LIABILITY',
                'risk_description': 'Clause imposes unlimited liability on one party without any caps or limitations',
                'example_clause_text': 'The Supplier shall be liable for all damages, losses, costs, and expenses of any kind whatsoever, without limitation, arising from this Agreement.',
                'severity_weight': 0.9,
                'similarity_threshold': 0.7,
                'legal_reference': 'Unlimited liability clauses are heavily scrutinized under contract law',
                'court_treatment': 'Courts often find unlimited liability unconscionable in commercial contracts'
            },
            {
                'risk_name': 'One-Sided Termination Rights',
                'risk_type': 'TERMINATION',
                'risk_description': 'Only one party has the right to terminate for convenience while the other is locked in',
                'example_clause_text': 'Client may terminate this Agreement at any time for any reason upon 30 days notice. Supplier may not terminate except for material breach.',
                'severity_weight': 0.75,
                'similarity_threshold': 0.7,
                'legal_reference': 'One-sided termination creates imbalance of bargaining power',
                'court_treatment': 'Courts may find one-sided termination clauses unconscionable'
            },
            {
                'risk_name': 'Broad Indemnification Language',
                'risk_type': 'INDEMNIFICATION',
                'risk_description': 'Indemnification clause covers all claims including those arising from indemnified party\'s own negligence',
                'example_clause_text': 'Party A shall indemnify, defend, and hold harmless Party B from any and all claims, damages, losses, and expenses arising out of or relating to this Agreement, including those caused by Party B\'s negligence.',
                'severity_weight': 0.85,
                'similarity_threshold': 0.7,
                'legal_reference': 'Indemnification for own negligence must be explicit per anti-indemnity statutes',
                'court_treatment': 'Many jurisdictions void indemnification for sole negligence of indemnitee'
            },
            {
                'risk_name': 'Automatic IP Transfer Without Compensation',
                'risk_type': 'IP_OWNERSHIP',
                'risk_description': 'All intellectual property automatically transfers to one party without additional compensation',
                'example_clause_text': 'All intellectual property rights, including copyrights, patents, and trade secrets created under this Agreement, shall automatically vest in and belong exclusively to Client.',
                'severity_weight': 0.8,
                'similarity_threshold': 0.65,
                'legal_reference': 'IP assignment must be explicit and may require separate consideration',
                'court_treatment': 'Courts require clear and unambiguous language for IP transfer'
            },
            {
                'risk_name': 'Perpetual Confidentiality Without Exception',
                'risk_type': 'CONFIDENTIALITY',
                'risk_description': 'Confidentiality obligations last forever with no standard exceptions',
                'example_clause_text': 'Receiving Party shall maintain all Confidential Information in strict confidence in perpetuity and shall never disclose such information to any third party.',
                'severity_weight': 0.6,
                'similarity_threshold': 0.7,
                'legal_reference': 'Perpetual confidentiality may be unenforceable as restraint on trade',
                'court_treatment': 'Courts prefer reasonable time limits on confidentiality obligations'
            },
            {
                'risk_name': 'Automatic Renewal Without Notice',
                'risk_type': 'RENEWAL',
                'risk_description': 'Contract automatically renews for extended periods without advance notice to parties',
                'example_clause_text': 'This Agreement shall automatically renew for successive three-year terms unless terminated by either party at least 180 days prior to the end of the then-current term.',
                'severity_weight': 0.5,
                'similarity_threshold': 0.65,
                'legal_reference': 'Automatic renewal clauses with long notice periods may be unconscionable',
                'court_treatment': 'Courts scrutinize automatic renewals with excessive notice requirements'
            },
            {
                'risk_name': 'Exclusion of All Warranties',
                'risk_type': 'LIMITATION_OF_DAMAGES',
                'risk_description': 'Complete disclaimer of all warranties including implied warranties of merchantability',
                'example_clause_text': 'SUPPLIER PROVIDES ALL SERVICES "AS IS" AND DISCLAIMS ALL WARRANTIES, EXPRESS OR IMPLIED, INCLUDING MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, AND NON-INFRINGEMENT.',
                'severity_weight': 0.65,
                'similarity_threshold': 0.7,
                'legal_reference': 'UCC 2-316 governs warranty disclaimers',
                'court_treatment': 'Warranty disclaimers must be conspicuous and may be limited by statute'
            },
            {
                'risk_name': 'Waiver of Consequential Damages',
                'risk_type': 'LIMITATION_OF_DAMAGES',
                'risk_description': 'Complete waiver of right to recover consequential or indirect damages',
                'example_clause_text': 'IN NO EVENT SHALL EITHER PARTY BE LIABLE FOR ANY CONSEQUENTIAL, INDIRECT, INCIDENTAL, SPECIAL, OR PUNITIVE DAMAGES.',
                'severity_weight': 0.55,
                'similarity_threshold': 0.7,
                'legal_reference': 'Limitation of consequential damages is generally enforceable if reasonable',
                'court_treatment': 'Courts enforce consequential damages limitations in commercial contracts'
            },
            {
                'risk_name': 'Unilateral Modification Rights',
                'risk_type': 'GOVERNING_LAW',
                'risk_description': 'One party can unilaterally modify contract terms without consent',
                'example_clause_text': 'Company reserves the right to modify these terms at any time in its sole discretion. Continued use constitutes acceptance of modified terms.',
                'severity_weight': 0.7,
                'similarity_threshold': 0.65,
                'legal_reference': 'Unilateral modification clauses may lack mutual assent',
                'court_treatment': 'Courts may find unilateral modification clauses illusory and unenforceable'
            },
            {
                'risk_name': 'Mandatory Arbitration with Fee Shifting',
                'risk_type': 'DISPUTE_RESOLUTION',
                'risk_description': 'Mandatory arbitration where losing party pays all fees including winner\'s legal fees',
                'example_clause_text': 'All disputes shall be resolved by binding arbitration. The losing party shall pay all arbitration costs and the prevailing party\'s attorney fees.',
                'severity_weight': 0.65,
                'similarity_threshold': 0.7,
                'legal_reference': 'Arbitration clauses that discourage claims may be unconscionable',
                'court_treatment': 'Courts may strike down arbitration clauses that are procedurally unconscionable'
            }
        ]

        created_count = 0
        for data in risk_playbooks_data:
            # Generate embedding
            embedding = embedding_service.embed_text(data['example_clause_text'])

            # Create or update
            playbook, created = RiskPlaybook.objects.update_or_create(
                risk_name=data['risk_name'],
                defaults={
                    **data,
                    'embedding': embedding,
                    'embedding_model': 'all-MiniLM-L6-v2',
                    'is_active': True
                }
            )

            if created:
                created_count += 1
                self.stdout.write(f'  ✓ Created: {playbook.risk_name}')
            else:
                self.stdout.write(f'  ↻ Updated: {playbook.risk_name}')

        self.stdout.write(self.style.SUCCESS(f'Seeded {created_count} new risk playbooks'))

    def seed_intent_templates(self):
        """Seed intent templates with common legal intents"""
        self.stdout.write('Seeding intent templates...')

        intent_templates_data = [
            {
                'intent_name': 'Shift liability to counterparty',
                'intent_category': 'LIABILITY_SHIFT',
                'intent_description': 'Transfer liability and risk from one party to another party',
                'example_clause_text': 'Supplier shall assume all liability for damages arising from the Services, regardless of cause.',
                'party_impact': 'FAVOR_COUNTERPARTY',
                'risk_level': 'HIGH',
                'similarity_threshold': 0.65,
                'negotiation_guidance': 'Negotiate for mutual liability with caps based on contract value',
                'risk_mitigation': 'Request liability limitation to direct damages only with reasonable caps'
            },
            {
                'intent_name': 'Exclude consequential damages',
                'intent_category': 'DAMAGE_EXCLUSION',
                'intent_description': 'Prevent recovery of indirect, consequential, or punitive damages',
                'example_clause_text': 'Neither party shall be liable for consequential, indirect, incidental, special, or punitive damages.',
                'party_impact': 'NEUTRAL',
                'risk_level': 'MEDIUM',
                'similarity_threshold': 0.7,
                'negotiation_guidance': 'This is typically acceptable in commercial contracts',
                'risk_mitigation': 'Ensure limitation is mutual and carve out willful misconduct'
            },
            {
                'intent_name': 'Lock-in termination rights',
                'intent_category': 'TERMINATION_CONTROL',
                'intent_description': 'Restrict one party\'s ability to terminate while giving the other party flexibility',
                'example_clause_text': 'Client may terminate for convenience with 30 days notice. Vendor may only terminate for material breach after 90 days cure period.',
                'party_impact': 'FAVOR_COUNTERPARTY',
                'risk_level': 'HIGH',
                'similarity_threshold': 0.65,
                'negotiation_guidance': 'Request mutual termination for convenience rights',
                'risk_mitigation': 'Negotiate for balanced termination rights or exit fees'
            },
            {
                'intent_name': 'Transfer IP ownership',
                'intent_category': 'IP_TRANSFER',
                'intent_description': 'Transfer ownership of intellectual property created under the agreement',
                'example_clause_text': 'All work product, inventions, and intellectual property created shall be owned by Client.',
                'party_impact': 'FAVOR_COUNTERPARTY',
                'risk_level': 'HIGH',
                'similarity_threshold': 0.65,
                'negotiation_guidance': 'Negotiate for license instead of ownership or additional compensation',
                'risk_mitigation': 'Carve out pre-existing IP and reusable components'
            },
            {
                'intent_name': 'Establish payment obligations',
                'intent_category': 'PAYMENT_CONTROL',
                'intent_description': 'Define payment terms, amounts, and schedules',
                'example_clause_text': 'Client shall pay Vendor the fees set forth in Exhibit A within 30 days of invoice date.',
                'party_impact': 'MUTUAL',
                'risk_level': 'LOW',
                'similarity_threshold': 0.7,
                'negotiation_guidance': 'Standard payment terms, ensure clarity on late fees',
                'risk_mitigation': 'Include provisions for disputes and withholding'
            },
            {
                'intent_name': 'Impose confidentiality obligations',
                'intent_category': 'CONFIDENTIALITY_OBLIGATION',
                'intent_description': 'Require parties to maintain confidentiality of sensitive information',
                'example_clause_text': 'Receiving Party shall maintain Confidential Information in strict confidence and not disclose to third parties.',
                'party_impact': 'MUTUAL',
                'risk_level': 'LOW',
                'similarity_threshold': 0.7,
                'negotiation_guidance': 'Standard provision, ensure reasonable exceptions',
                'risk_mitigation': 'Include standard exceptions (public knowledge, prior possession, etc.)'
            },
            {
                'intent_name': 'Restrict competition',
                'intent_category': 'NON_COMPETE',
                'intent_description': 'Prevent one party from competing with the other party',
                'example_clause_text': 'Contractor agrees not to provide services to any competitor of Company during the term and for 2 years thereafter.',
                'party_impact': 'FAVOR_COUNTERPARTY',
                'risk_level': 'HIGH',
                'similarity_threshold': 0.65,
                'negotiation_guidance': 'Narrow scope to specific products/services and geography',
                'risk_mitigation': 'Limit duration and geographic scope, consider reasonableness'
            },
            {
                'intent_name': 'Require indemnification',
                'intent_category': 'INDEMNIFICATION',
                'intent_description': 'Obligate one party to defend and hold harmless the other party',
                'example_clause_text': 'Vendor shall indemnify, defend, and hold harmless Client from all third-party claims arising from the Services.',
                'party_impact': 'FAVOR_YOU',
                'risk_level': 'MEDIUM',
                'similarity_threshold': 0.7,
                'negotiation_guidance': 'Ensure indemnification is limited to party\'s own actions',
                'risk_mitigation': 'Carve out indemnification for indemnitee\'s negligence'
            },
            {
                'intent_name': 'Select governing law and venue',
                'intent_category': 'GOVERNING_LAW',
                'intent_description': 'Specify which jurisdiction\'s laws apply and where disputes are heard',
                'example_clause_text': 'This Agreement shall be governed by the laws of the State of Delaware, and parties consent to exclusive jurisdiction in Delaware courts.',
                'party_impact': 'NEUTRAL',
                'risk_level': 'LOW',
                'similarity_threshold': 0.7,
                'negotiation_guidance': 'Negotiate for neutral jurisdiction or party\'s home state',
                'risk_mitigation': 'Consider business-friendly states like Delaware or New York'
            },
            {
                'intent_name': 'Mandate arbitration for disputes',
                'intent_category': 'DISPUTE_RESOLUTION',
                'intent_description': 'Require disputes to be resolved through arbitration instead of litigation',
                'example_clause_text': 'All disputes shall be resolved by binding arbitration under AAA Commercial Rules.',
                'party_impact': 'NEUTRAL',
                'risk_level': 'MEDIUM',
                'similarity_threshold': 0.7,
                'negotiation_guidance': 'Ensure arbitration rules are fair and costs are shared',
                'risk_mitigation': 'Include carve-outs for injunctive relief and small claims'
            }
        ]

        created_count = 0
        for data in intent_templates_data:
            # Generate embedding
            embedding = embedding_service.embed_text(data['example_clause_text'])

            # Create or update
            template, created = IntentTemplate.objects.update_or_create(
                intent_name=data['intent_name'],
                defaults={
                    **data,
                    'embedding': embedding,
                    'embedding_model': 'all-MiniLM-L6-v2',
                    'is_active': True
                }
            )

            if created:
                created_count += 1
                self.stdout.write(f'  ✓ Created: {template.intent_name}')
            else:
                self.stdout.write(f'  ↻ Updated: {template.intent_name}')

        self.stdout.write(self.style.SUCCESS(f'Seeded {created_count} new intent templates'))

    def seed_approved_clauses(self):
        """Seed approved clauses with safer alternatives"""
        self.stdout.write('Seeding approved clauses...')

        approved_clauses_data = [
            {
                'clause_name': 'Balanced Liability Cap',
                'clause_type': 'LIABILITY',
                'clause_text': 'Each party\'s total liability under this Agreement shall be limited to the amounts paid or payable under this Agreement in the twelve (12) months preceding the event giving rise to the claim. This limitation shall not apply to: (a) either party\'s indemnification obligations; (b) breaches of confidentiality; or (c) willful misconduct or gross negligence.',
                'intent_name': 'Shift liability to counterparty',
                'protection_level': 'BALANCED',
                'jurisdiction': 'Common Law',
                'legal_notes': 'Standard balanced liability cap with appropriate carve-outs'
            },
            {
                'clause_name': 'Mutual Termination for Convenience',
                'clause_type': 'TERMINATION',
                'clause_text': 'Either party may terminate this Agreement for convenience upon ninety (90) days prior written notice to the other party. Upon such termination, Client shall pay Vendor for all services performed through the effective date of termination.',
                'intent_name': 'Lock-in termination rights',
                'protection_level': 'BALANCED',
                'jurisdiction': 'Common Law',
                'legal_notes': 'Provides mutual termination rights with reasonable notice period'
            },
            {
                'clause_name': 'IP License with Carve-Outs',
                'clause_type': 'IP_OWNERSHIP',
                'clause_text': 'Vendor grants Client a perpetual, royalty-free license to use work product created specifically for Client under this Agreement. Vendor retains ownership of: (a) pre-existing intellectual property; (b) general knowledge and skills; and (c) reusable tools and frameworks. Vendor may reuse such retained IP for other clients.',
                'intent_name': 'Transfer IP ownership',
                'protection_level': 'BALANCED',
                'jurisdiction': 'Common Law',
                'legal_notes': 'Provides license instead of transfer, protects vendor\'s reusable IP'
            },
            {
                'clause_name': 'Limited Indemnity',
                'clause_type': 'INDEMNIFICATION',
                'clause_text': 'Each party shall indemnify the other from third-party claims alleging that such party\'s performance under this Agreement infringes third-party intellectual property rights or violates applicable law. The indemnifying party\'s obligations are contingent upon the indemnified party: (a) promptly notifying the indemnifying party of the claim; (b) granting control of the defense; and (c) cooperating in the defense. This indemnification shall not apply to claims arising from the indemnified party\'s modifications or misuse.',
                'intent_name': 'Require indemnification',
                'protection_level': 'BALANCED',
                'jurisdiction': 'Common Law',
                'legal_notes': 'Mutual indemnification with standard procedures and limitations'
            },
            {
                'clause_name': 'Time-Limited Confidentiality with Standard Exceptions',
                'clause_type': 'CONFIDENTIALITY',
                'clause_text': 'Receiving Party shall maintain Confidential Information in confidence for five (5) years from disclosure and not disclose it to third parties. This obligation does not apply to information that: (a) is publicly available through no fault of Receiving Party; (b) was rightfully possessed prior to disclosure; (c) is independently developed; (d) is disclosed by a third party without restriction; or (e) must be disclosed by law.',
                'intent_name': 'Impose confidentiality obligations',
                'protection_level': 'BALANCED',
                'jurisdiction': 'Common Law',
                'legal_notes': 'Standard confidentiality provision with reasonable term and exceptions'
            },
            {
                'clause_name': 'Mutual Consequential Damages Waiver',
                'clause_type': 'LIMITATION_OF_DAMAGES',
                'clause_text': 'EXCEPT FOR BREACHES OF CONFIDENTIALITY, INDEMNIFICATION OBLIGATIONS, OR WILLFUL MISCONDUCT, NEITHER PARTY SHALL BE LIABLE FOR ANY INDIRECT, INCIDENTAL, CONSEQUENTIAL, SPECIAL, OR PUNITIVE DAMAGES, EVEN IF ADVISED OF THEIR POSSIBILITY.',
                'intent_name': 'Exclude consequential damages',
                'protection_level': 'BALANCED',
                'jurisdiction': 'Common Law',
                'legal_notes': 'Mutual waiver with appropriate carve-outs for serious breaches'
            },
            {
                'clause_name': 'Reasonable Non-Compete',
                'clause_type': 'NON_COMPETE',
                'clause_text': 'During the term of this Agreement, Vendor agrees not to provide substantially similar services to direct competitors of Client specifically identified in Exhibit A, within the geographic territory of [specify region]. This restriction shall not apply to: (a) Vendor\'s pre-existing client relationships; (b) services materially different from those provided to Client; or (c) Vendor\'s general industry participation.',
                'intent_name': 'Restrict competition',
                'protection_level': 'BALANCED',
                'jurisdiction': 'Common Law',
                'legal_notes': 'Narrow non-compete limited to specific competitors and services'
            },
            {
                'clause_name': 'Balanced Payment Terms',
                'clause_type': 'PAYMENT',
                'clause_text': 'Client shall pay Vendor the fees specified in the applicable Statement of Work within thirty (30) days of invoice date. Late payments shall accrue interest at the lesser of 1.5% per month or the maximum rate permitted by law. Client may withhold payment for disputed amounts by providing written notice of the dispute with reasonable detail. Parties shall work in good faith to resolve payment disputes within fifteen (15) days.',
                'intent_name': 'Establish payment obligations',
                'protection_level': 'BALANCED',
                'jurisdiction': 'Common Law',
                'legal_notes': 'Standard payment terms with dispute resolution mechanism'
            }
        ]

        created_count = 0
        for data in approved_clauses_data:
            # Generate embedding
            embedding = embedding_service.embed_text(data['clause_text'])

            # Create or update
            approved_clause, created = ApprovedClause.objects.update_or_create(
                clause_name=data['clause_name'],
                defaults={
                    **data,
                    'embedding': embedding,
                    'embedding_model': 'all-MiniLM-L6-v2',
                    'contract_types': ['MSA', 'SLA', 'SOW', 'NDA'],  # Applicable to most contract types
                    'is_active': True,
                    'version': 1
                }
            )

            if created:
                created_count += 1
                self.stdout.write(f'  ✓ Created: {approved_clause.clause_name}')
            else:
                self.stdout.write(f'  ↻ Updated: {approved_clause.clause_name}')

        self.stdout.write(self.style.SUCCESS(f'Seeded {created_count} new approved clauses'))
