import { motion } from "framer-motion";
import { Download, RefreshCw, CheckCircle2, Clock, FileBadge } from "lucide-react";
import { obtenirUrlTelechargement } from "../utils/api";

export default function ResultPanel({ tache, onNouveau }) {
  const estBatch = Boolean(tache?.batch);

  if (estBatch) {
    const items = tache.items || [];
    const totalPages = items.reduce((acc, item) => {
      const r = item?.resultat || {};
      return acc + (r.nombre_pages || r.nombre_slides || 1);
    }, 0);
    const totalWatermarks = items.reduce((acc, item) => {
      const r = item?.resultat || {};
      return acc + (r.pages_avec_watermark || r.slides_avec_watermark || 0);
    }, 0);
    const totalTempsMs = items.reduce((acc, item) => acc + (item.temps_traitement_ms || 0), 0);

    const statsBatch = [
      { label: "Fichiers traites", val: items.length, ic: FileBadge },
      { label: "Pages traitees", val: totalPages, ic: CheckCircle2 },
      { label: "Temps cumule", val: `${(totalTempsMs / 1000).toFixed(1)}s`, ic: Clock },
    ];

    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
        className="w-full max-w-4xl"
      >
        <div className="m3-glass-heavy rounded-[3rem] p-10 text-center shadow-[0_20px_40px_-10px_rgba(15,23,42,0.15)] relative overflow-hidden">
          <h3 className="text-4xl font-extrabold text-slate-900 mb-2">Batch termine</h3>
          <p className="text-slate-600 font-medium mb-8">
            {items.length} fichier(s) nettoye(s) • {totalWatermarks} watermark(s) supprime(s)
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
            {statsBatch.map(({ label, val, ic: Ic }) => (
              <div
                key={label}
                className="bg-white/60 backdrop-blur-md rounded-3xl p-5 border border-white shadow-sm flex flex-col items-center justify-center"
              >
                <div className="w-10 h-10 bg-amber-50 rounded-xl flex items-center justify-center mb-3">
                  <Ic className="w-5 h-5 text-amber-600" />
                </div>
                <p className="text-2xl font-black text-slate-900 mb-1">{val}</p>
                <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">{label}</p>
              </div>
            ))}
          </div>

          <div className="max-h-72 overflow-auto space-y-3 mb-8 px-1">
            {items.map((item) => {
              const urlItem = obtenirUrlTelechargement(item.id_tache);
              return (
                <div
                  key={item.id_tache}
                  className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 bg-white/70 border border-white rounded-2xl px-4 py-3 text-left"
                >
                  <div className="min-w-0">
                    <p className="font-bold text-slate-900 truncate">{item.nom_fichier}</p>
                    <p className="text-sm text-slate-500">{item.type_fichier?.toUpperCase()} • {(item.temps_traitement_ms / 1000).toFixed(1)}s</p>
                  </div>
                  <button
                    onClick={() => window.open(urlItem, "_blank")}
                    className="btn-m3-primary h-11 px-4 rounded-xl"
                  >
                    <Download className="w-4 h-4" />
                    Telecharger
                  </button>
                </div>
              );
            })}
          </div>

          <button onClick={onNouveau} className="btn-m3-secondary cursor-pointer h-14 px-8 text-lg rounded-[1.2rem]">
            <RefreshCw className="w-5 h-5" />
            Nouveau document
          </button>
        </div>
      </motion.div>
    );
  }

  const r = tache?.resultat || {};
  const url = obtenirUrlTelechargement(tache.id_tache);

  const pages = r.nombre_pages || r.nombre_slides || 1;
  const wm = r.pages_avec_watermark || r.slides_avec_watermark || (tache.watermark_detecte ? 1 : 0);
  const temps = `${(tache.temps_traitement_ms / 1000).toFixed(1)}s`;

  const stats = [
    { label: "Pages traitees", val: pages, ic: FileBadge },
    { label: "Watermarks effaces", val: wm, ic: CheckCircle2 },
    { label: "Temps record", val: temps, ic: Clock },
  ];

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
      className="w-full max-w-2xl"
    >
      <div className="m3-glass-heavy rounded-[3rem] p-12 text-center shadow-[0_20px_40px_-10px_rgba(15,23,42,0.15)] relative overflow-hidden">
        <div className="absolute -top-32 -left-32 w-64 h-64 bg-emerald-400/20 rounded-full blur-[80px] pointer-events-none" />
        <div className="absolute -bottom-32 -right-32 w-64 h-64 bg-amber-600/20 rounded-full blur-[80px] pointer-events-none" />

        <motion.div
          initial={{ scale: 0, rotate: -45 }}
          animate={{ scale: 1, rotate: 0 }}
          transition={{ type: "spring", stiffness: 200, delay: 0.1 }}
          className="relative w-24 h-24 mx-auto mb-8 rounded-[2rem] bg-emerald-100 flex items-center justify-center shadow-[inset_0_2px_4px_rgba(255,255,255,0.8)]"
        >
          <CheckCircle2 className="w-12 h-12 text-emerald-500" />
        </motion.div>

        <h3 className="text-4xl font-extrabold text-slate-900 mb-3">Parfait !</h3>
        <p className="text-slate-600 font-medium mb-10 px-6 max-w-md mx-auto truncate">
          Le document <span className="text-slate-900 font-bold">{tache.nom_fichier}</span> est 100% propre.
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 mb-12">
          {stats.map(({ label, val, ic: Ic }, i) => (
            <motion.div
              key={label}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 + i * 0.1 }}
              className="bg-white/60 backdrop-blur-md rounded-3xl p-6 border border-white shadow-sm flex flex-col items-center justify-center tilt-card"
            >
              <div className="w-10 h-10 bg-amber-50 rounded-xl flex items-center justify-center mb-4">
                <Ic className="w-5 h-5 text-amber-600" />
              </div>
              <p className="text-3xl font-black text-slate-900 mb-1">{val}</p>
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">{label}</p>
            </motion.div>
          ))}
        </div>

        <div className="flex flex-col sm:flex-row gap-4">
          <button onClick={() => window.location.href = url} className="btn-m3-primary cursor-pointer flex-1 h-16 text-lg rounded-[1.5rem] shadow-[0_8px_32px_0_rgba(217,119,6,0.1)]">
            <Download className="w-6 h-6" />
            Recuperer le fichier
          </button>
          <button onClick={onNouveau} className="btn-m3-secondary cursor-pointer flex-1 h-16 text-lg rounded-[1.5rem]">
            <RefreshCw className="w-6 h-6" />
            Nouveau document
          </button>
        </div>
      </div>
    </motion.div>
  );
}
 