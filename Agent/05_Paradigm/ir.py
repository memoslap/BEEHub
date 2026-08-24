# converter/ir.py  (illustrative — adapt field names to your actual .exp constructs)
from dataclasses import dataclass, field
from enum import Enum

class StimKind(str, Enum):
    BITMAP = "bitmap"; SOUND = "sound"; VIDEO = "video"; TEXT = "text"; BLANK = "blank"

@dataclass
class Stimulus:
    id: str
    kind: StimKind
    asset: str | None = None        # filename for bitmap/sound/video
    text: str | None = None
    pos: tuple[float, float] = (0.0, 0.0)

@dataclass
class Event:
    stimulus_id: str
    duration_ms: int | None          # None = until response
    onset_ms: int | None = None      # absolute onset, if specified
    port_code: int | None = None     # EEG trigger
    collect_response: bool = False
    response_keys: list[str] = field(default_factory=list)
    response_timeout_ms: int | None = None
    # spans the parser could NOT map deterministically go here:
    raw_pcl: str | None = None       # verbatim PCL for LLM translation

@dataclass
class Paradigm:
    name: str
    background_rgb: tuple[int, int, int]     # 0–255, Presentation convention
    font_size_px: int
    refresh_hz: float | None                 # if known; needed for frame-based timing
    trials: list[list[Event]]                # trial = ordered list of events
    randomize: bool = False
    metadata: dict = field(default_factory=dict)  # provenance, source hash, etc.
