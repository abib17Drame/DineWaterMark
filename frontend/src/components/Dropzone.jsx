import { useCallback, useEffect, useRef, useState } from "react";
import { useDropzone } from "react-dropzone";
import { motion, AnimatePresence } from "framer-motion";
import { UploadCloud, FileText, Image, Presentation, X, Eraser } from "lucide-react";

const ICONES = { pdf: FileText, pptx: Presentation, image: Image };

const FORMATS = {
  "application/pdf": [".pdf"],
  "application/vnd.openxmlformats-officedocument.presentationml.presentation": [".pptx"],
  "image/png": [".png"],
  "image/jpeg": [".jpg", ".jpeg"],
};

function getType(f) {
  const ext = f.name.split(".").pop().toLowerCase();
  if (ext === "pdf") return "pdf";
  if (ext === "pptx") return "pptx";
  return "image";
}

function taille(o) {
  if (o < 1024) return `${o} o`;
  if (o < 1048576) return `${(o / 1024).toFixed(1)} Ko`;
  return `${(o / 1048576).toFixed(1)} Mo`;
}

export default function Dropzone({ onFichiersAcceptes, desactive }) {
  const [fichiers, setFichiers] = useState([]);
  const [modeWatermark, setModeWatermark] = useState("auto");
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
      onFichiersAcceptes(fichiers, modeWatermark);
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
        className={`dropzone-base ${fichiers.length > 0 ? "p-7 md:p-9" : "p-12"} ${isDragActive ? "dropzone-active" : "dropzone-idle"} ${desactive ? "opacity-50 pointer-events-none" : "cursor-pointer"}`}
      >
        <input {...getInputProps()} />

        <motion.div
          animate={isDragActive ? { y: -10, scale: 1.1 } : { y: 0, scale: 1 }}
          className="w-24 h-24 mb-6 rounded-[2rem] bg-amber-100 flex items-center justify-center shadow-inner-light"
        >
          <UploadCloud className={`w-10 h-10 ${isDragActive ? "text-primary-dark" : "text-primary"}`} />
        </motion.div>

        <h3 className="text-2xl font-bold text-secondary mb-2">
          {isDragActive ? "Relachez pour analyser" : (fichiers.length > 0 ? "Documents prets" : "Deposez vos documents")}
        </h3>
        <p className="text-secondary-light font-medium mb-6">
          {fichiers.length > 0
            ? "Ajoutez-en d'autres ou lancez le nettoyage ci-dessous"
            : <>ou <span className="text-primary hover:text-primary-dark underline decoration-2 underline-offset-4 cursor-pointer">parcourez vos fichiers</span></>}
        </p>

        <div className="flex gap-2 justify-center">
          {["PDF", "PPTX", "PNG", "JPG"].map(fmt => (
            <span key={fmt} className="px-3 py-1 bg-white text-secondary-light border border-amber-200 rounded-lg text-sm font-semibold shadow-sm">{fmt}</span>
          ))}
        </div>
      </motion.div>

      <AnimatePresence>
        {fichiers.length > 0 && (
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, scale: 0.95 }} className="mt-6 flex flex-col gap-4">
            <div ref={actionsRef} className="sticky bottom-3 z-20 m3-glass-heavy rounded-[1.5rem] p-4 border border-amber-100 shadow-lg">
              <div className="flex flex-col lg:flex-row gap-4 items-stretch lg:items-end">
                <div className="flex-1">
                  <p className="text-sm font-bold text-secondary mb-2">Mode de detection watermark</p>
                  <div className="grid grid-cols-3 gap-1 p-1 rounded-xl bg-amber-50 border border-amber-200">
                    {[
                      { value: "auto", label: "Auto" },
                      { value: "notebook", label: "Notebook" },
                      { value: "gemini", label: "Gemini" },
                    ].map((mode) => (
                      <button
                        key={mode.value}
                        type="button"
                        onClick={() => setModeWatermark(mode.value)}
                        className={`h-10 rounded-lg text-sm font-bold transition-all ${modeWatermark === mode.value ? "bg-primary text-white shadow-sm" : "text-secondary-light hover:bg-white"}`}
                      >
                        {mode.label}
                      </button>
                    ))}
                  </div>
                  <p className="text-xs text-secondary-light font-medium mt-2">
                    Astuce: choisissez Gemini pour eviter le flou sur des images Gemini.
                  </p>
                </div>

                <button onClick={lancer} className="btn-m3-primary w-full lg:w-auto lg:min-w-[260px] h-14 rounded-[1.1rem]">
                  <Eraser className="w-5 h-5" />
                  Nettoyer {fichiers.length > 1 ? `${fichiers.length} fichiers` : "le document"}
                </button>
              </div>
            </div>

            <div className="max-h-[280px] overflow-y-auto pr-1 space-y-3">
              {fichiers.map((f, i) => {
              const Ic = ICONES[getType(f)] || FileText;
              return (
                <div key={i} className="flex flex-col sm:flex-row items-center gap-4 bg-white p-4 rounded-[1.5rem] shadow-sm border border-amber-100 relative overflow-hidden group">
                  <div className="w-12 h-12 bg-amber-50 rounded-xl flex items-center justify-center shrink-0">
                    <Ic className="w-6 h-6 text-primary" />
                  </div>
                  <div className="flex-1 min-w-0 text-center sm:text-left">
                    <p className="font-bold text-secondary truncate">{f.name}</p>
                    <p className="text-sm text-secondary-light font-medium">{taille(f.size)}</p>
                  </div>
                  <button onClick={(e) => { e.stopPropagation(); retirer(i); }} className="w-10 h-10 rounded-full bg-red-50 text-red-500 hover:bg-red-500 hover:text-white flex items-center justify-center transition-colors">
                    <X className="w-5 h-5" />
                  </button>
                </div>
              );
              })}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
 