import { runDanger } from "danger-rules";

// Tune thresholds here, or disable a check by setting it to 0/false. See
// https://github.com/evansdoe/danger-rules for what each option does and
// its default.
runDanger({
  // maxCommitsPerAuthor: 5,
  // requireCommitSigning: true,
});
