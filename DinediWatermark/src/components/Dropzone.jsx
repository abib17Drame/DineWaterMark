import { useCallback, useEffect, useRef, useState } from "react";
import { useDropzone } from "react-dropzone";
import { motion, AnimatePresence } from "framer-motion";
import { UploadCloud, FileText, Image, Presentation, X, Eraser } from "lucide-react";

const ICONES = { pdf: FileText, pptx: Presentation, image: Image };

const FORMATS = {
  "image/png": [".png"],
  "image/jpeg": [".jpg", ".jpeg"],
  "image/webp": [".webp"],
  "video/mp4": [".mp4"],
  "video/webm": [".webm"],
};

function getType(f) {
  if (f.type.startsWith("video/")) return "video";
  return "image";
}

function taille(o) {
  if (o < 1024) return `${o} o`;
  if (o < 1048576) return `${(o / 1024).toFixed(1)} Ko`;
  return `${(o / 1048576).toFixed(1)} Mo`;
}

export default function Dropzone({ onFichiersAcceptes, desactive }) {
  const [fichiers, setFichiers] = useState([]);
  const actionsRef = useRef(null);

  const onDrop = useCallback((acceptes) => {
    setFichiers(acceptes);
  }, []);

  useEffect(() => {
    if (fichiers.length > 0) {
      actionsRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }
  }, [fichiers.length]);

  const retirer = (i) => setFichiers((prev) => prev.filter((_, idx) => idx !== i));
  const lancer = () => {
    if (fichiers.length > 0) {
      onFichiersAcceptes(fichiers);
    }
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop, accept: FORMATS, maxSize: 50 * 1024 * 1024, disabled: desactive, multiple: true,
  });

  return (
    <div className="w-full">

      <motion.div
        {...getRootProps()}
        whileHover={!desactive ? { scale: 1.01 } : {}}
        whileTap={!desactive ? { scale: 0.99 } : {}}
        className={`dropzone-base ${isDragActive ? "dropzone-active" : "dropzone-idle"} ${desactive ? "opacity-50 pointer-events-none" : "cursor-pointer"} p-4 sm:p-8 flex flex-col items-center justify-center min-h-[160px] md:min-h-[220px]`}
      >
        <input {...getInputProps()} />
        
        <motion.div
          animate={isDragActive ? { y: -5, scale: 1.05 } : { y: 0, scale: 1 }}
          className="w-12 h-12 sm:w-16 sm:h-16 mb-3 sm:mb-4 rounded-[1rem] sm:rounded-[1.5rem] bg-amber-100 flex items-center justify-center shadow-inner-light"
        >
          <UploadCloud className={`w-6 h-6 sm:w-8 sm:h-8 ${isDragActive ? "text-primary-dark" : "text-primary"}`} />
        </motion.div>

        <h3 className="text-lg sm:text-xl font-bold text-secondary mb-1 text-center">
          {isDragActive ? "Relachez pour analyser" : "Deposez vos documents"}
        </h3>
        <p className="text-secondary-light text-xs sm:text-sm font-medium mb-3 sm:mb-4 text-center">
          ou <span className="text-primary hover:text-primary-dark underline decoration-2 underline-offset-4 cursor-pointer">parcourez vos fichiers</span>
        </p>

        <div className="flex gap-2 justify-center flex-wrap">
          <span className="px-2 sm:px-3 py-1 bg-white text-emerald-700 border border-emerald-200 rounded-lg text-[10px] sm:text-sm font-semibold shadow-sm">Images (PNG/JPG/WEBP)</span>
          <span className="px-2 sm:px-3 py-1 bg-white text-blue-700 border border-blue-200 rounded-lg text-[10px] sm:text-sm font-semibold shadow-sm">Vidéos (MP4/WEBM)</span>
        </div>
      </motion.div>

      <AnimatePresence>
        {fichiers.length > 0 && (
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, scale: 0.95 }} className="mt-4 md:mt-8 flex flex-col items-center gap-4 md:gap-6">
            
            <div className="w-full max-h-[320px] overflow-y-auto pr-2 space-y-3" ref={actionsRef}>
              {fichiers.map((f, i) => {
              const Ic = ICONES[getType(f)] || FileText;
              return (
                <motion.div 
                  initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.05 }}
                  key={i} 
                  className="flex items-center gap-3 md:gap-4 bg-white/60 backdrop-blur-md p-3 md:p-4 rounded-[1rem] md:rounded-[1.2rem] shadow-sm border border-amber-100 hover:bg-white/80 transition-colors group"
                >
                  <div className="w-10 h-10 md:w-12 md:h-12 bg-amber-100/50 rounded-xl flex items-center justify-center shrink-0">
                    <Ic className="w-5 h-5 md:w-6 md:h-6 text-amber-600" />
                  </div>
                  <div className="flex-1 min-w-0 text-left">
                    <p className="font-bold text-sm md:text-base text-slate-800 truncate">{f.name}</p>
                    <p className="text-[10px] md:text-xs text-slate-500 font-medium uppercase tracking-wider">{getType(f)} • {taille(f.size)}</p>
                  </div>
                  <button onClick={(e) => { e.stopPropagation(); retirer(i); }} className="w-8 h-8 md:w-10 md:h-10 rounded-full bg-slate-100/50 text-slate-400 hover:bg-red-50 hover:text-red-500 flex items-center justify-center transition-all group-hover:shadow-sm shrink-0">
                    <X className="w-4 h-4 md:w-5 md:h-5" />
                  </button>
                </motion.div>
              );
              })}
            </div>

            <div className="w-full pt-2 border-t border-amber-200/50 flex justify-center">
              <button onClick={lancer} className="btn-m3-primary w-full sm:w-auto min-w-0 md:min-w-[280px] h-12 md:h-14 rounded-xl md:rounded-2xl text-base md:text-lg shadow-lg shadow-amber-600/20 hover:shadow-amber-600/40">
                <Eraser className="w-5 h-5 mr-1" />
                Nettoyer {fichiers.length > 1 ? `les ${fichiers.length} fichiers` : "ce fichier"}
              </button>
            </div>

          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
 