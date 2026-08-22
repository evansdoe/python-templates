import { runDanger } from "danger-rules";

// This is a workspace: "source changed" means any member's
// projects/<name>/src/, not one repo-wide src/, so the markers need a
// leading slash to match the nested shape.
runDanger({
  sourcePathMarker: "/src/",
  testsPathMarker: "/tests/",
  // maxCommitsPerAuthor: 5,
  // requireCommitSigning: true,
});
