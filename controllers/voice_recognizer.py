import json
import uuid
import numpy as np
import librosa
from pathlib import Path
from typing import Dict, List, Optional, Union, Tuple

from controllers.base import BaseController
from resemblyzer import VoiceEncoder, preprocess_wav

ArrayLikeAudio = Union[str, np.ndarray, Tuple[np.ndarray, int]]

def _l2_normalize(v: np.ndarray, eps: float = 1e-9) -> np.ndarray:
    n = np.linalg.norm(v) + eps
    return v / n

def _load_wav(
    wav_or_path: ArrayLikeAudio,
    target_sr: int = 16000,
    mono: bool = True
) -> Tuple[np.ndarray, int]:
    if isinstance(wav_or_path, str):
        wav, sr = librosa.load(wav_or_path, sr=target_sr, mono=mono)
        return wav.astype(np.float32), sr
    elif isinstance(wav_or_path, tuple) and len(wav_or_path) == 2:
        wav, sr = wav_or_path
        if mono and wav.ndim > 1:
            wav = librosa.to_mono(wav)
        if sr != target_sr:
            wav = librosa.resample(wav, orig_sr=sr, target_sr=target_sr)
            sr = target_sr
        return wav.astype(np.float32), sr
    else:
        wav = np.asarray(wav_or_path, dtype=np.float32)
        if mono and wav.ndim > 1:
            wav = librosa.to_mono(wav)
        return wav, target_sr

def _extract_voiced_chunks(
    wav: np.ndarray,
    sr: int,
    max_seconds: float,
    top_db: float = 25.0
) -> np.ndarray:
    """
    Extrae regiones con voz (no silencio) y concatena hasta max_seconds.
    Usa energy-based split (rápido).
    """
    if wav.size == 0:
        return wav
    intervals = librosa.effects.split(wav, top_db=top_db)  # [[start, end], ...]
    pieces = []
    acc = 0.0
    limit = int(max_seconds * sr)
    for s, e in intervals:
        seg = wav[s:e]
        if acc + len(seg) > limit:
            seg = seg[: max(0, limit - int(acc))]
        if seg.size > 0:
            pieces.append(seg)
            acc += len(seg)
        if acc >= limit:
            break
    if not pieces:
        # si no detectó voz, limita a max_seconds del centro
        center = len(wav) // 2
        half = int((max_seconds * sr) / 2)
        return wav[max(0, center - half): center + half]
    return np.concatenate(pieces)

class VoiceRecognizerController(BaseController):
    """
    Reconocimiento de locutor con énfasis en:
    - Reconocer: máxima velocidad (embedding rápido sobre ~4 s de voz).
    - Asignar/Enroll: máxima precisión (agregación de múltiples micro-segmentos).
    Backend único: Resemblyzer (sin fallback).
    """

    def __init__(
        self,
        storage_path: Optional[str] = None,
        threshold: float = 0.72,
        target_sr: int = 16000,
        recognize_seconds: float = 4.0,
        enroll_window_sec: float = 2.4,
        enroll_window_hop: float = 0.6,
        enroll_voice_cap_sec: float = 18.0,
    ):
        """
        threshold: umbral por defecto para decidir 'desconocido'.
        recognize_seconds: segundos de voz útil para embedding rápido.
        enroll_window_sec/hop: micro-ventanas para promediar (precisión).
        enroll_voice_cap_sec: máximo de voz útil a usar por muestra en enroll.
        """
        self.encoder = VoiceEncoder()  # Resemblyzer
        self.threshold = float(threshold)
        self.target_sr = int(target_sr)
        self.recognize_seconds = float(recognize_seconds)
        self.enroll_window_sec = float(enroll_window_sec)
        self.enroll_window_hop = float(enroll_window_hop)
        self.enroll_voice_cap_sec = float(enroll_voice_cap_sec)

        # Galería en memoria
        # person_id -> {"proto": np.ndarray(shape [D], L2), "count": int}
        self.gallery: Dict[str, Dict[str, Union[np.ndarray, int]]] = {}

        # Índice denso (matriz) para búsquedas ultrarrápidas
        self._names: List[str] = []
        self._protos: Optional[np.ndarray] = None  # shape [N, D]
        self._dirty_index = True

        # Persistencia
        self.storage_path = Path(storage_path) if storage_path else None
        if self.storage_path:
            meta = self.storage_path.with_suffix(".json")
            npz = self.storage_path.with_suffix(".npz")
            if meta.exists() and npz.exists():
                self.load_gallery(str(self.storage_path))

    # ========= Embeddings =========
    def _embed_fast(self, wav_or_path: ArrayLikeAudio) -> np.ndarray:
        """
        Embedding para reconocimiento: rápido, usa ~recognize_seconds de voz útil.
        """
        wav, sr = _load_wav(wav_or_path, self.target_sr)
        wav_v = _extract_voiced_chunks(wav, sr, self.recognize_seconds)
        # Preprocess_wav maneja normalizado y asegura 16 kHz si indicas source_sr
        wav_p = preprocess_wav(wav_v, source_sr=sr)
        emb = self.encoder.embed_utterance(wav_p)
        return _l2_normalize(emb)

    def _embed_precise(self, wav_or_path: ArrayLikeAudio) -> np.ndarray:
        """
        Embedding para enroll: muy preciso.
        - Extrae hasta enroll_voice_cap_sec de voz útil.
        - Genera múltiples micro-ventanas (deslizantes) y promedia.
        """
        wav, sr = _load_wav(wav_or_path, self.target_sr)
        voiced = _extract_voiced_chunks(wav, sr, max_seconds=self.enroll_voice_cap_sec)
        if voiced.size < int(1.0 * sr):
            # si casi no hay voz, cae al embedding estándar
            wav_p = preprocess_wav(voiced, source_sr=sr)
            emb = self.encoder.embed_utterance(wav_p)
            return _l2_normalize(emb)

        win = int(self.enroll_window_sec * sr)
        hop = int(self.enroll_window_hop * sr)
        embs = []
        for start in range(0, max(1, len(voiced) - win + 1), hop):
            seg = voiced[start:start + win]
            if len(seg) < win:
                break
            seg_p = preprocess_wav(seg, source_sr=sr)
            e = self.encoder.embed_utterance(seg_p)
            embs.append(e)
        if not embs:
            seg_p = preprocess_wav(voiced, source_sr=sr)
            embs = [self.encoder.embed_utterance(seg_p)]
        proto = _l2_normalize(np.mean(np.stack(embs, axis=0), axis=0))
        return proto

    # ========= Galería / Índice =========
    def _rebuild_index(self):
        self._names = sorted(self.gallery.keys())
        if not self._names:
            self._protos = None
        else:
            self._protos = np.stack([self.gallery[n]["proto"] for n in self._names], axis=0)
        self._dirty_index = False

    def list_persons(self) -> List[str]:
        return sorted(self.gallery.keys())

    def remove_person(self, person_id: str):
        if person_id in self.gallery:
            del self.gallery[person_id]
            self._dirty_index = True

    def clear(self):
        self.gallery.clear()
        self._dirty_index = True

    # ========= API principal =========
    def enroll(self, person_id: str, samples: List[ArrayLikeAudio]):
        """
        Inscribe/actualiza una persona con máxima precisión.
        Recomendado: ≥2–3 muestras variadas.
        """
        if not samples:
            raise ValueError("Debes proporcionar al menos una muestra para el enrollment.")
        embs = [self._embed_precise(s) for s in samples]
        proto = _l2_normalize(np.mean(np.stack(embs, axis=0), axis=0))
        self.gallery[person_id] = {"proto": proto.astype(np.float32), "count": len(samples)}
        self._dirty_index = True

    def add_sample(self, person_id: str, sample: ArrayLikeAudio):
        """
        Añade una muestra y recalcula el prototipo (preciso).
        """
        if person_id not in self.gallery:
            # si no existe, comportarse como enroll
            return self.enroll(person_id, [sample])

        # fusiona cuidadosamente con el prototipo existente
        new_emb = self._embed_precise(sample)
        old_proto = self.gallery[person_id]["proto"]
        old_count = int(self.gallery[person_id]["count"])
        # media incremental (mantiene estabilidad numérica y rapidez)
        new_count = old_count + 1
        fused = _l2_normalize((old_proto * old_count + new_emb) / new_count)
        self.gallery[person_id] = {"proto": fused.astype(np.float32), "count": new_count}
        self._dirty_index = True

    def recognize(
        self,
        sample: ArrayLikeAudio,
        threshold: Optional[float] = None,
        top_k: int = 1
    ) -> Dict:
        """
        Identificación 1:N ultrarrápida (matmul con índice denso).
        Devuelve:
        {
          "label": "<person_id>" | "desconocido",
          "score": <mejor_similitud>,
          "ranking": [("person_id", score), ...]  # hasta top_k
        }
        """
        if not self.gallery:
            raise RuntimeError("Galería vacía. Inscribe personas primero.")
        if self._dirty_index:
            self._rebuild_index()

        q = self._embed_fast(sample)  # rápido
        thr = float(self.threshold if threshold is None else threshold)

        # matmul denso: [N, D] @ [D] -> [N]
        sims = (self._protos @ q)  # ya L2-normalizados => coseno
        idx_sorted = np.argsort(-sims)  # descendente
        best_idx = int(idx_sorted[0])
        best_score = float(sims[best_idx])
        best_name = self._names[best_idx]
        label = best_name if best_score >= thr else "desconocido"

        k = max(1, int(top_k))
        ranking = [(self._names[int(i)], float(sims[int(i)])) for i in idx_sorted[:k]]

        return {"label": label, "score": best_score, "ranking": ranking}

    def verify(
        self,
        person_id: str,
        sample: ArrayLikeAudio,
        threshold: Optional[float] = None
    ) -> Dict:
        """
        Verificación 1:1 rápida (usa embedding rápido por coherencia de latencia).
        Si prefieres máxima precisión, llama _embed_precise en tu flujo antes de verificar.
        """
        if person_id not in self.gallery:
            raise KeyError(f"Persona '{person_id}' no encontrada.")
        thr = float(self.threshold if threshold is None else threshold)
        q = self._embed_fast(sample)
        score = float(np.dot(q, self.gallery[person_id]["proto"]))
        return {"is_match": score >= thr, "score": score, "threshold": thr}

    # ========= Persistencia =========
    def save_gallery(self, path: Optional[str] = None):
        """
        Guarda:
        - <path>.npz: matriz protos (N,D)
        - <path>.json: metadatos y nombres
        """
        base = Path(path) if path else (self.storage_path or Path(f"voice_gallery_{uuid.uuid4().hex}"))
        base = base.with_suffix("")

        names = sorted(self.gallery.keys())
        if names:
            protos = np.stack([self.gallery[n]["proto"] for n in names], axis=0).astype(np.float32)
            counts = [int(self.gallery[n]["count"]) for n in names]
        else:
            protos = np.zeros((0, 256), dtype=np.float32)  # tamaño típico resemblyzer
            counts = []

        np.savez_compressed(base.with_suffix(".npz"), protos=protos)
        meta = {"names": names, "counts": counts}
        with open(base.with_suffix(".json"), "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)

        self.storage_path = base
        self._dirty_index = True

    def load_gallery(self, path: str):
        base = Path(path).with_suffix("")
        npz_path = base.with_suffix(".npz")
        json_path = base.with_suffix(".json")
        if not (npz_path.exists() and json_path.exists()):
            raise FileNotFoundError(f"No se encontraron {npz_path} y {json_path}.")

        with open(json_path, "r", encoding="utf-8") as f:
            meta = json.load(f)
        data = np.load(npz_path)

        names = meta.get("names", [])
        counts = meta.get("counts", [1] * len(names))
        protos = data["protos"]

        self.gallery.clear()
        for i, n in enumerate(names):
            self.gallery[n] = {"proto": protos[i], "count": int(counts[i])}

        self.storage_path = base
        self._dirty_index = True

    # ========= Config =========
    def set_threshold(self, value: float):
        self.threshold = float(value)

    # ========= BaseController =========
    def run(self, command: str, **kwargs):
        cmd = command.lower()
        if cmd == "enroll":
            return self.enroll(kwargs["person_id"], kwargs["samples"])
        if cmd == "add_sample":
            return self.add_sample(kwargs["person_id"], kwargs["sample"])
        if cmd == "recognize":
            return self.recognize(kwargs["sample"], kwargs.get("threshold"), kwargs.get("top_k", 1))
        if cmd == "verify":
            return self.verify(kwargs["person_id"], kwargs["sample"], kwargs.get("threshold"))
        if cmd == "save":
            return self.save_gallery(kwargs.get("path"))
        if cmd == "load":
            return self.load_gallery(kwargs["path"])
        if cmd == "list":
            return self.list_persons()
        if cmd == "remove":
            return self.remove_person(kwargs["person_id"])
        if cmd == "clear":
            return self.clear()
        if cmd == "set_threshold":
            return self.set_threshold(kwargs["value"])
        raise ValueError(f"Comando no reconocido: {command}")
