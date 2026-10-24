import sys
import unittest
from datetime import date
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "academic_search"))
from search import load_profile, score_job, rank_jobs, markdown_report, valid_url

PROFILE = load_profile()

def job(**extra):
    data = {
        "title": "Assistant Professor, Machine Learning and Healthcare Analytics",
        "institution": "Example Institute",
        "location": "Lucknow, India",
        "url": "https://example.edu/faculty/100",
        "description": "Teaching and research in machine learning, medical imaging and business analytics",
        "deadline": "2026-12-10",
    }
    data.update(extra)
    return data

class AcademicSearchTests(unittest.TestCase):
    def setUp(self):
        self.today = date(2026, 10, 24)

    def test_relevant_faculty_is_high_fit(self):
        result = score_job(job(), PROFILE, self.today)
        self.assertGreaterEqual(result["score"], 80)
        self.assertEqual(result["status"], "review")

    def test_expired_deadline_does_not_surface_as_live(self):
        result = score_job(job(deadline="2026-01-15"), PROFILE, self.today)
        self.assertEqual(result["status"], "expired")
        self.assertEqual(result["score"], 0)

    def test_missing_deadline_is_not_invented(self):
        result = score_job(job(deadline=""), PROFILE, self.today)
        self.assertEqual(result["deadline"], "")
        self.assertTrue(any("unknown" in f for f in result["flags"]))

    def test_associate_requires_manual_eligibility_review(self):
        result = score_job(job(title="Associate Professor, Information Systems"), PROFILE, self.today)
        self.assertEqual(result["status"], "eligibility_review")

    def test_phd_student_not_a_target(self):
        result = score_job(job(title="PhD Student Machine Learning"), PROFILE, self.today)
        self.assertEqual(result["status"], "not_target")

    def test_international_requires_work_rights_check(self):
        result = score_job(job(location="London, UK"), PROFILE, self.today)
        self.assertTrue(any("work authorization" in f for f in result["flags"]))

    def test_duplicate_url_deduplicated(self):
        items = rank_jobs([job(), job(title="Machine Learning Faculty")], PROFILE, self.today)
        self.assertEqual(len(items), 1)

    def test_non_https_url_is_not_linked(self):
        self.assertFalse(valid_url("javascript:alert(1)"))
        report = markdown_report([score_job(job(url="javascript:alert(1)"), PROFILE, self.today)], self.today)
        self.assertNotIn("](javascript:", report)

if __name__ == "__main__":
    unittest.main()
