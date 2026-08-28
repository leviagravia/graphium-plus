# Graphium — Canonical Roadmap

Canonical document 2 of 3.
Initial freeze: 2026-08-13 — G00.
Rebaseline: 2026-08-14 — seven-editor competitive synthesis + FeatherPad audit + G04 native-edit/performance redesign + Menu Architecture R3.

## Product direction

Graphium is the **lightweight trust editor**: a **FAST + SIMPLE + SAFE + NATIVE GTK** single-document plain-text editor for Linux. It targets Leafpad/L3afpad-style quick-edit users and the quick-edit subset of Mousepad/FeatherPad users: people who want a file to open immediately, a calm conventional editor surface, a small number of useful persistent conveniences, and unusually strong assurance that Save will not silently alter, convert or overwrite the wrong file.

Permanent primary comparator set: **Leafpad / L3afpad / Mousepad / FeatherPad**.
Supporting mature-source oracles are selected per work item and may include Airpad, Janus, Parchment, gedit, GNOME Text Editor, NEdit, JOE, Lite XL, Calamus published baselines and other directly audited mature sources.

Competitive rules:

1. Leafpad/L3afpad are the reference for immediacy and low cognitive load, not for physical save safety.
2. Mousepad is the primary operational-maturity comparator for lifecycle, monitoring, printing and ordinary desktop completeness.
3. FeatherPad is the permanent speed-plus-maturity comparator: its feature density is evidence that richer internals do not excuse poor launch latency. Graphium targets FeatherPad users who value speed and plain-text maturity but do not depend on tabs, sessions, syntax or column editing.
4. Parchment is the scope-discipline reference, while its implicit Open/Save normalization remains a negative persistence oracle.
5. Graphium must prefer invisible maturity over visible feature count. Feature count is not the competitive axis.
6. Open and Save are content-neutral unless the user explicitly requests a transformation.
7. Safety and performance may never be weakened to improve one another.
8. A mature-source audit must actively search for evidence that contradicts Graphium's proposed design; confirmation-only comparison is invalid methodology.

Minimum convenience floor for v1:

- persistent Word Wrap, font, line numbers, compact status visibility and useful window geometry;
- tab width and spaces/tabs policy where relevant;
- System/Light/Dark appearance without a theme platform;
- trustworthy Find/Replace, Recent Files, printing, conventional shortcuts and useful offline Help;
- status information with line/column, Saved/Modified, encoding and EOL, plus word/character counts when cheap enough not to violate performance budgets.

Deliberate non-goals remain: tabs inside one window, syntax highlighting, projects/workspaces, IDE facilities, plugins, cloud, collaboration, embedded browser, AI and feature-platform expansion.

## Menu Architecture R3 — frozen product surface

Graphium v1 uses exactly six top-level menus: **File · Edit · Search · View · Document · Help**. The six-menu count is not itself considered bloat; bloat is defined instead as duplicated state/configuration surfaces, workflow-irrelevant diagnostics, or feature families that move Graphium toward multi-document/code-editor/platform scope.

Semantic ownership is frozen:

- **File** — persistence and document/file lifecycle;
- **Edit** — local text editing plus preferences that have no clearer direct command;
- **Search** — content search and navigation;
- **View** — how the active text is presented;
- **Document** — observed representation/state facts and explicit representation conversion;
- **Help** — user understanding, shortcuts and compact support information.

Target command surface at v1 closure:

- **File** — New, Open…, Open Recent, Save, Save As…, Save a Copy…, Save Version Copy…, Reload from Disk, Properties…, Page Setup…, Print Preview, Print…, Quit. `Close` is not a separate v1 command because one-process/one-window/one-document gives New and Quit the two distinct lifecycle outcomes already needed.
- **Edit** — Undo, Redo, Cut, Copy, Paste, Delete, Select All, Preferences…. `Paste as Plain Text` is unnecessary because Graphium is itself a plain-text editor.
- **Search** — Find…, Find Next, Find Previous, Replace…, Go to Line…. Next/Previous are first-class command-authority actions. Regex/fuzzy/multi-file search remain outside the v1 MUST scope.
- **View** — Status Bar, Line Numbers, Word Wrap, Font…, Zoom In/Out/Reset, Appearance (System/Light/Dark), Full Screen. Toolbar remains **DEFERRED to the G06 mature-source audit** and is not pre-authorized by the menu architecture.
- **Document** — Encoding, Line Endings, Statistics…. Encoding/EOL submenus must show current representation as an observation and label conversion as an explicit user action; normal Save is never conversion. Tab width/spaces-tabs do not belong here because they are editor behavior, not document representation.
- **Help** — User Guide, Keyboard Shortcuts, About. System Information is folded into About rather than promoted to a separate menu command.

Persistent settings follow a **single-surface rule**: when a setting has a clear direct command (`Word Wrap`, `Line Numbers`, `Status Bar`, `Appearance`, `Font`, and a toolbar toggle if later adopted), that command changes and persists the setting. Preferences does not duplicate it. Initial Preferences ownership is limited to tab width, tabs/spaces behavior and future settings that lack a clearer direct command. Safety invariants are never user-disableable preferences.

`Properties…` is the compact home for file/document facts (location, size/observation, encoding/BOM/EOL, Saved/Modified, writable state, useful symlink/hard-link information). The capability proposed as `Check File on Disk` is retained, but routed as a **Check Now** action inside Properties and as G11 automatic monitoring, not as a permanent primary Document-menu item.

Compact status v1 MUST information is line/column + encoding/EOL + Saved/Modified. Live word/character counts are optional only after cheapness proof; full counts remain available on demand through `Statistics…`.

There is no v1 top-level `Tools`, `Window`, `Format`, `Language`, `Session` or `Plugins` menu.

## Cross-cutting performance method

G04 replaces the earlier heterogeneous benchmark idea with two explicitly different metrics:

- **FIRST_VISIBLE** — common external oracle used identically for Graphium, Leafpad, L3afpad, Mousepad and FeatherPad: process start to first new X11 top-level mapped for the exact spawned PID. Cross-product ratios are valid only for this common metric.
  Comparator launches must be process-isolated when an editor is single-instance/server-capable: Mousepad no-server mode and FeatherPad `--standalone`; never relax exact-PID ownership to accommodate forwarding.
- **FIRST_EDITABLE** — exact Graphium-internal oracle: process start to requested Open completion + mapped window + focused Gtk.TextView, signalled through an inherited pipe with one complete READY record. This is an exact Graphium regression/admission metric, not a comparator ratio.

G12's attempted common external FIRST_EDITABLE oracle was rejected after mature-source and T480 evidence showed that the compared editors do not expose one homogeneous external load/editability lifecycle. Cross-product FIRST_EDITABLE ratios are therefore forbidden for v1. FIRST_VISIBLE remains the common external comparator metric; Graphium's inherited-pipe FIRST_EDITABLE remains Graphium-only regression/admission evidence.

Normal benchmark series use one uncounted priming run followed by at least seven measured runs, reporting median and p90. Real user XDG/configuration is never mutated.

Performance checkpoints:

- **G04** — first GTK shell, FIRST_VISIBLE comparator baseline, exact Graphium FIRST_EDITABLE baseline;
- **G06** — view/status checkpoint;
- **G08** — printing startup-isolation checkpoint;
- **G10** — preferences/appearance checkpoint;
- **G11** — live-monitor startup/idle checkpoint;
- **G12** — final competitive qualification with common exact-PID FIRST_VISIBLE, Graphium-internal FIRST_EDITABLE self-regression and stable post-visible RSS.

## Serial roadmap

### G00 — Architecture Bootstrap / Technology & Boundary Contract
Status: **CLOSED / CERTIFIED / PUBLISHED**

Published commit: `1e9db0eed37d0c860c36c1e07c0dc77bbf59ff95`
Certified tree: `2023683019894366729e3ddc5f3652dbe9d5d0c2`

Freeze Graphium identity, Python/PyGObject/GTK3 technology, Gtk.TextView baseline, package boundaries, XDG isolation, one-document/one-writer authority rules, W116 selective-extraction policy and three-document canonical cap.

### G01 — Document Identity / Load / Serialize Foundation
Status: **CLOSED / CERTIFIED / PUBLISHED**

Published commit: `bf7878c3cdc5cf895b0ffba86b854860c34936a4`
Certified tree: `2334e0c71f01a1b0a30bcb9298911c7c0cafe042`

Strong local-file identity, stable loads, strict encoding/BOM/EOL representation and content-neutral serialization foundation.

### G02 — History / Editor Transaction / Savepoint Session
Status: **CLOSED / CERTIFIED / PUBLISHED**

Published commit: `b91af48a5688772ceffc7eac202c68e1815d7a36`
Certified tree: `3e5b24263d4086a3eccf4897b038b8992703db79`

Publishes the permanent savepoint principle: Saved/Modified is a relation between positive monotonic editor-state IDs, not text equality and not a sticky GtkTextBuffer flag. G02's full-snapshot `TextHistory` remains historical/headless regression material; G04 performs the explicitly authorized architecture review and does not use that storage engine as the active GTK native-edit history.

### G03 — Guarded Save / Save As Foundation
Status: **CLOSED / CERTIFIED / PUBLISHED**

Published commit: `e7045e0ce1c79da71c9968bdfa052df25a5378b7`
Certified tree: `42fe5340e1181199db86ed69cfa93b4735e45666`

Single physical `GuardedFileWriter`, strict pre-mutation serialization, same-directory staging, full-write/fsync semantics, late target revalidation, race-safe Save As, symlink-preserving logical identity, hardlink fail-closed policy and bind-after-commit semantics. No direct-write fallback.

### G04 — Native Edit Integration Hardening + Thin GTK Shell + File Lifecycle + Scientific Performance Baseline
Status: **CLOSED / CERTIFIED / PUBLISHED**

Published commit: `283f1aa5352c2403ac9e0a945b87cc82cd08cff0`
Certified publication tree: `5e2aa256a47739c45f9c79f39a9685b5c6a454d6`
Validated product tree: `9138a273c2363ef2d43adf64470b3273d49c8eae`

Desktop certification and publication completed on 2026-08-14: 196/196 non-desktop tests PASS, strict gates PASS, True-GTK bounded-responsiveness PASS, NON_UNIQUE topology PASS, active Cinnamon shortcut audit PASS, exact FIRST_EDITABLE admission PASS, common FIRST_VISIBLE comparison PASS against Leafpad/L3afpad/Mousepad/FeatherPad, human desktop validation 4/4 PASS, product equivalence PASS for 62 runtime/user-help files, HEAD=origin/main=remote main, worktree CLEAN and final publication phase `G04_PUBLICATION_PASS`.

G04 is rebuilt rather than patched after two withdrawn pre-publication candidate transports exposed defects in the harness and, more importantly, weaknesses in the earlier architecture assumptions.

Mandatory G04 outcomes:

1. **Native delta history**
   - insertion/deletion deltas, not full-document snapshots per keystroke;
   - GtkTextBuffer `begin-user-action` / `end-user-action` plus structural continuity as grouping evidence;
   - no wall-clock timeout as semantic Undo authority;
   - preserve G02 monotonic state-ID/savepoint semantics;
   - Undo/Redo remains available on a realistic 1 MiB multiline document after a small edit;
   - changed-payload memory is bounded independently of base document size;
   - document byte size and pathological logical-line width are tested separately.

2. **Quick-edit process topology**
   - one invocation/process owns one window and one active document;
   - `G_APPLICATION_NON_UNIQUE`;
   - a second invocation must not hijack/replace the first process's document;
   - several command-line files fan out to separate Graphium processes/windows.

3. **Thin classic GTK3 shell**
   - Gtk.ApplicationWindow + Gtk.TextView + Gtk.ScrolledWindow;
   - File: New/Open/Save/Save As/Quit;
   - Edit: Undo/Redo/Cut/Copy/Paste/Delete/Select All;
   - Help: User Guide/Keyboard Shortcuts/About, loaded lazily;
   - no GtkSourceView, toolbar, tabs, syntax or project UI.

4. **Core file lifecycle**
   - failed Open preserves current document;
   - New/Open/Quit use Save/Discard/Cancel only when Modified;
   - merely deciding whether to discard must not copy the whole buffer;
   - Save synchronizes exact current buffer text once at the physical-save boundary;
   - all physical writes continue through G03.

5. **Renderer safety / pathological logical-line contract**
   - initial GtkTextView interactive budget: 20,000 Unicode characters per logical line;
   - a file over the budget is refused before GtkTextBuffer installation, leaving the current document exact;
   - no truncation, marker substitution, automatic wrapping or inserted line breaks;
   - insertion/paste and newline-deleting joins cannot create an over-budget line;
   - the budget is a Graphium safety policy, not a claimed universal GTK hard limit;
   - future paged/streamed exact viewing is deferred and cannot be simulated with the same GtkTextView.

6. **Scientific performance baseline**
   - Graphium exact FIRST_EDITABLE via atomic inherited-pipe handshake;
   - common FIRST_VISIBLE oracle for Graphium/Leafpad/L3afpad/Mousepad/FeatherPad;
   - no ready-file existence race;
   - no cross-product ratio based on heterogeneous readiness definitions.

7. **Desktop closure**
   - full non-desktop suite and strict gates first;
   - True-GTK native-edit/savepoint/realistic-multiline-large-file gate;
   - separate automated huge-line Open/paste refusal gate;
   - NON_UNIQUE topology gate;
   - active Linux Mint/Cinnamon accelerator collision audit;
   - exact and comparator performance receipts;
   - one final human desktop validation only after all automated gates pass.

### G05 — Search Menu Core / Find / Replace / Go to Line + Trustworthiness Gate
Status: **CLOSED / CERTIFIED / PUBLISHED**

Published commit: `a9083daf22ab23cf6cd20841be643510e35d700d`
Certified tree: `12d55249263e006cc68fa304f3c3cc2a9ef73acb`
Validated product tree: `295fa67e4943c35d80e605e214e51ee861350fe6`

Establish the top-level **Search** command authority with Find…, Find Next, Find Previous, Replace… and Go to Line…. Next/Previous are true commands shared by menu/shortcuts/Help rather than UI-private buttons.

Frozen G05 scope after direct G04 source audit and mature-source falsification audit:
- literal current-document search only; no regex, fuzzy or multi-file search;
- query and replacement fields are single-line Unicode text; query is non-empty, replacement may be empty;
- Match Case is adopted; Whole Word and search history are deferred;
- one automatic wrap for Find Next/Previous, with no wrap preference;
- current match is the native selection; eager highlight-all/background scanning is rejected;
- Find/Find Next/Find Previous never alter editor state identity/history/Saved-Modified;
- Replace One uses one-click acquisition: replace current exact match or acquire the next match and replace it in the same activation;
- Replace All freezes non-overlapping matches from the original source, precomputes the final text, verifies G04 renderability before mutation, applies changes in descending source-offset order, and advances exactly one DeltaHistory state/Undo group;
- replacement is applied through Graphium-owned expected-delete/inverse-rollback programmatic delta handling, not legacy full-document snapshot transactions and not a generic renderer-guard bypass;
- Go to Line is a simple 1-based bounded line navigation command;
- explicit-command scanning only: no persistent index, worker or background search state; case-insensitive working memory is logical-line bounded; Find Next/Previous do not materialize all matches; Replace All is fail-closed above 50,000 frozen source matches or the DeltaHistory Undo payload budget.

Trustworthiness tests MUST cover ASCII, Unicode casefold and exact original offsets, empty/short/long replacements, selection/navigation boundaries, wrap, zero-change no-op semantics, stale-plan rejection, failure rollback, exact Saved/Modified through Replace/Undo/Redo, realistic large multiline documents, pathological-line guard interaction and Replace All as one logical Undo transaction. G05 closure also requires `LIGHTWEIGHT_BUDGET_GATE=PASS`.
### G06 — View Menu Core / Compact Status + Lightweight Presentation + Performance Checkpoint
Status: **CLOSED / CERTIFIED / PUBLISHED**

Published commit: `aae14ef000ea44674cb9bbb7b3a87e3af00c0b18`
Published tree: `c2b372082cf44280f9717045578822e7b92bef12`
Certified C2 tree: `52d4f07c4757e85f6ebeec87398ec8ec3b6e30bb`

Implement the direct **View** surface: Status Bar, Line Numbers, Word Wrap, Font family+size, Zoom In/Out/Reset and Full Screen. Appearance remains routed to G10 and is not implemented early. Compact status MUST show line/column + Saved/Modified + encoding/EOL without whole-document scanning. Word/character counts remain on-demand in G07 Statistics because G06 has no cheapness proof that would justify live document-wide analytics.

Frozen G06 decisions after direct G05 source audit, mature-source falsification audit and the T480 NON-CANDIDATE line-number probe:
- **Word Wrap = ADOPT**, using native `Gtk.WrapMode.WORD_CHAR`; persistent direct View setting.
- **Line Numbers = ADOPT**, using the native `Gtk.TextView` LEFT border window; draw only visible logical lines; wrapped display-line continuations receive no additional number; persistent direct View setting; no GtkSourceView, parallel scrolling widget, background index or line cache.
- **Status Bar = ADOPT**, compact and event-driven; persistent visibility; MUST fields only line/column + encoding/EOL + Saved/Modified.
- **Font = ADOPT**, persistent family+size applied through CSS/provider rather than deprecated `override_font`.
- **Zoom = ADOPT**, transient 100%-relative magnification separate from the configured font; Reset Zoom means 100%; no document/history/config mutation.
- **Full Screen = ADOPT**, transient window presentation state.
- **Toolbar = REJECT v1** after Lightweight Budget audit: the small Graphium command surface does not justify a duplicate button surface or toolbar state.
- **Appearance = DEFER G10**, preserving the serial roadmap.

Persistent direct View settings are stored in one small XDG product config and are written only on explicit user changes. No background settings writer, session database, scanner or settings platform is introduced. Repeat FIRST_EDITABLE and common FIRST_VISIBLE performance checkpoint against Leafpad/L3afpad/Mousepad/FeatherPad before G06 closure. G06 cannot close without `LIGHTWEIGHT_BUDGET_GATE=PASS`.
#- Performance checkpoint must include self-regression against the certified G04 T480 FIRST_EDITABLE/FIRST_VISIBLE Graphium baseline; time limit = max(+25%, +75 ms), RSS = max(+25%, +20 MiB). Cross-product FIRST_EDITABLE remains forbidden until G12.

## G07 — Recent / Save Copy / Version Copy / Properties / Statistics
Status: **CLOSED / CERTIFIED / PUBLISHED**
Historical implementation lineage: **IMPLEMENTATION R1 BUILT**, then desktop-certified/published after the frozen qualification chain.

Baseline: published G06 commit `aae14ef000ea44674cb9bbb7b3a87e3af00c0b18`, tree `c2b372082cf44280f9717045578822e7b92bef12`.

Complete the high-value **File/Document** conveniences without adding session/workspace state: Open Recent, Save a Copy, Save Version Copy, Graphium-specific Properties and on-demand Statistics. Recent is bounded file history only, not session restoration. Copy and Version Copy reuse the sole guarded writer but never rebind the active document, move the savepoint/history or touch Recent. Properties is a compact read-only surface for accepted logical/canonical identity, disk/representation facts and Saved/Modified; **Check Now** performs a fresh strong read-only observation and never accepts/reloads the session baseline. Statistics captures the live buffer only on explicit activation and computes document/selection Lines/Words/Characters in a pure GTK-free O(n) function.

Frozen G07 constraints: recent state is lazy atomic `XDG_STATE_HOME/graphium/recent-files.json`, schema `{"version":1,"paths":[...]}`, cap 10 and mode 0600; no DB/XBEL/global recent authority, session restoration, automatic backup, version timeline/index, background statistics, file monitor, Reload, second writer or second document authority. No new default G07 accelerator. Desktop/manual validation is forbidden until headless/strict architecture, Statistics performance, Lightweight Budget and real-App True-GTK gates pass.
### G08 — Page Setup / Print Preview / Print + Startup-Isolation Checkpoint
Status: **CLOSED / CERTIFIED / PUBLISHED**

Complete the **File** printing group with Page Setup…, Print Preview and Print…. Printing is desktop-complete but lazily initialized; dormant print code may not materially tax quick-edit startup. Page Setup is a Graphium authority rather than a fixed inherited pagination constant. Repeat startup-isolation/performance evidence.

**G08 responsiveness repair checkpoint (2026-08-19):** the initial synchronous design was measured on the T480 at ~109.6 s for a 1 MiB / 787-page export, while 5 KiB native Preview returned in ~45 ms. GTK-native `allow_async` + `done` made the 1 MiB Preview entry return in ~6 ms, but a real-mainloop diagnostic then localized the remaining freeze inside eager document-global `begin-print` pagination. The authorized second repair keeps native GTK/Pango/Cairo and moves measurement to bounded incremental `paginate` callbacks (16 KiB target / 64 logical lines, logical-line chunk boundaries). Exact-tree T480 requalification subsequently passed, including bounded callback latency, heartbeat responsiveness, cancel/done cleanup and document neutrality; no Graphium worker/service/custom preview/GtkSourceView was introduced.
### G09 — Explicit Text Transformations Only / No Format-Menu Expansion
Status: **CLOSED / CERTIFIED / PUBLISHED**

Uppercase, Lowercase, Title Case, Duplicate Line/Selection, Move Lines, Trim Trailing Spaces, Remove Extra Spaces, Join Lines and Reflow Paragraph remain eligible only as explicit user actions after their own mature-source/scope review. They must not create implicit Open/Save cleanup, and they do **not** justify a permanent top-level `Format` menu. Parchment-style implicit cleanup during Open/Save remains a permanent negative oracle.
### G10 — Persistent Essential Preferences / Appearance / Desktop Polish + Performance Checkpoint
Status: **FAILED / NOT PUBLISHED — TERMINAL**

Candidate R1 and Candidate R2 each ended in a valid user-visible product failure; the G10 candidate line is exhausted at 2/2 and R3 is forbidden. G10 is not reopened or published retroactively. A later NON-CANDIDATE recovery proved the useful Preferences, Appearance, normal-window geometry and local-file DnD behavior, but that recovery is evidence/carry-forward only and is not a canonical G10 release. G11 selectively reproduces those proven behaviors from the canonical GS07 parent without carrying failed-G10 Candidate/release lineage.

### G11 — Reload + Strong Live External-File Safety + Slow-Filesystem Gate
Status: **CLOSED / CERTIFIED / PUBLISHED**

G11 adds ordinary **File -> Reload from Disk (F5)**, strong live external-file monitoring and the slow-filesystem safety boundary. Reload is deliberately asymmetric with Save: Saved reloads directly; Modified offers only Cancel or **Discard Changes and Reload**. Reload never invokes the writer or touches Recent. Filesystem monitor events are **interrupts, not truth**: event -> debounce/coalescing -> fresh strong G01-grade observation -> material classification -> low-noise nonmodal UI. At most one strong observation runs concurrently, outside the GTK main thread; stale lifecycle generations and already-obsolete pending results are suppressed. No periodic polling, automatic reload, monitor truth shortcut or second file-identity authority exists.

The hostile safety contract remains: accepted A -> another process replaces A with B -> ordinary Save must never silently overwrite B. Current source covers local content change, same-size/same-mtime byte changes, atomic replacement, missing files, direct-symlink target changes and logical symlink retarget/removal, own-Save suppression, one-worker generation ownership and slow-observer GTK responsiveness. G11 Candidate R1 was certified on source tree `a3cc213e844155ef632c720a7d320412a2ac574a`; the authorized finalizer then published commit `10be01b7909c3efe6f76b4c80ea46d1586aea65c` with tree `82619dfb95df46a33ca6d0e08ade282be44ff2c1`, and verified HEAD=origin/main=remote main with a clean worktree. Candidate accounting closed at **1/2 used**. The separate post-publication read-only audit passed with zero blockers, after which G12 was explicitly authorized.
### G12 — V1 Product Closure / Six-Menu Competitive Qualification
Status: **CLOSED / CERTIFIED / PUBLISHED**

Close all v1 MUST features, packaging/install behavior, the frozen **File/Edit/Search/View/Document/Help** architecture, offline Help and keyboard documentation, True-GTK regression and anti-bloat audit. Verify that command authority, menu labels, accelerators and Help remain synchronized; no top-level Tools/Window/Format/Language/Session/Plugins menu appears. Verify Preferences does not duplicate direct persistent View commands, representation conversion remains explicit and distinct from Save, System Information is folded into About, and Check Now is routed through Properties/monitoring rather than diagnostic-menu expansion.

Do not make Graphium-vs-comparator FIRST_EDITABLE claims: the G12 common external oracle experiment is retired because mature products own different load/editability lifecycles. Publish one common exact-PID FIRST_VISIBLE receipt, exact Graphium-internal FIRST_EDITABLE/self-regression evidence and stable post-visible Graphium/Mousepad RSS, and report gaps honestly against Leafpad, L3afpad, Mousepad and FeatherPad. V1 competitive closure requires: no perceptible quick-edit regression versus the lightweight set; no silent Save normalization; no silent overwrite after accepted identity becomes stale; exact Saved/Modified through Undo/Redo/late Save; useful persistent conveniences without preference-platform bloat; low-noise monitoring; continued identity as a plain-text quick editor rather than a reduced IDE; and no known pathological logical-line shape silently admitted into a renderer path already demonstrated to hang.

**G12 contract freeze — 2026-08-24.** The published G11 post-publication audit passed and the user explicitly opened G12. The source-first closure/design reconciliation freezes five implementation slices: (S1) explicit Encoding/Line Endings conversion with one composite text-state + representation Saved/Modified relation; (S2) bounded Document-menu and Help/command synchronization; (S3) a minimal product-only prefix/staging install projection and desktop entry; (S4) a qualification-only common AT-SPI exact-PID disposable-input FIRST_EDITABLE oracle; (S5) final source-only anti-bloat/canonical convergence. Encoding targets are only Graphium-reopenable Unicode/BOM profiles; line-ending targets are LF/CRLF/CR; mixed EOL is observation only. Normal Save remains non-converting unless the user has explicitly changed the representation state. Help wording is frozen to the already implemented `User Guide / Keyboard Shortcuts / About`. AppStream metadata is deferred until a project-license authority exists rather than guessed. G12 Candidate attempts remain 0/2 and no T480 run is permitted until source-only S1-S5 are exhausted.

**G12-S1 source-only closure — 2026-08-24.** Representation State Foundation is implemented and locally qualified NON-CANDIDATE. `DocumentSession` now owns current/saved serialization profiles inside the same composite Saved/Modified relation; Save/Save As capture the current profile exactly, late completion cannot clean a newer representation choice, copy/version-copy serializes the current profile without advancing the active saved relation, and a fresh post-commit load remains authoritative where bytes carry no physical EOL evidence. No GTK/menu implementation is included in S1; that remains S2.

**G12-S2 source-only closure — 2026-08-24.** The frozen Document surface is now implemented as `Encoding / Line Endings / Statistics…` through the existing product-owned command catalog. Encoding exposes only UTF-8, UTF-8 BOM, UTF-16 LE/BE BOM and UTF-32 LE/BE BOM; Line Endings exposes only LF/CRLF/CR. The GTK actions project directly onto the single S1 `DocumentSession` representation authority, perform no immediate write and create no text Undo entry. Compact Status now projects the current selected representation (including unsaved conversion choices and mixed-EOL observation), and User Guide/Keyboard Shortcuts are synchronized with the same command surface. No new accelerator, menu authority, writer, preference or background subsystem is introduced. S3 remains the next source-only slice.

**G12-S3 source-only closure — 2026-08-24.** Minimal product-only installation is implemented by one standard-library `bin/graphium-install` entrypoint. Default user prefix is `~/.local`; explicit `--prefix` and `--destdir` support package staging. The projection contains only the private Graphium runtime package/launcher/offline Help, a relative public launcher symlink, and `io.github.leviagravia.Graphium.desktop` under `share/applications`. Tests/evidence/canonical docs/selftest/installer and bytecode caches are excluded. The desktop entry uses the frozen application ID, `Exec=graphium %F`, `text/plain`, GTK/Utility/TextEditor categories and the generic `accessories-text-editor` icon. AppStream remains explicitly deferred. S4 common external FIRST_EDITABLE oracle is next; T480 remains forbidden until source-only S4-S5 are exhausted.

**G12-S4 source-only closure — 2026-08-24.** The common external FIRST_EDITABLE qualification oracle is implemented under `tests/desktop/harness/first_editable.py`, with no product/runtime dependency. It uses one named disposable 0 B/5 KiB/1 MiB/10 MiB fixture, isolated HOME/XDG roots, exact process isolation (Mousepad `--disable-server`, FeatherPad `--standalone`), monotonic start immediately before spawn, AT-SPI exact-PID accessible ownership, required Text + EditableText and EDITABLE/FOCUSED/VISIBLE/SHOWING states, one unique `KEY_STRING` input token, and local count/caret/token acceptance without clipboard or Save. One priming run plus seven measured runs produces median and p90; missing executable/AT-SPI/exact-PID editor/input acceptance is comparative BLOCKED rather than Graphium product FAIL. Headless Release protocol tests prove command/isolation/acceptance/static boundaries; dead desktop-harness helpers were deleted and drain/wait ownership consolidated so Structural Continuity remains PASS without rebaseline. S5 final source-only convergence is next; no T480 run is permitted before S5 is exhausted.

**G12-S5 source-only closure — 2026-08-24.** Final convergence is complete. The six-menu order now has one product-owned authority (`TOP_LEVEL_MENUS`) consumed by the GTK menu builder; Help is exactly User Guide / Keyboard Shortcuts / About; About contains compact Python/GTK/display support information instead of a separate diagnostics command; Preferences remains limited to tab width and tabs/spaces; Check Now remains inside Properties. Source-proven dead code was removed without deleting framework callbacks or safety authorities. Product version advances from published G11 `0.0.11` to unpublished G12 `0.0.12`. G09 and G11 canonical status lines are now converged with actual history. S1-S5 are exhausted source-first; the next allowed step is one consolidated automated NON-CANDIDATE T480 platform qualification, subject to explicit authorization, with Candidate attempts still 0/2 and manual tests 0.

**G12 first consolidated platform STOP and oracle rebuild — 2026-08-25.** The authorized 18-lane NON-CANDIDATE T480 run passed lanes 1-14, including all 293 permanent local authorities, Structural Continuity and 10/10 permanent True-GTK sections, then stopped at Lane 15 before any G12 closure checkpoint was emitted. Source-first mature/Calamus audit proved the new closure gate queried the wrong menu owner and exposed broader S4 oracle defects before lanes 16-18 were reached. The initial S4 rule `focused EditableText + accepted token` is superseded because it did not prove requested file Open completion and because `empty` had drifted into a named 0-byte file. Rebuild rules are now binding: exact workload count+sentinel witness before input, true no-file empty startup, separate FIRST_VISIBLE and FIRST_EDITABLE series, contamination tripwire, BLOCKED comparator = incomplete receipt, stable multi-sample idle RSS, balanced run order and complete raw/hash/version receipt. Lane 15 must inspect the concrete window-owned menubar and use semantic postconditions rather than fixed drains. Candidate attempts remain 0/2; no product-core failure was proven.

**G12 rebuilt platform Lane-18 STOP / source-only oracle repair — 2026-08-25.** The rebuilt consolidated NON-CANDIDATE T480 run validly passed lanes 1-17, including all 10 permanent True-GTK sections, rebuilt GTK closure, installed-product smoke and G12-vs-G11 internal performance self-regression. Lane 18 stopped with `unexpected_text_mutation_during_input_acceptance`. The user explicitly confirmed that no human or other external input occurred during that run. Source-first comparison with AT-SPI and mature editors proved the classifier invalid: `KEY_STRING` delivery does not promise an atomic N->N+token-length document transition, while the real XInput2 tripwire had been stopped before the acceptance interval. The common oracle is therefore amended to keep the real key/button tripwire active for the complete measured interval and to perform the controlled edit through the exact-PID object's `EditableText.insert_text()` interface. Acceptance is exact count + token-at-insertion-position; intermediate asynchronous accessibility propagation is permitted and is never inferred to be contamination. Global `generate_keyboard_event(KEY_STRING)` is rejected for this qualification oracle. No Graphium product core/safety authority is changed.

**G12 focused Lane-18 BLOCKED / common-FIRST-EDITABLE retirement — 2026-08-25.** The focused requalification correctly returned `BLOCKED_INCOMPLETE`, not PASS or product FAIL, with 33 blocked series spread across all five applications. Deep re-audit shows the common external FIRST_EDITABLE model itself is invalid for v1: AT-SPI focus/text/editability and direct `EditableText` mutation do not constitute one homogeneous load/keyboard-readiness lifecycle across Leafpad, L3afpad, Mousepad, FeatherPad and Graphium. The final G12 comparative model therefore returns to G04: FIRST_VISIBLE is the sole cross-product latency metric; Graphium's exact READY-pipe FIRST_EDITABLE remains Graphium-only; the invalid 1.5x/1.75x editable targets are withdrawn rather than moved to another metric. FIRST_VISIBLE also recovers G07's mandatory exact-PID post-exit X11 quiescence and detailed blocked-run diagnostics. Stable post-visible RSS remains a separate process-level Graphium/Mousepad comparison. Candidate attempts remain 0/2 and no product-core failure is proven.


**G12 FIRST_VISIBLE/RSS source-only rebaseline — 2026-08-25.** The invalid common external FIRST_EDITABLE authority has been removed rather than repaired again. Permanent comparator primitives now live in `tests/desktop/harness/comparators.py` and own only isolated commands, true-empty/named workloads and disposable HOME/XDG setup. The rebaselined competitive authority contains no AT-SPI, focus, Accessible Text/EditableText or generated input. FIRST_VISIBLE uses current exact-PID X11 ownership with no pre-XID novelty gate, mandatory post-exit X11 quiescence, incremental raw diagnostics and balanced run order. Stable post-visible RSS is measured separately for Graphium/Mousepad after exact-PID visibility using five samples spanning at least 0.4 s with <=1 MiB spread. The invalid 1.5x/1.75x editable targets are withdrawn, not transplanted; G04 FIRST_VISIBLE gates and the independent <=150 MiB / <=2.5x Mousepad memory target remain. Local permanent qualification is 293/293 PASS and Structural Continuity remains PASS with reduced validation/harness LOC. Product runtime is byte-identical; Candidate attempts remain 0/2.

**G12 focused FIRST_VISIBLE/RSS platform proof + post-platform audit — 2026-08-25.** The authorized focused NON-CANDIDATE T480 proof on source tree `648c4891b7e1ee2cb798b747fafb50fd7ed817ba`, product subtree `1eb5c018574d330907d7f0cab0353074e7b37fe6`, completed `PASS_COMPLETE` with zero blocked comparators. FIRST_VISIBLE medians were Graphium/Mousepad 347.914/238.786 ms empty and 350.446/242.890 ms at 5 KiB, satisfying the frozen <=2.0x-or-absolute gates (ratios 1.457 and 1.443); 1 MiB/10 MiB remain report-only. Stable post-visible RSS was Graphium 56.62 MiB versus Mousepad 46.50 MiB (1.218x), satisfying both <=150 MiB and <=2.5x gates. Receipt SHA-256 is `9031403e1de3ec68db070c00e43c0d6d633799ba84fbafc10f2dcfe99fec7059`. Combined with the already valid Lane 1-17 product/GTK evidence on the byte-identical product subtree, G12 now has complete NON-CANDIDATE platform evidence. Post-platform source audit found no product/runtime/test blocker; only canonical current-status drift was corrected. Candidate R1 remains undeclared at 0/2 and requires separate explicit authorization.

**G12 Candidate R1 certification + publication authorization — 2026-08-25.** Candidate R1 was declared and certified on exact source tree `7c855a0058e180c557d0fbb0c1de51af378e7bdf`, product subtree `1eb5c018574d330907d7f0cab0353074e7b37fe6`, by evidence adoption plus exact local requalification: 293/293 permanent local tests PASS, rebaselined competitive authority PASS, Structural Continuity PASS, 0 manual tests, and no new T480 because the platform-bound product/test/launcher/user-help bytes were unchanged from the complete platform evidence boundary. Candidate accounting is 1/2 used, 1/2 remaining. The user has now explicitly authorized publication. The fail-closed finalizer must prove the published G11 parent, exact publication target tree, unchanged certified runtime/test/user-help bytes, local authorities, evidence manifest, commit/push/fetch synchronization and a clean worktree. G13/G14 remain post-v1 and must not enter this publication transaction.

**G12 / Graphium v1 publication closure + post-publication canonical convergence — 2026-08-25.** The authorized fail-closed finalizer published commit `cb71d9575f7c347fd10334cd7ddb54e5c921ea34`, tree `4e4651b9323c080716bfb28340fa274bd48c0017`, with product subtree `1eb5c018574d330907d7f0cab0353074e7b37fe6`. It proved 293/293 local tests PASS, rebaselined competitive authority PASS, Structural Continuity PASS, `HEAD=origin/main=remote main`, and worktree CLEAN. The subsequent read-only audit found no product/test/platform blocker and only a pre-finalizer canonical-state drift; this revision is the authorized document/evidence-only convergence that records the completed release without changing `graphium/`, `bin/`, `tests/` or `docs/user/`. The historical pre-publication certification receipt remains unchanged; additive `evidence/G12_PUBLICATION_FINAL_RECEIPT_20260825.txt` records the final publication facts. G12 and Graphium v1 are therefore CLOSED / CERTIFIED / PUBLISHED. G13 remains POST-V1 HIGH-PRIORITY BACKLOG / NOT OPENED and requires a separate authorization after a final read-only sync audit.

### G13 — Crash Recovery Cache
Status: **CLOSED / CERTIFIED / PUBLISHED**

G13 is part of completing Graphium Core as a safety/recovery capability, not an ordinary feature expansion. The frozen design uses a private `XDG_STATE_HOME/graphium/recovery` artifact that is never the accepted user target and never gains Save authority. S1 completed the self-validating record/codec, UUID-private storage, atomic durability, corruption rejection and advisory ownership lock. S2 completed fixed 30-second one-shot coalescing, main-context capture, one dedicated lazy recovery worker, generation fencing and exact lifecycle invalidation. S3 completed lazy orphan discovery, lock-claim/reread exclusion, one-artifact startup presentation, strong target revalidation, exact-match named restore versus fail-closed unbound restore, and empty post-crash Undo/Redo. S4 has now closed on the exact S3 bytes: 336/336 local permanent authorities PASS, Structural Continuity PASS, post-implementation mature-source/source-confinement audit PASS, and a focused automated fresh-process T480 True-GTK proof 4/4 PASS for clean startup, Start Without Recovering, Discard Recovery and Recover Untitled, with source tree identical before/after. No manual test was required. Pre-Candidate consolidation advances the next unpublished product version from published `0.0.12` to `0.0.13` without changing any recovery implementation byte. Candidate R1 was declared and certified; attempt accounting is 1/2 used and 1/2 remaining. The authorized fail-closed finalizer subsequently published G13 as commit `053bcde3f5bcb4f51ce9edd8a89538a7630949ae`, tree `eb6925d3b779fa8ae12d1d0947a31fe460fbee0e`, product subtree `033ae482b19cf81a4852cf4e22773b2740387443`. Publication requalified 336/336 local authorities, G13 focused 43/43 and Structural Continuity, adopted S4 True-GTK 4/4, and ended `HEAD=origin/main=remote main` with a CLEAN worktree. The post-publication audit found only canonical pre-finalizer wording drift; this document/evidence-only convergence records the final state without changing product/test/user-help bytes.

### G14 — External Spellcheck
Status: **CLOSED / CERTIFIED / PUBLISHED**

After G13, complete Graphium Core with a bounded optional/on-demand external spell check. Preferred boundary is an external Hunspell subprocess created only for explicit **Check Spelling…** use: no live/background scanning, daemon, startup dictionary load or mandatory Python Hunspell binding. Absence/failure of Hunspell or dictionaries must fail as an optional capability and must not affect editor startup or document safety.

### Product editions after Core completion

The product line is cumulative unless a later explicit decision changes it:

- **Graphium Core:** the lightweight editor plus G13 Crash Recovery Cache and G14 External Spellcheck.
- **Graphium Plus:** Core plus a compact native icon toolbar and a Writing Workspace adapted from Calamus. The toolbar is only another projection of existing actions; the Workspace must remain bounded/on-demand and must not create a second document lifecycle.
- **Graphium Ultra:** Plus plus a Markdown viewer/editor.

Plus and Ultra are roadmap definitions only and are **NOT OPENED**. Their capability modules must not contaminate Core startup/runtime or duplicate Save/document authorities.

**G14 opening + S1 protocol/span checkpoint — 2026-08-25.** After the final post-G13 sync audit PASS and explicit user authorization, G14 opened source-first. The frozen Core design is `Document -> Check Spelling…` / F2 with optional system Hunspell only on explicit invocation; no startup probe/dictionary load, live underline, daemon, binding, personal-dictionary write or persistent language preference. S1 implements only the GTK-free bounded Unicode word-span model plus the confined external `hunspell -a -i UTF-8 --check-apostrophe` pipe session. Every token line is `^`-prefixed, shell execution is forbidden, document paths are never passed, protocol/suggestions are bounded and strictly parsed, timeout/cancel closes and reaps the child, and a 1 MiB single-line document is token-scanned rather than sent as a raw Hunspell line. S1 adds no command/menu/dialog/editor mutation and keeps version `0.0.13`. Candidate remains undeclared and requires separate authorization after later slices.

## Permanent routing rules

1. Serial Gxx only; no G05 implementation while G04 is open.
2. Canonical authority remains exactly three documents.
3. Source audits, matrices, receipts, benchmark JSON and User Guide are non-canonical evidence/product material summarized into the MO.
4. Graphium and Calamus evolve independently after provenance-recorded extraction.
5. Every visible function added or materially changed updates the offline User Guide/shortcut documentation in the same candidate.
6. Every new accelerator is checked against the active Linux Mint/Cinnamon global bindings; `Ctrl+Alt+L` is forbidden.
7. Verified dead code is removed rather than retained as speculative compatibility surface; cleanup must rerun full tests/gates.
8. Mature-source audit is falsification-oriented: record the Graphium assumption, contradictory mature evidence, viable alternative and resulting decision before ADOPT/ADAPT/REJECT/DEFER.
9. A harness/oracle stop is classified before product repair. It is not a reason to cycle candidates by trial-and-error.
10. Safety and content neutrality are never performance toggles.
11. Permanent competitive qualification uses Leafpad, L3afpad, Mousepad and FeatherPad; missing comparator evidence blocks the comparative receipt rather than being silently omitted.
12. Recovery, if implemented post-v1, is a cache separate from the user target and never gains implicit Save authority.


G06 qualification rebaseline after the retired integrated NON-CANDIDATE line:
- `G06_INTEGRATED_CHECKPOINT_LINE=RETIRED`; no R3;
- next T480 run is a separately authorized **G06 product candidate**, not another checkpoint;
- candidate validation is a fresh-process gate matrix: published G04 regression, published
  G05 regression, G06 View semantics with exact clean lifecycle boundaries and zero expected
  modals, G06 View performance, topology/shortcut audit, FIRST_EDITABLE, common FIRST_VISIBLE
  comparators, G05 Search performance and G06 startup self-regression;
- outer timeouts are last-resort process containment; modal/lifecycle ownership belongs to
  the individual gate;
- manual G06 validation starts only after all automated lanes PASS.

G06 product-candidate freeze after modal/lifecycle re-audit:
- the product runtime is byte-for-byte unchanged from the pre-re-audit G06 implementation;
- only qualification harness/tests/authority/evidence changed during the re-audit;
- candidate automation uses separate fresh-process/fresh-XDG lanes and does not reuse the retired integrated checkpoint state;
- candidate packaging must pass directory/file permission-topology validation before manifest/tree checks.

G06 Candidate C1 performance stop and Lane-4 rebaseline:
- C1 functional G04/G05/G06 True-GTK lanes PASS; C1 stopped before manual validation in the
  old G06 View-performance lane; performance verdict remained UNRESOLVED;
- old repeated toggle/reset performance oracle is RETIRED as cumulative re-layout stress;
- new oracle is `SINGLE_TRANSITION_FRESH_PROCESS`: one discarded priming process plus seven
  measured fresh processes per scenario, fresh HOME/XDG, exactly one View transition each;
- latency ends on the first post-transition GTK `after-paint`; worker-local timeout is 30 s
  with a 15 s frame deadline; parent/lane timeout is containment only;
- scenarios: line-numbers-1m, wrap-1m, line-numbers-10m, wrap-10m, zoom-10m,
  font-apply-10m, status-1000-updates;
- all previous budgets remain frozen; Font Apply 10 MiB adds p90 <= 500 ms;
- no Graphium runtime change is permitted merely to repair the retired oracle;
- Candidate C2 may be built only from this redesigned qualification boundary and must be
  fully fresh-package qualified before any optional T480 execution.


### G06 closure / G07 handoff — 2026-08-16

G06 has a desktop-certified C2 product tree `52d4f07c4757e85f6ebeec87398ec8ec3b6e30bb`. The G06 publication payload changes canonical authority/evidence only; it does not alter the certified Graphium runtime. After the publication finalizer proves the remote real state, G06 is CLOSED/CERTIFIED/PUBLISHED.

**Next serial item: G07 — Recent / Save Copy / Version Copy / Properties / Statistics.** G07 MUST NOT implement before: read-only audit of the published G06 source, direct mature-source falsification audit, explicit ADOPT/ADAPT/REJECT/DEFER matrix, Lightweight Budget review and contract freeze. Priority mature sources are Mousepad 0.7.0, FeatherPad source-derived authority already preserved in the bundle, gedit/GNOME Text Editor, Leafpad/L3afpad for minimalism contrast, and Calamus W115/W116 provenance only as a design reference for Copy/Version Copy/Properties semantics (never as a runtime dependency).


### G07 R1 startup qualification correction — 2026-08-16

The first exact R1 T480 NON-CANDIDATE qualification passed all functional/True-GTK G04-G07 lanes, Statistics, View, topology, shortcut and Search gates but failed the startup self-regression gate. Failure-specific direct mature-source re-audit isolated document-grade `fsync(file)+fsync(directory)` in the new Recent convenience-store write on every successful Open. FeatherPad, GNOME Text Editor, Mousepad, gedit and NEdit all contradict the need for that durability level; Leafpad/L3afpad remain the minimalism negative oracle. The frozen Recent contract is clarified as `G07_RECENT_DURABILITY=ATOMIC_CONVENIENCE_NO_FSYNC`: retain 0600 complete-temp + atomic replace, remove only Recent fsync barriers. No document-save safety is weakened and no background service is introduced. A fresh T480 NON-CANDIDATE startup requalification is mandatory before any G07 desktop candidate.

G07 R1 comparator-stop re-audit (2026-08-17): a startup-repair NON-CANDIDATE rerun reached and passed
all Graphium product/view/statistics gates through Graphium FIRST_VISIBLE, then a single Leafpad launch
produced no new X11 top-level for the exact spawned PID. Direct mature-source re-audit of Leafpad,
L3afpad, Mousepad 0.7.0, FeatherPad and GNOME Text Editor confirms the exact-PID ownership oracle but
exposes two harness defects: missing explicit post-process X11 quiescence/block diagnostics, and an
anti-bloat Graphium self-gate incorrectly dependent on complete competitor telemetry. Runtime product
changes are forbidden for this stop. Harness-only repair: comparator blocks are exit-3 comparative
blocks with incremental partial receipts and no silent retry; G06 startup self-regression consumes only
Graphium measurements. Full comparative evidence remains mandatory before candidate promotion.


### G07 closure / G08 handoff — 2026-08-18

G07 completed the full desktop qualification on the T480. The certified publication-line source tree before authority-only closure is `12f24dbc265247bd9c014e2494fb91fc82f07af1`. Automated qualification passed 304/304 tests, strict architecture, G04/G05/G06/G07 True-GTK, contamination-aware G06 View performance, G07 Statistics performance, topology, Cinnamon shortcut audit, exact Graphium FIRST_EDITABLE, complete Graphium/Leafpad/L3afpad/Mousepad/FeatherPad FIRST_VISIBLE comparison, G05 Search performance and G06 startup self-regression. The user then reported **7/7 manual desktop tests PASS**. One valid product candidate attempt was consumed; earlier R1 desktop stops were classified as invalid execution/oracle-harness defects after failure-specific direct mature-source audits and do not count as product FAILs.

Publication may alter only the three canonical authority documents plus additive certification evidence; `graphium/`, `bin/`, user-facing product documentation, tests and qualification tools remain byte-for-byte equivalent to the certified G07 publication-line source. G07 is not called PUBLISHED until the finalizer proves the exact final tree, commits, pushes, fetches, verifies `HEAD=origin/main=remote main`, and leaves the worktree clean.

**Next serial item after publication: G08 — Page Setup / Print Preview / Print + Startup-Isolation Checkpoint.** G08 implementation is forbidden until a read-only audit of the real published G07 repository, a direct mature-source printing audit, an explicit ADOPT / ADAPT / REJECT / DEFER matrix, Lightweight Budget review, startup-isolation design and contract freeze are complete. Priority source authorities: Leafpad `src/gtkprint.c` as the thin GTK3 print-operation model; Mousepad `mousepad-print.c/.h` as the mature GTK3 print/settings model; gedit print job/preview/app page-setup code as the richer GTK3 contrast; FeatherPad `featherpad/printing.cpp/.h` and print-dialog call sites as the Qt lightweight-power contrast; GNOME Text Editor as a GTK4 modern contrast where printing support exists in the supplied source; L3afpad as minimalism/feature-pressure contrast. No web substitute is permitted for this audit.


### G08 implementation checkpoint — 2026-08-18

Published G07 baseline was independently proven on the T480 before G08 work began:
commit `7a3f49218dbabdbd6e47114a5fde2f4999f9c841`, tree
`198164be38e77538b92f45d5d53fe4b0c1929955`, with
`HEAD=origin/main=remote main` and a clean worktree.

The required read-only G07 audit, direct preserved mature-source printing audit, explicit
ADOPT/ADAPT/REJECT/DEFER matrix, Lightweight Budget and G08 contract freeze completed before
implementation. The isolated G08 implementation now contains the frozen File printing group,
strict lazy print-module/Page-Setup ownership, native GTK preview and Pango/Cairo pagination.
It is **not a desktop candidate**. Candidate attempts consumed remain **0/2**.

Before any candidate declaration the T480 NON-CANDIDATE PyGObject/GTK3 print-binding probe must
PASS, followed by the frozen True-GTK/hostile startup-isolation/performance and Lightweight Budget
gates. A probe failure is boundary evidence, not a product candidate FAIL, and requires direct
failure-specific mature-source re-audit before repair.


**G08 exact-once cleanup follow-up (2026-08-19):** the first incremental T480 requalification proved cheap begin-print and bounded paginate callbacks, then exposed duplicate Graphium render cleanup: native `end-print` was followed by `_clear_active()` invoking `job.end_print()` again from `done`. Failure-specific gedit/GNOME Text Editor re-audit confirmed separate ownership. The repair makes native `end-print` the normal one-time render cleanup and reserves the `done` fallback for paths where GTK never emitted it. Pagination is unchanged; NON-CANDIDATE requalification remains required.


### G08 closure / G09 handoff — 2026-08-20

G08 completed the full T480 qualification on exact certified product tree `420238bd82e7051fa01d002b92660a0ad4b1d40c`. Final predesktop qualification passed 319/319 non-desktop tests, strict gates, G04/G05/G06/G07 True-GTK regressions, G08 binding/hostile/startup-isolation lanes, incremental 1 MiB Preview responsiveness, topology, Cinnamon shortcut audit, hostile FIFO startup, G07-vs-G08 FIRST_EDITABLE startup delta, common FIRST_VISIBLE comparison, G06 startup self-regression, G05 Search performance, G06 View performance and G07 Statistics performance.

Candidate R1 consumed attempt 1/2 and was retired after a composite manual Test 6 FAIL. Failure-specific NON-CANDIDATE diagnosis on the unchanged product tree proved the product overlap/lifecycle behavior and localized the failure to an unowned human timing window. Candidate R2 therefore reused the same product tree and strengthened the validation oracle rather than changing runtime. R2 passed the full 20-lane automated matrix and manual Tests 1–5. Its initial Test 6 close check was an incomplete user procedure, not a product FAIL; the authorized manual reissue preserved the candidate and consumed no new attempt. The reissue passed responsiveness/Preview lifecycle and confirmed normal window close plus process exit. Final manual result: **6/6 PASS**. Candidate history remains 2/2 attempts used.

Publication preserves the certified runtime and user-facing implementation byte-for-byte. Only the three canonical authority documents, additive `G08_DESKTOP_CERTIFICATION_RECEIPT_20260820.txt` evidence and regenerated `evidence/SHA256SUMS.txt` differ from the certified tree. G08 becomes **CLOSED / CERTIFIED / PUBLISHED** only when the publication finalizer proves the target tree, commits, pushes, fetches, verifies `HEAD = origin/main = remote main`, and leaves the canonical worktree clean.

**Next serial item: G09 — Explicit Text Transformations Only / No Format-Menu Expansion.** G09 remains PENDING until a separate authorization and its own published-G08 read-only audit, mature-source review, Lightweight Budget check and contract freeze.

### G09 implementation checkpoint — 2026-08-20

The published-G08 source audit, direct mature-source audit, ADOPT/ADAPT/REJECT/DEFER matrix,
Lightweight Budget and contract freeze completed before implementation. G09 is now implemented in
an isolated copy as a NON-CANDIDATE: Edit -> Transform Text contains exactly Uppercase, Lowercase,
Duplicate Line / Selection, Move Lines Up, Move Lines Down and Trim Trailing Spaces. Move Lines
uses Alt+Up / Alt+Down; the other four commands have no default accelerator. No top-level Format
menu, GtkSourceView, background service, persistent transform settings or second mutation authority
was added.

The implementation reuses `NativeEditorController.apply_prevalidated_programmatic_group()` as the
sole mutation/Undo/rollback authority and adds one pure GTK-free planner. Build-host qualification is
35/35 focused and 354/354 full headless PASS. Desktop/True-GTK, Cinnamon collision, live canonical
Git and 1 MiB integrated action gates remain PRE-CANDIDATE work on the T480. Candidate attempts
remain 0/2 and Candidate R1 requires separate authorization only after that qualification passes.


### G09 closure / G10 handoff — 2026-08-21

G09 completed full T480 qualification on exact certified product tree
`92bcae4fcf72684872a9fa675007156bd0a4de3c`. PRE-CANDIDATE qualification PASSed before candidate
declaration. Candidate R1 then PASSed all 20 automated lanes. Manual Tests 1-4 PASSed in the original
run. The original Test 5 automatic disk postcondition PASSed, while the subsequent human FAIL was
classified after source-first/mature-source re-audit as an invalid manual-oracle false negative rather
than a product failure. A first manual-only reissue stopped before Graphium launch on a Bash harness
defect; the corrected reissue preserved the exact product tree, declared no R2, consumed no new
attempt and PASSed Tests 5-6. Composed manual result: **6/6 PASS**. Candidate-line accounting remains
**1/2 attempt used**, with no product FAIL.

The certified G09 surface is intentionally narrow: Edit -> Transform Text exposes Uppercase,
Lowercase, Duplicate Line / Selection, Move Lines Up, Move Lines Down and Trim Trailing Spaces;
Alt+Up/Alt+Down are the only new accelerators. G09 adds no top-level Format menu, GtkSourceView,
background work, persistent transform state, implicit Open/Save cleanup or second mutation/history
authority.

Publication preserves `graphium/`, `bin/`, `docs/user/`, `tests/` and `tools/` byte-for-byte from the
certified tree. Only the three canonical authority documents, additive
`G09_DESKTOP_CERTIFICATION_RECEIPT_20260821.txt` evidence and regenerated
`evidence/SHA256SUMS.txt` may differ. G09 becomes **CLOSED / CERTIFIED / PUBLISHED** only when the
publication finalizer proves the exact target tree, commits, pushes, fetches, verifies
`HEAD = origin/main = remote main`, and leaves the canonical worktree clean.

**Next serial item: G10 — Persistence Layer / Preferences Dialog without duplicating direct View
commands.** G10 remains PENDING until separate authorization plus a read-only audit of the published
G09 repository, direct mature-source review, explicit ADOPT / ADAPT / REJECT / DEFER matrix,
Lightweight Budget review and contract freeze. No G10 implementation is authorized by G09
publication.


GS07 VALIDATION REBASELINE (2026-08-21)
The active qualification architecture is permanent and concern-oriented: Behavioral/Unit, Integration/Filesystem, True-GTK Desktop, Packaging/Release. Historical Gxx qualification names and executable evidence/doc prose oracles are retired from active validation. G10 remains frozen until GS07 desktop rebaseline is proven on T480.

### GS07 structural validation cutover assessment — 2026-08-22

GS01-GS07 structural simplification has passed its formal T480 and anti-cosmetic assessment on
source tree `fc6673e35d4f47bbe74a9a6c0de3a3f44cca8c81`. Legacy G09 shadow equivalence, all four
permanent qualification authorities, deletion proof, authority/dependency reduction, no-shim,
packaging separation and product/release separation are PASS. Final mature-source comparison also
PASSes.

Status: **READY FOR CANONICAL CUTOVER, NOT YET CUT OVER**. G10 remains frozen at candidate 0/2 until
a separate GS07 canonical Git cutover transaction commits/pushes/verifies the rebaseline. Only after
that transaction passes may G10 resume from the simplified permanent qualification architecture.

### GS07 canonical cutover — 2026-08-22

GS07 is the canonical validation-architecture rebaseline after the authorized Git cutover succeeds.
The rebaseline preserves the G09 product behavior while replacing historical Gxx executable
validation with four permanent concern-oriented authorities and passing the binding net-reductive
structural gate. After cutover, **G10 is unfrozen with candidate attempts 0/2** and resumes from this
simplified qualification architecture. No retired Gxx harness or compatibility layer may be restored.


**G13 Candidate R1 certification — 2026-08-25.** The user explicitly authorized Candidate R1 from the exact Candidate-ready line. Candidate R1 is declared and certified on the frozen `0.0.13` source after exact local requalification: 173/173 Behavioral, 150/150 Integration and 13/13 Packaging/Release = 336/336 PASS, G13 focused 43/43 PASS and Structural Continuity PASS. The already completed S4 fresh-process T480 True-GTK recovery proof 4/4 is adopted: after that platform proof the only product-byte change is the source-proven version literal in `graphium/product.py`; recovery, lifecycle, GTK recovery, tests, launcher and user documentation remain unchanged. No new T480 or manual test is required. Candidate accounting is 1/2 used and 1/2 remaining. Publication remains separately unauthorized.


**G13 publication authorization — 2026-08-25.** After Candidate R1 certification, the user explicitly authorized continuation with G13. Publication must start from canonical post-G12-sync HEAD `f32beeeca58fdc4d68b7d9253ec98d2b76b38018` / tree `23c6dde1b69f36b71dcaa6eb0deb4b19f2370075`, preserve the certified Candidate product subtree `033ae482b19cf81a4852cf4e22773b2740387443`, tests subtree `b1911fdee492d9fea5655182913d9e63eb8c37ed`, launchers and user documentation byte-for-byte, and allow only the three canonical documents plus additive G13 certification evidence and regenerated evidence manifest to differ from Candidate R1. The finalizer must requalify 336/336 local authorities, prove Structural Continuity, commit/push/fetch, verify `HEAD=origin/main=remote main`, and leave the worktree CLEAN. No new T480/manual test is required; S4 True-GTK 4/4 remains binding. G14 remains Core / NOT OPENED.

**G13 publication closure + post-publication canonical convergence — 2026-08-25.** The authorized fail-closed finalizer published G13 commit `053bcde3f5bcb4f51ce9edd8a89538a7630949ae`, tree `eb6925d3b779fa8ae12d1d0947a31fe460fbee0e`, product subtree `033ae482b19cf81a4852cf4e22773b2740387443`, version `0.0.13`, with subject `G13: add crash recovery cache`. It proved 336/336 local authorities PASS, G13 focused 43/43 PASS, Structural Continuity PASS, S4 True-GTK 4/4 adopted, `HEAD=origin/main=remote main`, worktree CLEAN, no new T480 functional tests and no manual tests. The subsequent read-only audit found no product/test/platform blocker and only pre-finalizer canonical-state drift. This authorized convergence changes only the three canonical documents plus additive `evidence/G13_PUBLICATION_FINAL_RECEIPT_20260825.txt` and regenerated `evidence/SHA256SUMS.txt`; `graphium/`, `bin/`, `tests/` and `docs/user/` remain byte-identical to the published G13 product. G13 is CLOSED / CERTIFIED / PUBLISHED. G14 remains Core / NOT OPENED and requires a final post-sync read-only audit plus separate explicit opening authorization.


### G14-S2 — Spell session + Graphium edit authority — COMPLETE / NON-CANDIDATE

S2 is complete after explicit authorization. A GTK-free per-dialog spell session now owns request/issue
progress, exact-session Ignore/Ignore-All, stale state-id fencing and replacement planning. Replace delegates
exclusively to the existing `NativeEditorController.apply_prevalidated_programmatic_group()` authority, so
one changed correction is one normal Undo/Redo unit, a same-text correction is a no-op, representation
profile is preserved and no target-file write occurs before ordinary Save.

The future command identity is frozen centrally as `Document -> Check Spelling…` / `F2` but is not yet
projected into GTK; S3 remains responsible for menu/action/dialog/help wiring and worker-to-main-context
result dispatch. S2 passed 190/190 Behavioral, 167/167 Integration, 14/14 Packaging/Release = 371/371,
G14 focused unique 35/35 and Structural Continuity at 4764/1198 LOC without rebaseline. T480/manual/Git are
zero; Candidate is not declared and attempts are not opened.

**Next serial step:** G14-S3 — Thin GTK dialog / action / help — requires explicit authorization.

### G14-S3 — Thin GTK dialog / action / help — COMPLETE / NON-CANDIDATE (2026-08-25)

After explicit authorization, S3 projects the frozen spellcheck authority as **Document → Check Spelling…**
with **F2** and a minimal on-demand GTK dialog. The spell adapter is lazy-imported from the action, uses at
most one worker only after the first actual token request, keeps Hunspell I/O off the GTK main thread and
returns results through the GLib main context. Help/shortcut documentation now describes the capability.
No live/background spell engine, language preference, personal dictionary, autocorrect or grammar checker
is added. Candidate/Git/T480/manual remain unopened by S3.

**Next serial step:** G14-S4 — consolidated exact-byte qualification, Lightweight Budget and Candidate
readiness. It requires separate explicit authorization.


### G14 S4 closure / Candidate readiness — 2026-08-25

G14 S1-S3 is complete as NON-CANDIDATE implementation. S4 requalified the exact S3 bytes with
190/190 Behavioral, 167/167 Integration and 16/16 Packaging/Release = **373/373 PASS**, G14 focused
37/37 PASS and Structural Continuity PASS. The focused fresh-process T480 probe on exact source tree
`3c31e2072666b11e81b731fdb8532e950a37d12c` then passed **4/4** automated True-GTK scenarios and proved
clean startup creates no spell thread or Hunspell child. Manual tests remain zero.

The pre-Candidate source audit found only serial release-identity incompleteness: the S4 tree still reported
the already-published G13 version `0.0.13`. The NON-CANDIDATE Candidate-readiness consolidation advances
only `graphium/product.py` to **`0.0.14`** plus the three canonical authority documents. Spellcheck protocol,
controller, GTK adapter, all other product bytes, tests, launchers and user documentation remain identical
to the T480-proven S4 tree; no new T480/manual validation is required for the version-literal-only delta.

Status: **G14 CANDIDATE R1 AUTHORIZATION READY / NOT DECLARED / attempts 0/2**. Candidate declaration and
certification require separate explicit authorization. Publication is not authorized. Graphium Plus and
Graphium Ultra remain defined but not opened.

**G14 Candidate R1 certification — 2026-08-25.** The user explicitly authorized Candidate R1 from the exact Candidate-ready line. Candidate R1 is declared and certified on the frozen `0.0.14` source after exact local requalification: 190/190 Behavioral, 167/167 Integration and 16/16 Packaging/Release = 373/373 PASS, G14 focused 37/37 PASS, Structural Continuity PASS and Lightweight static PASS. The already completed S4 fresh-process T480 True-GTK spellcheck proof 4/4 and clean-startup no-spell-thread/child runtime proof are adopted: after that platform proof the only product-byte change is the source-proven version literal in `graphium/product.py`; spellcheck protocol/session/controller/GTK bytes, tests, launcher and user documentation remain unchanged. No new T480 or manual test is required. Candidate accounting is 1/2 used and 1/2 remaining. Publication remains separately unauthorized.



### 24.3 G14 Candidate R1 publication authorization

G14 Candidate R1 is certified on exact source tree `0d629e31762836e3fe7574e8f1fd16e0166b336e`, product
subtree `396be05aaa0cc32e18341889e5494163151f4606`, version `0.0.14`. Candidate qualification is
190 Behavioral + 167 Integration + 16 Packaging/Release = 373/373 PASS, G14 focused 37/37 PASS,
Structural Continuity PASS and Lightweight static PASS. The binding S4 platform proof is True-GTK 4/4
plus `PASS_NO_STARTUP_SPELL_THREAD_OR_CHILD`; manual tests are 0. Candidate accounting is 1/2 used and
1/2 remaining.

The user explicitly authorized the separate fail-closed publication transaction. It starts only from
canonical HEAD `8a847a793b9d84f76161c41cce261dd82b3deb17` / tree
`65318ce6847304ccbcce31767311857fb42798f3`, applies the exact certified G14 line, preserves the Candidate
product/tests/launchers/user-doc bytes, allows only the three canonical documents plus additive G14
certification evidence and regenerated evidence manifest to differ from Candidate, and commits with subject
`G14: add external spellcheck`. No new T480/manual test is required. Graphium Plus and Ultra remain unopened.

G14 remains **CANDIDATE R1 CERTIFIED / PUBLICATION AUTHORIZED / FINALIZER REQUIRED** until the finalizer
actually succeeds and remote synchronization is proved. A post-publication read-only audit remains mandatory
before Core closure is considered canonically converged or any Plus work is opened.


### G14 / Graphium Core publication closure + post-publication canonical convergence — 2026-08-25

The authorized G14 finalizer published commit `51fc8f329be730a237f28e195fb1617de07a93d8`, tree `b0469a014a2451cfd2fa92a942583eeab02d25e1`, product subtree
`396be05aaa0cc32e18341889e5494163151f4606`, version `0.0.14`, with subject `G14: add external spellcheck`. Publication preserved
the certified Candidate product/tests/launchers/user-documentation bytes, requalified 373/373 permanent
local authorities and G14 focused 37/37, proved Structural Continuity and Lightweight static, adopted the
S4 True-GTK 4/4 plus clean-startup no-spell-thread/child runtime proof, synchronized
`HEAD=origin/main=remote main`, and finished with a CLEAN worktree. No new T480 functional or manual test
was required. Candidate attempt accounting remains 1/2 used and 1/2 unused historically.

The mandatory post-publication read-only audit found no product/test/platform/Lightweight Budget failure and
only canonical pre-finalizer state drift. This authorized five-path document/evidence-only convergence records
the final publication commit/tree/status, preserves all historical pre-publication evidence, adds an immutable
final G14 publication receipt and leaves `graphium/`, `bin/`, `tests/` and `docs/user/` byte-identical to
the published product. **G14 is CLOSED / CERTIFIED / PUBLISHED. Graphium Core is FEATURE-COMPLETE / CLOSED /
CERTIFIED / PUBLISHED.**

**Graphium Plus:** **DEFINED / AUTHORIZATION-READY AFTER FINAL POST-SYNC READ-ONLY AUDIT / NOT OPENED**.
Plus remains Core + compact native icon toolbar + Writing Workspace adapted from Calamus. No Plus source,
entrypoint, toolbar or Workspace implementation is authorized by this convergence.

**Graphium Ultra:** **DEFINED / NOT OPENED**. Ultra remains Plus + Markdown viewer/editor and requires a later
separate authorization after Plus governance.

**Next step:** final post-G14-sync read-only audit. Only after that PASS may Graphium Plus be formally opened
by a separate explicit user authorization.

### G15 — Core Corrective Maintenance — OPEN / NON-CANDIDATE (2026-08-26)

After final G14/Core publication, user review identified a bounded set of Core correctness/usability debts.
Graphium Plus is therefore deferred: G15 is a Core corrective line and does not open the Plus toolbar or
Writing Workspace. The approved serial slices are:

1. **G15-S1 Application Icon Identity** — proprietary Graphium application icon for launcher/window/About,
   using the stable application ID and standard hicolor installation.
2. **G15-S2 Tab Controls Simplification** — remove the undersized Preferences surface and expose Tab Width
   plus Insert Spaces directly.
3. **G15-S3 Hunspell Dictionary Selection** — choose among actually installed Hunspell dictionaries while
   retaining System default; no GUI-language selector and no i18n subsystem is introduced.
4. **G15-S4 Transform Text Shortcuts** — add Uppercase/Lowercase accelerators only after GTK/Cinnamon
   keyboard-namespace audit, and document them in Help.
5. **G15-S5 Help / About / Legal Closure** — User Guide wording and Latin-name note; About icon, author,
   copyright and GPL-3.0-or-later; existing private repository URL remains unchanged.
6. **G15-S6 Integral Regression / Structural Audit** — prove the corrective line remains lightweight and
   does not create duplicate authorities.

Candidate remains separately gated and requires explicit authorization after all NON-CANDIDATE slices.
Version remains `0.0.14` during the implementation slices; release identity may advance only during a later
Candidate-readiness consolidation.

#### G15-S1 — Application Icon Identity

Direct-source comparison with Leafpad/L3afpad, Mousepad, gedit/GNOME Text Editor and FeatherPad selected a
single identity name: `io.github.leviagravia.Graphium`. The user-supplied icon is retained as exact SVG
artwork in hand-tuned 16/24/32/48 sizes plus one scalable authority. The `.desktop` entry uses the stable
icon name, the installer projects the five assets into the standard hicolor hierarchy, and source execution
uses those same repo-local files as a process-local fallback without a GResource/branding framework.
64/128/256/512 duplicate SVGs are intentionally not carried. Toolbar/action icons remain out of scope.

G15-S1 is **NON-CANDIDATE TRUE-GTK PASS / CLOSED**. Local qualification passed and the focused T480 proof
verified hicolor lookup, source default-icon resolution and a real Graphium window under the single application
icon authority. Source/package identity remained unchanged; manual tests were 0, Candidate remained NO and no
attempt or Git mutation was consumed.


#### G15-S2 — Tab Controls Simplification — NON-CANDIDATE TRUE-GTK PASS / CLOSED

The mandatory direct-source audit was completed before implementation. G15-S2 removes the generic
`Edit -> Preferences…` surface and reuses the existing settings authority through direct `Edit -> Tab Width`
(2/3/4/8/Other…) and checked `Edit -> Insert Spaces Instead of Tabs` actions. Other… preserves the full
1..32 domain with a narrow chooser. No config migration or new runtime authority/dependency/module was added.
The three changed runtime files are net -8 lines relative to G15-S1. Focused RED->GREEN gates and the
post-audit full selftest pass 190/190 Behavioral, 167/167 Integration and 27/27 Packaging/Release. The focused
T480 True-GTK probe passed real Edit-menu topology, direct action state, fixed/custom widths, Cancel neutrality,
persistence rollback and fresh-window persisted projection. Source/package identity remained unchanged; manual
tests were 0, Candidate remained NO and no attempt or Git mutation was consumed.

#### G15-S3 — Hunspell Dictionary Selection — NON-CANDIDATE TRUE-GTK PASS / CLOSED

After the mandatory direct-source audit of Mousepad, gedit, GNOME Text Editor, FeatherPad, Leafpad/L3afpad
and Hunspell CLI authority, G15-S3 keeps the existing explicit external Hunspell architecture. The spelling
dialog owns a Dictionary combo with System default plus verified installed Hunspell base dictionaries.
Discovery is on-demand via bounded `hunspell -D` under `LC_ALL=C`; only real `.aff` + `.dic` pairs are accepted.
Explicit selection uses one `-d <base>` argv pair. Selection is dialog-local, non-persistent and restarts the
current pass safely after fencing stale callbacks and reaping the old child. No GUI-language selector, spell
preference, document metadata, new module/framework/dependency or startup probe is added.

Local qualification passed 190/190 Behavioral, 176/176 Integration and 27/27 Packaging/Release = 393/393.
The focused T480 True-GTK proof then discovered the real installed dictionaries `en_US`, `it_CH`, `it_IT` and
passed real combo enumeration, explicit dictionary switch/restart with Ignore All reset, process cleanup,
document neutrality and external-edit stale fencing. Source/package identity remained unchanged; manual tests
were 0, Candidate remained NO and no attempt or Git mutation was consumed.

#### G15-S4 — Transform Text Shortcuts — NON-CANDIDATE TRUE-GTK PASS / CLOSED

Mandatory mature-source comparison plus a read-only T480 GTK/Cinnamon namespace audit froze the exact pair
`Ctrl+U` = Uppercase and `Ctrl+Shift+L` = Lowercase. `Ctrl+Shift+U` is permanently rejected because GTK3 owns
that sequence for Unicode code-point input; `Ctrl+Alt+L` is rejected because Cinnamon owns it for lock screen.
The T480 audit proved both selected bindings valid and free of Graphium, Gtk.TextView and active Cinnamon
collisions on the Italian XKB layout.

Implementation changes only the existing command accelerator authority and Help projection; text-transform
semantics, selection requirements, history and document ownership remain unchanged. No module, dependency,
settings key, persistence or keyboard manager is added. Local qualification passed 190/190 Behavioral,
176/176 Integration and 29/29 Packaging/Release = 395/395. The focused T480 True-GTK proof then passed 43/43
focused gates, real GTK accelerator routing and transform behavior with history/savepoint and selection-only
semantics unchanged. Source/package identity remained unchanged; manual tests were 0, Candidate remained NO
and no attempt or Git mutation was consumed.

#### G15-S5 — Help / About / Legal Closure — NON-CANDIDATE TRUE-GTK PASS / CLOSED

Mandatory source-first comparison selected the standard mature-editor pattern: one repository license authority
plus standard About metadata. Graphium now has one top-level `LICENSE` with an explicit GPL-3.0-or-later project
grant followed by the byte-exact GNU GPLv3 body from the mature local corpus. Product metadata records author,
copyright, SPDX license identity and the unchanged private repository URL/label. `Gtk.AboutDialog` projects
those values using its standard authors/copyright/license/website fields, retains Python/GTK/display support
information and reuses the G15-S1 default application/window icon instead of creating an About-specific logo.

The installer projects exactly one LICENSE copy into the private installed root. The User Guide intro is
reflowed as one natural paragraph and ends with the approved one-sentence Latin `graphium` explanation. Help
topology remains User Guide / Keyboard Shortcuts / About and G15-S4 shortcut documentation stays unchanged.
Focused RED->GREEN gates pass; permanent local qualification passes 190/190 Behavioral, 176/176 Integration
and 40/40 Packaging/Release = 406/406. No module/dependency/config/thread/subprocess/network/custom legal UI
was added. Version remained 0.0.14 throughout the NON-CANDIDATE implementation slices. The focused automated T480 True-GTK About proof subsequently passed installed LICENSE projection, standard About metadata, GPL-3.0-or-later, repository retention, system information and reuse of the G15-S1 application icon authority with source/package identity unchanged. Manual tests were 0, Candidate remained NO and no attempt or Git mutation was consumed.



#### G15-S6 — Integral Regression / Structural Audit — PASS / NO PRODUCT DELTA

S6 introduced no product or test behavior. Exact cumulative S1-S5 source was compared with the exact G14
handover baseline and the mature corpus. Structural gates passed 34/34. Runtime modules remain 57 -> 57,
new import roots/dependencies are 0, only 7/57 runtime modules differ from G14, and the cumulative runtime
delta is +274 LOC (+2.43%), of which +248 is confined to the two pre-existing spelling owners. The S3 growth
was reclassified as essential external-process safety rather than accidental complexity. Integral permanent
qualification on the exact cumulative source passed 190/190 Behavioral, 176/176 Integration and 40/40
Packaging/Release = 406/406. No new T480/manual run was justified because S6 has no product delta and each
S1-S5 changed platform property already has focused True-GTK proof.

#### G15 Candidate-readiness / exact freeze — PASS / CANDIDATE R1 AUTHORIZATION READY

All NON-CANDIDATE slices S1-S6 are complete. The only product-byte change after the final S5 True-GTK proof
is the serial release-identity literal `graphium/product.py`: published G14 `0.0.14` -> unpublished G15
`0.0.15`. The S1-S5 feature implementation bytes, launchers and user documentation remain unchanged from
the exact S5 T480-proven source; only release-identity/test expectation plus canonical/evidence convergence
are added by readiness. No new T480/manual execution establishes a new product property for this identity-only
delta.

Status: **G15 CANDIDATE R1 AUTHORIZATION READY / NOT DECLARED / attempts 0/2**. Candidate declaration and
certification require separate explicit user authorization. Publication is not authorized. Graphium Plus
remains NOT OPENED.

#### G15 Candidate R1 certification / publication authorization — 2026-08-26

G15 Candidate R1 is declared and certified on the frozen `0.0.15` source tree
`42884dfbd4c5abd725d928bcb76e1064dbec23b7`, with product subtree
`1f63eca6724b379abab8e8d534667723e57276f6`, tests `875cae3f501fd566b49ee25b5bf613f72cedb1d7` and
user docs `8f5d3ef7dbe936eab18c2ed8447a487a6fe337df`. Exact Candidate qualification is 190/190 Behavioral,
176/176 Integration and 40/40 Packaging/Release = **406/406 PASS**, structural gates **34/34 PASS**, and the
focused S1-S5 T480 True-GTK proofs are adopted. Manual tests are 0. Candidate attempt 1/2 is consumed; 1/2
remains.

The separate publication-readiness audit passed and the user explicitly authorized publication. The fail-closed
publication transaction must preserve all Candidate product/test/user-doc/bin/data/LICENSE bytes and may alter
only the three canonical documents, additive `evidence/G15_DESKTOP_CERTIFICATION_RECEIPT_20260826.txt`, and
`evidence/SHA256SUMS.txt`. It starts only from canonical post-G14-sync HEAD
`cd685ecf060a57e5239f641e9e30dd7a7b8144e5`, tree `8cfe2c194829e3d59487b2f596129c36cfe1856f`,
with commit subject **`G15: complete core corrective maintenance`**. No new T480/manual test is required for
publication. G15 is **CANDIDATE R1 CERTIFIED / PUBLICATION AUTHORIZED / FINALIZER REQUIRED** until the
transaction actually completes. Graphium Plus remains **NOT OPENED**.


### G15 publication closure + post-publication canonical convergence — 2026-08-26

The authorized fail-closed G15 finalizer published commit `16b645ed653be5b44efa8721db11cca63f0633bd`, tree `e433758d1d68ef5bea6528e15e65d786e0679d31`, product subtree
`1f63eca6724b379abab8e8d534667723e57276f6`, version `0.0.15`, with subject `G15: complete core corrective maintenance`. Publication preserved
the certified Candidate product/tests/launcher/user-document/data/LICENSE bytes, requalified 406/406 permanent
local authorities plus 34/34 G15 structural gates, adopted all focused S1-S5 T480 True-GTK proofs, synchronized
`HEAD=origin/main=remote main`, and finished with a CLEAN worktree. No new T480 functional or manual test was
required. Candidate attempt accounting remains 1/2 used and 1/2 unused historically.

The mandatory post-publication read-only audit found no product/test/platform/structural/packaging failure and
only the expected pre-finalizer canonical-state drift. This authorized five-path document/evidence-only
convergence records the final publication facts, preserves all historical pre-publication evidence, adds an
immutable G15 publication receipt and leaves `graphium/`, `bin/`, `tests/`, `docs/user/`, `data/` and `LICENSE`
byte/mode-identical to the published product. **G15 and Graphium Core 0.0.15 are CLOSED / CERTIFIED / PUBLISHED.**

**Graphium Plus:** **DEFINED / NOT OPENED**. No Plus source, entrypoint, toolbar or Workspace implementation is
authorized by this convergence.

**Graphium Ultra:** **DEFINED / NOT OPENED**.

### G16 — About Icon Corrective Closure — NON-CANDIDATE TRUE-GTK PASS / CLOSED

A real post-G15 user screenshot exposed a narrow About-logo product/oracle gap: GtkAboutDialog displayed the
GTK missing-image placeholder rather than Graphium's icon. Mandatory source-first comparison with Mousepad,
Leafpad/L3afpad, GNOME Text Editor and FeatherPad confirmed explicit About application-icon projection as the
mature pattern. GTK3 `logo-icon-name` defaults to `image-missing`, so the G15-S5 implicit inheritance assumption
and its non-null-16x16 pixbuf oracle are superseded.

G16 is deliberately corrective and confined. The existing About owner explicitly uses the existing
`APPLICATION_ICON_NAME` when the icon theme resolves it and otherwise reuses the existing Graphium default
window-icon list, selecting the exact 48x48 hand-tuned pixbuf for source runs. No new icon asset, path,
authority, module, dependency, GResource, config, thread or subprocess is introduced. Local permanent
qualification passes 190/190 Behavioral + 176/176 Integration + 45/45 Release = **411/411 PASS**. Version remains
0.0.15 while NON-CANDIDATE. Candidate remains NO, attempt consumed NO, Git mutation NO. The focused automated True-GTK source-run + staged-install identity probe passed exact Graphium logo identity, rejected image-missing, preserved source/package identity and required 0 manual tests.


### G16 pre-Candidate blockers — NON-CANDIDATE TRUE-GTK PASS / CLOSED

The About-icon correction is NON-CANDIDATE True-GTK PASS. Candidate-readiness remains blocked by two later user-visible defects: Light appearance left the custom line-number gutter dark, and real installed Hunspell/it_IT exposed a multi-record `hunspell -a` response group that the one-record parser rejected while the UI incorrectly suggested installing Hunspell. Mandatory mature/authoritative comparison is complete and the corrective contract is frozen.

The NON-CANDIDATE repair preserves the existing Gtk.TextView LEFT border-window and paints it from the same style context before glyphs; it adds no gutter palette authority. The Hunspell boundary now consumes a bounded complete response group, preserves single-record behavior, aggregates multi-record groups conservatively, retains timeout/cancel/reap/stale fencing and separates installation absence from protocol/timeout/runtime errors. No tokenizer or dependency migration is allowed. Local qualification is **421/421 PASS** (190 Behavioral, 181 Integration, 50 Release); runtime modules remain 57. Version remains 0.0.15 and Candidate remains NO. Focused real-GTK gutter + real-it_IT Hunspell validation passed on the T480 with source/package identity unchanged and 0 manual tests.


### G16 Candidate-readiness / exact freeze — PASS / CANDIDATE R1 AUTHORIZATION READY

All G16 NON-CANDIDATE corrective properties are now closed. About icon identity, Light/Dark/System line-number gutter rendering and real installed `hunspell`/`it_IT` multi-record response handling all have focused T480 True-GTK proof with source/package identity unchanged and **0 manual tests**. Permanent local qualification on the exact cumulative implementation is 190/190 Behavioral + 181/181 Integration + 50/50 Packaging/Release = **421/421 PASS**.

Candidate readiness advances only the serial release identity from published `0.0.15` to unpublished `0.0.16`, plus the corresponding release-oracle expectation and canonical/evidence convergence. No feature implementation byte is changed after the final T480 proof. Candidate R1 is **NOT DECLARED**; attempts remain **0/2**. Canonical Git mutation and publication remain unauthorized. Graphium Plus remains **DEFINED / NOT OPENED**.


#### G16 About Credits Light corrective — LOCAL PASS / TRUE-GTK PENDING

User desktop validation of the pre-Candidate 0.0.16 `.deb` produced 4/5 PASS and one product FAIL: the standard `GtkAboutDialog` Credits viewport remained dark under explicit Light appearance. Source-first comparison confirmed that Graphium's single application CSS provider, not the dialog layer, must own this background. The RED->GREEN repair changes only `graphium/adapters/gtk/appearance.py`, extending the existing Light/Dark editor-family rule to `dialog viewport.view`; no custom Credits dialog, second CSS provider, new palette authority, dependency, module or config is added. Focused release gates pass 4/4, Behavioral 190/190 and Release 54/54; the integration tree and Hunspell owners are byte-identical to the previously qualified G16 source. Candidate-readiness remains blocked until one focused True-GTK Credits Light/Dark/System proof passes. Candidate=NO, attempts=0/2, Git mutation=NO.

#### G16 final pre-Candidate closure — TRUE-GTK PASS / CANDIDATE READINESS RESTORED

The post-readiness manual Credits Light failure is repaired without expanding architecture: only the existing appearance authority projects the standard GtkAboutDialog `viewport.view`. The single authorized harness reissue passed real source and staged-installed GtkAboutDialog Credits in System/Light/Dark with contrast checks, black-panel rejection, System restoration and About-logo regression. The initial stopped run was INVALID HARNESS before product execution and consumed no attempt. All G16 corrective properties are now NON-CANDIDATE closed. Candidate R1 remains **NOT DECLARED**, attempts **0/2**, Git mutation **NO**.

### G16 Candidate R1 certification / publication authorization — 2026-08-27

G16 Candidate R1 is **DECLARED_AND_CERTIFIED** on the exact 0.0.16 source tree `48ef29541e1068cb890c305c4ddfa57aab7310bd`, product subtree `e09d45ec07aad4956c0edead777cb61588eb758a`. Final desktop verification is PASS; known user-visible G16 defects open = 0. Attempt accounting: 1/2 used, 1/2 remaining.

Publication is now explicitly authorized but not yet complete. The fail-closed finalizer may change exactly five Candidate-relative paths: the three canonical documents, additive `evidence/G16_DESKTOP_CERTIFICATION_RECEIPT_20260827.txt`, and regenerated `evidence/SHA256SUMS.txt`. Commit subject: **`G16: finalize core corrective release`**. No product/test/user-doc/bin/data/LICENSE byte may change and no new T480/manual test is required for publication.

Status: **G16 CANDIDATE R1 CERTIFIED / PUBLICATION AUTHORIZED / FINALIZER REQUIRED**. Graphium Core is not definitively closed until publication and post-publication canonical convergence both PASS. Graphium Plus and Ultra remain **DEFINED / NOT OPENED**.



### G16 publication closure + post-publication canonical convergence — 2026-08-27

The authorized G16 fail-closed publication finalizer harness reissue published commit
`b4b447423de8eb6f6d4022639497ca1f6b3daca6`, tree `90c651815400851ebcc0ff5300b2807261fb33fe`, product subtree
`e09d45ec07aad4956c0edead777cb61588eb758a`, version `0.0.16`, with subject
`G16: finalize core corrective release`. Publication preserved all certified Candidate product/test/user-doc/bin/
data/LICENSE bytes, passed 190/190 Behavioral and 54/54 Packaging/Release, adopted the binding 181/181
Integration authority on byte-identical owners, preserved the complete G16 True-GTK evidence chain and final
user desktop validation, synchronized `HEAD=origin/main=remote main`, and finished CLEAN with zero known
user-visible G16 defects. Candidate accounting remains 1/2 used and 1/2 unused historically.

The earlier stopped publication-finalizer run was harness-only and pre-mutation; it is not a product/Candidate
failure. The authorized reissue changed only the runner and completed publication on the unchanged target.

This five-path post-publication document/evidence convergence records the final publication facts and leaves the
published product bytes untouched. **G16 and Graphium Core 0.0.16 are CLOSED / CERTIFIED / PUBLISHED /
CANONICALLY CONVERGED.**

**Immediate next activity:** Graphium's GitHub public surface and release preparation. Before making the
repository public, perform the mandatory full-history read-only hygiene audit, then install the final README/logo,
repository description/topics, release metadata and certified `.deb` artifact. This is distribution/publication
work, not a new Graphium Core feature line.

**Graphium Plus:** **DEFINED / NOT OPENED**. Opening Plus requires a new explicit authorization and a fresh
source-first mature-editor audit under the Plus contract.

**Graphium Ultra:** **DEFINED / NOT OPENED**.

### Graphium Plus 0.0.1 — Candidate R2 CERTIFIED / PUBLICATION AUTHORIZED — 2026-08-28

Plus S0-S9 and the bounded post-R1 usability closure are complete. The certified 0.0.1 product consists of
Graphium Core plus the compact native toolbar and bounded local Workspace. Final user desktop validation is PASS;
Candidate R2 installed projection/smoke is PASS; known open product blockers = 0. Candidate accounting is 2/2
used, 0/2 remaining.

The authorized publication is the first commit in the separate `graphium-plus` product line after exact public
Core lineage commit `8899c94006757c066c88739ff84bf8e1a6cb1b35`. The first GitHub remote state is intentionally
PRIVATE. After product publication PASS, perform a separate GitHub public-surface closure: install an accurate
Graphium Plus README, expose the red Plus icon as primary identity, retain the original Graphium icon only in a
small "Built on Graphium Core" lineage section, set description/topics, create the Plus `v0.0.1` release when its
release artifact is frozen, verify anonymous endpoints, and only then make the repository PUBLIC.

Graphium Ultra remains DEFINED / NOT OPENED and requires separate explicit authorization after Plus publication
and public-surface closure.

