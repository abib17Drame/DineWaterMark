import { processWatermarkImageData } from "../gemini-core/watermarkProcessor.js";
import { getEmbeddedAlphaMap } from "../gemini-core/embeddedAlphaMaps.js";
import { removeGeminiVideoWatermark } from "../gemini-core/video/videoExport.js";

function getFileImageData(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      const img = new Image();
      img.onload = () => {
        const canvas = document.createElement("canvas");
        canvas.width = img.width;
        canvas.height = img.height;
        const ctx = canvas.getContext("2d");
        ctx.drawImage(img, 0, 0);
        resolve({
          imageData: ctx.getImageData(0, 0, img.width, img.height),
          canvas
        });
      };
      img.onerror = reject;
      img.src = e.target.result;
    };
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

export async function processImageLocal(fichier) {
  try {
    const startMs = Date.now();
    
    // -- VIDEO PROCESSING --
    if (fichier.type.startsWith("video/")) {
      console.log("Démarrage du traitement vidéo local...");
      const result = await removeGeminiVideoWatermark(fichier, {
        alphaGain: 1,
        adaptiveAlpha: true,
        highQualityCleanup: true,
        sampleCount: 12,
        preserveAudio: true,
        allowLowConfidence: true
      });
      
      const finalUrl = URL.createObjectURL(result.blob);
      
      return {
        status: "termine",
        preview_orig: URL.createObjectURL(fichier),
        preview_nette: finalUrl,
        blob: result.blob,
        nom_fichier: fichier.name,
        temps_traitement_ms: Date.now() - startMs
      };
    }
    
    // -- IMAGE PROCESSING --
    // 1. Convert File to ImageData
    const { imageData, canvas } = await getFileImageData(fichier);
    
    // 2. Fetch required alpha maps
    const alpha48 = getEmbeddedAlphaMap(48);
    const alpha96 = getEmbeddedAlphaMap(96);
    
    // 3. Process Watermark
    const result = processWatermarkImageData(imageData, { 
        fast: false,
        alpha48,
        alpha96
    });
    
    // Determine the result image data
    const finalImageData = result?.imageData || result;
    
    if (!finalImageData || !finalImageData.data) {
        console.warn("No image data returned from processor, fallback to original");
        return null;
    }

    // 4. Convert back to Blob
    const ctx = canvas.getContext("2d");
    ctx.putImageData(finalImageData, 0, 0);
    
    const blob = await new Promise(r => canvas.toBlob(r, fichier.type || "image/png"));
    const finalUrl = URL.createObjectURL(blob);
    
    return {
      status: "termine",
      preview_orig: URL.createObjectURL(fichier),
      preview_nette: finalUrl,
      blob: blob,
      nom_fichier: fichier.name,
      temps_traitement_ms: Date.now() - startMs
    };
  } catch (error) {
    console.error("Erreur processImageLocal:", error);
    throw error;
  }
}