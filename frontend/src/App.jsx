import { useState, useCallback } from "react";
import { Toaster, toast } from "react-hot-toast";
import { motion, AnimatePresence } from "framer-motion";
import { ShieldCheck, Zap, Layers } from "lucide-react";

import Navbar from "./components/Navbar";
import Dropzone from "./components/Dropzone";
import ProgressPanel from "./components/ProgressPanel";
import ResultPanel from "./components/ResultPanel";
import { supprimerWatermark, traitementBatch, obtenirStatut } from "./utils/api";

const ETAPES = { UPLOAD: "upload", TRAITEMENT: "traitement", RESULTAT: "resultat" };

export default function App() {
  const [etape, setEtape] = useState(ETAPES.UPLOAD);
  const [tache, setTache] = useState(null);
  const [progression, setProgression] = useState(0);
  const [message, setMessage] = useState("");
  const [nomFichier, setNomFichier] = useState("");
  const [preview, setPreview] = useState(null);

  const pollStatut = useCallback((idTache) => {
    let actif = true;

    const verifier = async () => {
      if (!actif) return;
      try {
        const statut = await obtenirStatut(idTache);
        if (!actif) return;

        setProgression(statut.progression || 0);
        setMessage(statut.message || "");

        if (statut.preview_orig && statut.preview_nette) {
          setPreview({
            orig: statut.preview_orig,
            nette: statut.preview_nette,
            page: statut.page_courante
          });
        }

        if (statut.status === "termine") {
          actif = false;
          setTache(statut);
          setEtape(ETAPES.RESULTAT);
          toast.success("Watermark supprime !");
        } else if (statut.status === "erreur") {
          actif = false;
          toast.error(statut.message || "Erreur de traitement");
          setEtape(ETAPES.UPLOAD);
        } else {
          setTimeout(verifier, 1000);
        }
      } catch {
        if (!actif) return;
        actif = false;
        toast.error("Impossible de contacter le serveur");
        setEtape(ETAPES.UPLOAD);
      }
    };

    verifier();
  }, []);

  const pollStatutsBatch = useCallback((idsTaches) => {
    let actif = true;

    const verifier = async () => {
      if (!actif) return;

      try {
        const statuts = await Promise.all(idsTaches.map((id) => obtenirStatut(id)));
        if (!actif) return;

        const progressionMoyenne = Math.round(
          statuts.reduce((acc, statut) => acc + (statut.progression || 0), 0) / statuts.length
        );
        const terminees = statuts.filter((s) => s.status === "termine").length;
        const enErreur = statuts.filter((s) => s.status === "erreur").length;

        setProgression(progressionMoyenne);
        setMessage(`Traitement batch: ${terminees}/${statuts.length} terminé(s)`);

        const previewSource = statuts.find((s) => s.preview_orig && s.preview_nette);
        if (previewSource) {
          setPreview({
            orig: previewSource.preview_orig,
            nette: previewSource.preview_nette,
            page: previewSource.page_courante,
          });
        }

        if (enErreur > 0) {
          actif = false;
          toast.error("Une ou plusieurs tâches du batch ont échoué");
          setEtape(ETAPES.UPLOAD);
          return;
        }

        if (terminees === statuts.length) {
          actif = false;
          setTache({
            batch: true,
            items: statuts,
            nom_fichier: `${statuts.length} fichiers`,
          });
          setEtape(ETAPES.RESULTAT);
          toast.success(`Batch terminé (${statuts.length} fichiers)`);
          return;
        }

        setTimeout(verifier, 1000);
      } catch {
        if (!actif) return;
        actif = false;
        toast.error("Impossible de suivre le statut du batch");
        setEtape(ETAPES.UPLOAD);
      }
    };

    verifier();
  }, []);

  const lancerTraitement = useCallback(async (fichiers, modeWatermark = "auto") => {
    const fichiersBatch = fichiers || [];
    if (fichiersBatch.length === 0) return;

    const estBatch = fichiersBatch.length > 1;
    const fichier = fichiersBatch[0];

    setNomFichier(estBatch ? `${fichiersBatch.length} fichiers` : fichier.name);
    setProgression(0);
    setMessage("Initialisation...");
    setPreview(null);
    setEtape(ETAPES.TRAITEMENT);

    try {
      if (estBatch) {
        const reponse = await traitementBatch(fichiersBatch, false, false, modeWatermark);

        if (reponse.fichiers_rejetes?.length) {
          toast((t) => (
            <span>
              {reponse.fichiers_rejetes.length} fichier(s) rejeté(s) dans le batch
              <button onClick={() => toast.dismiss(t.id)} className="ml-3 underline">OK</button>
            </span>
          ));
        }

        pollStatutsBatch(reponse.ids_taches || []);
      } else {
        const reponse = await supprimerWatermark(fichier, false, modeWatermark);
        pollStatut(reponse.id_tache);
      }
    } catch (err) {
      const detail = err.response?.data?.detail;
      const msg = typeof detail === "string"
        ? detail
        : detail?.message || "Erreur lors de l'upload";
      toast.error(msg);
      setEtape(ETAPES.UPLOAD);
    }
  }, [pollStatut, pollStatutsBatch]);

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
                  className="text-5xl md:text-7xl font-black text-secondary leading-[1.1] tracking-tight mb-6"
                >
                  Effacez le filigrane. <br />
                  <span className="text-gradient-primary">Sublimez tous vos documents.</span>
                </motion.h1>

                <motion.p
                  initial={{ y: 20, opacity: 0 }}
                  animate={{ y: 0, opacity: 1 }}
                  transition={{ delay: 0.3, duration: 0.7 }}
                  className="text-lg text-secondary-light font-medium"
                >
                  Glissez vos PDF, PPTX ou images PNG/JPG. Le moteur detecte et supprime les filigranes NotebookLM et Gemini en preservant la qualite.
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
                className="mt-16 grid grid-cols-1 md:grid-cols-3 gap-6 w-full max-w-4xl"
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
  