# ⚔️ MOTUS-VIGILUS

> "Le Mouvement Veille" — Extracteur Cinétique Universel pour Avatars Roblox R15

## Vision

MOTUS-VIGILUS extrait l'animation d'une vidéo `.mp4` et la convertit en fichier `.fbx` compatible avec les avatars Roblox R15. Pipeline 100% gratuit, exécuté sur Google Colab.

## Architecture

| Frégate | Script | Rôle | Input | Output |
|---------|--------|------|-------|--------|
| **U-ALPHA** (L'Auspex) | `core/motus_extract.py` | Extraction + Transmutation | `.mp4` | `.npz` |
| **U-GAMMA** (La Forge) | `core/motus_forge.py` | Manifestation FBX | `.npz` + `.blend` | `.fbx` |

## Pipeline

```
📹 .mp4 → [Frégate U-ALPHA] → 📦 .npz → [Frégate U-GAMMA] → 🎮 .fbx
```

## Quick Start (Google Colab)

1. Ouvrir `notebooks/MOTUS_VIGILUS_Colab.ipynb` dans Google Colab
2. Uploader une vidéo `.mp4`
3. Sélectionner FPS cible (30/60/120), Lissage, Root Motion
4. Lancer → Télécharger `MOTUS_VIGILUS.fbx`

## Spécifications

- **Extraction** : MediaPipe Pose Landmarker (33 landmarks 3D)
- **Multi-personnage** : Jusqu'à 4 sujets (1 fichier `.npz` par personne)
- **Détection de scènes** : PySceneDetect (découpe automatique aux cuts)
- **Lissage** : Savitzky-Golay (scipy)
- **Upscaling temporel** : Interpolation Bézier (30/60/120 FPS)
- **Export** : Blender 4.x headless → FBX avec bake animation
- **Coût** : 0€ (Colab gratuit + open-source)

## Structure

```
MOTUS-VIGILUS/
├── core/              # Scripts Python (Frégates)
├── templates/         # Template Blender R15
├── notebooks/         # Notebook Colab
├── docs/              # Documentation technique
├── inputs/            # Vidéos sources
└── outputs/           # Fichiers .npz et .fbx
```

## Doctrine

Construit selon le framework **ATOM-IC** (Analyse, Transmutation, Optimisation, Manifestation) et les **10 Lois de la Voie Royale**.

## Licence

Usage interne — EXODUS V2 Pipeline.
