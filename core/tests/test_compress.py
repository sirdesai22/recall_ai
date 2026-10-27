import os
import tempfile
import unittest
from compress import group_into_sessions, heuristic_summary, delete_frame_files


def row(ts, app="Chrome", title="", id_=0):
    return {"id": id_, "timestamp": ts, "app_name": app, "window_title": title, "raw_text": "", "frame_path": ""}


class TestGroupIntoSessions(unittest.TestCase):
    def test_empty_rows(self):
        assert group_into_sessions([]) == []

    def test_single_row(self):
        sessions = group_into_sessions([row(100)])
        assert len(sessions) == 1

    def test_small_gap_same_session(self):
        sessions = group_into_sessions([row(100), row(200), row(299)])
        assert len(sessions) == 1

    def test_gap_over_five_minutes_splits(self):
        sessions = group_into_sessions([row(100), row(200), row(200 + 301)])
        assert len(sessions) == 2

    def test_gap_of_exactly_limit_stays(self):
        # gap > SESSION_GAP splits; gap == SESSION_GAP does not
        sessions = group_into_sessions([row(100), row(100 + 300)])
        assert len(sessions) == 1

    def test_app_change_splits_even_without_gap(self):
        sessions = group_into_sessions([row(100, "Chrome"), row(101, "Slack")])
        assert len(sessions) == 2

    def test_small_sessions_are_returned_not_dropped(self):
        # regression: sub-MIN_FRAMES sessions used to be silently dropped forever
        sessions = group_into_sessions([row(100), row(101)])
        assert len(sessions) == 1
        assert len(sessions[0]) == 2


class TestHeuristicSummary(unittest.TestCase):
    def test_includes_app_and_count(self):
        s = heuristic_summary([row(100, "Chrome", "GitHub PR")])
        assert "Chrome" in s and "1 frames" in s

    def test_includes_first_unique_title(self):
        session = [row(100, "Chrome", "GitHub PR"), row(101, "Chrome", "GitHub PR")]
        assert "GitHub PR" in heuristic_summary(session)

    def test_handles_missing_titles(self):
        s = heuristic_summary([row(100, "Finder")])
        assert "Finder" in s
        assert ":" not in s.split("(")[1]


class TestDeleteFrameFiles(unittest.TestCase):
    def test_deletes_existing_file(self):
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            path = f.name
        delete_frame_files([path])
        assert not os.path.exists(path)

    def test_silently_skips_missing_files(self):
        delete_frame_files(["/nonexistent/path/frame.png"])  # must not raise


if __name__ == "__main__":
    unittest.main()
