import { motion, AnimatePresence } from "framer-motion";
import { Loader2, ArrowRight } from "lucide-react";

export default function ProgressPanel({ progression, message, nomFichier, preview }) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className="w-full max-w-4xl m3-glass-surface rounded-[2rem] sm:rounded-[2.5rem] p-5 sm:p-10 text-center shadow-[0_20px_40px_-10px_rgba(15,23,42,0.15)] flex flex-col"
    >
      <div className="flex flex-col sm:flex-row items-center justify-between mb-4 sm:mb-8 gap-3 sm:gap-4 px-2 sm:px-4">
        <h3 className="text-xl sm:text-3xl font-extrabold text-secondary flex items-center gap-2 sm:gap-3">
          <Loader2 className="w-5 h-5 sm:w-8 sm:h-8 text-amber-600 animate-spin" />
          Analyse en cours
        </h3>
        <p className="text-secondary-light text-xs sm:text-base font-medium truncate max-w-[150px] sm:max-w-sm bg-white/60 px-3 sm:px-4 py-1 sm:py-1.5 rounded-full border border-amber-200/50 shadow-sm">
          {nomFichier}
        </p>
      </div>

      <div className="w-full flex-1 min-h-[200px] sm:min-h-[300px] bg-slate-50/50 rounded-2xl sm:rounded-3xl p-4 sm:p-6 border border-slate-200/50 mb-4 sm:mb-8 overflow-hidden relative shadow-inner flex flex-col items-center justify-center">
        {!preview ? (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex flex-col items-center">
            <div className="relative w-16 h-16 sm:w-24 sm:h-24 bg-amber-100 rounded-[1.5rem] sm:rounded-[2rem] flex items-center justify-center shadow-[inset_0_2px_4px_rgba(255,255,255,0.8)] mb-4 sm:mb-6">
              <Loader2 className="w-8 h-8 sm:w-12 sm:h-12 text-amber-600 animate-spin" />
              <div className="absolute -inset-2 bg-amber-600/20 blur-xl rounded-full -z-10 animate-glow-pulse" />
            </div>
            <p className="text-slate-400 font-bold uppercase tracking-widest text-[10px] sm:text-sm">Traitement en cours...</p>
          </motion.div>
        ) : (
          <>
            <p className="absolute top-2 sm:top-4 text-[10px] sm:text-sm font-bold text-slate-400 tracking-widest uppercase z-10">
              Comparaison en direct • Page {preview.page}
            </p>
            
            <div className="flex items-center justify-center gap-2 sm:gap-12 mt-6 sm:mt-8 w-full">
              {/* Flipbook AVANT */}
              <div className="relative perspective-[1500px]">
                <div className="absolute inset-0 bg-red-500/20 rounded-xl blur-[20px] sm:blur-[30px] -z-10" />
                <AnimatePresence mode="wait">
                  <motion.div
                    key={`avant-${preview.page}`}
                    initial={{ rotateY: 90, opacity: 0, scale: 0.95, x: 20 }}
                    animate={{ rotateY: 0, opacity: 1, scale: 1, x: 0 }}
                    exit={{ rotateY: -90, opacity: 0, scale: 0.95, x: -20 }}
                    transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
                    style={{ transformOrigin: "left", transformStyle: "preserve-3d" }}
                    className="relative rounded-xl sm:rounded-2xl overflow-hidden shadow-[10px_0_30px_rgba(0,0,0,0.15)] border border-red-100 bg-white p-1 sm:p-2"
                  >
                    <div className="absolute top-2 sm:top-4 left-2 sm:left-4 bg-red-500 text-white text-[8px] sm:text-[10px] font-black uppercase px-1.5 sm:px-2 py-0.5 sm:py-1 rounded sm:rounded-md shadow-sm z-10">Avant</div>
                    <div className="absolute top-0 bottom-0 left-0 w-2 sm:w-4 bg-gradient-to-r from-slate-300 to-transparent opacity-40 z-10 mix-blend-multiply" />
                    <img src={`data:image/jpeg;base64,${preview.orig}`} className="w-[100px] sm:w-[280px] h-[140px] sm:h-[400px] object-contain opacity-90" alt="Avant" />
                  </motion.div>
                </AnimatePresence>
              </div>

              <div className="w-8 h-8 sm:w-14 sm:h-14 bg-white/80 backdrop-blur-md rounded-full flex items-center justify-center shadow-lg z-20 shrink-0 border border-slate-100">
                <ArrowRight className="w-4 h-4 sm:w-7 sm:h-7 text-amber-500" />
              </div>

              {/* Flipbook APRES */}
              <div className="relative perspective-[1500px]">
                <div className="absolute inset-0 bg-emerald-500/30 rounded-xl blur-[20px] sm:blur-[30px] -z-10" />
                <AnimatePresence mode="wait">
                  <motion.div
                    key={`apres-${preview.page}`}
                    initial={{ rotateY: 90, opacity: 0, scale: 0.95, x: 20 }}
                    animate={{ rotateY: 0, opacity: 1, scale: 1, x: 0 }}
                    exit={{ rotateY: -90, opacity: 0, scale: 0.95, x: -20 }}
                    transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1], delay: 0.1 }}
                    style={{ transformOrigin: "left", transformStyle: "preserve-3d" }}
                    className="relative rounded-xl sm:rounded-2xl overflow-hidden shadow-[10px_0_30px_rgba(0,0,0,0.2)] border border-emerald-100 bg-white p-1 sm:p-2"
                  >
                    <div className="absolute top-2 sm:top-4 left-2 sm:left-4 bg-emerald-500 text-white text-[8px] sm:text-[10px] font-black uppercase px-1.5 sm:px-2 py-0.5 sm:py-1 rounded sm:rounded-md shadow-sm z-10">Aprés</div>
                    <div className="absolute top-0 bottom-0 left-0 w-2 sm:w-4 bg-gradient-to-r from-slate-300 to-transparent opacity-40 z-10 mix-blend-multiply" />
                    <img src={`data:image/jpeg;base64,${preview.nette}`} className="w-[100px] sm:w-[280px] h-[140px] sm:h-[400px] object-contain" alt="Apres" />
                  </motion.div>
                </AnimatePresence>
              </div>
            </div>
          </>
        )}
      </div>

      <div className="relative w-full h-2.5 sm:h-4 rounded-full bg-amber-100 overflow-hidden mb-3 sm:mb-4 shadow-inner">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${progression}%` }}
          transition={{ duration: 0.3, ease: "linear" }}
          className="absolute inset-y-0 left-0 rounded-full bg-gradient-to-r from-amber-400 to-amber-600"
        />
        <div className="absolute inset-0 rounded-full bg-[linear-gradient(90deg,transparent,rgba(255,255,255,0.4),transparent)] bg-[length:200%_100%] animate-mesh" />
      </div>

      <div className="flex items-center justify-between px-1 sm:px-2">
        <p className="text-secondary font-semibold text-xs sm:text-base">{message || "Traitement en cours..."}</p>
        <span className="text-amber-600 font-bold text-sm sm:text-lg">{progression}%</span>
      </div>
    </motion.div>
  );
}
 