import logging
from faster_whisper import WhisperModel
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TranscriptionService:
    def __init__(self, model_size="small", device="cpu", compute_type="int8"):
        """
        Initialize the TranscriptionService.
        
        Args:
            model_size (str): Size of the Whisper model (tiny, base, small, medium, large).
            device (str): Device to run on ("cpu" or "cuda").
            compute_type (str): Quantization type ("int8", "float16", "float32").
        """
        logger.info(f"Initializing TranscriptionService with model={model_size}, device={device}, compute_type={compute_type}")
        try:
            self.model = WhisperModel(model_size, device=device, compute_type=compute_type)
            logger.info("TranscriptionService initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize TranscriptionService: {e}")
            raise

    def transcribe(self, audio_path: str):
        """
        Transcribe an audio file.
        
        Args:
            audio_path (str): Path to the audio file.
            
        Returns:
            str: The transcribed text.
        """
        if not os.path.exists(audio_path):
            logger.error(f"Audio file not found: {audio_path}")
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        logger.info(f"Starting transcription for: {audio_path}")
        try:
            segments, info = self.model.transcribe(audio_path, beam_size=5)
            
            full_text = ""
            for segment in segments:
                full_text += segment.text + " "
            
            result = full_text.strip()
            logger.info(f"Transcription completed. Length: {len(result)} chars")
            return result
        except Exception as e:
            logger.error(f"Error during transcription: {e}")
            raise

# Singleton instance or factory can be used
# transcription_service = TranscriptionService()
