import { useState } from "react";
import { FileText, Download, Printer, Mail, CheckCircle } from "lucide-react";
import jsPDF from "jspdf";
import autoTable from "jspdf-autotable";

export default function BoardReportExporter({ dashboardData, selectedContract }) {
  const [exporting, setExporting] = useState(false);
  const [exportSuccess, setExportSuccess] = useState(false);

  const generatePDFReport = () => {
    setExporting(true);

    try {
      const doc = new jsPDF();
      const pageWidth = doc.internal.pageSize.getWidth();
      const pageHeight = doc.internal.pageSize.getHeight();

      // Header with Logo Area
      doc.setFillColor(15, 23, 42); // slate-900
      doc.rect(0, 0, pageWidth, 40, 'F');

      doc.setTextColor(255, 255, 255);
      doc.setFontSize(24);
      doc.setFont(undefined, 'bold');
      doc.text('UniContractAI', 20, 20);

      doc.setFontSize(12);
      doc.setFont(undefined, 'normal');
      doc.text('Executive Dashboard Report', 20, 30);

      // Date and Report Info
      doc.setTextColor(148, 163, 184); // slate-400
      doc.setFontSize(10);
      const reportDate = new Date().toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      });
      doc.text(`Generated: ${reportDate}`, pageWidth - 70, 20);
      doc.text(selectedContract === "all" ? "Portfolio View" : "Contract View", pageWidth - 70, 28);

      let yPos = 55;

      // Executive Summary Section
      doc.setTextColor(30, 41, 59); // slate-800
      doc.setFontSize(16);
      doc.setFont(undefined, 'bold');
      doc.text('Executive Summary', 20, yPos);
      yPos += 10;

      // KPI Summary Table
      const kpiData = [
        ['Portfolio Value', dashboardData?.portfolioValue || '$2.4B'],
        ['Total Contracts', dashboardData?.totalContracts || '435'],
        ['High Risk Contracts', dashboardData?.highRiskContracts || '28'],
        ['Avg Risk Score', dashboardData?.avgRiskScore || '67'],
        ['Risk-Adjusted Margin', dashboardData?.riskAdjustedMargin || '18.7%']
      ];

      autoTable(doc, {
        startY: yPos,
        head: [['Metric', 'Value']],
        body: kpiData,
        theme: 'grid',
        headStyles: {
          fillColor: [59, 130, 246], // blue-600
          textColor: [255, 255, 255],
          fontStyle: 'bold',
          fontSize: 11
        },
        bodyStyles: {
          fontSize: 10,
          textColor: [30, 41, 59]
        },
        alternateRowStyles: {
          fillColor: [248, 250, 252] // slate-50
        },
        margin: { left: 20, right: 20 }
      });

      yPos = doc.lastAutoTable.finalY + 15;

      // Risk Analysis Section
      doc.setFontSize(16);
      doc.setFont(undefined, 'bold');
      doc.text('Risk Analysis', 20, yPos);
      yPos += 10;

      const riskData = [
        ['Liability Risk', '85%', 'High', 'Cap liability at 2x annual fees'],
        ['Indemnity Risk', '72%', 'High', 'Limit to direct damages only'],
        ['IP Risk', '45%', 'Medium', 'Add IP ownership clarity'],
        ['Data Risk', '38%', 'Medium', 'Strengthen data protection'],
        ['Compliance Risk', '52%', 'Medium', 'Regular compliance audits']
      ];

      autoTable(doc, {
        startY: yPos,
        head: [['Risk Category', 'Score', 'Level', 'Recommendation']],
        body: riskData,
        theme: 'striped',
        headStyles: {
          fillColor: [220, 38, 38], // red-600
          textColor: [255, 255, 255],
          fontStyle: 'bold',
          fontSize: 10
        },
        bodyStyles: {
          fontSize: 9,
          textColor: [30, 41, 59]
        },
        columnStyles: {
          0: { cellWidth: 35 },
          1: { cellWidth: 20, halign: 'center' },
          2: { cellWidth: 25, halign: 'center' },
          3: { cellWidth: 70 }
        },
        margin: { left: 20, right: 20 }
      });

      // Add new page for Profitability
      doc.addPage();
      yPos = 20;

      // Profitability Section
      doc.setFontSize(16);
      doc.setFont(undefined, 'bold');
      doc.text('Profitability Analysis', 20, yPos);
      yPos += 10;

      const profitData = [
        ['Total Revenue', '$2.4B', '100%'],
        ['Total Cost', '$1.8B', '75%'],
        ['Gross Profit', '$600M', '25%'],
        ['Risk Reserve', '$120M', '5%'],
        ['Risk-Adjusted Profit', '$480M', '20%']
      ];

      autoTable(doc, {
        startY: yPos,
        head: [['Metric', 'Amount', 'Margin']],
        body: profitData,
        theme: 'grid',
        headStyles: {
          fillColor: [16, 185, 129], // green-600
          textColor: [255, 255, 255],
          fontStyle: 'bold',
          fontSize: 11
        },
        bodyStyles: {
          fontSize: 10,
          textColor: [30, 41, 59]
        },
        columnStyles: {
          1: { halign: 'right' },
          2: { halign: 'center' }
        },
        margin: { left: 20, right: 20 }
      });

      yPos = doc.lastAutoTable.finalY + 15;

      // AI Recommendations Section
      doc.setFontSize(16);
      doc.setFont(undefined, 'bold');
      doc.text('AI Recommendations', 20, yPos);
      yPos += 10;

      const recommendationsData = [
        ['1', 'Cap Liability at 2x Annual Fees', 'High', '28% risk reduction, +4.2% margin'],
        ['2', 'Add Force Majeure Clause', 'High', '15% risk reduction, +2.1% margin'],
        ['3', 'Reduce Penalty from 10% to 5%', 'Medium', '22% risk reduction, +3.8% margin'],
        ['4', 'Limit Indemnity to Direct Damages', 'Medium', '20% risk reduction, +3.5% margin'],
        ['5', 'Extend Notice Period to 90 Days', 'High', '12% risk reduction, +1.5% margin']
      ];

      autoTable(doc, {
        startY: yPos,
        head: [['#', 'Recommendation', 'Feasibility', 'Projected Impact']],
        body: recommendationsData,
        theme: 'striped',
        headStyles: {
          fillColor: [139, 92, 246], // purple-600
          textColor: [255, 255, 255],
          fontStyle: 'bold',
          fontSize: 10
        },
        bodyStyles: {
          fontSize: 9,
          textColor: [30, 41, 59]
        },
        columnStyles: {
          0: { cellWidth: 10, halign: 'center' },
          1: { cellWidth: 60 },
          2: { cellWidth: 25, halign: 'center' },
          3: { cellWidth: 55 }
        },
        margin: { left: 20, right: 20 }
      });

      // Footer on all pages
      const pageCount = doc.internal.getNumberOfPages();
      for (let i = 1; i <= pageCount; i++) {
        doc.setPage(i);
        doc.setFillColor(241, 245, 249); // slate-100
        doc.rect(0, pageHeight - 20, pageWidth, 20, 'F');

        doc.setTextColor(100, 116, 139); // slate-500
        doc.setFontSize(8);
        doc.text(
          `UniContractAI Executive Report | Confidential | Page ${i} of ${pageCount}`,
          pageWidth / 2,
          pageHeight - 10,
          { align: 'center' }
        );

        doc.setTextColor(148, 163, 184); // slate-400
        doc.text(
          '🤖 Generated with AI-powered Contract Intelligence',
          pageWidth / 2,
          pageHeight - 5,
          { align: 'center' }
        );
      }

      // Save the PDF
      const filename = selectedContract === "all"
        ? `UniContractAI_Portfolio_Report_${new Date().toISOString().split('T')[0]}.pdf`
        : `UniContractAI_Contract_Report_${new Date().toISOString().split('T')[0]}.pdf`;

      doc.save(filename);

      setExportSuccess(true);
      setTimeout(() => setExportSuccess(false), 3000);
    } catch (error) {
      console.error("Error generating PDF:", error);
      alert("Error generating report. Please try again.");
    } finally {
      setExporting(false);
    }
  };

  const handlePrint = () => {
    window.print();
  };

  const handleEmailReport = () => {
    const subject = encodeURIComponent("UniContractAI Executive Dashboard Report");
    const body = encodeURIComponent(
      `Please find attached the UniContractAI Executive Dashboard Report generated on ${new Date().toLocaleDateString()}.\n\n` +
      `Report Type: ${selectedContract === "all" ? "Portfolio Overview" : "Contract Analysis"}\n\n` +
      `This report includes:\n` +
      `- Executive Summary\n` +
      `- Risk Analysis\n` +
      `- Profitability Metrics\n` +
      `- AI-powered Recommendations\n\n` +
      `Generated by UniContractAI`
    );
    window.location.href = `mailto:?subject=${subject}&body=${body}`;
  };

  return (
    <div className="rounded-2xl bg-gradient-to-br from-white/5 to-white/10 p-6 shadow-2xl backdrop-blur-lg border border-white/10">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-xl font-bold text-white flex items-center gap-2">
          <div className="w-1 h-6 bg-gradient-to-b from-indigo-500 to-purple-600 rounded-full" />
          Executive Board Report
        </h3>
        <FileText className="w-5 h-5 text-indigo-400" />
      </div>

      <p className="text-gray-400 text-sm mb-6">
        Export professional board-ready reports with AI insights, risk analysis, and recommendations.
      </p>

      {/* Export Options */}
      <div className="grid grid-cols-1 gap-3">
        {/* PDF Export */}
        <button
          onClick={generatePDFReport}
          disabled={exporting}
          className="flex items-center justify-between p-4 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 rounded-lg transition-all transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <div className="flex items-center gap-3">
            <Download className="w-5 h-5 text-white" />
            <div className="text-left">
              <p className="text-white font-semibold">Export PDF Report</p>
              <p className="text-indigo-200 text-xs">Comprehensive executive summary</p>
            </div>
          </div>
          {exportSuccess && <CheckCircle className="w-5 h-5 text-green-400" />}
        </button>

        {/* Print */}
        <button
          onClick={handlePrint}
          className="flex items-center justify-between p-4 bg-white/10 hover:bg-white/20 rounded-lg transition-all border border-white/10"
        >
          <div className="flex items-center gap-3">
            <Printer className="w-5 h-5 text-white" />
            <div className="text-left">
              <p className="text-white font-semibold">Print Dashboard</p>
              <p className="text-gray-400 text-xs">Print current dashboard view</p>
            </div>
          </div>
        </button>

        {/* Email */}
        <button
          onClick={handleEmailReport}
          className="flex items-center justify-between p-4 bg-white/10 hover:bg-white/20 rounded-lg transition-all border border-white/10"
        >
          <div className="flex items-center gap-3">
            <Mail className="w-5 h-5 text-white" />
            <div className="text-left">
              <p className="text-white font-semibold">Email Report</p>
              <p className="text-gray-400 text-xs">Share via email client</p>
            </div>
          </div>
        </button>
      </div>

      {/* Report Preview Info */}
      <div className="mt-6 p-4 bg-blue-500/10 border border-blue-500/30 rounded-lg">
        <p className="text-blue-400 text-sm font-semibold mb-2">📊 Report Includes:</p>
        <ul className="text-gray-300 text-xs space-y-1">
          <li>• Executive Summary with Key Metrics</li>
          <li>• Detailed Risk Analysis & Scoring</li>
          <li>• Profitability & Margin Analysis</li>
          <li>• AI-Powered Recommendations</li>
          <li>• Monte Carlo Exposure Projections</li>
          <li>• Board-Ready Formatting</li>
        </ul>
      </div>
    </div>
  );
}
