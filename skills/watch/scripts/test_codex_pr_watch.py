import contextlib
import io
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import codex_pr_watch as watch  # noqa: E402

SHA = "1234567890abcdef1234567890abcdef12345678"
OTHER = "abcdef1234567890abcdef1234567890abcdef12"
BOT = {"login": watch.BOT}
DONE = "2026-01-02T10:00:00.500000Z"


def summary(status="✅ **Completed**", commit=SHA[:7], when=DONE, user=BOT):
    row = f'| 📝 **Code Review** | {status} <relative-time datetime="{when}">x</relative-time> | `{commit}` | New commits |'
    return {"user": user, "html_url": "https://example.invalid/c1",
            "body": watch.MARKER + "\n\n| Review | Status | Commit | Review trigger |\n| --- | --- | --- | --- |\n" + row}


def review(at="2026-01-02T09:59:58Z", commit=SHA, state="COMMENTED", ident=7, user=BOT):
    return {"id": ident, "user": user, "commit_id": commit, "state": state, "submitted_at": at,
            "body": "<details>kept</details>", "html_url": "https://example.invalid/r7"}


def thumb(at="2026-01-02T10:00:03Z", user=BOT, content="+1"):
    return {"user": user, "content": content, "created_at": at}


class Board:
    """Answers for gh. A list is served one item per read and its last item stays."""

    def __init__(self, **answers):
        self.answers = {"pull": {"state": "open", "head": {"sha": SHA}}, "comments": [], "reviews": [],
                        "reactions": [], "inline": [], **answers}
        self.posts = 0
        self.now = 0.0
        self.said = []

    def take(self, key):
        value = self.answers[key]
        turns = isinstance(value, list) and (key == "pull" or value and isinstance(value[0], (list, Exception)))
        if turns:
            value = value.pop(0) if len(value) > 1 else value[0]
        if isinstance(value, Exception):
            raise value
        return value

    def api(self, path, *more):
        if more:
            self.posts += 1
            return self.take("post")
        path, _, query = path.partition("?")
        page = int(query.rsplit("=", 1)[1]) if query else 1
        key = ("comments" if path.endswith("issues/5/comments") else "inline" if path.endswith("pulls/5/comments")
               else path.rsplit("/", 1)[1] if not path.endswith("pulls/5") else "pull")
        value = self.take(key)
        return value if key == "pull" else value[(page - 1) * 100:page * 100]

    def run(self, timeout=90, trigger=False, bot=watch.BOT):
        def sleep(seconds):
            self.now += seconds
        return watch.Watch("o/r", 5, SHA, bot, trigger, self.api).run(
            timeout, 30, clock=lambda: self.now, sleep=sleep, log=self.said.append)


class Verdicts(unittest.TestCase):
    def test_completed_and_a_later_thumb_is_approved(self):
        stop = Board(comments=[summary()], reactions=[thumb()]).run()
        self.assertEqual((stop.code, stop.label), (0, "APPROVED"))

    def test_a_review_for_the_commit_is_findings_with_its_whole_body_and_inline_comments(self):
        inline = [{"pull_request_review_id": 7, "path": "a.py", "line": 3, "body": "wrong", "html_url": "u1"},
                  {"pull_request_review_id": 8, "path": "b.py", "line": 1, "body": "another round", "html_url": "u2"}]
        stop = Board(comments=[summary()], reviews=[review()], reactions=[thumb()], inline=inline).run()
        self.assertEqual(stop.code, 2)
        self.assertIn("<details>kept</details>", stop.text)
        self.assertIn("--- a.py:3 ---\nwrong", stop.text)
        self.assertNotIn("another round", stop.text)

    def test_completed_without_review_or_thumb_is_no_approval(self):
        stop = Board(comments=[summary()]).run()
        self.assertEqual(stop.code, 3)
        self.assertIn("neither a review nor a +1", stop.text)

    def test_a_thumb_from_before_the_completion_does_not_approve(self):
        self.assertEqual(Board(comments=[summary()], reactions=[thumb("2026-01-02T09:40:00Z")]).run().code, 3)

    def test_a_review_of_an_earlier_round_does_not_hide_a_later_clean_one(self):
        board = Board(comments=[summary()], reviews=[review(at="2026-01-02T09:30:00Z")], reactions=[thumb()])
        self.assertEqual(board.run().code, 0)

    def test_a_review_that_appears_late_wins_over_waiting(self):
        board = Board(comments=[summary()], reviews=[[], [review()]])
        self.assertEqual(board.run().code, 2)

    def test_a_review_that_appears_while_the_thumb_is_read_is_findings(self):
        board = Board(comments=[summary()], reviews=[[], [review()]], reactions=[thumb()])
        self.assertEqual(board.run(timeout=0).code, 2)

    def test_other_authors_and_other_commits_are_not_the_bot(self):
        human = {"login": "codex-fan"}
        board = Board(comments=[summary(user=human)], reviews=[review(user=human)], reactions=[thumb(user=human)])
        self.assertIn("no review summary", board.run().text)
        board = Board(comments=[summary()], reviews=[review(commit=OTHER)], reactions=[thumb(content="eyes")])
        self.assertEqual(board.run().code, 3)
        board = Board(comments=[summary(user=human)], reactions=[thumb(user=human)])
        self.assertEqual(board.run(bot="Codex-Fan").code, 0)

    def test_running_or_another_commit_waits(self):
        running = summary("🔄 **Running** since")
        self.assertIn("running", Board(comments=[running], reactions=[thumb()]).run().text)
        other = Board(comments=[summary(commit=OTHER[:7])], reactions=[thumb()]).run()
        self.assertEqual(other.code, 3)
        self.assertIn(OTHER[:7], other.text)
        board = Board(comments=[[running], [summary()]], reactions=[thumb()])
        self.assertEqual(board.run().code, 0)

    def test_the_summary_is_found_past_the_first_page(self):
        filler = [{"user": {"login": "someone"}, "body": "note"}] * 100
        self.assertEqual(Board(comments=filler + [summary()], reactions=[thumb()]).run().code, 0)

    def test_an_unknown_summary_form_is_an_error(self):
        for comments in ([summary("❌ **Failed**")], [summary(), summary()],
                         [{**summary(), "body": watch.MARKER + "\nnew layout"}]):
            stop = Board(comments=comments, reactions=[thumb()]).run()
            self.assertEqual((stop.code, stop.label), (1, "ERROR"))
            self.assertIn(comments[-1]["body"], stop.text)


class Heads(unittest.TestCase):
    def test_a_closed_pull_request_stops(self):
        stop = Board(pull={"state": "closed", "head": {"sha": SHA}}, comments=[summary()], reactions=[thumb()]).run()
        self.assertEqual((stop.code, stop.label), (4, "PR_NOT_OPEN"))

    def test_the_expected_head_is_awaited_and_nothing_is_asked_before_it(self):
        old = {"state": "open", "head": {"sha": OTHER}}
        new = {"state": "open", "head": {"sha": SHA}}
        board = Board(pull=[old, new], comments=[summary()], reactions=[thumb()])
        self.assertEqual(board.run().code, 0)
        board = Board(pull=[old], post={"created_at": DONE})
        self.assertEqual(board.run(trigger=True).code, 3)
        self.assertEqual(board.posts, 0)
        board = Board(pull=[old, old, old, new], post={"created_at": DONE})
        stop = board.run(trigger=True)
        self.assertEqual((stop.code, board.posts), (3, 0))
        self.assertIn("nothing was posted", stop.text)

    def test_a_head_that_moves_away_is_an_error(self):
        pulls = [{"state": "open", "head": {"sha": SHA}}, {"state": "open", "head": {"sha": OTHER}}]
        stop = Board(pull=list(pulls), comments=[summary("🔄 **Running** since")]).run()
        self.assertEqual(stop.code, 1)
        self.assertIn(OTHER, stop.text)
        stop = Board(pull=pulls, comments=[summary()], reactions=[thumb()]).run()
        self.assertEqual(stop.code, 1)


class Reads(unittest.TestCase):
    def test_a_failed_read_is_tried_again_and_never_read_as_empty(self):
        lost = watch.Unreadable("timeout")
        board = Board(comments=[summary()], reviews=[lost, [review()]], reactions=[thumb()])
        self.assertEqual(board.run().code, 2)
        board = Board(comments=[summary()], reviews=[review()], inline=[lost, []])
        self.assertEqual(board.run().code, 2)
        board = Board(comments=[summary()], reactions=[lost, [thumb()]])
        self.assertEqual(board.run().code, 0)

    def test_reads_that_keep_failing_are_an_error(self):
        board = Board(comments=[watch.Unreadable("timeout")])
        stop = board.run(timeout=3600)
        self.assertEqual(stop.code, 1)
        self.assertIn("5 reads in a row", stop.text)
        stop = Board(comments=[[{"user": None, "body": ""}]]).run(timeout=3600)
        self.assertEqual(stop.code, 1)

    def test_gh_tells_a_refusal_from_a_lost_answer(self):
        class Done:
            def __init__(self, returncode, stdout="", stderr=""):
                self.returncode, self.stdout, self.stderr = returncode, stdout, stderr
        real = watch.subprocess.run
        try:
            watch.subprocess.run = lambda *a, **k: Done(1, stderr="gh: Not Found (HTTP 404)")
            with self.assertRaises(watch.Stop):
                watch.gh("repos/o/r/pulls/5")
            watch.subprocess.run = lambda *a, **k: Done(1, stderr="dial tcp: i/o timeout")
            with self.assertRaises(watch.Unreadable):
                watch.gh("repos/o/r/pulls/5")
            watch.subprocess.run = lambda *a, **k: Done(0, stdout="")
            with self.assertRaises(watch.Unreadable):
                watch.gh("repos/o/r/pulls/5")
            watch.subprocess.run = lambda *a, **k: Done(0, stdout='{"state": "open"}')
            self.assertEqual(watch.gh("repos/o/r/pulls/5"), {"state": "open"})
        finally:
            watch.subprocess.run = real


class Requests(unittest.TestCase):
    def test_nothing_is_posted_without_the_flag(self):
        board = Board()
        self.assertEqual(board.run().code, 3)
        self.assertEqual(board.posts, 0)

    def test_a_request_is_posted_once_and_an_older_completion_is_not_its_answer(self):
        board = Board(comments=[summary()], reactions=[thumb()], post={"created_at": "2026-01-02T10:05:00Z"})
        stop = board.run(trigger=True)
        self.assertEqual((stop.code, board.posts), (3, 1))
        self.assertIn("older than the review request", stop.text)
        same_second = Board(comments=[summary()], reactions=[thumb()], post={"created_at": "2026-01-02T10:00:00Z"})
        self.assertEqual(same_second.run(trigger=True).code, 3)
        soon = Board(comments=[summary(when="2026-01-02T10:05:04Z")], reactions=[thumb("2026-01-02T10:04:58Z")],
                     post={"created_at": "2026-01-02T10:05:00Z"})
        self.assertEqual(soon.run(trigger=True).code, 3)
        later = summary(when="2026-01-02T10:09:00Z")
        board = Board(comments=[later], reactions=[thumb("2026-01-02T10:09:02Z")],
                      post={"created_at": "2026-01-02T10:05:00Z"})
        self.assertEqual((board.run(trigger=True).code, board.posts), (0, 1))

    def test_a_request_that_may_not_have_been_posted_is_not_repeated(self):
        for answer in (watch.Unreadable("timeout"), {"id": 1}):
            board = Board(post=answer)
            stop = board.run(trigger=True, timeout=3600)
            self.assertEqual((stop.code, board.posts), (1, 1))

    def test_a_review_from_before_the_request_is_not_the_requested_one(self):
        board = Board(comments=[summary(when="2026-01-02T10:06:00Z")], reactions=[thumb("2026-01-02T10:06:02Z")],
                      reviews=[review(at="2026-01-02T10:04:30Z")], post={"created_at": "2026-01-02T10:05:00Z"})
        self.assertEqual(board.run(trigger=True).code, 0)


class Arguments(unittest.TestCase):
    def test_a_usage_error_leaves_with_1_and_not_with_the_code_of_findings(self):
        for argv in ([], ["--repo", "o/r", "--pr", "5", "--sha", SHA[:7]]):
            out = io.StringIO()
            with contextlib.redirect_stdout(out), self.assertRaises(SystemExit) as left:
                watch.main(argv)
            self.assertEqual(left.exception.code, 1)
            self.assertTrue(out.getvalue().startswith("VERDICT: ERROR"))


if __name__ == "__main__":
    unittest.main()
