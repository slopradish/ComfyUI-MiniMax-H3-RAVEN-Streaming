"""
MiniMax H3 RAVEN Scene & Character Memory Vault
-----------------------------------------------
Persistent two-tier memory bank for infinite streaming and multi-scene continuity.
Captures keyframe latent plates and character facial embeddings in system RAM,
allowing seamless return to previous rooms, characters, and settings.
"""

from typing import Dict, Any, Optional, List
import torch


class SceneMemoryVault:
    """Singleton memory vault for long-term scene and character latent recall."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SceneMemoryVault, cls).__new__(cls)
            cls._instance._scenes = {}
            cls._instance._characters = {}
            cls._instance._soundscapes = {}
        return cls._instance

    def clear(self):
        """Reset all cached scenes and characters."""
        self._scenes.clear()
        self._characters.clear()
        self._soundscapes.clear()

    def store_scene(self, scene_id: str, latent_plate: torch.Tensor, metadata: Optional[Dict[str, Any]] = None):
        """Store a latent snapshot of a scene environment on the host."""
        if latent_plate is not None:
            # Clone and move to CPU pinned/host to conserve GPU VRAM
            self._scenes[scene_id] = {
                "latent": latent_plate.detach().cpu().clone(),
                "metadata": metadata or {},
            }
            print(f"[SceneVault] Stored scene plate for '{scene_id}' in memory vault.")

    def get_scene(self, scene_id: str) -> Optional[torch.Tensor]:
        """Retrieve the cached latent plate for a scene."""
        entry = self._scenes.get(scene_id)
        if entry:
            return entry["latent"]
        return None

    def store_character(self, char_id: str, embedding_tokens: torch.Tensor, metadata: Optional[Dict[str, Any]] = None):
        """Store multimodal visual embedding tokens for a character."""
        if embedding_tokens is not None:
            self._characters[char_id] = {
                "embedding": embedding_tokens.detach().cpu().clone(),
                "metadata": metadata or {},
            }
            print(f"[SceneVault] Stored character embedding for '{char_id}' in memory vault.")

    def get_character(self, char_id: str) -> Optional[torch.Tensor]:
        """Retrieve visual embedding tokens for a character."""
        entry = self._characters.get(char_id)
        if entry:
            return entry["embedding"]
        return None

    def list_scenes(self) -> List[str]:
        return list(self._scenes.keys())

    def list_characters(self) -> List[str]:
        return list(self._characters.keys())


# Global singleton instance
SCENE_VAULT = SceneMemoryVault()
