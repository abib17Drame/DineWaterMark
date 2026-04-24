import axios from "axios";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";

const api = axios.create({ baseURL: API_BASE });

export async function supprimerWatermark(fichier, debug = false, watermarkMode = "auto") {
  const formData = new FormData();
  formData.append("file", fichier);
  formData.append("debug", debug);
  formData.append("watermark_mode", watermarkMode);
  const { data } = await api.post("/remove", formData);
  return data;
}

export async function traitementBatch(
  fichiers,
  mergePptx = false,
  debug = false,
  watermarkMode = "auto"
) {
  const formData = new FormData();
  fichiers.forEach((f) => formData.append("files", f));
  formData.append("merge_pptx", mergePptx);
  formData.append("debug", debug);
  formData.append("watermark_mode", watermarkMode);
  const { data } = await api.post("/batch", formData);
  return data;
}

export async function obtenirStatut(idTache) {
  const { data } = await api.get(`/status/${idTache}`);
  return data;
}

export function obtenirUrlTelechargement(idTache) {
  return `${API_BASE}/download/${idTache}`;
}

export async function obtenirStats() {
  const { data } = await api.get("/stats");
  return data;
}

export default api;
 