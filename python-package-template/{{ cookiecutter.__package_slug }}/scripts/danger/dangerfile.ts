import { danger, warn, fail, message, schedule } from "danger";

// Works on both GitHub (danger.github) and GitLab (danger.gitlab).
const isGitHub = Boolean(danger.github);

const title: string = isGitHub
  ? danger.github.pr.title
  : danger.gitlab.mr.title;

const description: string = isGitHub
  ? (danger.github.pr.body ?? "")
  : (danger.gitlab.mr.description ?? "");

const changed = [...danger.git.modified_files, ...danger.git.created_files];

// 1. Conventional Commits title.
const conventional =
  /^(build|chore|ci|docs|feat|fix|perf|refactor|revert|style|test)(\([a-z0-9._-]+\))?!?: [a-z].*$/;
if (!conventional.test(title.replace(/^Draft:\s*/i, ""))) {
  fail(
    `The title must follow Conventional Commits, e.g. \`feat(parser): add yaml support\`. Got: \`${title}\``,
  );
}

// 2. Non-empty description.
if (description.trim().length < 20) {
  warn("Please describe *what* changed and *why* in the description.");
}

// 3. Changelog reminder for source changes.
const touchesSource = changed.some((f) => f.startsWith("src/"));
const touchesChangelog = changed.includes("CHANGELOG.md");
if (touchesSource && !touchesChangelog) {
  warn("Source files changed but `CHANGELOG.md` was not updated.");
}

// 4. Tests alongside source changes.
const touchesTests = changed.some((f) => f.startsWith("tests/"));
if (touchesSource && !touchesTests) {
  warn("Source files changed without any change under `tests/`.");
}

// 5. Size guard. linesOfCode() returns a Promise, so it must be awaited
//    inside schedule() — calling it synchronously yields "[object Promise]".
schedule(async () => {
  const loc = (await danger.git.linesOfCode()) ?? 0;
  if (loc > 800) {
    warn(`This change is large (${loc} lines). Consider splitting it up.`);
  } else {
    message(`Change size: ${loc} lines across ${changed.length} files.`);
  }
});
