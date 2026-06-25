"""
PDF Export Service for Negotiation Memos
=========================================
Generates executive-grade PDF reports for What-If analysis results.

Features:
- Professional formatting with company branding
- Risk visualizations and KPIs
- Monte Carlo confidence intervals
- Negotiation recommendations
- Exportable for board meetings / stakeholder reviews

Requires: reportlab (pip install reportlab)
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
import io

logger = logging.getLogger(__name__)

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import (
        SimpleDocTemplate, Table, TableStyle, Paragraph,
        Spacer, PageBreak, Image as RLImage
    )
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False
    logger.warning("reportlab not installed. PDF export will not work.")


class PDFExporter:
    """
    PDF export for What-If analysis and negotiation memos.

    Generates board-room ready PDF reports.
    """

    def __init__(self):
        """Initialize PDF exporter"""
        if not HAS_REPORTLAB:
            raise ImportError("reportlab is required for PDF export. Install with: pip install reportlab")

    def export_what_if_analysis(
        self,
        contract_name: str,
        simulation_result: Dict[str, Any],
        user_name: str = 'User'
    ) -> bytes:
        """
        Export What-If simulation results to PDF.

        Args:
            contract_name: Name of the contract
            simulation_result: What-If simulation results
            user_name: Name of requesting user

        Returns:
            PDF bytes
        """
        buffer = io.BytesIO()

        # Create PDF document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=0.75*inch,
            bottomMargin=0.75*inch
        )

        # Build content
        story = []
        styles = getSampleStyleSheet()

        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1e40af'),
            spaceAfter=30,
            alignment=TA_CENTER
        )

        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#64748b'),
            spaceAfter=12,
            alignment=TA_CENTER
        )

        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#1e40af'),
            spaceAfter=12,
            spaceBefore=20
        )

        # === Header ===
        story.append(Paragraph("What-If Analysis Report", title_style))
        story.append(Paragraph(
            f"Contract: {contract_name}",
            subtitle_style
        ))
        story.append(Paragraph(
            f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}",
            subtitle_style
        ))
        story.append(Spacer(1, 0.3*inch))

        # === Executive Summary ===
        story.append(Paragraph("Executive Summary", heading_style))

        removed_clause = simulation_result.get('removed_clause', {})
        delta = simulation_result.get('delta', {})

        summary_data = [
            ['Metric', 'Value'],
            ['Removed Clause ID', str(removed_clause.get('id', 'N/A'))],
            ['Clause Type', removed_clause.get('type', 'N/A')],
            ['Clause Risk Score', f"{removed_clause.get('risk_score', 0):.3f}"],
            ['Risk Before', f"{delta.get('risk_before', 0):.3f}"],
            ['Risk After', f"{delta.get('risk_after', 0):.3f}"],
            ['Risk Reduction', f"{delta.get('risk_reduction', 0):.3f}"],
            ['Risk Reduction %', f"{delta.get('risk_reduction_pct', 0):.1f}%"],
        ]

        summary_table = Table(summary_data, colWidths=[3*inch, 3*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
        ]))

        story.append(summary_table)
        story.append(Spacer(1, 0.3*inch))

        # === Financial Exposure (if available) ===
        if 'exposure' in simulation_result:
            story.append(Paragraph("Financial Exposure Impact", heading_style))

            exposure = simulation_result['exposure']
            exp_data = exposure.get('exposure', {})

            exposure_data = [
                ['Metric', 'Amount'],
                ['Exposure Before', f"₹{exp_data.get('before', 0):,.2f}"],
                ['Exposure After', f"₹{exp_data.get('after', 0):,.2f}"],
                ['Exposure Reduced', f"₹{exp_data.get('delta', 0):,.2f}"],
                ['Reduction %', f"{exp_data.get('reduction_pct', 0):.1f}%"],
            ]

            exposure_table = Table(exposure_data, colWidths=[3*inch, 3*inch])
            exposure_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#059669')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.lightgreen, colors.white])
            ]))

            story.append(exposure_table)
            story.append(Spacer(1, 0.3*inch))

        # === Monte Carlo Analysis (if available) ===
        if 'monte_carlo' in simulation_result:
            story.append(Paragraph("Monte Carlo Confidence Analysis", heading_style))

            mc = simulation_result['monte_carlo']
            delta_mc = mc.get('delta', {})

            mc_data = [
                ['Metric', 'Value'],
                ['Simulations Run', f"{mc.get('iterations', 0):,}"],
                ['Mean Reduction', f"₹{delta_mc.get('mean', 0):,.2f}"],
                ['P90 Reduction', f"₹{delta_mc.get('p90', 0):,.2f}"],
                ['Confidence Statement', ''],
            ]

            mc_table = Table(mc_data, colWidths=[3*inch, 3*inch])
            mc_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#7c3aed')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.lightblue, colors.white])
            ]))

            story.append(mc_table)

            # Confidence statement
            confidence = mc.get('confidence_statement', '')
            if confidence:
                story.append(Spacer(1, 0.1*inch))
                conf_para = Paragraph(f"<i>{confidence}</i>", styles['Normal'])
                story.append(conf_para)

            story.append(Spacer(1, 0.3*inch))

        # === Negotiation Priorities ===
        story.append(Paragraph("Negotiation Priority Changes", heading_style))

        negotiation = simulation_result.get('negotiation', {})
        priority_shifts = negotiation.get('priority_shifts', [])

        if priority_shifts:
            shift_data = [['Clause ID', 'Before', 'After']]
            for shift in priority_shifts[:10]:  # Top 10
                shift_data.append([
                    str(shift.get('clause_id', 'N/A')),
                    shift.get('priority_before', 'N/A'),
                    shift.get('priority_after', 'N/A')
                ])

            shift_table = Table(shift_data, colWidths=[2*inch, 2*inch, 2*inch])
            shift_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#dc2626')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
            ]))

            story.append(shift_table)
        else:
            story.append(Paragraph("No significant priority changes detected.", styles['Normal']))

        story.append(Spacer(1, 0.3*inch))

        # === Recommendations ===
        story.append(Paragraph("Recommendations", heading_style))

        risk_reduction_pct = delta.get('risk_reduction_pct', 0)

        if risk_reduction_pct > 20:
            recommendation = "STRONG RECOMMENDATION: Removing or renegotiating this clause significantly reduces contract risk. This should be a high priority in negotiations."
        elif risk_reduction_pct > 10:
            recommendation = "MODERATE RECOMMENDATION: This clause contributes notable risk. Consider negotiating better terms or seeking additional protections."
        elif risk_reduction_pct > 5:
            recommendation = "CONSIDER: This clause has some risk impact. Review in context of overall contract strategy."
        else:
            recommendation = "LOW PRIORITY: Removing this clause has minimal risk impact. Focus negotiation efforts elsewhere."

        story.append(Paragraph(recommendation, styles['Normal']))
        story.append(Spacer(1, 0.5*inch))

        # === Footer ===
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.grey,
            alignment=TA_CENTER
        )

        story.append(Paragraph(
            f"Generated by ContractAI | Prepared for: {user_name}",
            footer_style
        ))
        story.append(Paragraph(
            "This report is based on AI-powered graph analysis and Monte Carlo simulation",
            footer_style
        ))

        # Build PDF
        doc.build(story)

        # Get PDF bytes
        pdf_bytes = buffer.getvalue()
        buffer.close()

        return pdf_bytes

    def export_portfolio_summary(
        self,
        portfolio_data: Dict[str, Any],
        user_name: str = 'User'
    ) -> bytes:
        """
        Export portfolio exposure summary to PDF.

        Args:
            portfolio_data: Portfolio exposure data
            user_name: Name of requesting user

        Returns:
            PDF bytes
        """
        buffer = io.BytesIO()

        # Create PDF document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=0.75*inch,
            bottomMargin=0.75*inch
        )

        story = []
        styles = getSampleStyleSheet()

        # Header
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1e40af'),
            spaceAfter=30,
            alignment=TA_CENTER
        )

        story.append(Paragraph("Portfolio Exposure Report", title_style))
        story.append(Paragraph(
            f"Generated: {datetime.now().strftime('%B %d, %Y')}",
            styles['Normal']
        ))
        story.append(Spacer(1, 0.3*inch))

        # Summary
        summary_data = [
            ['Metric', 'Value'],
            ['Total Exposure', portfolio_data.get('total_exposure_formatted', '₹0')],
            ['Total Contracts', str(portfolio_data.get('total_contracts', 0))],
            ['Concentration Risk', portfolio_data.get('concentration', {}).get('risk_level', 'N/A')],
        ]

        summary_table = Table(summary_data, colWidths=[3*inch, 3*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey)
        ]))

        story.append(summary_table)

        # Build PDF
        doc.build(story)

        pdf_bytes = buffer.getvalue()
        buffer.close()

        return pdf_bytes


# Convenience functions
def export_what_if_pdf(
    contract_name: str,
    simulation_result: Dict[str, Any],
    user_name: str = 'User'
) -> bytes:
    """Export What-If analysis to PDF"""
    exporter = PDFExporter()
    return exporter.export_what_if_analysis(contract_name, simulation_result, user_name)


def export_portfolio_pdf(
    portfolio_data: Dict[str, Any],
    user_name: str = 'User'
) -> bytes:
    """Export portfolio summary to PDF"""
    exporter = PDFExporter()
    return exporter.export_portfolio_summary(portfolio_data, user_name)
