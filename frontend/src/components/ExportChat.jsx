import { Download } from 'lucide-react';
import jsPDF from 'jspdf';

export default function ExportChat({ messages, conversationTitle = 'Chat History', className = '' }) {

  const exportToPDF = () => {
    try {
      const doc = new jsPDF();
      const pageWidth = doc.internal.pageSize.getWidth();
      const pageHeight = doc.internal.pageSize.getHeight();
      const margin = 20;
      const maxWidth = pageWidth - 2 * margin;
      let yPos = margin;

      // Title
      doc.setFontSize(18);
      doc.setFont('helvetica', 'bold');
      doc.text(conversationTitle, margin, yPos);
      yPos += 10;

      // Subtitle
      doc.setFontSize(10);
      doc.setFont('helvetica', 'normal');
      doc.setTextColor(128, 128, 128);
      doc.text(`Exported on ${new Date().toLocaleString()}`, margin, yPos);
      yPos += 15;

      // Messages
      doc.setFontSize(11);
      doc.setFont('helvetica', 'normal');

      messages.forEach((msg, index) => {
        // Check if we need a new page
        if (yPos > pageHeight - margin - 30) {
          doc.addPage();
          yPos = margin;
        }

        // Message header
        doc.setFont('helvetica', 'bold');
        doc.setTextColor(...(msg.type === 'user' ? [37, 99, 235] : [34, 197, 94]));
        const header = msg.type === 'user' ? 'You:' : 'AI Assistant:';
        doc.text(header, margin, yPos);
        yPos += 7;

        // Message content
        doc.setFont('helvetica', 'normal');
        doc.setTextColor(0, 0, 0);
        const lines = doc.splitTextToSize(msg.content, maxWidth);

        lines.forEach((line) => {
          if (yPos > pageHeight - margin - 10) {
            doc.addPage();
            yPos = margin;
          }
          doc.text(line, margin, yPos);
          yPos += 5;
        });

        // Sources (if AI message)
        if (msg.type === 'assistant' && msg.sources && msg.sources.length > 0) {
          yPos += 3;
          doc.setFontSize(9);
          doc.setTextColor(128, 128, 128);
          doc.text('Sources:', margin, yPos);
          yPos += 5;

          msg.sources.forEach((source, idx) => {
            if (yPos > pageHeight - margin - 10) {
              doc.addPage();
              yPos = margin;
            }
            const sourceText = `• ${source.filename || source.original_filename || 'Unknown'}${source.pageNumbers ? ` (Pages: ${source.pageNumbers.join(', ')})` : ''}`;
            doc.text(sourceText, margin + 5, yPos);
            yPos += 5;
          });
        }

        yPos += 10; // Space between messages
      });

      // Save PDF
      const filename = `${conversationTitle.replace(/[^a-z0-9]/gi, '_')}_${Date.now()}.pdf`;
      doc.save(filename);
    } catch (error) {
      console.error('Error exporting to PDF:', error);
      alert('Failed to export chat. Please try again.');
    }
  };

  return (
    <button
      onClick={exportToPDF}
      className={`flex items-center gap-2 px-4 py-2 bg-green-500 hover:bg-green-600 text-white rounded-lg transition-colors duration-200 ${className}`}
      title="Export chat to PDF"
    >
      <Download className="w-4 h-4" />
      <span className="text-sm font-medium">Export PDF</span>
    </button>
  );
}
