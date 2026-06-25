import RAGSearch from '../components/RAGSearch';

const RAGSearchPage = () => {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl md:text-4xl font-bold text-white mb-1">
          RAG-Powered Contract Search
        </h1>
        <p className="text-slate-400 text-sm md:text-base">
          Ask questions about your contracts in natural language using AI-powered semantic search
        </p>
      </div>

      {/* RAG Search Component */}
      <RAGSearch />
    </div>
  );
};

export default RAGSearchPage;
