"""Error types for shotxray."""


class ShotXrayError(Exception):
    """Base error for anything shotxray cannot do honestly."""


class FFmpegMissingError(ShotXrayError):
    """ffmpeg/ffprobe are not on PATH."""


class ProbeError(ShotXrayError):
    """ffprobe could not read the file (not a video, corrupt, unsupported)."""


class AnalysisError(ShotXrayError):
    """A step of the analysis failed (scene detection, frame grab, audio)."""
