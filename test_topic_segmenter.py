import unittest

from topic_segmenter import group_topic_segments, safe_topic_name


def record(start, end, topic_id, topic_name, source="chunks/chunk_000.mp4"):
    return {"source_video": source, "chunk_start": 0, "segment": {
        "start": start, "end": end, "topic_id": topic_id, "topic_name": topic_name,
    }}


class TopicSegmenterTests(unittest.TestCase):
    def test_groups_sorts_and_merges_overlaps(self):
        records = [
            record(1100, 1155, "cpu_registers", "CPU Registers", "chunks/chunk_002.mp4"),
            record(320, 370, "cpu-registers", "CPU Registers"),
            record(360, 410, "cpu_registers", "CPU Registers"),
            record(760, 810, "interrupts", "Interrupts", "chunks/chunk_001.mp4"),
        ]
        groups = group_topic_segments(records)
        self.assertEqual(list(groups), ["cpu_registers", "interrupts"])
        cpu = groups["cpu_registers"]["segments"]
        self.assertEqual([(x["segment"]["start"], x["segment"]["end"]) for x in cpu],
                         [(320.0, 410.0), (1100.0, 1155.0)])

    def test_safe_topic_name(self):
        self.assertEqual(safe_topic_name("CPU Registers & Architecture"),
                         "CPU_Registers_Architecture")


if __name__ == "__main__":
    unittest.main()
