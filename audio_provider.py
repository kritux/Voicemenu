import os

class FileAudioProvider:
    def get_audio_bytes(self, path: str) -> bytes:
        if not os.path.exists(path):
            raise FileNotFoundError(f"Audio file not found: {path}")
        with open(path, 'rb') as f:
            return f.read() 