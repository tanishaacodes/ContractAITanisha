import { useEffect, useState } from "react";
import api from "../utils/api";

const ContractClusters = () => {
  const [html, setHtml] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    api.get("/contracts/classify/clusters/")
      .then(res => setHtml(res.data.html))
      .catch(() => setError("Not enough contracts to visualize clustering"));
  }, []);

  if (error) {
    return <p className="text-red-400 p-6">{error}</p>;
  }

  return (
    <div className="p-6 bg-slate-900 rounded-xl">
      <h1 className="text-2xl font-bold text-white mb-4">
        Contract Topic Clustering (BERTopic)
      </h1>

      <iframe
        title="BERTopic Clustering"
        srcDoc={html}
        className="w-full h-[650px] rounded-lg border border-slate-700"
      />
    </div>
  );
};

export default ContractClusters;
