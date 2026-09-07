# Schemify
Built a video summarization and clipping tool that processes long videos by transcribing audio, sending text to a locally hosted Ollama LLM via its REST API, and extracting key segments into short clips.

## Outputs

`output/final.mp4` remains the original continuous condensed lecture: all selected
segments are clipped and stitched in timeline order.

When the model supplies topic metadata, Schemify also writes independent videos
to `output/topics/<safe_topic_name>/<safe_topic_name>.mp4`. A topic video joins
all of that topic's selected segments in chronological order, even when they are
separated in the original lecture. Overlapping selections for the same topic and
source chunk are merged before clips are created.

## Selection schema

The existing fields are unchanged. Topic fields are optional for backward
compatibility:

```json
{
  "start": 320.5,
  "end": 410.2,
  "text": "...",
  "topic_id": "cpu_registers",
  "topic_name": "CPU Registers"
}
```

Older Ollama responses or saved selections without `topic_id` still create the
normal condensed video; they simply do not generate topic videos.
