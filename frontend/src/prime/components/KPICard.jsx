export default function KPICard({ title, value, danger = false, icon: Icon }) {
  return (
    <div className={`rounded-2xl p-6 shadow-2xl backdrop-blur-lg bg-gradient-to-br from-white/10 to-white/5 border ${
        danger ? "border-red-500/50 shadow-red-500/20" : "border-white/10"
      } hover:scale-105 hover:-translate-y-1 transition-transform duration-200`}
    >
      <div className="flex items-center justify-between mb-3">
        <p className="text-sm text-gray-400 uppercase tracking-wide">{title}</p>
        {Icon && (
          <div className={`p-2 rounded-lg ${danger ? "bg-red-500/20" : "bg-cyan-500/20"}`}>
            <Icon className={`w-5 h-5 ${danger ? "text-red-400" : "text-cyan-400"}`} />
          </div>
        )}
      </div>
      <h2 className={`text-3xl font-bold ${danger ? "text-red-400" : "text-white"}`}>
        {value}
      </h2>
      <div className={`h-1 mt-3 rounded-full ${danger ? "bg-red-500/30" : "bg-cyan-500/30"}`} />
    </div>
  );
}
