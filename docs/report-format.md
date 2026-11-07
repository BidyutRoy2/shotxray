# Report format (`report.json`)

`shotxray analyze` writes `report.json` — the machine-readable contract.
The Markdown and HTML reports render this same data, so the formats never
disagree.

```jsonc
{
  "tool": "shotxray",
  "version": "0.1.0",
  "info": {
    "path": "trailer.mp4",
    "duration": 6.0,            // seconds (float)
    "width": 1280, "height": 720,
    "fps": 30.0,
    "video_codec": "h264",
    "audio_codec": "aac",
    "subtitle_codec": null,
    "bitrate": 123456,          // bits/second, null when unknown
    "format_name": "mov,mp4,m4a,3gp,3g2,mj2",
    "has_audio": true,
    "has_subtitles": false,
    "has_video": true,
    "creation_time": null,      // from container metadata when present
    "aspect": "16:9 widescreen",
    "resolution_label": "720p",
    "chapters": []              // [{start, title}] when the file has chapters
  },
  "shots": [
    {
      "index": 1,
      "start": 0.0, "end": 2.0, "duration": 2.0,
      "dominant_color": "#ffff00",   // #rrggbb, null when unreadable
      "brightness": 226,            // 0-255 mean luma, null when unreadable
      "thumbnail": "thumbs/shot-01.png"  // relative to the report dir
    }
  ],
  "pacing": {
    "shot_count": 3,
    "avg_shot_length": 2.0,
    "cuts_per_minute": 20.0,
    "shortest_shot": 2.0,
    "longest_shot": 2.0,
    "label": "medium"           // fast-cut | medium | slow | single-shot
  },
  "audio": {
    "has_audio": true,
    "mean_volume_db": -21.3,
    "max_volume_db": -3.1,
    "silences": [{ "start": 2.0, "end": 3.0, "duration": 1.0 }],
    "segments": [{ "start": 0.0, "end": 2.0, "duration": 2.0 }],
    "silence_total": 1.0
  },
  "captions": {
    "codec": "mov_text",
    "cue_count": 2,
    "words": 5,
    "cues": [{ "start": "00:00:00.500", "end": "00:00:01.500", "text": "Hello world" }]
  },
  "score": {
    "total": 85, "grade": "B",
    "components": [
      { "name": "Metadata", "earned": 25, "possible": 25, "note": "..." }
    ]
  }
}
```

Notes for consumers:

- `report.json` **excludes** the `brief` text (it lives in `brief.md`); every
  other field is identical to the in-memory report.
- `captions` is `{"cue_count": 0, "cues": []}` when the file has no subtitle
  stream. `audio` is `{"has_audio": false}` when there is no audio stream.
- Timestamps are seconds (float) except caption cues, which keep SRT
  `HH:MM:SS.mmm` strings.
- `dominant_color` / `brightness` are `null` only when the frame could not
  be read; a shot is never dropped for a failed thumbnail.
- The schema is versioned by the top-level `version` field. v0.1.0 consumers
  should treat unknown fields as ignorable and missing optional fields as
  `null`.
