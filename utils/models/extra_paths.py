"""
Extra Model Paths Support for TTS Audio Suite
Implements support for ComfyUI's extra_model_paths.yaml configuration file
"""

import os
import yaml
import folder_paths
from typing import List, Dict, Any, Optional
import logging

class TtsExtraPathsManager:
    """
    Manager for TTS model paths that respects ComfyUI's extra_model_paths.yaml configuration.
    
    This ensures TTS Audio Suite uses the same shared model directories as other ComfyUI nodes,
    preventing model duplication and enabling shared storage configurations.
    """
    
    def __init__(self):
        self.tts_folders = {}
        self._load_tts_paths()
    
    def _load_tts_paths(self):
        """Load TTS-specific paths from ComfyUI's folder_paths system"""
        # First, check if TTS folders are already registered with ComfyUI
        if hasattr(folder_paths, 'folder_names_and_paths'):
            global_folders = folder_paths.folder_names_and_paths
            
            # Look for existing TTS-related folders
            for folder_type in ['TTS', 'tts', 'text_to_speech', 'voice_models', 'voices']:
                if folder_type in global_folders:
                    self.tts_folders[folder_type] = global_folders[folder_type][0]  # Get paths list
        
        # configure default TTS structure (if not already configured)
        self._setup_default_tts_paths()
    
    def _setup_default_tts_paths(self):
        """Set up default TTS paths using ComfyUI's models directory structure"""
        models_dir = folder_paths.models_dir
        
        # Register TTS folder types with ComfyUI's folder_paths system
        tts_model_types = {
            'TTS': {
                'paths': [os.path.join(models_dir, 'TTS')],
                'extensions': {'.safetensors', '.bin', '.pt', '.pth', '.ckpt', 'folder'}
            },
            'voices': {
                'paths': [
                    os.path.join(models_dir, 'voices'),           # Primary: standard ComfyUI location
                    os.path.join(models_dir, 'TTS', 'voices')     # Fallback: logical TTS organization
                ],
                'extensions': {'.wav', '.mp3', '.flac', '.ogg', 'folder'}
            }
        }
        
        # Register with ComfyUI's system so other nodes can also use these paths
        for folder_type, config in tts_model_types.items():
            if folder_type not in self.tts_folders:
                folder_paths.add_model_folder_path(folder_type, config['paths'][0])
                self.tts_folders[folder_type] = config['paths']
    
    def get_tts_model_directory(self, model_type: str = 'TTS') -> str:
        """
        Get the primary TTS model directory for a given type.
        
        Args:
            model_type: Type of TTS model ('TTS', 'TTS_voices', etc.)
            
        Returns:
            Primary directory path for this model type
        """
        if model_type in self.tts_folders and self.tts_folders[model_type]:
            return self.tts_folders[model_type][0]  # Return first (primary) path
        
        # Fallback to default if not configured
        models_dir = folder_paths.models_dir
        return os.path.join(models_dir, 'TTS')
    
    def get_all_tts_model_paths(self, model_type: str = 'TTS') -> List[str]:
        """
        Get all configured TTS model directories for a given type.
        
        This includes both the default ComfyUI models folder and any extra_model_paths
        configured directories.
        
        Args:
            model_type: Type of TTS model ('TTS', 'TTS_voices', etc.)
            
        Returns:
            List of all directory paths for this model type
        """
        if model_type in self.tts_folders:
            return self.tts_folders[model_type].copy()
        
        # Fallback to default
        models_dir = folder_paths.models_dir
        return [os.path.join(models_dir, 'TTS')]
    
    def find_model_in_paths(self, model_name: str, model_type: str = 'TTS', 
                           subdirs: Optional[List[str]] = None) -> Optional[str]:
        """
        Find a model file or directory in any of the configured TTS paths.
        
        Args:
            model_name: Name of the model to find
            model_type: Type of TTS model ('TTS', 'TTS_voices', etc.)
            subdirs: Optional list of subdirectories to check (e.g., ['chatterbox', 'f5tts'])
            
        Returns:
            Full path to the model if found, None otherwise
        """
        search_paths = self.get_all_tts_model_paths(model_type)
        
        # Search in all configured paths
        for base_path in search_paths:
            # Search directly in base path
            if self._check_model_at_path(base_path, model_name):
                return os.path.join(base_path, model_name)
            
            # Search in subdirectories if specified
            if subdirs:
                for subdir in subdirs:
                    subpath = os.path.join(base_path, subdir)
                    if self._check_model_at_path(subpath, model_name):
                        return os.path.join(subpath, model_name)
        
        return None
    
    def _check_model_at_path(self, base_path: str, model_name: str) -> bool:
        """Check if a model exists at the given path"""
        if not os.path.exists(base_path):
            return False
        
        full_path = os.path.join(base_path, model_name)
        
        # Check if it's a file
        if os.path.isfile(full_path):
            return True
        
        # Check if it's a directory (for model folders)
        if os.path.isdir(full_path):
            return True
        
        return False
    
    def get_preferred_download_path(self, model_type: str = 'TTS', 
                                  engine_name: Optional[str] = None) -> str:
        """
        Get the preferred path for downloading new models.
        
        This respects extra_model_paths.yaml configuration - if a user has configured
        a shared models directory, new downloads will go there instead of the default.
        
        Args:
            model_type: Type of TTS model ('TTS', 'TTS_voices', etc.)
            engine_name: Optional engine name for organization (e.g., 'chatterbox', 'f5tts')
            
        Returns:
            Full path where new models should be downloaded
        """
        # Get the primary (first) configured path
        base_path = self.get_tts_model_directory(model_type)
        
        # Add engine subdirectory if specified
        if engine_name:
            base_path = os.path.join(base_path, engine_name)
        
        # Ensure directory exists
        os.makedirs(base_path, exist_ok=True)
        
        return base_path
    
    def register_tts_engine_paths(self, engine_name: str, custom_paths: Dict[str, str]):
        """
        Register custom paths for a specific TTS engine.
        
        Args:
            engine_name: Name of the engine (e.g., 'chatterbox', 'f5tts')
            custom_paths: Dictionary of path types to paths
        """
        for path_type, path in custom_paths.items():
            folder_type = f"TTS_{engine_name}_{path_type}"
            folder_paths.add_model_folder_path(folder_type, path)
            self.tts_folders[folder_type] = [path]
    
    def get_voices_directory(self) -> str:
        """Get the primary directory for voice files, respecting extra_model_paths.yaml"""
        # Check for configured voices paths first
        if 'voices' in self.tts_folders and self.tts_folders['voices']:
            primary_path = self.tts_folders['voices'][0]
            os.makedirs(primary_path, exist_ok=True)
            return primary_path
        
        # Fallback to default models/voices
        models_dir = folder_paths.models_dir
        voices_dir = os.path.join(models_dir, 'voices')
        os.makedirs(voices_dir, exist_ok=True)
        return voices_dir
    
    def get_all_voices_paths(self) -> List[str]:
        """Get all configured voice directories including fallbacks"""
        paths = []
        
        # Add configured voices paths (includes both models/voices and models/TTS/voices)
        if 'voices' in self.tts_folders:
            paths.extend(self.tts_folders['voices'])
        else:
            # Fallback to default structure if not configured
            models_dir = folder_paths.models_dir
            paths.extend([
                os.path.join(models_dir, 'voices'),           # Primary
                os.path.join(models_dir, 'TTS', 'voices')     # Fallback
            ])
        
        # Note: voices_examples/ is handled by the existing VoiceDiscovery class
        # We don't include it here to avoid duplicating that functionality
        
        return paths


# Global instance
_tts_paths_manager = TtsExtraPathsManager()

def get_tts_model_directory(model_type: str = 'TTS') -> str:
    """Get the primary TTS model directory for downloads"""
    return _tts_paths_manager.get_tts_model_directory(model_type)

def get_all_tts_model_paths(model_type: str = 'TTS') -> List[str]:
    """Get all TTS model search paths"""
    return _tts_paths_manager.get_all_tts_model_paths(model_type)

def find_model_in_paths(model_name: str, model_type: str = 'TTS', 
                       subdirs: Optional[List[str]] = None) -> Optional[str]:
    """Find a model in any configured TTS path"""
    return _tts_paths_manager.find_model_in_paths(model_name, model_type, subdirs)

def get_preferred_download_path(model_type: str = 'TTS', 
                               engine_name: Optional[str] = None) -> str:
    """Get preferred path for new model downloads"""
    return _tts_paths_manager.get_preferred_download_path(model_type, engine_name)

def get_voices_directory() -> str:
    """Get the voices directory respecting extra_model_paths.yaml"""
    return _tts_paths_manager.get_voices_directory()

def get_all_voices_paths() -> List[str]:
    """Get all configured voice search paths"""
    return _tts_paths_manager.get_all_voices_paths()


def _comfy_base_path() -> Optional[str]:
    return getattr(folder_paths, "base_path", None) or None


def get_floyo_loras_path() -> Optional[str]:
    """Absolute ComfyUI/#models/loras path Floyo materializes user LoRAs into."""
    base_path = _comfy_base_path()
    if not base_path:
        return None
    return os.path.join(base_path, "#models", "loras")


def _absolute_under_comfy(path: str) -> str:
    if os.path.isabs(path):
        return os.path.normpath(path)
    base_path = _comfy_base_path()
    if base_path:
        return os.path.normpath(os.path.join(base_path, path))
    return os.path.normpath(os.path.abspath(path))


def _is_peft_adapter_dir(path: str) -> bool:
    return os.path.isdir(path) and os.path.isfile(os.path.join(path, "adapter_config.json"))


def get_all_loras_paths() -> List[str]:
    """Return ComfyUI's registered models/loras directories."""
    loras_dirs: List[str] = []
    try:
        loras_dirs = list(folder_paths.get_folder_paths("loras"))
    except Exception:
        pass
    if not loras_dirs:
        models_dir = getattr(folder_paths, "models_dir", None)
        if models_dir:
            loras_dirs = [os.path.join(models_dir, "loras")]
    floyo_loras = get_floyo_loras_path()
    normalized = {_absolute_under_comfy(path) for path in loras_dirs if path}
    if floyo_loras and os.path.normpath(floyo_loras) not in normalized:
        loras_dirs.append(floyo_loras)
    return [_absolute_under_comfy(path) for path in loras_dirs if path]


def get_preferred_loras_path() -> str:
    """Primary loras directory for new LoRA/adapter/training output.

    Prefer Floyo's watched ``#models/loras`` folder when present so uploaded
    and trained adapters persist. The first registered loras path is often the
    shared SSD cache, which Floyo does not sync back to the user.
    """
    paths = get_all_loras_paths()
    for path in paths:
        normalized = path.replace("\\", "/")
        if normalized.rstrip("/").endswith("#models/loras"):
            os.makedirs(path, exist_ok=True)
            return path
    if paths:
        os.makedirs(paths[0], exist_ok=True)
        return paths[0]
    fallback = os.path.join(folder_paths.models_dir, "loras")
    os.makedirs(fallback, exist_ok=True)
    return fallback


def get_legacy_moss_lora_paths() -> List[str]:
    """Previous MOSS adapter location, kept as a discovery fallback."""
    paths: List[str] = []
    seen = set()
    for base_path in get_all_tts_model_paths("TTS"):
        candidate = os.path.join(base_path, "moss_tts", "loras")
        normalized = os.path.normpath(candidate)
        if normalized not in seen:
            seen.add(normalized)
            paths.append(candidate)
    return paths


def is_floyo_loras_dir(path: str) -> bool:
    return str(path or "").replace("\\", "/").rstrip("/").endswith("#models/loras")


def normalize_lora_ref(value: str) -> str:
    """Strip Floyo / local: prefixes down to a path relative to models/loras."""
    text = str(value or "").strip().replace("\\", "/")
    if text.startswith("local:"):
        text = text[6:]
    lowered = text.lower()
    prefixes = (
        "(as-input)#models/loras/",
        "(as-output)#models/loras/",
        "#models/loras/",
        "models/loras/",
    )
    for prefix in prefixes:
        if lowered.startswith(prefix):
            text = text[len(prefix):]
            break
    return text.lstrip("/")


def to_as_input_loras_path(value: str) -> Optional[str]:
    """Rewrite ``#models/loras/X`` to ``(as-input)#models/loras/X``.

    Floyo only downloads LoRA *folders* when the prompt uses the as-input prefix.
    Bare ``#models/loras/<folder>`` is treated as an output directory.
    """
    text = str(value or "").strip()
    if not text or text.lower() == "none":
        return None
    if text.startswith("local:"):
        text = text[6:]
    if (
        "/" in text
        and not text.startswith("#")
        and not text.startswith("(")
        and not text.startswith("models/")
        and "://" not in text
    ):
        parts = text.split("/")
        if len(parts) == 2 and all(parts):
            return None
    relative = normalize_lora_ref(text)
    if not relative:
        return None
    return f"(as-input)#models/loras/{relative}"


def resolve_loras_adapter_dir(name: str) -> Optional[str]:
    """Resolve a PEFT adapter folder, preferring Floyo ``#models/loras``."""
    raw = str(name or "").strip()
    if not raw:
        return None

    for candidate in (raw, _absolute_under_comfy(raw)):
        if _is_peft_adapter_dir(candidate):
            return candidate

    relative = normalize_lora_ref(raw)
    if not relative:
        return None
    if _is_peft_adapter_dir(relative):
        return relative
    absolute_relative = _absolute_under_comfy(relative)
    if _is_peft_adapter_dir(absolute_relative):
        return absolute_relative

    floyo_root = get_floyo_loras_path()
    if floyo_root:
        floyo_candidate = os.path.join(floyo_root, relative)
        if _is_peft_adapter_dir(floyo_candidate):
            return floyo_candidate

    search_roots = list(get_all_loras_paths()) + get_legacy_moss_lora_paths()
    try:
        input_dir = folder_paths.get_input_directory()
    except Exception:
        input_dir = None
    if input_dir:
        search_roots.extend(
            [
                os.path.join(input_dir, "models", "loras"),
                os.path.join(input_dir, "#models", "loras"),
            ]
        )

    seen = set()
    for root in search_roots:
        if not root:
            continue
        normalized = _absolute_under_comfy(root)
        if normalized in seen:
            continue
        seen.add(normalized)
        candidate = os.path.join(normalized, relative)
        if _is_peft_adapter_dir(candidate):
            return candidate
    return None


def register_tts_engine_paths(engine_name: str, custom_paths: Dict[str, str]):
    """Register custom paths for a specific TTS engine"""
    return _tts_paths_manager.register_tts_engine_paths(engine_name, custom_paths)

# Initialize TTS paths with ComfyUI integration
def initialize_tts_paths():
    """Initialize TTS paths integration with ComfyUI's folder_paths system"""
    global _tts_paths_manager
    _tts_paths_manager._load_tts_paths()

# Auto-initialize on import
initialize_tts_paths()