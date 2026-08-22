// Danger's CLI only strips `import ... from "danger"` out of the literal
// entrypoint dangerfile.ts before executing it -- a *value* import of the
// same name from any other file (this one included) survives untouched into
// a real `require("danger")` call, which throws ("looks like you're trying
// to import the danger module"). `import type` is safe: it always erases at
// compile time, so it can never produce that call. The actual danger/warn/
// fail/message/schedule values are injected as real globals by the CLI
// before the dangerfile (and anything it requires) executes.
import type { DangerDSLType } from "danger";

declare const danger: DangerDSLType;
declare function warn(message: string, file?: string, line?: number): void;
declare function fail(message: string, file?: string, line?: number): void;
declare function message(message: string, file?: string, line?: number): void;
declare function schedule(asyncFunction: (resolve?: () => void) => void | Promise<unknown>): void;

export interface DangerRulesConfig {
  /** Require the PR/MR title to follow Conventional Commits. */
  conventionalCommitTitle?: boolean;
  /** Minimum description length in characters. 0 disables the check. */
  minDescriptionLength?: number;
  /** Substring that marks a member's source dir, e.g. "/src/" in projects/geo-core/src/geo_core/. */
  sourcePathMarker?: string;
  /** File expected to change alongside sourcePathMarker. */
  changelogFile?: string;
  /** Substring that marks a member's tests dir, e.g. "/tests/". */
  testsPathMarker?: string;
  /** Warn when the diff exceeds this many changed lines. 0 disables the check. */
  maxLinesChanged?: number;
  /** Warn when one author has more than this many commits on the PR/MR. 0 disables the check. */
  maxCommitsPerAuthor?: number;
  /** Fail when a commit isn't signed. GitHub only -- see checkCommitSigning below. */
  requireCommitSigning?: boolean;
}

const DEFAULTS: Required<DangerRulesConfig> = {
  conventionalCommitTitle: true,
  minDescriptionLength: 20,
  sourcePathMarker: "/src/",
  changelogFile: "CHANGELOG.md",
  testsPathMarker: "/tests/",
  maxLinesChanged: 800,
  maxCommitsPerAuthor: 0,
  requireCommitSigning: false,
};

const CONVENTIONAL_COMMIT_RE =
  /^(build|chore|ci|docs|feat|fix|perf|refactor|revert|style|test)(\([a-z0-9._-]+\))?!?: [a-z].*$/;

/**
 * Runs the shared rule set against the current PR/MR. Works on both GitHub
 * (danger.github) and GitLab (danger.gitlab). Pass a config object to tune
 * thresholds or disable a check (set it to 0/false); see DangerRulesConfig
 * for what each option does.
 *
 * Path checks use substring markers rather than prefixes -- this is a
 * workspace, so "source changed" means any member's projects/<name>/src/,
 * not one fixed top-level src/.
 */
export function runDanger(config: DangerRulesConfig = {}): void {
  const cfg: Required<DangerRulesConfig> = { ...DEFAULTS, ...config };

  const isGitHub = Boolean(danger.github);
  const title: string = isGitHub ? danger.github.pr.title : danger.gitlab.mr.title;
  const description: string = isGitHub
    ? (danger.github.pr.body ?? "")
    : (danger.gitlab.mr.description ?? "");

  const changed = [...danger.git.modified_files, ...danger.git.created_files];

  if (cfg.conventionalCommitTitle && !CONVENTIONAL_COMMIT_RE.test(title.replace(/^Draft:\s*/i, ""))) {
    fail(
      `The title must follow Conventional Commits, e.g. \`feat(geo-core): add crs support\`. Got: \`${title}\``,
    );
  }

  if (cfg.minDescriptionLength > 0 && description.trim().length < cfg.minDescriptionLength) {
    warn("Please describe *what* changed and *why* in the description.");
  }

  const touchesSource = changed.some((f) => f.includes(cfg.sourcePathMarker));
  const touchesChangelog = changed.includes(cfg.changelogFile);
  if (touchesSource && !touchesChangelog) {
    warn(`Source files changed but \`${cfg.changelogFile}\` was not updated.`);
  }

  const touchesTests = changed.some((f) => f.includes(cfg.testsPathMarker));
  if (touchesSource && !touchesTests) {
    warn(`Source files changed without any change under a \`${cfg.testsPathMarker}\` directory.`);
  }

  if (cfg.maxCommitsPerAuthor > 0) {
    checkCommitsPerAuthor(cfg.maxCommitsPerAuthor, isGitHub);
  }

  if (cfg.requireCommitSigning) {
    checkCommitSigning(isGitHub);
  }

  if (cfg.maxLinesChanged > 0) {
    // linesOfCode() returns a Promise, so it must be awaited inside
    // schedule() -- calling it synchronously yields "[object Promise]".
    schedule(async () => {
      const loc = (await danger.git.linesOfCode()) ?? 0;
      if (loc > cfg.maxLinesChanged) {
        warn(`This change is large (${loc} lines). Consider splitting it up.`);
      } else {
        message(`Change size: ${loc} lines across ${changed.length} files.`);
      }
    });
  }
}

function checkCommitsPerAuthor(max: number, isGitHub: boolean): void {
  const commits: any[] = isGitHub ? danger.github.commits : danger.gitlab.commits;
  const counts = new Map<string, number>();
  for (const c of commits) {
    const author: string = isGitHub
      ? (c.author?.login ?? c.commit?.author?.name ?? "unknown")
      : (c.author_name ?? "unknown");
    counts.set(author, (counts.get(author) ?? 0) + 1);
  }
  for (const [author, count] of counts) {
    if (count > max) {
      warn(
        `@${author} has ${count} commits on this PR (threshold: ${max}). Consider squashing ` +
          `related commits so the history stays easy to follow.`,
      );
    }
  }
}

function checkCommitSigning(isGitHub: boolean): void {
  if (!isGitHub) {
    // GitLab's MR DSL doesn't expose per-commit signature verification the
    // way GitHub's Commits API does, so this can only run on GitHub. Flag it
    // rather than silently skip -- enforce via GitLab's own push rules
    // instead (Settings -> Repository -> Push Rules -> Reject unsigned
    // commits).
    message(
      "requireCommitSigning is set, but commit signature verification isn't available " +
        "through Danger's GitLab DSL. Enforce this at the GitLab project level instead " +
        "(Settings → Repository → Push Rules → Reject unsigned commits).",
    );
    return;
  }
  const commits: any[] = danger.github.commits;
  const unsigned = commits.filter((c) => c.commit?.verification && !c.commit.verification.verified);
  if (unsigned.length > 0) {
    fail(
      `${unsigned.length} commit(s) are not signed: ${unsigned
        .map((c) => String(c.sha).slice(0, 7))
        .join(", ")}. Sign your commits (\`git commit -S\`) before merging.`,
    );
  }
}
