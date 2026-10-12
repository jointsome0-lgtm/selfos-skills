#!/usr/bin/env python3
"""Wait for the Codex review verdict on one commit of a pull request.

The bot keeps one comment on the pull request that starts with MARKER and
names the commit of its latest review and that review's status. With findings
it submits a review for the commit just before the status turns Completed.
Without findings it reacts +1 on the pull request just after. A verdict is
read only for a Completed status that names the expected commit, and only from
one of these two: no review alone never means approval.

Exit codes: 0 APPROVED, 2 FINDINGS, 3 TIMEOUT, 4 PR_NOT_OPEN, 1 ERROR.
"""
import argparse
import json
import re
import subprocess
import sys
import time
from datetime import datetime, timedelta

BOT = "chatgpt-codex-connector[bot]"
MARKER = "<!-- codex-pull-request-review-summary -->"
ROW = "📝 **Code Review**"
# A review belongs to a completion that follows it by at most this much.
REVIEW_BEFORE = timedelta(seconds=120)
# The +1 follows the completion; this covers two clocks that differ a little.
THUMB_BEFORE = timedelta(seconds=10)
FAILED_READS = 5
GIVEN_UP = re.compile(r"\(HTTP (401|404|422)\)")


class Unreadable(Exception):
    """GitHub gave no usable answer; the same read may work later."""


class Stop(Exception):
    def __init__(self, code, label, text):
        super().__init__(text)
        self.code, self.label, self.text = code, label, text


def moment(text):
    return datetime.fromisoformat(text.replace("Z", "+00:00"))


def gh(*args):
    try:
        done = subprocess.run(["gh", "api", *args], capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise Unreadable(str(exc)) from exc
    if done.returncode:
        error = done.stderr.strip() or "gh failed"
        if GIVEN_UP.search(error):
            raise Stop(1, "ERROR", error)
        raise Unreadable(error)
    try:
        return json.loads(done.stdout)
    except ValueError as exc:
        raise Unreadable("gh printed no JSON") from exc


class Watch:
    def __init__(self, repo, pr, sha, bot=BOT, trigger=False, api=gh):
        self.pull = f"repos/{repo}/pulls/{pr}"
        self.issue = f"repos/{repo}/issues/{pr}"
        self.sha, self.bot, self.trigger, self.api = sha, bot.casefold(), trigger, api
        self.seen = False
        self.after = None
        self.late = lambda: False

    def pages(self, path):
        found, page = [], 1
        while True:
            part = self.api(f"{path}?per_page=100&page={page}")
            found += part
            if len(part) < 100:
                return found
            page += 1

    def mine(self, items):
        return [item for item in items if item["user"]["login"].casefold() == self.bot]

    def head(self):
        pull = self.api(self.pull)
        if pull["state"] != "open":
            raise Stop(4, "PR_NOT_OPEN", "The pull request is closed or merged.")
        head = pull["head"]["sha"]
        if head != self.sha and self.seen:
            raise Stop(1, "ERROR", f"The head moved to {head}. Start again for that commit.")
        return head

    def summary(self):
        """The status, its time and the commit of the bot's latest review, or None without a summary."""
        found = [c for c in self.mine(self.pages(self.issue + "/comments")) if c["body"].startswith(MARKER)]
        if not found:
            return None
        rows = [line for line in found[-1]["body"].splitlines() if ROW in line]
        cells = [cell.strip() for cell in rows[0].split("|")] if len(found) == 1 and len(rows) == 1 else []
        commit = re.fullmatch(r"`([0-9a-f]{7,40})`", cells[3]) if len(cells) > 3 else None
        when = re.search(r'datetime="([^"]+)"', cells[2]) if commit else None
        status = next((name for name in ("Completed", "Running") if when and f"**{name}**" in cells[2]), None)
        if not status:
            raise Stop(1, "ERROR", "The bot's review summary has a form this script does not know:\n"
                       + "\n".join(c["body"] for c in found))
        return status, moment(when[1]), commit[1]

    def reviews(self, when):
        return [r for r in self.mine(self.pages(self.pull + "/reviews"))
                if r["commit_id"] == self.sha and r.get("submitted_at")
                and moment(r["submitted_at"]) >= when - REVIEW_BEFORE]

    def findings(self, reviews):
        ids = {r["id"] for r in reviews}
        lines = [f"Reviewed commit: {self.sha}"]
        for r in reviews:
            lines += [f"Review: {r['html_url']} ({r['state']})", r.get("body") or "", ""]
        for c in self.pages(self.pull + "/comments"):
            if c.get("pull_request_review_id") in ids:
                lines += [f"--- {c['path']}:{c.get('line') or c.get('original_line') or '?'} ---",
                          c["body"], c["html_url"], ""]
        return "\n".join(lines)

    def look(self):
        """A verdict as a Stop, or the words for what is still awaited."""
        head = self.head()
        if head != self.sha:
            return f"GitHub reports head {head}, not yet the expected {self.sha}"
        self.seen = True
        if self.trigger and not self.after:
            if self.late():
                return "the time ran out before a review could be requested; nothing was posted"
            try:
                self.after = moment(self.api(self.issue + "/comments", "-f", "body=@codex review")["created_at"])
            except Unreadable as exc:
                raise Stop(1, "ERROR", f"The review request may not have been posted ({exc}). "
                           "Look at the pull request before asking again.") from exc
            return "a review was requested"
        row = self.summary()
        if row is None:
            return f"no review summary from {self.bot} yet"
        status, when, commit = row
        if not self.sha.startswith(commit):
            return f"the bot's summary names commit {commit}"
        if status == "Running":
            return "the review is running"
        # GitHub gives the request's time in whole seconds.
        if self.after and when < self.after + timedelta(seconds=1):
            return "the summary is older than the review request"
        reviews = self.reviews(when)
        thumbs = [] if reviews else [r for r in self.mine(self.pages(self.issue + "/reactions"))
                                     if r["content"] == "+1" and moment(r["created_at"])
                                     >= max(when - THUMB_BEFORE, self.after or when - THUMB_BEFORE)]
        # A review that shows up only now, beside the +1, is still this completion's.
        reviews = reviews or thumbs and self.reviews(when)
        if reviews:
            text = self.findings(reviews)
            self.head()
            return Stop(2, "FINDINGS", text)
        if thumbs and self.summary() == row and self.head() == self.sha:
            return Stop(0, "APPROVED", f"Reviewed commit: {self.sha}\n"
                        f"Completed at {when.isoformat()}, +1 at {thumbs[-1]['created_at']}, no review.")
        return "the review is completed, and neither a review nor a +1 for it is visible yet"

    def run(self, timeout, interval, clock=time.monotonic, sleep=time.sleep, log=print):
        deadline, failed, said = clock() + timeout, 0, None
        self.late = lambda: clock() >= deadline
        while True:
            try:
                state = self.look()
                failed = 0
            except Stop as stop:
                state = stop
            except (Unreadable, KeyError, TypeError, ValueError, IndexError) as exc:
                failed += 1
                state = f"GitHub could not be read ({type(exc).__name__}: {exc})"
                if failed == FAILED_READS:
                    state = Stop(1, "ERROR", f"{failed} reads in a row failed. Last: {state}")
            if isinstance(state, Stop):
                return state
            if state != said:
                log(state)
                said = state
            left = deadline - clock()
            if left <= 0:
                return Stop(3, "TIMEOUT", f"No verdict for {self.sha}. Last seen: {state}.")
            sleep(min(interval, left))


class Parser(argparse.ArgumentParser):
    def error(self, message):
        # argparse leaves with 2, which is FINDINGS here.
        print(f"VERDICT: ERROR\n{message}")
        sys.exit(1)


def main(argv=None):
    parser = Parser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repo", required=True, metavar="OWNER/NAME")
    parser.add_argument("--pr", required=True, type=int)
    parser.add_argument("--sha", required=True, help="the full pushed commit, from git rev-parse HEAD")
    parser.add_argument("--bot", default=BOT, help="the reviewer's exact login (default: %(default)s)")
    parser.add_argument("--interval", type=int, default=30, help="seconds between looks (default: %(default)s)")
    parser.add_argument("--timeout", type=int, default=1500, help="seconds to wait (default: %(default)s)")
    parser.add_argument("--trigger", action="store_true",
                        help='post "@codex review" once and accept only a review completed after it')
    args = parser.parse_args(argv)
    if not re.fullmatch(r"[0-9a-f]{40}", args.sha):
        parser.error("--sha takes all 40 characters of the commit")
    watch = Watch(args.repo, args.pr, args.sha, args.bot, args.trigger)
    stop = watch.run(args.timeout, max(args.interval, 1), log=lambda text: print(text, file=sys.stderr, flush=True))
    print(f"VERDICT: {stop.label}\n{stop.text}")
    return stop.code


if __name__ == "__main__":
    sys.exit(main())
