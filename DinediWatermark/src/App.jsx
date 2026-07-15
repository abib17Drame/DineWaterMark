import { useState, useCallback } from "react";
import { Toaster, toast } from "react-hot-toast";
import { motion, AnimatePresence } from "framer-motion";
import { ShieldCheck, Zap, Layers } from "lucide-react";

import Navbar from "./components/Navbar";
import Dropzone from "./components/Dropzone";
import ProgressPanel from "./components/ProgressPanel";
import ResultPanel from "./components/ResultPanel";
import { processImageLocal } from "./utils/api";

const ETAPES = { UPLOAD: "upload", TRAITEMENT: "traitement", RESULTAT: "resultat" };

export default function App() {
  const [etape, setEtape] = useState(ETAPES.UPLOAD);
  const [tache, setTache] = useState(null);
  const [progression, setProgression] = useState(0);
  const [message, setMessage] = useState("");
  const [nomFichier, setNomFichier] = useState("");
  const [preview, setPreview] = useState(null);

  // Pas de polling backend nécessaire puisque tout se passe dans le navigateur

  const lancerTraitement = useCallback(async (fichiers) => {
    const fichiersBatch = fichiers || [];
    if (fichiersBatch.length === 0) return;

    const estBatch = fichiersBatch.length > 1;
    const fichier = fichiersBatch[0];

    setNomFichier(estBatch ? `${fichiersBatch.length} fichiers` : fichier.name);
    setProgression(10);
    setMessage("Analyse en cours...");
    setPreview(null);
    setEtape(ETAPES.TRAITEMENT);

    try {
      if (estBatch) {
        toast.error("Le traitement par lot arrive bientôt !");
        setEtape(ETAPES.UPLOAD);
      } else {
        const result = await processImageLocal(fichier);
        if (result) {
          setProgression(100);
          setTache(result);
          setEtape(ETAPES.RESULTAT);
          toast.success("Watermark Gemini supprimé !");
        } else {
          toast.error("Aucun watermark Gemini détecté ou supporté.");
          setEtape(ETAPES.UPLOAD);
        }
      }
    } catch (err) {
      toast.error(err.message || "Erreur lors du traitement");
      setEtape(ETAPES.UPLOAD);
    }
  }, []);

  const reset = () => {
    setEtape(ETAPES.UPLOAD);
    setTache(null);
    setProgression(0);
  };

  const avantages = [
    { ic: Zap, titre: "Fulgurant", desc: "< 5s pour 20 pages" },
    { ic: Layers, titre: "Pixels intacts", desc: "Mise en page preservee a 100%" },
    { ic: ShieldCheck, titre: "Securise", desc: "Purge auto de la RAM" },
  ];

  return (
    <div className="min-h-screen relative overflow-hidden">
      <Navbar />

      <Toaster
        position="bottom-center"
        toastOptions={{
          style: {
            background: "#1C1917",
            color: "#fff",
            borderRadius: "100px",
            boxShadow: "0 10px 20px rgba(0,0,0,0.1)",
            padding: "16px 24px",
          },
        }}
      />

      <main className="relative z-10 flex flex-col items-center justify-center min-h-[100dvh] px-4 pt-24 pb-12 w-full max-w-7xl mx-auto">
        <AnimatePresence mode="wait">
          {etape === ETAPES.UPLOAD && (
            <motion.div
              key="upload"
              initial={{ opacity: 0, scale: 0.95, filter: "blur(10px)" }}
              animate={{ opacity: 1, scale: 1, filter: "blur(0px)" }}
              exit={{ opacity: 0, scale: 1.05, filter: "blur(10px)" }}
              transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
              className="w-full flex flex-col items-center"
            >
              <div className="text-center mb-10 md:mb-14 max-w-2xl px-4">
                <motion.h1
                  initial={{ y: 20, opacity: 0 }}
                  animate={{ y: 0, opacity: 1 }}
                  transition={{ delay: 0.2, duration: 0.7 }}
                  className="text-4xl md:text-5xl font-black text-secondary leading-[1.1] tracking-tight mb-4"
                >
                  Effacez le filigrane. <br />
                  <span className="text-gradient-primary">Sublimez vos documents.</span>
                </motion.h1>

                <motion.p
                  initial={{ y: 20, opacity: 0 }}
                  animate={{ y: 0, opacity: 1 }}
                  transition={{ delay: 0.3, duration: 0.7 }}
                  className="text-base text-secondary-light font-medium"
                >
                  Glissez vos fichiers. Le moteur supprime les filigranes Gemini avec une precision mathematique.
                </motion.p>
              </div>

              <motion.div
                initial={{ y: 30, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ delay: 0.4, duration: 0.7 }}
                className="w-full max-w-3xl tilt-card"
              >
                <Dropzone onFichiersAcceptes={lancerTraitement} />
              </motion.div>

              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.6, duration: 0.8 }}
                className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-6 w-full max-w-4xl"
              >
                {avantages.map(({ ic: Ic, titre, desc }, i) => (
                  <motion.div
                    key={titre}
                    whileHover={{ y: -5 }}
                    className="bg-white/40 backdrop-blur-xl border border-white p-6 rounded-3xl shadow-sm flex flex-col items-center text-center"
                  >
                    <div className="w-12 h-12 bg-amber-100 rounded-2xl flex items-center justify-center mb-4 text-primary">
                      <Ic className="w-6 h-6" />
                    </div>
                    <h4 className="text-secondary font-bold text-lg mb-1">{titre}</h4>
                    <p className="text-secondary-light text-sm font-medium">{desc}</p>
                  </motion.div>
                ))}
              </motion.div>
            </motion.div>
          )}

          {etape === ETAPES.TRAITEMENT && (
            <motion.div
              key="processing"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 1.1 }}
              transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
              className="w-full h-full flex items-center justify-center"
            >
              <ProgressPanel progression={progression} message={message} nomFichier={nomFichier} preview={preview} />
            </motion.div>
          )}

          {etape === ETAPES.RESULTAT && tache && (
            <motion.div
              key="result"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, y: 50 }}
              transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
              className="w-full h-full flex items-center justify-center"
            >
              <ResultPanel tache={tache} onNouveau={reset} />
            </motion.div>
          )}
        </AnimatePresence>
      </main>
    </div>
  );
}
  