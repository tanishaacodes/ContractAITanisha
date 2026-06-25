import { useState } from "react";
import { useParams } from "react-router-dom";
import api from "../utils/api";

const ContractQA = () => {
  const { id } = useParams(); // Get contract ID from URL
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState([]);

  const askQuestion = async () => {
    if (!question.trim()) return;

    setLoading(true);

    try {
      const res = await api.post("/rag/qa", {
        query: `CONTRACT_ID: ${id}\nQUESTION: ${question}`
      });

      const responseAnswer = res.data.answer || "No answer returned.";

      setAnswer(responseAnswer);

      // Save chat history
      setHistory((prev) => [
        ...prev,
        {
          q: question,
          a: responseAnswer,
        },
      ]);

      setQuestion("");
    } catch (error) {
      console.error(error);
      setAnswer("Error fetching answer from AI.");
    }

    setLoading(false);
  };

  return (
    <div className="p-6 text-white max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-4">Ask Questions About Contract</h1>
      <p className="text-slate-400 mb-6">
        Contract ID: <span className="text-blue-400">{id}</span>
      </p>

      {/* QUESTION INPUT */}
      <div className="bg-slate-800 p-4 rounded-lg mb-4">
        <textarea
          rows="4"
          className="w-full bg-slate-700 p-3 rounded text-white outline-none border border-slate-600"
          placeholder="Ask something about this contract..."
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
        ></textarea>

        <button
          onClick={askQuestion}
          disabled={loading}
          className="mt-3 bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded text-white"
        >
          {loading ? "Thinking..." : "Ask"}
        </button>
      </div>

      {/* ANSWER BOX */}
      {answer && (
        <div className="bg-slate-800 p-4 rounded-lg mt-4">
          <h2 className="text-lg font-semibold mb-2">AI Answer</h2>
          <p className="text-slate-300 whitespace-pre-line">{answer}</p>
        </div>
      )}

      {/* CHAT HISTORY */}
      {history.length > 0 && (
        <div className="mt-6">
          <h2 className="text-lg font-semibold mb-2">Previous Questions</h2>
          <div className="space-y-3">
            {history.map((h, i) => (
              <div key={i} className="bg-slate-800 p-4 rounded-lg">
                <p className="font-bold text-blue-300">Q: {h.q}</p>
                <p className="text-slate-300 mt-1 whitespace-pre-line">
                  {h.a}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default ContractQA;
