# Investigation map

Read this for an initial generation or a full regeneration when no current
engineering document gives you a map. Cover:

1. what the project delivers, to whom, and through which entry points;
2. how value and data move from input to outcome, including review,
   validation and rejection gates;
3. controls, privacy, security and trust boundaries;
4. how it is run and supported, and the CI gates that protect it, including
   CI jobs whose path rules match this package's files;
5. verified upstream and downstream connections to any other program or repository, supported or not. For every artifact the project reads or
   writes, search the whole repository for every other program that writes or
   reads it, including notebooks, scripts and other programs' source. Name
   each search in your report. Never read production or customer data;
6. what the project's real inputs do today: when the repository commits
   inputs the project reads and its entry point is read-only and needs no
   network access or credentials, run it over them and report aggregate
   counts only. Never print, quote or copy the inputs' content;
7. plans, design documents and git history for roadmap and progress.
