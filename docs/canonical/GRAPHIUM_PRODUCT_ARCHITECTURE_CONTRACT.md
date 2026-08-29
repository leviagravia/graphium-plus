# Graphium — Product & Architecture Contract

Canonical document 1 of 3.
Initial freeze: 2026-08-13 — G00.
Current publication boundary: **G16 / Graphium Core CLOSED / CERTIFIED / PUBLISHED** at commit `b4b447423de8eb6f6d4022639497ca1f6b3daca6`, tree `90c651815400851ebcc0ff5300b2807261fb33fe`, product subtree `e09d45ec07aad4956c0edead777cb61588eb758a`, product version `0.0.16`. The authorized fail-closed publication finalizer qualified 190/190 Behavioral and 54/54 Packaging/Release, adopted the binding 181/181 Integration authority on byte-identical owners, preserved the complete G16 True-GTK platform evidence chain and final desktop validation, and proved `HEAD=origin/main=remote main` with a CLEAN worktree. Candidate R1 consumed attempt 1/2; the unused 1/2 remains historical and G16 is not reopened. This document/evidence-only post-publication convergence may advance repository HEAD but does not replace the authoritative G16/Core product publication commit/tree above. Graphium Plus is **DEFINED / NOT OPENED**; Graphium Ultra is **DEFINED / NOT OPENED**.
G12 / Graphium v1 remains CLOSED / CERTIFIED / PUBLISHED at commit `cb71d9575f7c347fd10334cd7ddb54e5c921ea34`, tree `4e4651b9323c080716bfb28340fa274bd48c0017`, product subtree `1eb5c018574d330907d7f0cab0353074e7b37fe6`; later governance-only commits do not replace that product publication identity.

## 1. Product identity

Graphium is a native Linux desktop text editor derived by selective, provenance-recorded extraction from the published Calamus W116 baseline. Graphium is an **independent product**, not a Calamus edition and not a feature-flag profile of the Calamus source tree.

Graphium v1 is:

- GTK native;
- **single-document**;
- general-purpose plain-text editing first;
- filesystem-first: the edited file is the source of truth;
- local/offline;
- deliberately small in UI surface but strong in file safety.

Graphium v1 is not a knowledge base, academic editor, IDE, project manager or multi-document session host.

## 2. Technology freeze

G00 selects:

- implementation language: **Python 3**;
- desktop toolkit: **PyGObject + GTK 3**;
- editor widget baseline: **Gtk.TextView** inside Gtk.ScrolledWindow;
- typography/printing: Pango + PangoCairo where required;
- filesystem implementation baseline: Python standard library, with Gio allowed only behind an adapter when a desktop-native facility such as live file monitoring requires it;
- tests: Python `unittest` plus source/static boundary gates;
- data encoding inside the program: Unicode Python strings, with file encoding/BOM/EOL represented explicitly by the document-safety domain;
- no GtkSourceView dependency is required by v1.

Rationale: this maximizes reuse of the W116 safety/editor/print work, keeps deployment compatible with the Calamus technology family, and avoids adding a dependency merely to obtain features Graphium can already provide itself.

## 3. Layer boundary

Target package layout:

```text
graphium/
  domain/          # pure product/domain rules; no gi
  application/     # use cases, ports, controllers; no gi
  adapters/
    gtk/           # only location permitted to import gi/GTK directly
  infrastructure/  # pure filesystem/settings implementations where possible; no GTK
  composition.py   # GTK-free composition descriptor/root policy
```

The direct `gi` / GTK dependency boundary is **`graphium.adapters.gtk`**.

Rules:

1. `domain` must not import application, adapters, infrastructure or composition.
2. `application` may import domain but must not import adapters.
3. `infrastructure` must not own product state or document identity.
4. GTK adapters implement ports and translate toolkit events; they do not own business semantics.
5. Composition is explicit. No service locator, global application state bag or plugin registry.
6. Runtime Graphium source must not import Calamus modules. Reuse is one-time extraction with provenance, then Graphium evolves independently.

## 4. Authority model

Graphium v1 has exactly **one active document authority**.

The document session owns the accepted binding and saved-state identity. UI widgets are projections/adapters, not a second document model.

Graphium v1 has exactly **one physical writer authority** for normal persisted document writes. Save, Save As and copy/version operations must converge on the appropriate guarded writer contract rather than inventing parallel write paths.

The live file monitor is observation-only. Gio events are interrupts, never accepted truth. Fresh strong observation remains the sole external-file classifier input; the monitor may report changed/deleted/replaced states but may not become a second file identity, automatic reload authority, accepted-baseline authority or automatic overwrite authority.

## 5. XDG isolation

Graphium owns independent XDG locations:

```text
$XDG_CONFIG_HOME/graphium   (fallback ~/.config/graphium)
$XDG_DATA_HOME/graphium     (fallback ~/.local/share/graphium)
$XDG_CACHE_HOME/graphium    (fallback ~/.cache/graphium)
$XDG_STATE_HOME/graphium    (fallback ~/.local/state/graphium)
```

Graphium must never read or mutate Calamus configuration merely because source logic originated there.

The desktop application ID is **DEFERRED in G00** until repository/packaging identity is explicitly frozen. It must not be guessed.

## 6. W116 extraction policy

ADOPT selective extraction from the certified Calamus W116 commit `33331672f5ba8fcc6a7e1ede9ab849638579f0c7`, tree `db11fee424273c0a383145c132b645c15581b30a`.

High-value source families reserved for later work items:

- document identity / loader / serializer;
- document save / guarded writer;
- document session / savepoint state;
- Save a Copy / Save Version Copy;
- history / editor transaction;
- search model;
- selected navigation and text-transform primitives;
- line numbers, typography, view preferences;
- print runtime.

REJECT:

- copying `bin/calamus`;
- copying Calamus application composition wholesale;
- a shared `calamus-core` runtime library;
- conditional editions or feature flags inside Calamus;
- runtime imports from Graphium back into Calamus.

Each imported component must receive Graphium naming, Graphium tests and explicit provenance.

## 7. V1 functional boundary

MUST families:

- New / Open / Recent;
- Save / Save As / Save a Copy / Save Version Copy;
- Properties;
- Page Setup / Print Preview / Print;
- Undo / Redo and clipboard basics;
- Find / Replace / Find Next / Find Previous;
- Go to Line;
- Word Wrap / Line Numbers / Font / Zoom / Status Bar;
- selected basic text transformations;
- persistent essential preferences and System/Light/Dark appearance;
- explicit Saved/Modified state;
- encoding/BOM/EOL visibility and bounded explicit representation conversion;
- save-time and live external-file safety;
- User Guide / Keyboard Shortcuts / About.

SHOULD:

- drag-and-drop file open;
- window geometry restore;
- offline spellcheck after core v1 if it remains low-risk.

OUT OF V1:

- tabs or multiple documents in one window;
- split editor;
- projects/workspaces and file-browser panels;
- Markdown preview or outline/navigator;
- Research, Bibliography, References, Source Notes;
- Scratchpad, Clips, Tags, backlinks or knowledge graph;
- rich text/WYSIWYG;
- plugin system, macros, terminal, Git, LSP, debugger;
- cloud, collaboration, embedded browser or AI;
- autosave/recovery until separately designed and audited.

## 8. Canonical-document policy

**MAXIMUM CANONICAL DOCUMENTS: 3.** This is a permanent Graphium project constraint.

The complete canonical set is:

1. `GRAPHIUM_PRODUCT_ARCHITECTURE_CONTRACT.md` — product, technology, architecture and frozen boundaries.
2. `GRAPHIUM_ROADMAP.md` — serial Gxx work-item routing and current status.
3. `GRAPHIUM_MEMORIA_OPERATIVA.txt` — append-only operational history, evidence summary and decisions.

No Gxx may create a fourth canonical document. A work item updates one or more of these three instead.

Test logs, SHA manifests, provenance maps, release receipts, generated inventories, desktop-run logs and the end-user User Guide are **non-canonical evidence/product material**. They may support a decision but cannot override these three authorities.

## 9. Method

- Gxx work items are serial.
- A later Gxx does not begin as implementation until the preceding item reaches its required closure state.
- For the current Gxx, the assistant performs source audit, falsification-oriented mature-source comparison, implementation, complete non-desktop tests, strict gates, source bundle and incremental MO update autonomously.
- Headless/domain logic is implemented and tested before GTK wiring where feasible; GTK adapters remain thin.
- The user is asked only for the final desktop validation after the candidate has passed the preceding automated gates. That validation uses an isolated Graphium copy, never Calamus or the installed user configuration.
- Graphium does not progress by numbered trial-and-error candidate attempts. A pre-product harness/oracle stop or product defect is localized and re-audited against relevant mature sources; the whole discovered failure/design class is repaired and fully revalidated before another final desktop validation is requested.
- Failures are classified before repair; harness/oracle failures are not silently converted into product failures.
- Git publication is a separate explicit operation on the user's machine. Only the user executes Git-mutating stage/commit/push commands on the T480.

## 10. G00 closure conditions

G00 may close without a desktop run because it implements no product feature and no GTK shell. It must instead prove:

- Graphium identity is independent from Calamus;
- XDG paths are independent;
- package boundaries exist;
- core source has no Calamus runtime imports;
- GTK import boundary is mechanically enforced;
- the canonical-document cap is mechanically enforced;
- the roadmap and MO identify G00 and the next work item.

## 11. G01 — Document Identity / Load / Serialize Foundation

Freeze: 2026-08-14.

`G01_CONTRACT=FROZEN`
`G01_SCOPE=DOCUMENT_IDENTITY_LOAD_SERIALIZE_FOUNDATION`
`G01_GTK_REQUIRED=NO`
`G01_SECOND_DOCUMENT_AUTHORITY=FORBIDDEN`
`G01_PHYSICAL_WRITER_IMPLEMENTATION=DEFERRED_TO_G03`

### 11.1 Ownership and layer placement

G01 introduces no document session and no physical writer. It freezes only immutable
accepted-load values, stable local-file loading, and pure byte serialization policy.

- `graphium.domain.document_identity` owns immutable identity/load metadata values and typed load failures.
- `graphium.domain.document_serialization` owns pure representation profiles and byte serialization.
- `graphium.infrastructure.document_loader` owns local filesystem observation/read operations and returns domain values.
- no G01 module may import `gi`/GTK;
- G01 does not instantiate a second active-document authority.

The future G02 `DocumentSession` will own one accepted `DocumentFileState`. G01 merely defines the value that G02 may accept atomically. The future G03 guarded writer will be the one physical writer authority and will consume G01 serialization rather than creating a second codec/EOL model.

### 11.2 File visit contract

Graphium G01 visits **regular local files** only. The visit rule is extension-neutral: Graphium does not require `.txt`, `.md` or another filename suffix in order to recognize a document.

The stable loader:

1. preserves an absolute normalized logical path without replacing it by `realpath`;
2. opens bytes and requires a regular-file target;
3. observes descriptor identity before and after the read;
4. rejects torn/unstable reads after one retry by default;
5. preserves canonical path and `(device, inode)` separately from the logical path;
6. records exact accepted raw-byte SHA-256 as equivalence evidence, never as filesystem identity;
7. records size, mtime-ns, mode and read-only mode observation;
8. derives encoding/BOM/EOL metadata before newline normalization;
9. returns editor text LF-normalized;
10. rejects decoded NUL content as outside Graphium's plain-text scope.

FIFO/socket/device visiting and remote URI semantics are outside G01.

### 11.3 Codec policy

- BOM-aware UTF-8, UTF-16 LE/BE and UTF-32 LE/BE are supported.
- **no BOM means strict UTF-8**.
- no locale fallback and no heuristic legacy-encoding guessing are allowed.
- the BOM is removed from editor text and retained as metadata.
- invalid bytes fail with a typed encoding error.

A future explicit “Open with Encoding…” may add a user-selected decode path, but must not silently weaken the G01 default loader.

### 11.4 EOL and internal text policy

G01 records LF, CRLF and CR counts, dominant style, mixedness and final-newline state from decoded source text. Dominant style is the most frequent style; ties use first occurrence. A file with no separator records `LineEnding.NONE`.

Graphium's in-memory editor representation is **LF-normalized**. Serialization converts only at the byte boundary:

- an accepted source retains its encoding, BOM and dominant EOL profile;
- a source with no separator uses LF if later editing introduces newlines;
- a new unbound document defaults to UTF-8, no BOM, LF;
- mixed-EOL normalization requires explicit consent before serialization can proceed;
- serialization is strict and may not replace unrepresentable characters.

G01 serialization performs no filesystem mutation.

### 11.5 Hard anti-scope

G01 MUST NOT implement:

- G02 history, editor transaction, savepoint/dirty state or `DocumentSession`;
- G03 guarded/atomic Save or Save As;
- G04 GTK shell, Open chooser or buffer wiring;
- live external-file monitoring;
- Recent Files, copy/version commands, Properties UI;
- encoding heuristics, autosave, remote files, tabs or a document registry.

### 11.6 Provenance

G01 is a selective adaptation of the Calamus W116 published `calamus_document_identity.py`, `calamus_document_loader.py` and `calamus_document_serializer.py` semantics. Runtime imports from Calamus remain forbidden. Exact source hashes and adaptation decisions live in non-canonical G01 provenance evidence and are summarized in the MO.


## 12. Performance & Perceived Latency Budget

Rebaseline: 2026-08-14 — G04 deep mature-source audit.

`PERFORMANCE_PERCEIVED_LATENCY_BUDGET=FROZEN`
`PERMANENT_COMPARATORS=Leafpad,L3afpad,Mousepad,FeatherPad`
`PRIMARY_TARGET_SEGMENT=QUICK_EDIT_SIMPLE_TEXT_EDITOR_USERS`
`SAFETY_MAY_NOT_BE_DISABLED_FOR_BENCHMARKS=YES`
`PERFORMANCE_HETEROGENEOUS_ORACLE_RATIOS=FORBIDDEN`
`PRODUCT_CATEGORY=LIGHTWEIGHT_TRUST_EDITOR`
`FEATURE_COUNT_IS_NOT_THE_COMPETITIVE_AXIS=YES`
`NORMAL_SAVE_IS_CONTENT_NEUTRAL=YES`
`FILE_MONITOR_IS_OBSERVATION_TRIGGER_NOT_TRUTH_AUTHORITY=YES`
`V1_TABS_SYNTAX_IDE_PLUGIN_PLATFORM=FORBIDDEN`
`SAFETY_AND_PERFORMANCE_MAY_NOT_WEAKEN_EACH_OTHER=YES`

### 12.1 Positioning

Graphium freezes **FAST + SIMPLE + SAFE + NATIVE GTK** and the product category **LIGHTWEIGHT TRUST EDITOR**. Leafpad/L3afpad are the immediacy/low-cognitive-load references; Mousepad is the primary operational-maturity comparator; FeatherPad is the permanent speed-plus-maturity comparator proving that greater feature density does not excuse poor launch latency. Graphium targets the quick-edit subset of Mousepad/FeatherPad users rather than their tab/session/syntax/column-editing power-user segment.

### 12.2 Comparator set and falsifiable receipts

Every desktop-capable checkpoint records the actually installed Leafpad, L3afpad, Mousepad and FeatherPad versions on the T480, together with Graphium version/tree, sample hashes, run count, metric definition and environment isolation. Missing comparators block the comparative receipt; they do not become a product failure.

### 12.3 Two metrics that must not be conflated

**FIRST_VISIBLE** is the common cross-product metric: process start -> first new X11 top-level mapped for the exact spawned process. The same external X11 oracle is used for Graphium, Leafpad, L3afpad, Mousepad and FeatherPad. Ratios may be calculated only within this common metric.

Comparator process-isolation is part of the oracle contract, not an implementation detail: Mousepad is launched with its no-server mode when supported, and FeatherPad is launched with `--standalone` because FeatherPad is single-instance by default. A comparator build that cannot provide the required isolated-process mode BLOCKS the comparative receipt; the oracle must not be weakened to accept a window owned by a different pre-existing PID.

**FIRST_EDITABLE** is the exact Graphium-internal metric: process start -> requested file Open (if any) completed -> window mapped -> Gtk.TextView focused -> one complete READY record emitted. G04 transports this record through an inherited pipe, not a filesystem ready flag. It is exact Graphium regression/admission evidence but is **not** numerically compared with comparator FIRST_VISIBLE values.

Direct source audit established why this distinction is mandatory: Leafpad and L3afpad show their window before completing command-line file Open, while Airpad follows a different ordering. Therefore `first mapped window` cannot be silently relabelled `first editable`.

G12 source and T480 qualification attempted such a common external FIRST_EDITABLE oracle and rejected it. The mature products do not expose one homogeneous external load/editability lifecycle: Leafpad/L3afpad complete Open synchronously after showing the window, gedit and GNOME Text Editor own explicit loading state, FeatherPad owns an asynchronous loading lifecycle, and Graphium owns its inherited-pipe READY boundary. AT-SPI focus/text/editability and direct accessibility mutation are projections, not a universal transaction/completion authority. Therefore **v1 cross-product FIRST_EDITABLE ratios are permanently forbidden**. G12 reports common FIRST_VISIBLE plus exact Graphium-internal FIRST_EDITABLE/self-regression evidence instead; the invalid 1.5x/1.75x editable-ratio targets are retired rather than silently transplanted onto another metric.

### 12.4 Workloads and statistics

Both applicable G04 metrics cover empty, 5 KiB, 1 MiB and 10 MiB UTF-8/LF files. Normal series use one uncounted priming run plus at least seven measured runs. Report median and p90; Graphium exact measurements also record RSS. Real user configuration must not be read/mutated for benchmarking.

### 12.5 G04 admission

Graphium exact FIRST_EDITABLE must satisfy:

- empty median <= 750 ms;
- 5 KiB median <= 900 ms;
- idle RSS <= 200 MiB.

The common FIRST_VISIBLE receipt also applies the existing quick-edit admission comparison against Mousepad:

- Graphium empty FIRST_VISIBLE <= 2.0x Mousepad or <= 750 ms;
- Graphium 5 KiB FIRST_VISIBLE <= 2.0x Mousepad or <= 900 ms;
- Graphium idle RSS <= 200 MiB.

Leafpad and L3afpad gaps are always reported. These thresholds are admission ceilings, not marketing claims.

### 12.6 Permanent regression budget

After G04, relative to the immediately preceding published Graphium desktop baseline, >10% median regression in empty/5 KiB, >15% in 1/10 MiB, or >15% idle-RSS growth blocks closure until explained and explicitly accepted. Noise is handled by rerunning complete series, never by cherry-picking.

### 12.7 Startup discipline

Subsystems not needed for the first editable document remain off the critical path where reasonable. Help content, Print/Preview/Page Setup, optional spellcheck and later nonessential services are lazy. Performance optimizations may never weaken G01-G03 safety, encoding/EOL neutrality, exact savepoint semantics or guarded writes.


## 13. G02 — History / Editor Transaction / Savepoint Session

Freeze: 2026-08-14.

`G02_CONTRACT=FROZEN`
`G02_SCOPE=HISTORY_TRANSACTION_SAVEPOINT_SESSION`
`G02_GTK_REQUIRED=NO`
`G02_DIRTY_AUTHORITY=EDITOR_STATE_ID_RELATION`
`G02_PHYSICAL_WRITER=FORBIDDEN`
`G02_TARGET_USERS=Leafpad,L3afpad,Mousepad_quick_edit`

### 13.1 Target-user consequence

G02 serves Leafpad/L3afpad/Mousepad-style quick-edit users by making Undo/Redo and Saved/Modified behavior trustworthy **without adding visible workflow complexity**. History sophistication is an internal safety/maturity mechanism, not a reason to add timelines, persistent undo, history panels or session machinery to the UI.

The user-facing mental model remains simple:

- type -> Modified;
- save -> Saved;
- Undo/Redo may naturally return to the exact saved state;
- opening or creating a document does not create fake undo steps.

### 13.2 Stable editor-state identity

Every committed text state owned by `TextHistory` receives a positive monotonically increasing `state_id`. State identities are **never reused** during one history lifetime, including after pruning or after a new branch discards redo history.

Caret/selection-only refreshes preserve the current text-state identity. The current insertion position and selection-bound position remain part of the restorable history snapshot, including selection direction, but they do not make a clean text state dirty by themselves.

A new branch after Undo receives a fresh identity even when its text happens to equal text that existed on the discarded branch. Therefore text equality or content digest equality may never be used as the Saved/Modified authority.

### 13.3 Savepoint-aware DocumentSession

The one active `DocumentSession` owns:

- current LF-normalized text;
- at most one accepted G01 `DocumentFileState`;
- `current_editor_state_id`;
- `saved_editor_state_id`.

`modified` is derived only from the relation:

```text
current_editor_state_id == saved_editor_state_id != None  -> Saved
otherwise                                                   -> Modified
```

Pending native text that has not yet been committed to history has no stable current state ID and is therefore Modified. If a native edit nets back to the already committed current text before the group is committed, the existing stable identity may be reconciled immediately.

A **late save** completion may mark only the exact editor-state identity whose bytes were actually accepted by the future G03 writer. If the current editor has already advanced to a newer state, accepting the older saved identity must leave the document Modified.

External-file changed/deleted/replaced state is not the dirty-state authority and remains a separate concern for G11.

### 13.4 Transaction grouping and rollback

`EditorTransactionController` is GTK-free. It coordinates a buffer port, `TextHistory`, and `DocumentSession`.

Required semantics:

- one logical programmatic edit becomes at most one committed Undo step;
- nested programmatic transactions are rejected;
- failed programmatic actions restore visible buffer, history and session exactly;
- Undo/Redo restoration includes text, insertion offset and selection-bound offset;
- a failed Undo/Redo buffer restore must roll history/session/buffer back to the pre-operation checkpoint;
- New/Open replacement is not an ordinary edit and resets history rather than becoming Undoable document content;
- actual Gtk.TextBuffer `begin-user-action` / `end-user-action` signal wiring and native debounce timing are deferred to G04, where the GTK adapter must call this headless authority rather than duplicate it.

### 13.5 Bounded history / large-document policy

Graphium uses bounded full-text snapshots in G02 because they are simple, predictable and appropriate to the quick-edit target. Default policy:

- 100 history steps;
- 750,000 characters maximum per snapshot for Undo history;
- 2,500,000 characters approximate aggregate snapshot budget.

When a document exceeds the per-snapshot threshold, Graphium keeps a current stable state identity but disables multi-snapshot Undo for that document state instead of multiplying large copies in memory. Saving remains possible. G04/G12 performance evidence may tighten this policy but may not substitute a more complex engine without explicit architecture review.

### 13.6 G02/G03/G04 boundary

G02 performs **no physical write** and imports no GTK/Gio. `accept_saved_state()` is only a state-transition hook for G03: it may be called after G03 has successfully written and accepted the corresponding state.

G03 owns the guarded physical writer and Save/Save As orchestration.
G04 owns the Gtk.TextBuffer adapter, native user-action events, debounce/timing policy and visual Saved/Modified projection.

G02 must not pre-implement either layer.


## 14. G03 — Guarded Save / Save As

Freeze: 2026-08-14.

`G03_CONTRACT=FROZEN`
`G03_SCOPE=GUARDED_SAVE_SAVE_AS`
`G03_GTK_REQUIRED=NO`
`G03_SINGLE_PHYSICAL_WRITER=GuardedFileWriter`
`G03_DIRECT_WRITE_FALLBACK=FORBIDDEN`
`G03_HARDLINK_POLICY=FAIL_CLOSED`
`G03_SAVE_AS_REBIND_BEFORE_COMMIT=FORBIDDEN`
`G03_TARGET_USERS=Leafpad,L3afpad,Mousepad_quick_edit`

### 14.1 Target-user consequence

Graphium's quick-edit user must experience Save as an ordinary, immediate editor operation. The complexity below is **invisible safety**, not a new workflow. G03 adds no dialogs, monitor, conflict panel, backup manager or history UI. The future G04 chooser remains responsible for path selection and human overwrite consent; G03 owns only transactional persistence safety.

### 14.2 One physical writer authority

`graphium.infrastructure.guarded_file_writer.GuardedFileWriter` is the only Graphium v1 authority permitted to perform authoritative document namespace mutation. There is no direct/truncate fallback and no second atomic writer.

The guarded lane is:

1. capture one stable G02 editor state;
2. derive strict G01 serialization before filesystem mutation;
3. observe the exact target and topology;
4. create an exclusive unpredictable sibling stage in the target directory;
5. write all bytes and apply required metadata;
6. `fsync` the staged inode; sync failure is fatal before commit;
7. revalidate logical path, parent identity and target immediately before commit;
8. commit through the topology-appropriate namespace operation;
9. `fsync` the parent directory;
10. reload through the G01 stable loader and verify the committed fingerprint;
11. advance only the exact captured G02 editor-state identity.

Graphium does **not** claim a mathematically linearizable filesystem CAS against arbitrary non-cooperating writers. Existing-target replacement remains a guarded late-check followed by atomic namespace replacement.

### 14.3 Ordinary Save guard

Ordinary Save requires:

- a named active `DocumentSession`;
- the accepted G01 `DocumentFileState` installed by Open or a previous confirmed save;
- the exact current stable G02 editor-state ID.

Writer observation checks the accepted target against fresh physical evidence, including object identity where present, size, mtime/ctime, mode, owner/group, link count and SHA-256 content fingerprint. Same-size + same-mtime but different bytes must fail closed.

If the accepted baseline is absent, the target disappeared, identity/topology changed, or required metadata cannot enter the safe lane, ordinary Save fails before authoritative target mutation. It does not silently reacquire a new baseline and overwrite.

### 14.4 Serialization boundary

G01 remains the representation authority:

- accepted encoding is preserved;
- BOM policy is preserved;
- homogeneous EOL is preserved;
- mixed EOL requires explicit normalization consent from the future G04 user-facing boundary;
- new/unbound document default for Save As is UTF-8, no BOM, LF;
- encoding is strict and replacement-character fallback is forbidden;
- decoded/serialized NUL content remains outside Graphium's plain-text scope.

Serialization must complete before stage/target mutation.

### 14.5 Symlink and hardlink policy

For an active document opened through a stable symlink:

- the logical path remains the document binding;
- the physical/canonical regular-file target receives the atomic commit;
- the logical symlink itself is preserved;
- logical parent and symlink relation are late-revalidated before commit.

A dangling/cyclic/retargeted symlink fails closed.

An existing target with `st_nlink != 1` is outside the G03 guarded replacement lane and fails closed. Graphium does not silently break a hardlink group and does not fall back to in-place truncate/write.

### 14.6 Failure-atomic staging

Existing authoritative bytes remain untouched on every pre-commit failure, including:

- strict encoding failure;
- stage creation collision/substitution;
- short/injected write failure;
- stage `fsync` failure;
- metadata/xattr preservation failure;
- parent replacement/retarget;
- target mutation/deletion/replacement during staging;
- late stale-target mismatch.

Stage files are best-effort cleaned after failure.

### 14.7 Save As transaction

G03 does not create a GTK chooser. Future G04 owns destination selection and human overwrite consent.

After the destination is accepted, G04 supplies an immutable `SaveTargetObservation` to `DocumentSaveService.save_as()`.

Required identity semantics:

- target choice alone does not rebind `DocumentSession`;
- pre-commit failure leaves the previous logical binding and savepoint relation unchanged;
- Save As to the currently active physical object routes ordinary guarded Save semantics;
- an absent target uses a no-overwrite namespace commit (`link`-style lane) so an attacker/process creating the final name before commit is not overwritten;
- an existing accepted overwrite target is late-revalidated before atomic replacement;
- only after namespace commit does the session bind the new logical path and mark the captured editor-state ID saved.

### 14.8 Post-commit truthfulness

Once the namespace commit happened, Graphium must not throw a normal retry-shaped "nothing was saved" error.

Outcomes distinguish at least:

- `COMMITTED_CONFIRMED`;
- `COMMITTED_DURABILITY_UNCERTAIN` when parent-directory durability could not be confirmed;
- `COMMITTED_BASELINE_UNAVAILABLE` when a fresh stable post-save baseline cannot be reacquired/verified.

A post-commit baseline-unavailable result retains the logical document path but clears accepted `file_state`. The next ordinary Save therefore fails closed until a baseline is deliberately re-established by a later lifecycle boundary. No blind automatic second write is permitted.

### 14.9 G02 integration

The save transaction persists the captured stable editor state, not "whatever text exists when I/O finishes".

After a committed result, `DocumentSession.accept_committed_save()` marks exactly the captured `editor_state_id` saved. If editing advanced while I/O was in progress, the newer current state remains Modified.

Pre-commit failure never advances the savepoint.

### 14.10 G03/G04/G11 boundary

G03 remains GTK-free and adds no:

- `GtkFileChooser`;
- permanent `Gio.FileMonitor`;
- auto-reload;
- merge/diff conflict UI;
- deleted/renamed background state machine;
- Recent Files side effects;
- backup/local-history subsystem.

G04 owns chooser/consent and visible Save/Save As wiring. G11 owns observation-only live external-file monitoring. Both must call the existing G03/G02 authorities rather than create new file/session authorities.



## 15. G04 — Native Edit Integration Hardening / Thin GTK Shell / Core File Lifecycle

Rebuild freeze: 2026-08-14, after deep mature-source falsification audit.

`G04_CONTRACT=FROZEN`
`G04_NATIVE_HISTORY=DELTA_BASED`
`G04_NATIVE_EDIT_TIMER_AUTHORITY=FORBIDDEN`
`G04_FULL_BUFFER_CAPTURE_PER_NATIVE_EDIT=FORBIDDEN`
`G04_APPLICATION_TOPOLOGY=ONE_PROCESS_ONE_WINDOW_ONE_DOCUMENT`
`G04_APPLICATION_UNIQUENESS=NON_UNIQUE`
`G04_MULTI_FILE_CLI=ONE_PROCESS_PER_FILE`
`G04_GTK_EDITOR_WIDGET=Gtk.TextView`
`G04_GTK_SOURCEVIEW=FORBIDDEN`
`G04_TOOLBAR=ABSENT`
`G04_HELP=LAZY_OFFLINE`
`G04_PERFORMANCE_COMMON_METRIC=FIRST_VISIBLE`
`G04_PERFORMANCE_EXACT_INTERNAL_METRIC=FIRST_EDITABLE`
`G04_PERFORMANCE_READY_PROTOCOL=INHERITED_PIPE_ATOMIC_RECORD`
`G04_HETEROGENEOUS_READINESS_RATIO=FORBIDDEN`
`G04_TARGET_USERS=Leafpad,L3afpad,Mousepad_quick_edit,FeatherPad_quick_edit`
`G04_INTERACTIVE_LINE_BUDGET_CHARS=20000`
`G04_PATHOLOGICAL_LINE_POLICY=REFUSE_BEFORE_GTK_BUFFER_INSTALL`
`G04_PATHOLOGICAL_LINE_CONTENT_MUTATION=FORBIDDEN`

### 15.1 Explicit architecture review of the published G02 snapshot engine

G02 remains published historical authority for **editor-state identity and savepoint semantics**:

- positive monotonically increasing state IDs;
- state IDs never reused after Undo branching, pruning or rollback;
- Saved/Modified derived from current-state ID versus saved-state ID;
- late Save may mark only the exact persisted state saved;
- text equality alone is never the dirty-state oracle.

G04 is the explicit architecture review contemplated by G02 section 13.5. Direct source comparison against Leafpad, L3afpad, Airpad, Mousepad/GtkSourceView clients, gedit, GNOME Text Editor, NEdit and JOE showed that the active native editor should not retain a complete document snapshot per ordinary edit. Therefore:

- `TextHistory` remains available as published G02 headless/regression code;
- the active G04 GTK runtime composes `DeltaHistory` instead;
- the active native editor stores insertion/deletion payload plus offsets/view state, not the entire base document;
- document size itself is not a switch that disables ordinary Undo;
- a 1 MiB document with a one-character edit must retain normal Undo and store approximately that changed payload rather than another 1 MiB document copy.

This supersedes only G02's **active-runtime storage choice** and old 750,000-character native-Undo degradation assumption. It does not rewrite G02 history or invalidate its published tests/commit.

### 15.2 Native user-action and grouping authority

Wall-clock inactivity is not semantic evidence that an editing operation ended. The withdrawn pre-rebuild G04 design's fixed native-commit delay is forbidden.

The active GTK adapter records deltas from real `GtkTextBuffer` insertion/deletion signals and uses `begin-user-action` / `end-user-action` as the primary compound-action boundary. Across adjacent completed user actions, bounded structural coalescing may combine compatible contiguous single-character insertion/deletion runs. Whitespace class, operation kind/direction, non-contiguity, multi-character compound operations and the exact saved state are merge barriers.

Required consequences:

- Undo behavior does not change merely because the user typed faster/slower than a timeout;
- Save is a semantic merge barrier so Undo can land exactly on the saved state;
- programmatic edits outside a GTK user-action may create one explicit fallback group, but never by waiting for elapsed time;
- Undo/Redo replay is suppressed from re-recording itself;
- replay verifies expected deleted text and fails rather than silently applying a delta to an unexpected buffer state.

### 15.3 DocumentSession/live-buffer split

The mutable Gtk.TextBuffer is the live text surface but not a second savepoint authority. G04 allows `DocumentSession.current_editor_state_id` to advance without copying the full live text into the session on every native edit.

`DocumentSession.text_editor_state_id` records which editor-state identity the session's synchronized text represents. After an ordinary native edit, `text_is_current` may be false while Saved/Modified remains exact from state IDs.

Immediately before physical Save/Save As, `NativeEditorController.prepare_for_save()` must:

1. require no active native edit group;
2. verify delta-history current ID equals DocumentSession current ID;
3. capture the full GtkTextBuffer once;
4. synchronize that text to the exact current editor-state ID;
5. then call the existing G03 save service.

Merely asking whether New/Open/Quit should discard a Modified document must not capture/copy the whole buffer.

### 15.4 Process/window/document topology

Graphium v1 remains single-document. For the target quick-edit workflow, G04 freezes the stronger process topology:

**one invocation/process -> one Gtk.ApplicationWindow -> one active document.**

`Gtk.Application` uses `G_APPLICATION_NON_UNIQUE`. A second Graphium invocation must create its own process/window and must not forward an Open request into a pre-existing Graphium process. If one invocation receives several filenames, the first belongs to that process and remaining files are fanned out to separate Graphium processes, following the useful Airpad pattern.

File -> Open within one window may deliberately replace that window's current document after the normal Save/Discard/Cancel lifecycle. This is different from another OS/file-manager invocation hijacking an unrelated open document.

### 15.5 Thin visible shell

G04 exposes only the first credible classic quick-edit surface:

File:
- New
- Open…
- Save
- Save As…
- Quit

Edit:
- Undo
- Redo
- Cut
- Copy
- Paste
- Delete
- Select All

Help:
- User Guide
- Keyboard Shortcuts
- About

Help text is offline product material loaded only when requested. G04 has no toolbar. The optional toolbar question remains routed to G06 after direct source/target-user audit. GtkSourceView, tabs, syntax, sidebars and project/session UI remain outside G04.

### 15.6 File lifecycle and content neutrality

G04 may perform chooser/consent/UI orchestration but may not bypass G01-G03 authorities.

- Open loads/validates before replacing the current document.
- failed Open leaves current buffer/session/history intact.
- New/Open/Quit consult `DocumentSession.modified` and offer Save/Discard/Cancel.
- Save/Save As physically write only through `DocumentSaveService` -> `GuardedFileWriter`.
- Save As rebind remains commit-after-only.
- mixed EOL normalization requires explicit consent.
- no implicit trailing-space cleanup, final-newline insertion, encoding conversion, BOM conversion or line-ending normalization is permitted merely because Open/Save occurred.

### 15.7 Performance protocol

The old filesystem ready-file protocol is rejected because file existence was observable before a complete readiness record was guaranteed. G04 exact FIRST_EDITABLE uses an inherited pipe. The child emits one short newline-terminated `READY <pid> <monotonic_ns>` record with one `os.write()` after requested Open completion, window map and editor focus. The parent waits for a complete newline record and verifies the emitting PID.

Cross-product comparison uses the common external FIRST_VISIBLE oracle defined in section 12. FIRST_VISIBLE and FIRST_EDITABLE receipts are intentionally separate. A report must never infer that a competitor is editable merely because its window became visible.

### 15.8 Mature-source audit discipline / confirmation-bias countermeasure

For every Graphium design decision evaluated against mature software, evidence must state:

1. the Graphium assumption under test;
2. a mature source that contradicts or stresses that assumption;
3. the materially different model used by that source and why it works;
4. the Graphium decision that would change if the alternative evidence is stronger;
5. final ADOPT / ADAPT / REJECT / DEFER classification.

An audit that records only corroborating examples is incomplete. A pre-product harness/oracle stop triggers failure localization and re-audit of the whole failure class before another desktop candidate is issued; Graphium does not progress by numbered trial-and-error attempts.

### 15.9 Pathological logical-line / renderer-safety policy

The valid T480 manual product FAIL on the seven-editor candidate demonstrated that "1 MiB file" and "1 MiB single logical line" are not equivalent workloads. The failed fixture was one line of 1,048,576 characters. Delta Undo remained available, but navigating/rendering the line end could make the GtkTextView window unresponsive. Mature-source re-audit showed that long-line display is a distinct renderer problem: FeatherPad applies an explicit logical-line guard, NEdit bounds custom display work, and GNOME's own GtkTextView issue history documents severe long-line behavior.

G04 therefore freezes a **20,000 Unicode-character per logical line interactive-rendering budget** for the GtkTextView editor surface. This is a conservative Graphium product budget for the chosen renderer, not a claim that GTK has a universal 20,000-character hard limit. It may be changed only by later explicit renderer qualification.

Required semantics:

- G01 may still load/decode such input as valid plain text; renderability is a G04 interactive-surface concern.
- before `NativeEditorController.initialize_open()` installs loaded text into GtkTextBuffer, G04 scans logical-line width without splitting/rewriting the document; any line above the budget causes a typed refusal.
- failed renderability admission leaves current buffer, session, history and logical path unchanged.
- Graphium never truncates the line, inserts a marker, inserts line breaks, normalizes content or silently changes wrap mode to make the file fit.
- no read-only GtkTextView fallback is offered for the same pathological line, because the failure class is rendering/navigation itself; a future exact paged/streamed viewer is separate architecture.
- native insertion/paste is preflighted before GtkTextBuffer's default insertion handler; a deletion that would join line fragments above the budget is likewise stopped before default mutation.
- blocked edits do not advance editor-state identity or Undo history and surface an explicit warning.
- automated large-file qualification uses a realistic multiline 1 MiB document and actually moves/scrolls the cursor to the end before edit/Undo. Huge-line refusal is a separate automated guard test.

This policy preserves both sides of the product identity: **large ordinary text remains editable; pathological renderer input is refused without altering user bytes**.

### 15.10 Desktop closure gates

Before asking the user for final G04 desktop validation, the candidate must pass:

- all G00-G03 regressions;
- G04 delta-history/native-editor/lifecycle/performance-protocol tests;
- architecture/source strict gates;
- arbitrary-cwd bootstrap probes;
- True-GTK shell/Open/Save/savepoint/delta-history/realistic-multiline-1-MiB Undo gate;
- True-GTK pathological-line Open/paste refusal gate before GtkTextBuffer mutation;
- `NON_UNIQUE` one-process/one-window/one-document topology gate;
- active Linux Mint/Cinnamon shortcut collision audit;
- exact Graphium FIRST_EDITABLE admission receipt;
- common FIRST_VISIBLE Graphium/Leafpad/L3afpad/Mousepad/FeatherPad receipt, or a comparator-missing BLOCKED result rather than a false product FAIL.

Only after these automated desktop gates pass is human visual/lifecycle validation requested.


## 16. G05 — Search / Replace / Go to Line Trust Contract

Freeze: 2026-08-14, after audit of published G04 source plus L3afpad, FeatherPad, GTK 3 and GtkSourceView search models.

`G05_CONTRACT=FROZEN`
`G05_SEARCH_SCOPE=LITERAL_CURRENT_DOCUMENT_ONLY`
`G05_SEARCH_QUERY=SINGLE_LINE_NONEMPTY_UNICODE`
`G05_REPLACEMENT=SINGLE_LINE_UNICODE_MAY_BE_EMPTY`
`G05_MATCH_CASE=ADOPT`
`G05_WHOLE_WORD=DEFER`
`G05_REGEX=REJECT_V1`
`G05_FUZZY=REJECT_V1`
`G05_MULTI_FILE_SEARCH=REJECT_V1`
`G05_SEARCH_HISTORY=DEFER`
`G05_HIGHLIGHT_ALL=REJECT`
`G05_BACKGROUND_SEARCH=REJECT`
`G05_WRAP=AUTOMATIC_ONE_WRAP`
`G05_CURRENT_MATCH=NATIVE_SELECTION`
`G05_REPLACE_ALL_MATCH_SET=FROZEN_FROM_ORIGINAL_SOURCE`
`G05_REPLACE_ALL_UNDO_GROUPS=1`
`G05_REPLACE_ALL_RENDERABILITY=PREFLIGHT_FINAL_TEXT`
`G05_PROGRAMMATIC_REPLACE=DELTA_EXPECTED_DELETE_INVERSE_ROLLBACK`
`G05_GENERIC_RENDER_GUARD_BYPASS=FORBIDDEN`
`G05_LEGACY_FULL_SNAPSHOT_TRANSACTION=FORBIDDEN`
`G05_REPLACE_UNDO_PAYLOAD_MAX=DELTA_HISTORY_MAX_PAYLOAD`
`G05_CASEFOLD_WORKING_SET=LOGICAL_LINE_BOUNDED`
`G05_REPLACE_ALL_MATCH_CAP=50000`

### 16.1 Search authority and navigation

G05 adds a GTK-free current-document literal-search authority. Search text is Unicode `str`; offsets are editor character offsets and must map exactly back to the original buffer. Case-sensitive search is exact codepoint literal comparison. Case-insensitive search uses Unicode casefold semantics with explicit transformed-boundary-to-original-offset mapping so length-changing folds cannot produce partial-source-character matches. Because G05 queries are single-line and G04 already bounds interactive logical-line length, casefold working memory is line-bounded: Graphium folds/maps one logical line at a time instead of casefolding/caching the complete multi-megabyte document or allocating per-character document-wide offset tables.

Find Next starts after the current selection when a selection is active, otherwise at the insertion point. Find Previous starts before the current selection/insertion point. Each command may wrap exactly once. Search navigation changes only view/selection state: it does not allocate a DeltaHistory state ID, touch the savepoint, mark Modified or create Undo data.

The last accepted non-empty query and Match Case option are application command state so F3/Shift+F3 work after the search surface is hidden. No search history database or cross-document persistence is introduced.

### 16.2 Lightweight visible search surface

The top-level Search menu owns:
- Find… (`Ctrl+F`)
- Find Next (`F3`)
- Find Previous (`Shift+F3`)
- Replace… (`Ctrl+H`)
- Go to Line… (`Ctrl+G`)

Find/Replace use one lazily shown in-window `Gtk.SearchBar`. Find mode exposes one single-line query entry plus Match Case and navigation. Replace mode adds one single-line replacement entry and Replace / Replace All commands. Editing the fields alone does not scan/highlight the whole document. Escape closes the bar and returns focus to the editor. The current occurrence is represented by the native text selection, not a separate highlight-all subsystem.

Opening Find/Replace may prefill a non-empty single-line editor selection. A multiline selection is never copied into the one-line query field merely because it is selected.

### 16.3 Replace One

Replace One is a single activation, not an exact-selection availability trap:
1. if the current selection is the exact active match under the current query/options, use it;
2. otherwise acquire the next match using normal Find Next semantics;
3. replace exactly that source range;
4. if another match exists after the resulting caret, select it for the next activation.

The text mutation is one DeltaHistory group/state-ID advance and therefore one Undo step. If no match exists, nothing is mutated and no editor-state identity is allocated.

### 16.4 Replace All atomicity and non-cascading semantics

Replace All snapshots the current buffer text and current editor-state identity on explicit activation, determines all non-overlapping matches against that original source, and derives the complete final text before GTK mutation. Inserted replacement text is never searched again during the same activation.

Before mutation, the final text must pass the published G04 interactive renderability authority. G05 query/replacement fields are single-line, so a replacement cannot introduce/remove a logical-line boundary. The programmatic transaction may suppress ordinary GTK signal recording only after this full final-state preflight; it must not expose a generic or caller-controlled renderer-safety bypass.

Changed source ranges are applied in descending original offset order. Each deletion verifies the exact expected original text before mutation. The buffer adapter owns inverse rollback if any operation fails. NativeEditorController also checkpoints DeltaHistory and DocumentSession; history/session advance only after successful buffer application. If post-buffer authority commit fails, the exact inverse operation sequence restores the prior buffer before authority rollback. No full-document snapshot is stored in Undo history.

All changed ranges belong to one DeltaHistory group and produce exactly one new editor-state ID. Undo restores the exact original text/view and saved-state relation; Redo restores the replacement result. Zero effective changes produce no Undo group and no state-ID advance.

Before mutation, the total changed Undo payload for a programmatic replacement must fit `DeltaHistory.max_payload_chars`. A replacement exceeding that bound is refused explicitly before GTK mutation; Graphium does not silently make a successful Replace All non-undoable and does not allow one oversized group to defeat the published changed-payload memory bound. Independently, Replace All may freeze at most 50,000 source matches in one activation. The 50,001st match fails closed before final-text/replay-plan materialization. This is an explicit command-scale bound against Python object amplification, not a document-size limit and not a limit on Find Next/Previous, which never materialize the complete match set.

A replacement plan is tied to the exact source editor-state ID. A stale plan must be rejected rather than applied to a newer editor state.

### 16.5 Go to Line

Go to Line is 1-based, bounded to the current document line count, and only changes cursor/selection/view state. It does not alter document text, history or Saved/Modified state. No bookmark stack/navigation history is created in G05.

### 16.6 Lightweight Budget

G05 performs no startup search scan, idle scan, background worker, persistent index, full-document casefold cache or eager highlight-all computation. Whole Word, canonical-equivalence expansion, regex, fuzzy search and search history remain outside the frozen G05 MUST scope. Explicit command-time text capture is permitted and must be measured on realistic multiline 1 MiB and 10 MiB fixtures; if evidence shows unacceptable responsiveness, architecture must be re-audited rather than silently adding a background subsystem.

G05 cannot close without `LIGHTWEIGHT_BUDGET_GATE=PASS`.


## 17. G06 — View Menu Core / Compact Status / Lightweight Presentation

Freeze: 2026-08-15, after audit of published G05 source, target-user/mature-source comparison and the T480 NON-CANDIDATE native `Gtk.TextView` line-number probe.

`G06_CONTRACT=FROZEN`
`G06_IMPLEMENTATION_AUTHORIZED=YES`
`G06_VIEW_MENU=STATUS_BAR,LINE_NUMBERS,WORD_WRAP,FONT,ZOOM_IN,ZOOM_OUT,ZOOM_RESET,FULL_SCREEN`
`G06_APPEARANCE=DEFER_G10`
`G06_TOOLBAR=REJECT_V1`
`G06_WORD_WRAP=GTK_WORD_CHAR`
`G06_LINE_NUMBERS=GTK_TEXTVIEW_LEFT_BORDER_WINDOW`
`G06_LINE_NUMBER_DRAW_SCOPE=VISIBLE_LOGICAL_LINES_ONLY`
`G06_WRAPPED_CONTINUATION_NUMBERS=NO`
`G06_GTKSOURCEVIEW=FORBIDDEN`
`G06_LINE_NUMBER_BACKGROUND_INDEX=FORBIDDEN`
`G06_STATUS_FIELDS=LINE_COLUMN,ENCODING_EOL,SAVED_MODIFIED`
`G06_LIVE_WORD_CHAR_COUNT=DEFER_G07_STATISTICS`
`G06_FONT=PERSISTENT_FAMILY_SIZE_VIA_CSS_PROVIDER`
`G06_ZOOM=TRANSIENT_RELATIVE_TO_BASE_FONT`
`G06_ZOOM_RESET=100_PERCENT`
`G06_FULL_SCREEN=TRANSIENT`
`G06_PERSISTENT_DIRECT_VIEW_SETTINGS=WORD_WRAP,LINE_NUMBERS,STATUS_BAR,FONT`
`G06_SETTINGS_STORAGE=XDG_SMALL_ATOMIC_JSON`
`G06_SETTINGS_BACKGROUND_WRITE=FORBIDDEN`
`G06_LIGHTWEIGHT_BUDGET_GATE=REQUIRED`
`G06_STARTUP_REGRESSION_BASELINE=G04_CERTIFIED_T480`
`G06_STARTUP_TIME_REGRESSION_LIMIT=MAX_25_PERCENT_OR_75_MS`
`G06_STARTUP_RSS_REGRESSION_LIMIT=MAX_25_PERCENT_OR_20_MIB`
`G06_FIRST_EDITABLE_CROSS_PRODUCT_CLAIM=DEFER_G12_COMMON_EXTERNAL_ORACLE`

### 17.1 Single-surface View authority

G06 adds one top-level View menu. Status Bar, Line Numbers and Word Wrap are stateful direct commands whose current state is visible in the menu and persisted from that command surface. Font owns the persistent base family+size. These settings must not later be duplicated in Preferences merely to create a second route. Appearance remains reserved for G10. Toolbar is rejected for v1 rather than hidden behind a preference.

### 17.2 Native line-number gutter

Graphium remains a plain `Gtk.TextView` editor. Line numbers use the widget's native LEFT border window. Gutter width depends on the decimal digit width of the logical line count. Drawing begins from the logical line intersecting the current visible rectangle and advances only through logical lines intersecting that viewport. Wrapped display-line continuations receive no additional number. The gutter must never scan the document, maintain a background line index, create a second scrollable widget, mutate the buffer, allocate history state or require GtkSourceView.

The qualifying T480 NON-CANDIDATE probe on GTK 3.24.41 passed 1 MiB wrap-off, 1 MiB wrap-on and 10 MiB wrap-off. Maximum observed logical lines visited per draw was 40; buffer mutations were zero; manual alignment/scroll/wrap/resize/toggle checks passed. This validates the architecture, not a product candidate.

### 17.3 Compact status and representation projection

The status surface is deliberately cheap and event-driven. Cursor line/column comes from the current `GtkTextIter`; Saved/Modified comes from the published state-ID relation; encoding and EOL come from the accepted document representation metadata. Status refresh must not call whole-document text capture, word counting, character counting or background analytics. New documents project UTF-8/LF. Mixed EOL is shown as observed representation rather than silently normalized.

### 17.4 Font and Zoom separation

Font stores only base family+size. GTK presentation uses a view-local CSS provider; deprecated `Gtk.Widget.override_font` is forbidden. Zoom is a transient multiplier over that configured base font, bounded to a small product range and reset to 100%. Zoom does not change the persistent base font, document text, history, savepoint or representation.

### 17.5 Persistent settings boundary

Persistent direct View settings are a small GTK-free value object backed by one product-local XDG JSON file. Load is read-only and fail-soft. The file is created or replaced only after an explicit setting change, using same-directory temporary staging plus atomic replace. There is no watcher, background writer, settings database, synchronization service or session semantics. A persistence failure must not publish a new in-memory setting as though it were durable.

### 17.6 Lightweight Budget and closure

G06 rejects Toolbar v1 because it duplicates a small conventional menu/shortcut command set without sufficient quick-edit value. Live word/character counts remain deferred to on-demand Statistics. G06 must preserve the G04/G05 startup and comparator gates, measure integrated View responsiveness, and close only with `LIGHTWEIGHT_BUDGET_GATE=PASS`.


### 17.4 G06 automated GTK ownership contract

The retired G06 integrated NON-CANDIDATE checkpoint established a harness-ownership rule,
not a product exception. G06 product qualification MUST preserve the published synchronous
unsaved-change lifecycle and MUST NOT suppress its dialogs to simplify testing.

Frozen markers:

`G06_INTEGRATED_CHECKPOINT_LINE=RETIRED`
`G06_TRUE_GTK_EXPECTED_MODAL_COUNT=0`
`G06_TRUE_GTK_UNEXPECTED_MODAL=UNWIND_THEN_FAIL`
`G06_FIXTURE_OPEN_REQUIRES_EXACT_SAVED_STATE=YES`
`G06_EXPECTED_DIALOG_RESPONSE_OWNERSHIP=SCHEDULE_BEFORE_TRIGGER`
`G06_GLIB_SOURCE_OWNERSHIP=EXPLICIT_CLEANUP_REQUIRED`
`G06_OUTER_TIMEOUT_ROLE=LAST_RESORT_PROCESS_CONTAINMENT_ONLY`
`G06_QUALIFICATION_TOPOLOGY=FRESH_PROCESS_GATE_MATRIX`

For a G06 View semantic/performance scenario, replacing the active fixture is legal only
when `session.modified == False` and the current editor state identity equals the Saved
state identity. If a scenario intentionally tests a modal, its deterministic response must
be armed before the product call. G06 View semantics intentionally expects zero modals; an
unexpected visible `GtkDialog` may be responded to only to unwind a nested loop and MUST
then fail the gate. A generic dialog auto-canceller that lets the scenario continue is
forbidden.

The eventual G06 candidate runner orchestrates independent fresh-process gates. No new
R3 of the retired integrated checkpoint is permitted.

### 17.7 G06 View performance oracle rebaseline after Candidate C1

Candidate C1 passed the full functional G06 True-GTK View gate and stopped only in the
old monolithic View-performance lane. Static mature-source re-audit established that the
retired oracle repeatedly oscillated layout-affecting state in one 10 MiB TextView and
therefore measured cumulative re-layout stress rather than one interactive user request.
The old repeated-toggle/repeated-reset oracle is forbidden.

Frozen markers:

`G06_VIEW_PERFORMANCE_ORACLE=SINGLE_TRANSITION_FRESH_PROCESS`
`G06_VIEW_PERFORMANCE_PRIMING_PROCESSES=1`
`G06_VIEW_PERFORMANCE_MEASURED_PROCESSES=7`
`G06_VIEW_PERFORMANCE_TRANSITIONS_PER_WORKER=1`
`G06_VIEW_PERFORMANCE_FRAME_ORACLE=FIRST_POST_TRANSITION_AFTER_PAINT`
`G06_VIEW_PERFORMANCE_WORKER_TIMEOUT_SECONDS=30`
`G06_VIEW_PERFORMANCE_FRAME_DEADLINE_SECONDS=15`
`G06_VIEW_PERFORMANCE_FONT_APPLY_10M_P90_MAX_MS=500`
`G06_VIEW_PERFORMANCE_BUDGETS_WEAKENED=NO`

Each scenario owns one discarded fresh-process priming sample and seven measured fresh
processes, each with isolated HOME/XDG and exactly one View transition. Open/startup is
setup and remains outside the transition latency because G04 already owns startup/open
performance. The clock begins immediately before the View action and ends at the first
post-transition GTK frame-clock `after-paint`. A worker timeout names the exact scenario,
role and sample; the outer candidate-lane watchdog is last-resort containment only.

Measured scenarios are Line Numbers at 1/10 MiB, Word Wrap at 1/10 MiB, Zoom at 10 MiB,
Font Apply at 10 MiB, and 1000 Compact Status updates. Font Apply replaces only human
chooser input with deterministic Monospace 14; the real Graphium persistence -> base-font
-> CSS path remains measured. Existing budgets are retained and Font Apply adds a 500 ms
p90 ceiling. A budget miss is product-performance evidence; the oracle must not be relaxed
to manufacture a PASS.


## G06 desktop certification and publication closure payload — 2026-08-16

G06 Candidate C2 exact certified tree is `52d4f07c4757e85f6ebeec87398ec8ec3b6e30bb`. T480 certification completed with 266/266 non-desktop tests PASS, strict gates PASS, G04/G05/G06 True-GTK lanes PASS, redesigned single-transition fresh-process View performance PASS, Lightweight Budget PASS, topology and Cinnamon shortcut gates PASS, startup self-regression PASS, common FIRST_VISIBLE comparison PASS, and manual View validation 4/4 PASS.

The certified product scope is Status Bar, native Gtk.TextView visible-logical-line numbers, Word Wrap, persistent Font family+size, transient Zoom, transient Full Screen and Compact Status. Toolbar remains REJECT v1; Appearance remains DEFER G10; live document-wide counts remain DEFER G07 on-demand Statistics.

The two retired integrated NON-CANDIDATE checkpoints remain historical evidence only and MUST NOT be reused. C1's repeated-toggle performance oracle also remains retired. The accepted performance oracle is one priming process plus seven fresh measured processes per scenario, exactly one View transition per worker, action to first post-transition `after-paint`, fail-closed hard budgets.

This file belongs to the G06 publication payload. G06 is considered `CLOSED / CERTIFIED / PUBLISHED` only when `RUN_G06_FINALIZE_AND_PUBLISH.sh` completes with `FINAL_PHASE=G06_PUBLICATION_PASS` and verifies the real remote.


## G06 publication finalization — 2026-08-16

`G06_PUBLISHED_COMMIT=aae14ef000ea44674cb9bbb7b3a87e3af00c0b18`
`G06_PUBLISHED_TREE=c2b372082cf44280f9717045578822e7b92bef12`
`G06_PUBLICATION_FINAL_PHASE=G06_PUBLICATION_PASS`

The supplied finalizer completed successfully against the real `main` remote: HEAD, origin/main and remote main all resolved to the published commit, the worktree was clean and the canonical-document count remained three. G06 is therefore `CLOSED / CERTIFIED / PUBLISHED`.

## 18. G07 — Recent / Save Copy / Version Copy / Properties / Statistics

Freeze: 2026-08-16, after direct audit of the published G06 source plus Mousepad, FeatherPad, gedit, GNOME Text Editor, L3afpad, Leafpad, Parchment and backup-semantics contrasts.

`G07_CONTRACT=FROZEN`
`G07_IMPLEMENTATION_AUTHORIZED=YES`
`G07_BASELINE_COMMIT=aae14ef000ea44674cb9bbb7b3a87e3af00c0b18`
`G07_BASELINE_TREE=c2b372082cf44280f9717045578822e7b92bef12`
`G07_FILE_MENU=NEW,OPEN,OPEN_RECENT,SAVE,SAVE_AS,SAVE_A_COPY,SAVE_VERSION_COPY,PROPERTIES,QUIT`
`G07_DOCUMENT_MENU=STATISTICS`
`G07_NEW_DEFAULT_ACCELERATORS=NONE`
`G07_RECENT_CAP=10`
`G07_RECENT_STORAGE=XDG_STATE_ATOMIC_JSON_0600`
`G07_RECENT_DURABILITY=ATOMIC_CONVENIENCE_NO_FSYNC`
`G07_RECENT_JSON_SCHEMA=VERSION_1_PATHS_ONLY`
`G07_RECENT_SESSION_RESTORE=FORBIDDEN`
`G07_RECENT_TOUCH=SUCCESSFUL_OPEN_AND_BINDING_CHANGING_SAVE_ONLY`
`G07_COPY_WRITER=EXISTING_GUARDED_FILE_WRITER_ONLY`
`G07_COPY_BINDING_CHANGE=FORBIDDEN`
`G07_COPY_SAVEPOINT_HISTORY_CHANGE=FORBIDDEN`
`G07_VERSION_COPY_PATTERN=STEM_vNNNN_SUFFIX_MAX_PLUS_ONE`
`G07_VERSION_COPY_INDEX_OR_TIMELINE=FORBIDDEN`
`G07_PROPERTIES=READ_ONLY_ACCEPTED_FACTS`
`G07_CHECK_NOW=STRONG_READ_ONLY_OBSERVATION`
`G07_CHECK_NOW_ACCEPT_BASELINE=FORBIDDEN`
`G07_CHECK_NOW_RELOAD=FORBIDDEN`
`G07_CHECK_NOW_CLASSES=UNCHANGED,CONTENT_CHANGED,METADATA_CHANGED,REPLACED_OR_RETARGETED,MISSING,UNAVAILABLE_OR_UNSTABLE`
`G07_STRONG_OBSERVER=SHARED_BY_LOADER_AND_PROPERTIES`
`G07_STATISTICS=EXPLICIT_ON_DEMAND_ONLY`
`G07_STATISTICS_COUNTS=LINES,WORDS,CHARACTERS`
`G07_STATISTICS_WORKER_TIMER_CACHE=FORBIDDEN`
`G07_STATISTICS_1M_MEDIAN_MAX_MS=1000`
`G07_STATISTICS_10M_MEDIAN_MAX_MS=1500`
`G07_STATISTICS_RSS_MAX_MIB=260`
`G07_FILE_MONITOR=DEFER_G11`
`G07_RELOAD=DEFER_G11`
`G07_DOCUMENT_AUTHORITY_COUNT=1`
`G07_PHYSICAL_WRITER_AUTHORITY_COUNT=1`
`G07_LIGHTWEIGHT_BUDGET_GATE=REQUIRED`

### 18.1 Recent is history, not session state

Recent stores only normalized absolute logical paths, exact-string deduplicated and MRU ordered, with a hard cap of ten. It is lazy: initial window construction must not require reading the history file. Corrupt or missing history means empty history without startup mutation. Successful Open and successful binding-changing Save As/first Save may touch Recent after the document operation has completed. Ordinary Save, New, failed/cancelled Open, Save a Copy, Save Version Copy, Check Now and Statistics never touch it. Persistence failure is a nonfatal convenience failure and cannot roll back or falsify document/session truth.
 Persistence is atomic convenience-state replacement, not document-save crash durability: the 0600 temporary file is closed and atomically replaced without file/directory fsync barriers. This refinement is required to keep Recent off the quick-edit latency budget and does not weaken GuardedFileWriter or any document write.

### 18.2 Non-binding copy authority

Save a Copy and Save Version Copy synchronize the exact live editor state through the existing prepare-for-save boundary, serialize under the active accepted representation profile, and delegate physical target observation/commit only to the existing `GuardedFileWriter`. They deliberately never call the binding/savepoint acceptance lane. The active logical path, accepted file state, current/saved state identities, Modified/Saved relation, DeltaHistory and Recent remain unchanged. The active logical path and any existing alias to the active physical object are forbidden copy targets. Existing targets require the normal frozen observation plus explicit overwrite consent; mixed EOL requires the same explicit normalization consent as Save.

A named Version Copy uses the active logical directory and exact `<stem>_vNNNN<suffix>` family, choosing `max(existing numeric suffix)+1`, with a minimum width of four decimal digits and no 9999 cap. A candidate appearing after planning fails closed rather than silently renumbering. Untitled requires an explicit chooser with suggested `Untitled_v0001.txt` and remains Untitled after success. No automatic backup, retention policy, manifest, revision database or version browser exists in G07.

### 18.3 Properties and shared strong observation

Properties projects accepted session/file facts only. `Check Now` invokes one GTK-free strong observer shared with the document loader: open logical path, require regular file, compare descriptor state before/after while streaming SHA-256, and verify logical/resolved namespaces still name the observed object. Read-only and multiple-link files are observable facts rather than observation failures. Classification order is missing; unavailable/unstable; replacement/retarget; raw-content change; metadata-only change; unchanged. Check Now never changes the accepted `DocumentFileState`, logical binding, savepoint/history, buffer or stale-Save decision and never starts a monitor. Reload/monitor remain G11.

### 18.4 On-demand Statistics only

Statistics captures the current GtkTextBuffer text exactly once on explicit activation and delegates to a pure GTK-free O(n) function. Characters are Unicode code points (`len(text)`); Words are maximal non-whitespace runs using `str.isspace()`; Lines are zero for empty text and otherwise newline count plus one. Selection uses identical rules; no byte count is shown. There is no live status subscription, cache, timer, worker or background analytics. Candidate qualification includes fresh-process medians of at most 1000 ms at 1 MiB and 1500 ms at 10 MiB with worker RSS at most 260 MiB.

### 18.5 Lightweight and serial-roadmap boundary

G07 adds no session/workspace manager, DB/XBEL/global recent dependency, automatic backup, file monitor, Reload, mutable Properties controls, duplicate Preferences surface, second writer or second document authority. The top-level menu architecture advances to File/Edit/Search/View/Document/Help, with Document containing only Statistics in G07. No future placeholder commands are inserted. G07 cannot reach user manual desktop validation until headless regression + strict architecture + Statistics performance + Lightweight Budget + real-App True-GTK product gates pass.


### 18.6 G07 desktop certification and publication boundary

`G07_CERTIFIED_SOURCE_TREE=12f24dbc265247bd9c014e2494fb91fc82f07af1`
`G07_AUTOMATED_DESKTOP=PASS`
`G07_MANUAL_DESKTOP=7/7_PASS`
`G07_VALID_CANDIDATE_ATTEMPTS_CONSUMED=1/2`
`G07_PRODUCT_RUNTIME_MUTATION_AFTER_CERTIFICATION=FORBIDDEN`
`G07_PUBLICATION_AUTHORITY_DELTA=THREE_CANONICAL_DOCS_PLUS_ADDITIVE_CERTIFICATION_EVIDENCE_ONLY`
`G08_IMPLEMENTATION_BEFORE_PUBLISHED_G07_AUDIT_MATRIX_FREEZE=FORBIDDEN`

The G07 publication line preserves the certified product runtime and user-visible implementation exactly. Earlier desktop stops caused by shared-desktop input exposure, comparator launch incompleteness and an unpinned Gdk major in the qualification tripwire were classified only after direct mature-source/source-boundary audits; none establishes a Graphium product defect. Qualification infrastructure must keep explicit toolkit-major ownership (`Gdk 3.0` + `Gtk 3.0`), distinguish desktop contamination/comparator blocks from product verdicts and route any unattributed STOP to failure-specific mature-source re-audit before repair.

G08 inherits the single-document, one-writer, content-neutral, startup-budget and no-background-service constraints. Printing must be lazy and must not create a startup-path dependency merely because File contains Page Setup, Print Preview and Print. Page setup may become a Graphium-owned persisted authority only after the G08 mature-source matrix and contract freeze; no print worker/service/session manager is pre-authorized by G07 closure.


## 19. G08 — Page Setup / Print Preview / Print + Startup Isolation

Freeze and implementation checkpoint: 2026-08-18, after real G07 publication proof and direct
preserved-source audit of Leafpad, L3afpad, Mousepad, gedit, GNOME Text Editor and FeatherPad.

`G08_CONTRACT=FROZEN`
`G08_BASELINE_COMMIT=7a3f49218dbabdbd6e47114a5fde2f4999f9c841`
`G08_BASELINE_TREE=198164be38e77538b92f45d5d53fe4b0c1929955`
`G08_IMPLEMENTATION=BUILT_NONCANDIDATE`
`G08_DESKTOP_CANDIDATE=NOT_DECLARED`
`G08_VALID_CANDIDATE_ATTEMPTS_CONSUMED=0/2`
`G08_FILE_PRINT_GROUP=PAGE_SETUP,PRINT_PREVIEW,PRINT`
`G08_PAGE_SETUP_ACCELERATOR=NONE`
`G08_PRINT_PREVIEW_ACCELERATOR=CTRL_SHIFT_P`
`G08_PRINT_ACCELERATOR=CTRL_P`
`G08_PRINT_ADAPTER=graphium.adapters.gtk.printing`
`G08_PRINT_ADAPTER_STARTUP_IMPORT=FORBIDDEN`
`G08_PRINT_CONTROLLER_STARTUP_OBJECT=NONE`
`G08_PAGE_SETUP_PATH=XDG_CONFIG_HOME/graphium/page-setup.ini`
`G08_PAGE_SETUP_SERIALIZATION=GTK_NATIVE_GtkPageSetup_FILE`
`G08_PAGE_SETUP_MODE=0600`
`G08_PAGE_SETUP_WRITE=COMPLETE_TEMP_FSYNC_ATOMIC_REPLACE`
`G08_PAGE_SETUP_LOAD=FIRST_PRINT_FAMILY_ACTION_ONLY`
`G08_PAGE_SETUP_CORRUPT_MISSING=FAIL_SOFT_DEFAULT_NO_REPAIR_WRITE`
`G08_PRINT_SETTINGS=PERSISTENCE_FORBIDDEN_PROCESS_MEMORY_ONLY`
`G08_PRINT_OPERATION=FRESH_PER_PREVIEW_OR_PRINT`
`G08_PRINT_OPERATION_ASYNC=GTK_NATIVE_ALLOW_ASYNC`
`G08_PRINT_INFLIGHT_AUTHORITY=ONE_OPERATION_PER_WINDOW`
`G08_PRINT_COMPLETION=GTK_DONE_SIGNAL_OR_SYNCHRONOUS_RUN_RESULT`
`G08_PRINT_OVERLAP=REJECT_WHILE_INFLIGHT`
`G08_ASYNC_REPAIR_TRIGGER=MEASURED_1M_PRINT_RESPONSIVENESS_FAILURE_PLUS_MATURE_SOURCE_REAUDIT`
`G08_PREVIEW=NATIVE_GTK_PREVIEW`
`G08_CUSTOM_PREVIEW=FORBIDDEN`
`G08_RENDERING=PANGO_CAIRO`
`G08_PAGINATION=GTK_ASYNC_INCREMENTAL_PANGO_CHUNKS`
`G08_BEGIN_PRINT_DOCUMENT_SCAN=FORBIDDEN`
`G08_PAGINATION_SIGNAL=GTK_NATIVE_PAGINATE`
`G08_PAGINATION_CHUNK_TARGET_CHARS=16384`
`G08_PAGINATION_CHUNK_MAX_LOGICAL_LINES=64`
`G08_PAGINATION_CHUNK_BOUNDARY=LOGICAL_LINE_ONLY`
`G08_PAGINATION_GLOBAL_PANGO_LAYOUT=FORBIDDEN`
`G08_INCREMENTAL_PAGINATION_REPAIR=BUILT_NONCANDIDATE`
`G08_INCREMENTAL_PAGINATION_REQUALIFICATION=PENDING_T480`
`G08_VISUAL_LINE_SPLIT_ACROSS_PAGES=FORBIDDEN`
`G08_GTK_SOURCE_VIEW_DEPENDENCY=FORBIDDEN`
`G08_PRINT_WORKER_THREAD_TIMER_QUEUE=FORBIDDEN`
`G08_PRINT_SNAPSHOT=EXACT_LIVE_GtkTextBuffer_TEXT_ON_ACTIVATION`
`G08_PRINT_TITLE=LOGICAL_BASENAME_OR_UNTITLED`
`G08_PRINT_FONT=PERSISTENT_BASE_FONT_FAMILY_SIZE`
`G08_TRANSIENT_ZOOM_AFFECTS_PRINT=NO`
`G08_SCREEN_LINE_NUMBERS_AFFECT_PRINT=NO`
`G08_SCREEN_WORD_WRAP_AFFECTS_PRINT=NO`
`G08_DOCUMENT_AUTHORITY_CHANGE=FORBIDDEN`
`G08_SAVEPOINT_HISTORY_RECENT_CHANGE=FORBIDDEN`
`G08_STARTUP_PAGE_SETUP_IO=ZERO`
`G08_T480_PYGOBJECT_PRINT_BINDING_PROBE=REQUIRED_BEFORE_CANDIDATE`
`G08_T480_PYGOBJECT_PRINT_BINDING_PROBE_STATUS=PENDING`
`G08_LIGHTWEIGHT_BUDGET_GATE=REQUIRED`

### 19.1 Lazy ownership boundary

`graphium.adapters.gtk.window` owns only a `None` print-controller reference during normal window
construction. The print implementation is imported inside the first Page Setup / Preview / Print
action. Construction of that controller is the first permitted Page Setup load and the first
permitted `GtkPrintSettings` allocation for this subsystem. No print service, worker, timer, queue,
printer history or print preference platform exists.

Page Setup is product configuration, not user-document I/O. Its native GTK payload is stored under
the product XDG config namespace. A missing, corrupt, unreadable or non-regular payload resolves to
a fresh `Gtk.PageSetup` without repair writes. On a changed accepted Page Setup, Graphium serializes
the GTK-native payload completely to a mode-0600 temporary file, fsyncs that completed temporary,
atomically replaces the product config file, and only then publishes the candidate setup in memory.
Persistence failure leaves the prior setup authoritative and shows one warning.

### 19.2 Rendering and pagination

Preview and Print capture the exact live buffer once, including Modified or Untitled content without
Save. The print font is the persistent base family/point size from View -> Font; transient Zoom is
ignored. Screen Line Numbers and Word Wrap do not become print options. A fresh
`GtkPrintOperation` receives a copy of Page Setup and process-memory Print Settings. After the
measured 1 MiB synchronous responsiveness failure, the failure-specific mature-source re-audit
re-opened only GTK's native async lifecycle: `allow_async=TRUE`, with one operation/job retained
until GTK `done` (or an immediate non-IN_PROGRESS result on a platform that completes
synchronously). Graphium still owns no worker, thread, timer, queue, progress service or custom
preview. A second Page Setup / Preview / Print activation is rejected while that one operation is
in flight.

The first async repair proved that `GtkPrintOperation.run(PREVIEW)` can return in a few milliseconds,
but a failure-specific real-mainloop diagnostic then localized the remaining 1 MiB freeze inside the
eager `begin-print` callback: heartbeat remained live until `BEGIN_PRINT_ENTER`, after which the
single document-global Pango layout/pagination scan starved the main loop. That eager model is
retired.

`begin-print` is now document-size-independent: it initializes only font, printable geometry,
cursors and incremental paginator state. GTK's native `paginate` signal owns progressive pagination.
Each callback measures at most one Pango chunk (target 16 KiB, maximum 64 logical source lines), and
each chunk boundary is a logical-line boundary. A single over-target logical line is consumed whole;
G04's 20,000-character interactive-line gate already bounds that fallback. Chunk layouts use
WORD_CHAR wrapping at the actual printable width. The GTK-free incremental paginator combines
measured visual-line spans across chunk boundaries and commits page breaks only between complete
Pango visual lines. `set_n_pages()` is published only when pagination finishes.

Graphium deliberately does not replace this with GtkSourceView/GtkSourcePrintCompositor, a worker,
thread, timer, queue or custom preview. Measured Pango chunk layouts are retained only for the
operation lifetime so `draw-page` can render the exact already-measured visual lines through
PangoCairo without re-laying out the complete document. A visual line remains indivisible for
pagination; if one measured line exceeds the body height it occupies a page intact. Native GTK owns
Preview UI. All per-operation layout/page references are discarded exactly once. Native `end-print` owns normal
render-geometry release; `done` owns operation/result lifetime and must not repeat that cleanup. The
controller may invoke render cleanup from `done` only as a fallback when GTK never emitted
`end-print`, while retaining only the minimal operation/job ownership needed until completion.

### 19.3 Document neutrality and startup qualification

Page Setup / Preview / Print may not change buffer text, logical/canonical binding, accepted file
state, current/saved editor state IDs, Saved/Modified, DeltaHistory, Undo/Redo, Recent or document
bytes. The only persistent mutation in G08 is an explicitly changed accepted Page Setup config.
Print APPLY may retain a copy of `GtkPrintSettings` only for the remaining process lifetime.

Before candidate promotion the T480 must prove the exact PyGObject GTK3/PageSetup/PrintOperation/
PangoCairo bindings with `tools/g08_print_binding_probe.py`. It must then pass the frozen hostile FIFO
startup-I/O tripwire, print-module/object absence at startup, G04-G07 regression gates, G08 True-GTK,
startup/performance comparison against fresh published G07, comparator FIRST_VISIBLE evidence and
Lightweight Budget. No candidate may be declared from the local non-GI environment alone.

### 19.4 G08 certification and publication boundary — 2026-08-20

The freeze/checkpoint markers above remain historical authority and are intentionally preserved verbatim.
Current closure authority is additive:

`G08_DESKTOP_CERTIFIED_SOURCE_TREE=420238bd82e7051fa01d002b92660a0ad4b1d40c`
`G08_FINAL_PREDESKTOP_NONCANDIDATE=PASS`
`G08_T480_PYGOBJECT_PRINT_BINDING_PROBE_FINAL=PASS`
`G08_INCREMENTAL_PAGINATION_REQUALIFICATION_FINAL=PASS_T480`
`G08_CANDIDATE_R2_AUTOMATED_20_LANES=PASS`
`G08_CANDIDATE_R2_MANUAL=PASS_6_OF_6`
`G08_CANDIDATE_LINE_ATTEMPTS_USED=2_OF_2`
`G08_PUBLICATION_RUNTIME_MUTATION=FORBIDDEN`

The certified product contract is the exact R2 tree above. Publication may change only canonical status/evidence authority: the three files under `docs/canonical/`, additive G08 certification evidence and `evidence/SHA256SUMS.txt`. Runtime (`graphium/`), launchers (`bin/`), user documentation (`docs/user/`), tests and qualification tools must remain byte-for-byte equivalent to the certified product. Publication is valid only after fail-closed proof of the published G07 parent, exact target publication tree, remote fast-forward, `HEAD=origin/main=remote main` and clean worktree.

## 20. G09 — Explicit Text Transformations Only / No Format-Menu Expansion

`G09_CONTRACT=FROZEN`
`G09_BASELINE_COMMIT=5d1c342eafbff8b4b38f0656e0dbc1fe315362b4`
`G09_BASELINE_TREE=6535bf7d560ceaed3e31f407317fde0a8618ba47`
`G09_IMPLEMENTATION=BUILT_NONCANDIDATE`
`G09_DESKTOP_CANDIDATE=NOT_DECLARED`
`G09_VALID_CANDIDATE_ATTEMPTS_CONSUMED=0/2`
`G09_MENU=EDIT_TRANSFORM_TEXT_SUBMENU`
`G09_TOP_LEVEL_FORMAT_MENU=FORBIDDEN`
`G09_ACTIONS=UPPERCASE,LOWERCASE,DUPLICATE_LINE_SELECTION,MOVE_LINES_UP,MOVE_LINES_DOWN,TRIM_TRAILING_SPACES`
`G09_MOVE_LINES_UP_ACCELERATOR=ALT_UP`
`G09_MOVE_LINES_DOWN_ACCELERATOR=ALT_DOWN`
`G09_OTHER_ACCELERATORS=NONE`
`G09_PLANNER=GTK_FREE_IMMUTABLE_TRANSFORMATION_PLAN`
`G09_MUTATION_AUTHORITY=NATIVE_EDITOR_APPLY_PREVALIDATED_PROGRAMMATIC_GROUP`
`G09_SECOND_MUTATION_ENGINE=FORBIDDEN`
`G09_DIRECT_WINDOW_GTK_TEXT_MUTATION=FORBIDDEN`
`G09_GTKSOURCEVIEW=FORBIDDEN`
`G09_BACKGROUND_WORKER_TIMER_CACHE=FORBIDDEN`
`G09_PERSISTENT_TRANSFORM_STATE=FORBIDDEN`
`G09_CHANGED_SPAN_CAP=50000`
`G09_UNDO_GROUPS_PER_ACTUAL_TRANSFORM=1`
`G09_NOOP_STATE_ID_CHANGE=FORBIDDEN`
`G09_OPEN_SAVE_IMPLICIT_TRANSFORM=FORBIDDEN`
`G09_CASE_SCOPE=NONEMPTY_SELECTION_ONLY`
`G09_CASE_UNICODE=PYTHON_FULL_STRING_UPPER_LOWER_LOCALE_INDEPENDENT`
`G09_MOVE_TERMINAL_SENTINEL=MOVABLE_NO`
`G09_TRIM_WHITESPACE=U+0020_OR_U+0009_BEFORE_LF_OR_EOF_ONLY`
`G09_HEADLESS_PLANNER_1M_MEDIAN_MAX_MS=1000`
`G09_TRUE_GTK_1M_ACTION_MAX_SECONDS=3.0`
`G09_T480_PRE_CANDIDATE_QUALIFICATION=PENDING`

G09 adds only explicit, user-invoked plain-text transformations. The planner is application-layer,
GTK-free and stateless; all mutation, stale-plan rejection, renderer safety, Undo payload checks,
rollback and savepoint identity remain owned by the certified G05 native-editor programmatic edit
authority. Selection direction is part of the postcondition. Move Lines treats an LF-created final
zero-length sentinel as non-movable and preserves final-EOL representation under line swaps. Trim
Trailing Spaces removes only ASCII space/tab trailing runs and never runs automatically on Open or
Save. Candidate R1 remains forbidden until live canonical G08 Git identity and all T480
pre-candidate desktop/performance/shortcut gates pass.

### 20.1 G09 certification and publication boundary — 2026-08-21

The G09 freeze/checkpoint markers above remain historical authority and are intentionally preserved
verbatim. Current closure authority is additive:

`G09_DESKTOP_CERTIFIED_SOURCE_TREE=92bcae4fcf72684872a9fa675007156bd0a4de3c`
`G09_T480_PRE_CANDIDATE_QUALIFICATION=PASS`
`G09_CANDIDATE_R1_AUTOMATED_20_LANES=PASS`
`G09_CANDIDATE_R1_MANUAL=PASS_6_OF_6`
`G09_CANDIDATE_LINE_ATTEMPTS_USED=1_OF_2`
`G09_PRODUCT_FAILS=0`
`G09_PUBLICATION_RUNTIME_MUTATION=FORBIDDEN`

The original Test 5 human FAIL is not product authority: the runner had already proved the exact Trim
saved-byte postcondition, and the subsequent source-first/mature-source audit plus unchanged-tree
manual reissue established an invalid manual-oracle false negative. Reissue 1 stopped before product
launch on a harness-only Bash defect; Reissue 2 changed no product bytes and PASSed Tests 5 and 6.
Candidate R2 was never declared.

The certified product contract is the exact R1 tree above. Publication may change only canonical
status/evidence authority: the three files under `docs/canonical/`, additive G09 desktop-certification
evidence and `evidence/SHA256SUMS.txt`. Runtime (`graphium/`), launchers (`bin/`), user documentation
(`docs/user/`), tests and qualification tools must remain byte-for-byte equivalent to the certified
product. Publication is valid only after fail-closed proof of the published G08 parent, exact target
publication tree, remote fast-forward, `HEAD=origin/main=remote main` and clean worktree.


GS07 VALIDATION REBASELINE (2026-08-21)
The active qualification architecture is permanent and concern-oriented: Behavioral/Unit, Integration/Filesystem, True-GTK Desktop, Packaging/Release. Historical Gxx qualification names and executable evidence/doc prose oracles are retired from active validation. G10 remains frozen until GS07 desktop rebaseline is proven on T480.

### Permanent qualification boundary after GS07 assessment — 2026-08-22

The assessed permanent qualification architecture has four logical owners: Behavioral/Unit,
Integration/Filesystem, True-GTK Desktop, and Packaging/Release. Historical Gxx validation universes,
exact test-count/prose oracles and compatibility wrappers are not product architecture. Runtime
product identity contains stable product/version/application identity only; Candidate, attempt,
commit, tree and work-item lineage are external release-engineering state. Installed/runtime payload
excludes tests, legacy/shadow validation, certification evidence and qualification-only support.
The GS07 assessed tree is not canonical until a separate Git cutover transaction succeeds.

### GS07 canonical validation baseline — 2026-08-22

After a successful canonical Git cutover, the four permanent qualification authorities are the only
active validation ownership model: Behavioral/Unit, Integration/Filesystem, True-GTK Desktop and
Packaging/Release. Historical Gxx validation universes are provenance only. Runtime product bytes
must remain independent from Candidate/attempt/commit/tree/work-item state, and installed product
payload excludes the certification laboratory. Reintroducing compatibility wrappers or executable
historical validation requires a new source-grounded mature-source audit and explicit authorization.

## 21. G10 terminal boundary and G11 Reload / live-monitor contract — 2026-08-24

G10 did not publish. Candidate R1 and R2 each ended in a valid user-visible product failure; the
line is terminal at 2/2 and R3 is forbidden. A later NON-CANDIDATE recovery is retained only as a
carry-forward reference. G11 therefore derives formally from the canonical GS07 parent and selectively
reproduces only the proven user behavior needed for the v1 surface; Candidate/attempt/tree/publication
lineage remains external release engineering and never enters runtime identity.

`G11_RELOAD=FILE_RELOAD_FROM_DISK_F5`
`G11_RELOAD_MODIFIED_DECISION=CANCEL_OR_DISCARD_CHANGES_AND_RELOAD`
`G11_RELOAD_WRITER_INVOCATION=FORBIDDEN`
`G11_RELOAD_RECENT_MUTATION=FORBIDDEN`
`G11_MONITOR_BACKEND=GIO_FILE_MONITOR_WATCH_MOVES`
`G11_MONITOR_EVENT_AS_TRUTH=FORBIDDEN`
`G11_MONITOR_TRUTH=EXISTING_STRONG_OBSERVER_PLUS_CLASSIFIER`
`G11_PERIODIC_POLLING=FORBIDDEN`
`G11_MAX_CONCURRENT_STRONG_OBSERVATIONS=1`
`G11_GENERIC_JOB_FRAMEWORK=FORBIDDEN`
`G11_AUTO_RELOAD=FORBIDDEN`
`G11_EXTERNAL_UI=ONE_NONMODAL_INFOBAR`
`G11_DIRECT_SYMLINK_COVERAGE=RESOLVED_TARGET_PLUS_LOGICAL_PATH_TOPOLOGY`
`G11_CANDIDATE_ATTEMPTS=1_OF_2`

### 21.1 Reload is deliberate disk re-acceptance, not Save

Reload is available only for a named document. A Saved document may be fully reloaded directly. A
Modified document receives a dedicated destructive choice: Cancel, or Discard Changes and Reload.
Cancel preserves the buffer/session/history/binding exactly. Discard and Reload invokes no writer;
it completely loads and validates the current logical path and only then installs the fresh document
state. Reload never touches Recent. This is deliberately asymmetric with ordinary Save, which retains
the G03/G07 strong accepted-baseline and fail-closed stale-target policy.

### 21.2 Monitor events are interrupts; strong observation remains truth

The GTK/Gio adapter owns filesystem event subscription only. Relevant events are coalesced and schedule
`observe_document()` outside the GTK main thread. Classification remains the existing strong Check Now
classification against the immutable accepted `DocumentFileState`: unchanged, content changed,
metadata changed, replaced/retargeted, missing, or unavailable/unstable. No raw Gio event, mtime,
ETag or timer may establish accepted document truth.

Exactly one strong observation may execute concurrently. If a lifecycle transition creates a new
monitor generation while an older read is still running, the stale result is discarded but a pending
current-generation initial verification must still run. If newer verification work is already pending
within the same generation, the just-finished older result is suppressed and only the coalesced newer
observation may reach the UI. This prevents knowingly obsolete external-state presentation without
adding a worker pool, unbounded queue or generic job framework.

### 21.3 Lifecycle, symlink and UI ownership

Open/New/Save/Save As/Reload/accepted Close suspend or invalidate old monitor ownership and bind fresh
monitor state to the actual resulting accepted document. An initial asynchronous strong observation
closes the load-to-monitor-bind race. Untitled has no monitor. Graphium's own accepted writes therefore
do not rely on a time heuristic to suppress false external-change warnings.

For a directly symlink-opened document, one monitor covers the accepted resolved target and one narrow
parent-directory monitor filters events for the logical symlink path, so target-content change and
logical replacement/retarget/removal both cause fresh strong observation. Arbitrary ancestor symlink
component expansion is not part of the G11 contract without new evidence.

External change is presented through one persistent nonmodal `Gtk.InfoBar`. Content change and
replacement/retarget offer Reload; missing/unavailable states do not mutate the buffer; metadata-only
change is informational. The monitor never silently updates accepted `DocumentFileState` and never
auto-reloads.

### 21.4 Slow-filesystem and qualification boundary

Strong observation hashes content and therefore must not run on the GTK main thread. G11 has no
periodic poller or idle hashing. Scheduler-independent monitor state-machine semantics belong to the
permanent Behavioral/Unit authority: one-worker pending ownership, stale-generation discard,
same-generation obsolete-result suppression and the exactly-one follow-up scheduling decision. The
permanent True-GTK monitoring authority covers only the real platform boundary: Gio event ownership,
strong same-size/same-mtime detection through the production observer, own-Save suppression, atomic
replacement plus Guarded Save fail-closed behavior, missing files, direct symlink target/retarget cases,
slow-observer GTK-main-loop responsiveness and nonmodal UI/no-dialog-storm behavior.

The permanent qualification topology remains the four GS07 authorities only: Behavioral,
Integration/Filesystem, True-GTK Desktop and Packaging/Release. G11-specific executable validation
universes are forbidden. Manual Reload/monitoring tests are not qualification authority; modal response
and external fixture transitions are machine-owned. User-PC/T480 execution is permitted only when the
real Gio/GTK platform boundary cannot be established otherwise, and diagnostic reruns are forbidden.

## 22. G12 — V1 Product Closure / Six-Menu Competitive Qualification — contract freeze 2026-08-24

`G12_CONTRACT=FROZEN`
`G12_BASELINE_COMMIT=10be01b7909c3efe6f76b4c80ea46d1586aea65c`
`G12_BASELINE_TREE=82619dfb95df46a33ca6d0e08ade282be44ff2c1`
`G12_MODE=NONCANDIDATE_SOURCE_FIRST`
`G12_CANDIDATE_ATTEMPTS=0_OF_2`
`G12_TOP_LEVEL_MENUS=FILE,EDIT,SEARCH,VIEW,DOCUMENT,HELP`
`G12_REPRESENTATION_CONVERSION=EXPLICIT_DOCUMENT_STATE_NOT_IMMEDIATE_WRITE`
`G12_DIRTY_AUTHORITY=COMPOSITE_TEXT_STATE_PLUS_REPRESENTATION_RELATION`
`G12_SECOND_DIRTY_AUTHORITY=FORBIDDEN`
`G12_REPRESENTATION_UNDO=NOT_TEXT_UNDO`
`G12_NORMAL_SAVE_IMPLICIT_CONVERSION=FORBIDDEN`
`G12_PHYSICAL_WRITER=GuardedFileWriter_ONLY`
`G12_ENCODING_CHOICES=UTF8,UTF8_BOM,UTF16_LE_BOM,UTF16_BE_BOM,UTF32_LE_BOM,UTF32_BE_BOM`
`G12_LINE_ENDING_CHOICES=LF,CRLF,CR`
`G12_LEGACY_ENCODING_GUESSING=FORBIDDEN`
`G12_INSTALL_MODEL=MINIMAL_PRODUCT_ONLY_PREFIX_INSTALL`
`G12_APPSTREAM_METADATA=DEFERRED_UNTIL_PROJECT_LICENSE_AUTHORITY_EXISTS`
`G12_HELP_MENU=USER_GUIDE,KEYBOARD_SHORTCUTS,ABOUT`
`G12_COMMON_CROSS_PRODUCT_METRIC=FIRST_VISIBLE_ONLY`
`G12_COMMON_FIRST_EDITABLE=REJECTED_NO_HOMOGENEOUS_EXTERNAL_LIFECYCLE`
`G12_GRAPHIUM_FIRST_EDITABLE=INTERNAL_READY_PIPE_ONLY`
`G12_COMPARATOR_PROCESS_OWNERSHIP=EXACT_PID_PLUS_POST_EXIT_X11_QUIESCENCE`
`G12_COMPARATOR_BLOCKED=INCOMPLETE_NOT_PASS_NOT_PRODUCT_FAIL`
`G12_T480_BEFORE_SOURCE_ONLY_EXHAUSTION=FORBIDDEN`
`G12_PRODUCT_VERSION=0.0.12_PUBLISHED`
`G12_NONCANDIDATE_PLATFORM_PROOF=PASS_LANES_1_17_PLUS_REBASELINED_FIRST_VISIBLE_RSS`
`G12_PLATFORM_SOURCE_TREE=648c4891b7e1ee2cb798b747fafb50fd7ed817ba`
`G12_PRODUCT_SUBTREE=1eb5c018574d330907d7f0cab0353074e7b37fe6`
`G12_COMPETITIVE_RECEIPT_SHA256=9031403e1de3ec68db070c00e43c0d6d633799ba84fbafc10f2dcfe99fec7059`
`G12_CANDIDATE_R1=DECLARED_CERTIFIED_PUBLISHED_ATTEMPTS_1_OF_2`

### 22.1 Representation conversion extends the one document-state relation

G12 resolves the earlier v1 SHOULD/MUST tension in favor of the already frozen six-menu closure:
**Encoding** and **Line Endings** are v1 MUST commands because the Document menu is defined as the
home of observed representation facts and explicit conversion. This does not authorize encoding
guessing, locale fallback, a codec platform or implicit normalization.

The G02 editor-state relation remains the text-history authority, but G12 extends the final document
Saved/Modified relation to the exact pair of text identity and serialization profile. One active
`DocumentSession` owns both the current and saved representation profile; this is an extension of the
same document-state authority, not a second dirty flag. The final relation is:

```text
current_editor_state_id == saved_editor_state_id != None
AND current_representation_profile == saved_representation_profile  -> Saved
otherwise                                                           -> Modified
```

Open establishes current=saved representation from the accepted disk load. New establishes UTF-8,
no BOM, LF. A representation command changes only the current profile: it does not mutate text,
create a text Undo record, touch the filesystem or alter the accepted disk baseline. Choosing the exact
saved profile again naturally returns to Saved when the text identity is also at its savepoint.
Undo/Redo changes text history only; a pending representation choice survives text Undo/Redo.

The only exposed encoding targets are profiles that Graphium itself can reopen without heuristics:
UTF-8 without BOM; UTF-8 with BOM; UTF-16 LE/BE with BOM; UTF-32 LE/BE with BOM. UTF-16/32 without
BOM, locale encodings and guessed legacy code pages are not exposed. Line-ending targets are LF,
CRLF and CR. Mixed EOL is observable but never selectable as an output profile. Selecting any concrete
line ending on a mixed source is itself explicit normalization consent and clears the pending
`mixed_source` condition; changing encoding alone does not silently grant EOL-normalization consent.

Save, Save As, Save a Copy and Save Version Copy serialize the exact current representation profile
through the existing pure serializer and the one `GuardedFileWriter`. Save/Save As may advance only
the exact captured text state and captured representation state. If text or representation changes
while I/O is in flight, late completion leaves the newer current document Modified. Copy/version-copy
uses the current representation but never advances the active saved relation. A fresh post-commit load
remains the accepted disk fact; when serialized bytes cannot physically encode a preference (for
example a file containing no line separators), the accepted post-commit observation wins rather than
preserving a fictitious on-disk representation.

Document submenus separate observation from action through one stateful choice list: the active
radio choice is the current representation, choosing a different target is the explicit conversion
action, and choosing the exact-current target is a no-op. No extra `Current:` row or duplicated
`Convert to …` command family is required. The compact status and Properties remain truthful
projections of the current document representation and accepted disk facts respectively;
implementation must not invent a second representation cache.

### 22.2 Mature-source disposition for representation

Mousepad directly stores line-ending/BOM state beside its saved state and marks unbuffered
representation changes Modified; gedit carries explicit encoding/newline choices through Save As;
Leafpad/L3afpad normalize editor text internally and serialize with retained charset/line-ending state.
Graphium ADAPTs the mature principle but rejects weaker modified booleans, encoding guessing and any
second write path. Its exact state-ID safety is preserved by the composite relation above.

### 22.3 Minimal install/runtime projection

G12 closes install behavior without adopting a packaging framework. One small standard-library
installer under `bin/` owns a prefix-based, staging-capable installation. Default user prefix is
`~/.local`; an explicit `--prefix` and `--destdir` permit system/package staging. The installed product
projection is limited to:

- `PREFIX/lib/graphium/graphium/**` runtime package;
- `PREFIX/lib/graphium/bin/graphium` runtime launcher;
- `PREFIX/lib/graphium/docs/user/**` offline Help;
- `PREFIX/bin/graphium` launcher link into that private runtime root;
- `PREFIX/share/applications/io.github.leviagravia.Graphium.desktop`.

The desktop entry uses the existing application ID, `Exec=graphium %F`, `MimeType=text/plain`,
`Terminal=false`, appropriate Utility/TextEditor categories and the freedesktop generic
`accessories-text-editor` icon. A bespoke icon is not a G12 closure requirement. Tests, evidence,
canonical development documents, self-test launchers and qualification support are forbidden from
the installed runtime projection. Staged-install tests must prove launchability and exact exclusion.

AppStream/metainfo is DEFERRED rather than fabricated because Graphium has no frozen project-license
authority from which legally meaningful metadata can be derived. This deferral does not block ordinary
desktop launching, MIME association or v1 install behavior and may be revisited only with an explicit
license decision.

### 22.4 Help/command authority final wording

G12 freezes the already implemented, lower-churn Help wording: **User Guide**, **Keyboard Shortcuts**,
**About**. `Graphium Help` and `About Graphium` in the earlier roadmap target are superseded. This
matches the existing offline documents and conventional in-application Help-menu context without
adding redundant product-name words. Menu, command catalog and offline Help/shortcut documents must
derive from this same command authority. The earlier `System Information` idea is satisfied inside
About as compact support facts for the running Python, GTK and display backend; it never becomes a
separate diagnostics command, menu or subsystem.

### 22.5 Common competitive qualification oracle — FIRST_VISIBLE only

G12 closes the failed common-FIRST_EDITABLE experiment by returning to the two-metric model frozen in
G04. **FIRST_VISIBLE is the only homogeneous cross-product latency metric.** Graphium's inherited-pipe
FIRST_EDITABLE remains an exact product-owned metric and is used only for Graphium regression/admission;
no comparator FIRST_EDITABLE ratio is claimed in v1.

The common FIRST_VISIBLE protocol is qualification-only and owns only evidence that the compared
applications actually share:

1. `empty` is a true no-file launch; 5 KiB / 1 MiB / 10 MiB use exact-size disposable UTF-8/LF
   fixtures with recorded SHA-256 hashes;
2. each run uses fresh HOME/XDG roots and exact process isolation: Graphium/Leafpad/L3afpad normally,
   Mousepad with `--disable-server`, FeatherPad with `--standalone`;
3. the monotonic clock starts immediately before spawn;
4. readiness is the first current X11 top-level whose `_NET_WM_PID` equals the exact spawned PID. A
   pre-spawn XID novelty set is not a second ownership authority; exact PID is the semantic owner;
5. after every sample, terminate/kill if necessary and then wait, boundedly, until no X11 top-level is
   still owned by the exited PID before another fresh sample begins. Non-quiescence is comparator/X11
   BLOCKED evidence;
6. every blocked run preserves command, exact PID, process return code, exact-PID window snapshots and
   bounded stdout/stderr in the incremental receipt. Missing comparator/process isolation/X11 ownership
   yields `BLOCKED_INCOMPLETE`, never Graphium product FAIL and never PASS;
7. one priming/session-first observation plus at least seven measured runs is retained. Measured order is
   deterministic and balanced/interleaved across applications; no cherry-picking or silent sample
   replacement is allowed;
8. any real RawKeyPress/RawButtonPress during a measured run invalidates the execution as environmental
   contamination. The benchmark itself generates no input;
9. the receipt records versions, source/product identity, workload sizes/hashes, metric definition,
   isolation, raw runs, median, p90, execution order, blocked diagnostics and final target verdicts, and
   is persisted incrementally after every run.

The existing G04 FIRST_VISIBLE admissions remain the only hard cross-product latency gates: Graphium
empty <= 2.0x Mousepad or <= 750 ms, and Graphium 5 KiB <= 2.0x Mousepad or <= 900 ms. 1 MiB/10 MiB
gaps against all permanent comparators are reported without inventing a new ratio threshold. The former
G12 1.5x/1.75x FIRST_EDITABLE targets are **withdrawn as invalid**, not reinterpreted as FIRST_VISIBLE.

G12 retains the independent no-file memory target as **stable post-visible RSS**, not as a claim that a
generic external oracle knows each editor's internal idle lifecycle. For Graphium and Mousepad, after
exact-PID FIRST_VISIBLE the runner samples process RSS until five consecutive samples spanning at least
0.4 s have <= 1.0 MiB spread. The resulting median must satisfy Graphium <= 150 MiB and <= 2.5x
Mousepad. Failure to obtain a stable window is BLOCKED/INCOMPLETE; a fixed sleep is not called idle.

AT-SPI, Accessible Text/EditableText, focus state, sentinel projection and input synthesis/direct
accessibility mutation are intentionally absent from the cross-product comparative authority. They may
be used in product-specific accessibility tests only when that interface itself is the feature under
test; they are not promoted into file-load or keyboard-readiness authorities.

### 22.6 G12 source-only implementation slices and validation boundary

G12 is deliberately split so final closure cannot become a feature dump:

- **S1 — Representation state foundation:** composite Saved/Modified relation, exact conversion
  profiles, late-save/copy semantics and headless hostile tests.
- **S2 — Document menu + projection/help synchronization:** two bounded submenus, no new top-level
  menu, no new accelerator unless separately justified, user-guide updates and True-GTK source gates.
- **S3 — Minimal install projection:** prefix/staging installer, desktop entry and packaging/release
  tests proving product-only installation.
- **S4 — Cross-product readiness-oracle study:** the original AT-SPI common-FIRST_EDITABLE attempt is
  historically retained as a rejected experiment. The final permanent result is a small comparator
  primitive authority for isolated commands/workloads plus the common FIRST_VISIBLE receipt; no AT-SPI
  dependency or universal external FIRST_EDITABLE remains.
- **S5 — Final source-only convergence:** six-menu/anti-bloat/dead-code/canonical-status audit and
  complete permanent local authorities.

No T480 run is permitted before S1-S5 have exhausted source-provable work. If the exact source-only
pre-candidate tree then has no blocker, one consolidated automated NON-CANDIDATE T480 qualification
may be requested for the real GTK/X11/comparator/platform boundary. Human tests remain default 0
and are permitted only for a genuinely visual property not owned by permanent automation. Candidate
R1 remains undeclared at 0/2 until that boundary and the post-PASS source audit are complete.

### 22.7 S5 source-only convergence closure

S5 completes all source-provable v1 convergence before any platform run. `TOP_LEVEL_MENUS` in the
product command catalog is the sole six-menu ordering authority consumed by the GTK menu builder;
no second hardcoded menu topology remains. The exact Help surface is User Guide / Keyboard Shortcuts /
About, Preferences owns only Tab width and Insert spaces instead of tabs, Check Now remains inside
Properties, and About owns only compact support information rather than a diagnostics platform.

A reachability audit removes only source-proven dead code with no runtime/test/document references:
the obsolete composition descriptor API, an unused native-editor checkpoint, an unused native-group
wrapper, an unused session save-confirmation alias, an unused print page-setup copy property and an
unused GTK string-state helper. Framework-owned `Gtk.Application.do_activate` and `do_open` overrides
are explicitly retained despite direct-call reachability being absent.

G12 uses the next serial unpublished product version `0.0.12`; G11 remains the canonical `0.0.11`
release. S1-S5 are now source-only complete. Candidate R1 remains undeclared at 0/2. The only remaining
pre-candidate evidence boundary is one consolidated automated NON-CANDIDATE T480 qualification for
real GTK/X11/comparator behavior and final performance evidence; no manual test is authorized by
this closure.

### 22.8 Post-platform-stop oracle amendment

The first consolidated G12 NON-CANDIDATE T480 qualification passed lanes 1-14 and stopped at the new
Lane-15 closure gate before lanes 16-18. Source-first comparison with Leafpad, L3afpad, Mousepad,
FeatherPad, GNOME Text Editor, gedit and Calamus W116 proved a qualification-oracle class defect, not
a product-core failure. The immediate Lane-15 defect was querying `Gtk.Application.get_menubar()` even
though Graphium intentionally owns the concrete `Gtk.MenuBar` in `GraphiumWindow`. The broader audit
also invalidated the initial S4 completion rule because Leafpad/L3afpad/FeatherPad (and Graphium's own
`do_open()` ordering) can expose an editable/focused view before requested file Open completion.

The rebuilt closure contract therefore requires real window-owned menu inspection, semantic markers for
every closure postcondition, workload-load witnesses before FIRST_EDITABLE input, true no-file empty
startup, separate FIRST_VISIBLE measurement, explicit contamination ownership, BLOCKED != PASS,
truthful RSS naming/settlement and a complete raw comparative receipt. Product changes merely to make
a qualification oracle pass are forbidden. `DocumentSession`, composite Saved/Modified,
`GuardedFileWriter` and the strong monitor remain unchanged unless independent product evidence proves
otherwise.
### 22.9 Focused Lane-18 BLOCKED result and common-FIRST_EDITABLE retirement

The focused 2026-08-25 Lane-18 T480 run on source tree
`cda7d34a54a57e40a140ab0e8ddc70312fa06df3` ended `BLOCKED_INCOMPLETE` with 33 blocked series. The
pattern involved all five applications: widespread exact-PID FIRST_VISIBLE timeouts, all five empty
`EditableText` acceptance timeouts, and all five non-empty workload-witness timeouts. Graphium and
Mousepad still produced valid process RSS evidence, so the result does not support a Graphium-specific
product failure.

Deep direct-source re-audit against Leafpad, L3afpad, Mousepad, FeatherPad, gedit, GNOME Text Editor,
historical Graphium G04/G07 and Calamus W116 identifies the harness/contract errors: G07's mandatory
post-exit X11 quiescence was lost; XID novelty was added as a second ownership heuristic; focus,
accessibility exposure, file-load completion and editability were collapsed into ambiguous timeouts;
AT-SPI Text was promoted into a file-load transaction receipt; and `EditableText.insert_text()` was
promoted into a user-keyboard-readiness oracle even though mature editors own editing through their
actual view/input lifecycle. Block diagnostics also regressed below G07's already-frozen command/PID/
window/output capture standard.

Binding disposition: **retire the common external FIRST_EDITABLE experiment.** Do not keep repairing it
until it passes. Restore G04's explicit two-metric boundary, recover G07 exact-PID/quiescence/diagnostic
discipline for FIRST_VISIBLE, keep Graphium internal FIRST_EDITABLE for Graphium-only self-regression,
and keep stable post-visible RSS as a separate process-level comparison. No Graphium runtime or safety
authority is implicated by this rebaseline.
### 22.10 FIRST_VISIBLE/RSS source-only rebaseline closure

The source-only implementation of section 22.5 removes the rejected `first_editable.py` common oracle
and replaces it with `tests/desktop/harness/comparators.py`, which owns only comparator command/process
isolation, workload bytes and disposable environment setup. No AT-SPI import or accessibility lifecycle
assumption remains in the permanent cross-product harness. The external qualification authority uses
exact-PID X11 ownership, G07-style post-exit quiescence, complete blocked-run diagnostics, incremental
receipt persistence and balanced measured order. Stable post-visible RSS is a separate process metric.
All 293 permanent local tests pass and Structural Continuity is net-reductive versus the rejected
common-FIRST_EDITABLE tree. Graphium runtime bytes are unchanged.

## 23. G13 Crash Recovery Cache — frozen safety boundary

G13 recovery is restart-persistent **private application state**, never user-document Save. Its root is
`XDG_STATE_HOME/graphium/recovery`, created lazily only when storage is required. One active document
generation owns one random canonical UUID and therefore one current `<uuid>.recovery` artifact plus an
advisory `<uuid>.lock`; Graphium's `NON_UNIQUE` process topology forbids a single global recovery file.
A live process holds the advisory lock and process death releases ownership automatically; no session
database or clean-shutdown marker is introduced.

The recovery artifact is self-validating and versioned. The body is always normalized in-memory text
encoded as strict UTF-8. Current and saved encoding/BOM/EOL profiles are metadata only, along with the
capture time, generation/state token and, for named documents, a descriptive copy of accepted logical/
canonical path, device/inode when known and accepted SHA-256 fingerprint. Recovery metadata never
becomes `DocumentFileState`, a savepoint or accepted identity. Untitled recovery carries no invented file
identity. Corrupt, truncated, wrong-version or digest-invalid bytes fail closed.

`RecoveryArtifactStore` is a deliberately separate writer for this private UUID-derived state and has no
arbitrary destination-path API. It must not import or reuse `GuardedFileWriter`/normal Save authority.
`GuardedFileWriter` remains the sole physical writer authority for accepted user documents. Recovery
persistence uses a private unique temp file, complete write, file `fsync`, local length/digest readback,
atomic `os.replace`, then recovery-directory `fsync`; artifact/lock files are 0600 and the recovery root
is 0700. Failure cannot mutate the user target or Saved/Modified authority.

### 23.1 G13 implementation slices

- **S1 — storage core:** record/codec, XDG root, UUID artifact, advisory lock, atomic durability and
  headless hostile tests only. No GTK, scheduling, worker, lifecycle integration or restore UI.
- **S2 — lifecycle/state machine:** fixed 30-second one-shot scheduling/coalescing, stable buffer capture,
  one dedicated recovery worker, generation race protection and exact Save/Open/Reload/Close invalidation.
- **S3 — startup recovery:** lazy orphan discovery, live-lock exclusion, one claimed-and-reread orphan
  per launch, explicit-open association, Recover/Discard/Start Without Recovering presentation, strong
  target revalidation, exact-match named restore or fail-closed unbound restore, and empty post-crash
  Undo/Redo; no session browser/preferences. No-recovery startup creates neither recovery directory nor
  executor/thread.
- **S4 — consolidated exact-byte qualification:** permanent authorities and post-implementation mature
  audit; platform/T480 only if a real remaining claim is source-unprovable. Candidate requires separate
  authorization.

S1, S2 and S3 are complete as NON-CANDIDATE source work. S4 is also complete: the exact S3 tree passed 173 Behavioral + 150 Integration + 13 Packaging/Release = 336/336 local authorities, Structural Continuity, post-implementation mature-source falsification, and the indispensable fresh-process T480 True-GTK recovery probe 4/4 with identical pre/post source tree. The pre-Candidate consolidation advances the unpublished product identity to `0.0.13`; all recovery implementation bytes remain identical to the S4-proven tree. G13 Candidate R1 was explicitly authorized, declared and certified on the frozen 0.0.13 source. Candidate certification adopts the S4 True-GTK 4/4 platform proof because the only product-byte delta after that proof is the serial version literal in `graphium/product.py`; every recovery/lifecycle/GTK-recovery byte is unchanged. The exact Candidate re-passes 173 Behavioral + 150 Integration + 13 Packaging/Release = 336/336 and Structural Continuity. Attempt accounting is 1/2 used, 1/2 remaining; publication requires separate explicit authorization.



### 23.2 G13 Candidate R1 publication authorization

The user explicitly authorized continuation with G13 after Candidate R1 certification. Publication is a separate fail-closed Git transaction. The certified Candidate product subtree `033ae482b19cf81a4852cf4e22773b2740387443`, tests subtree `b1911fdee492d9fea5655182913d9e63eb8c37ed`, launchers and `docs/user/` are frozen publication inputs. Publication may change only the three canonical authority documents, additive `evidence/G13_DESKTOP_CERTIFICATION_RECEIPT_20260825.txt`, and regenerated `evidence/SHA256SUMS.txt` relative to the certified Candidate. The finalizer must start from canonical HEAD `f32beeeca58fdc4d68b7d9253ec98d2b76b38018` / tree `23c6dde1b69f36b71dcaa6eb0deb4b19f2370075`, apply the exact G13 Candidate delta, prove the frozen publication target tree, re-run 336/336 permanent local authorities and Structural Continuity, commit with subject `G13: add crash recovery cache`, push, verify `HEAD=origin/main=remote main`, and leave the worktree CLEAN. No new T480 functional or manual test is required by publication; the binding S4 True-GTK 4/4 evidence remains the platform proof.

### 23.3 G13 publication closure and canonical convergence

The user-executed fail-closed G13 publication finalizer completed successfully on 2026-08-25. The
authoritative product publication identity is commit `053bcde3f5bcb4f51ce9edd8a89538a7630949ae`, tree
`eb6925d3b779fa8ae12d1d0947a31fe460fbee0e`, product subtree
`033ae482b19cf81a4852cf4e22773b2740387443`, version `0.0.13`, commit subject
`G13: add crash recovery cache`. The finalizer proved Behavioral 173/173, Integration 150/150,
Packaging/Release 13/13 = 336/336 PASS, G13 focused 43/43 PASS, Structural Continuity PASS, adopted
the binding S4 True-GTK 4/4 proof, and finished with local HEAD, `origin/main` and real remote main
identical and a CLEAN worktree. No new T480 functional or manual test was required by publication.

The subsequent read-only audit found no product, test, platform or Candidate defect. It found only
pre-finalizer current-state wording in the precomputed publication target. This explicitly authorized
post-publication convergence changes only the three canonical documents plus additive final-publication
evidence and its SHA-256 manifest. `graphium/`, `bin/`, `tests/` and `docs/user/` remain byte-identical
to the published G13 product. The historical G13 Candidate/platform certification receipt remains
unchanged; `evidence/G13_PUBLICATION_FINAL_RECEIPT_20260825.txt` records the completed transaction.

G13 is therefore **CLOSED / CERTIFIED / PUBLISHED**. G14 External Spellcheck is the next Core work item
but remains **NOT OPENED**. It may be opened only after the final post-sync read-only audit passes and
the user gives separate explicit authorization.

### 24. G14 External Spellcheck Core boundary — S1

G14 is OPEN as NON-CANDIDATE work after explicit authorization. Its permanent capability boundary is optional and user-triggered: no spell process, dictionary discovery, worker or spell I/O belongs to startup/idle. S1 adds `graphium.domain.spellcheck` as the pure code-point span authority and `graphium.infrastructure.hunspell_session` as the only Hunspell subprocess authority. The latter accepts only an absolute resolved executable path, spawns an argv list with `shell=False`, uses `hunspell -a -i UTF-8 --check-apostrophe`, prefixes every checked token with `^`, never accepts a document pathname, bounds token/protocol/suggestion sizes, uses strict UTF-8 parsing, and owns terminate/kill/wait on timeout, cancellation, protocol fault or close.

Graphium owns document span mapping and Hunspell owns dictionary/morphology/suggestion semantics. Unicode letters and combining marks form lexical material; internal ASCII/U+2019 apostrophes and simple hyphens may remain inside spans; overlong spans are skipped. Arbitrary raw document lines are not a protocol unit. S1 has no GTK, menu/dialog, `DocumentSession`, edit/history or Save authority and does not create a generic external-tool framework. Later S2 must consume this boundary through the existing Graphium programmatic-edit authority rather than mutate `Gtk.TextBuffer` or the user target directly.


### 24.1 G14-S2 spell-session and edit-authority boundary

S2 adds a GTK-free `SpellCheckController` as a per-explicit-dialog state machine, not as a persistent
service. One session snapshots current editor text plus positive state identity, advances a code-point
cursor in document order, owns only exact-session Ignore/Ignore-All state, emits one immutable token request
at a time, and accepts only its matching result. Any editor state-id change while a request or issue is
outstanding makes the session stale and prevents mutation; external failure never authorizes an edit.

Spell replacement is planned from an exact `WordSpan` and is committed only through
`NativeEditorController.apply_prevalidated_programmatic_group()`. The native controller exposes a generic
`capture_programmatic_source()` + current-state-id fence but owns no Hunspell semantics. Changed replacement
is one normal Undo/Redo group; identical replacement is a no-op; custom or empty replacement remains an
explicit ordinary edit; final renderability, rollback, savepoint transition and notification are inherited
from the pre-existing programmatic edit authority. Spell checking does not change representation profile and
does not write the user target.

The command identity is frozen centrally as `CHECK_SPELLING_COMMAND = CommandSpec("check-spelling",
"Check Spelling…", "F2", "Document")` but is intentionally not yet projected in `COMMANDS`. S3 alone may
project that same identity into menu/action/accelerator/help and add the thin GTK dialog. No S2 runtime
path imports GTK or creates/spawns a spell worker/process.

S2 qualification is 190 Behavioral + 167 Integration + 14 Packaging/Release = 371/371 PASS, with G14
focused unique 35/35 PASS and Structural Continuity PASS (`validation_loc=4764`, `harness_loc=1198`) without
rebaseline. G14 remains NON-CANDIDATE; S3 requires separate explicit authorization.

### G14 external spellcheck — S3 GTK projection boundary (2026-08-25)

G14 S1/S2/S3 is implemented NON-CANDIDATE. The product command is exactly **Document → Check Spelling…**
with **F2**. The GTK adapter is lazy-imported only by that explicit action; normal startup/composition must
not import the adapter, resolve Hunspell, create a spell worker/thread, spawn a child, or scan dictionaries.

The dialog is deliberately thin: **System default** dictionary, one Unknown word, bounded suggestions or a
custom replacement, **Replace / Ignore / Ignore All / Close**. One dialog owns one `SpellCheckController`,
one `HunspellPipeSession`, and at most one single-worker executor created only at the first real token
request. Hunspell pipe I/O is off the GTK main thread and results are delivered by `GLib.idle_add`; dialog
close/fault cancels/reaps the child and shuts down the worker. The adapter never receives a document path
for Hunspell and owns no file writer, Save authority, alternate Gtk.TextBuffer mutation path or persistent
spell state.

Replace remains exclusively the S2 programmatic-edit authority and ordinary Undo/Redo semantics. Missing
Hunspell/dictionary/process/protocol failure must be user-visible and non-mutating. Live underline,
continuous scanning, daemon/service, automatic language detection, persistent language selection,
personal-dictionary management, Correct All, autocorrect and grammar checking remain outside G14 Core.

S3 does not itself establish desktop certification. Consolidated exact-byte qualification and any narrowly
necessary True-GTK proof belong to S4 before any Candidate declaration.


### 24.2 G14-S4 consolidated qualification and Candidate-readiness boundary

S4 closes the pre-Candidate qualification of the G14 Core spellcheck boundary. The exact S3 product bytes
passed the full permanent local authorities (190 Behavioral + 167 Integration + 16 Packaging/Release =
373/373), G14 focused unique 37/37 and Structural Continuity. A narrowly scoped fresh-process T480 probe on
exact source tree `3c31e2072666b11e81b731fdb8532e950a37d12c` passed 4/4 True-GTK scenarios: clean startup,
optional capability absent, Replace + ordinary Undo, and Ignore All. It also proved no spell worker/thread
or Hunspell child exists on clean startup. No manual test is required.

Candidate readiness may not reuse the published G13 version identity. The only allowed product change after
that platform proof is the serial identity literal in `graphium/product.py`, `0.0.13` -> `0.0.14`; the three
canonical documents may record the new governance state. Every spellcheck protocol/session/controller/GTK
byte, every other product byte, tests, launchers and user documentation must remain identical to the
S4-proven source. Because this delta cannot alter spellcheck/GTK behavior, the S4 4/4 platform evidence and
Lightweight Runtime PASS remain binding without a redundant T480 run.

G14 Candidate R1 was explicitly authorized, declared and certified on the frozen `0.0.14` source. Candidate
certification preserves the Candidate-ready product bytes and adopts the S4 True-GTK 4/4 plus Lightweight
Runtime proof because the only product-byte delta after that proof is the serial version literal in
`graphium/product.py`; every spellcheck protocol/session/controller/GTK byte is unchanged. The exact Candidate
re-passes 190 Behavioral + 167 Integration + 16 Packaging/Release = 373/373, G14 focused 37/37, Structural
Continuity and Lightweight static. Attempt accounting is 1/2 used, 1/2 remaining. Publication requires
separate explicit authorization.


### 24.3 G14 Candidate R1 publication authorization

The user explicitly authorized publication after G14 Candidate R1 certification. Publication is a separate
fail-closed Git transaction from canonical parent `8a847a793b9d84f76161c41cce261dd82b3deb17` / tree
`65318ce6847304ccbcce31767311857fb42798f3`. The certified Candidate source tree is
`0d629e31762836e3fe7574e8f1fd16e0166b336e`; product subtree
`396be05aaa0cc32e18341889e5494163151f4606`, tests subtree
`38463612ab04f1c213055d31bc1a971d55646e67`, and `docs/user/` subtree
`c470b92dbd0fc8db27143dea0306e8440e6b7521` are frozen publication inputs.

Relative to Candidate R1, publication may alter only the three canonical authority documents, additive
`evidence/G14_DESKTOP_CERTIFICATION_RECEIPT_20260825.txt`, and regenerated `evidence/SHA256SUMS.txt`.
`graphium/`, `bin/`, `tests/`, and `docs/user/` must remain byte-identical. The finalizer must re-run the
373/373 permanent local authorities, G14 focused 37/37, Structural Continuity and Lightweight static,
then prove the exact staged target, commit with subject `G14: add external spellcheck`, push/fetch, prove
`HEAD=origin/main=remote main`, and finish CLEAN.

The binding S4 True-GTK 4/4 and `PASS_NO_STARTUP_SPELL_THREAD_OR_CHILD` evidence remain the desktop/
Lightweight Runtime proof. Publication must not repeat T480/manual validation because no Candidate product
byte changes in the publication-only delta. Candidate accounting remains 1/2 used and 1/2 unused.
Graphium Plus and Graphium Ultra remain defined but unopened.


### 24.4 G14 / Graphium Core publication closure and canonical convergence

The authorized fail-closed G14 publication finalizer succeeded on the canonical repository and published
commit `51fc8f329be730a237f28e195fb1617de07a93d8`, tree `b0469a014a2451cfd2fa92a942583eeab02d25e1`, product subtree `396be05aaa0cc32e18341889e5494163151f4606`,
version `0.0.14`, with subject `G14: add external spellcheck`. The transaction requalified 190/190
Behavioral, 167/167 Integration and 16/16 Packaging/Release = 373/373 PASS, G14 focused 37/37 PASS,
Structural Continuity PASS and Lightweight static PASS; it adopted the binding S4 fresh-process True-GTK
4/4 and `PASS_NO_STARTUP_SPELL_THREAD_OR_CHILD` evidence, performed no new T480 functional or manual
test, proved `HEAD=origin/main=remote main`, and left the worktree CLEAN. Candidate accounting remains
1/2 used and 1/2 unused historically.

The mandatory read-only post-publication audit found no product, test, platform or Lightweight Budget
failure. Its only blocker was pre-finalizer canonical wording that could not know the final commit hash.
This separately authorized convergence therefore changes only the three canonical documents, adds
`evidence/G14_PUBLICATION_FINAL_RECEIPT_20260825.txt`, and regenerates `evidence/SHA256SUMS.txt`.
`graphium/`, `bin/`, `tests/` and `docs/user/` remain byte-identical to the published G14 product. The
historical `G14_DESKTOP_CERTIFICATION_RECEIPT_20260825.txt` remains immutable pre-publication evidence.

G14 and Graphium Core are **CLOSED / CERTIFIED / PUBLISHED / FEATURE-COMPLETE**. No G14 Candidate is
reopened and no remaining attempt is consumed. Graphium Plus and Graphium Ultra remain separate cumulative
product-line definitions; neither is opened by this convergence. Graphium Plus may become authorization-ready
only after the required final post-sync read-only audit confirms the converged repository.

## Application icon identity — G15 Core corrective authority

Graphium has one stable application icon identity: `io.github.leviagravia.Graphium`, equal to the existing
GTK/desktop application ID. The desktop entry must reference that icon by name, never by an absolute path
or by the generic `accessories-text-editor` identity.

The authoritative artwork is bounded to five SVG assets: hand-tuned 16x16, 24x24, 32x32 and 48x48 variants
plus one scalable variant. Source assets live under `data/icons/hicolor`; installation projects those exact
bytes under `<prefix>/share/icons/hicolor/.../apps/`. The installed private Python/runtime projection must
not duplicate the icon assets. Direct source execution may load the same repo-local five assets as a
process-local GTK default-icon fallback so it does not depend on a prior Graphium installation.

The same GTK default application/window icon is inherited by About when no independent About logo authority
is set. G15-S1 must not introduce GResource, a branding/resource framework, icon-cache subprocesses,
network lookup, toolbar/action icon packs, new background work or a second application identity.


### G15-S2 direct tab-control authority

Graphium has no general Preferences surface in G15-S2. The two pre-existing persistent editor-input settings
remain owned only by `ViewSettings` and `JsonViewSettingsStore`, with the unchanged `tab_width` and
`insert_spaces` keys, default 8/false and tab-width domain 1..32. Their user projection is direct and unique:
`Edit -> Tab Width -> 2 / 3 / 4 / 8 / Other…` and checked `Edit -> Insert Spaces Instead of Tabs`. `Other…`
is a narrow numeric chooser only and owns no persistence. A custom current width is represented by the
`Other…` action state.

Persistence commits before action/TextView projection; persistence failure must leave the prior semantic
snapshot, action state and TextView behavior intact. Merely changing either setting must not alter document
text, dirty state, history, file bytes or recovery authority. Existing plain-Tab insertion and modified-Tab
non-ownership remain unchanged. No GSettings, GtkSourceView, EditorConfig/modeline support, per-document
setting, migration layer or generic preferences framework is permitted by this slice.

### G15-S3 Hunspell dictionary-selection authority

Graphium retains the existing optional, explicit external Hunspell boundary and adds no spelling service,
plugin framework, binding, daemon, settings store or document metadata. Dictionary discovery occurs only
after the user invokes `Document -> Check Spelling…`; the already-existing single spell executor is reused.
The discovery child is short-lived, bounded, cancellable and fully reaped before a pipe-mode spell child may
start. Normal startup/import/idle behavior remains free of Hunspell discovery, worker and child-process cost.

Discovery invokes the resolved Hunspell executable with `-D`, `shell=False` and `LC_ALL=C`. Human headings
and search-path prose are not parsed as protocol. A selectable candidate must be an absolute bounded base path
reported by Hunspell for which both `<base>.aff` and `<base>.dic` are current regular files. Output size,
dictionary count and path size are bounded; unsafe control/comma semantics are rejected; duplicate dictionary
IDs remain distinct and are disambiguated with parent-path context. `System default` is always the first UI
choice and remains usable when discovery itself fails.

System default preserves the pre-G15 pipe argv with no `-d`. An explicit selection adds exactly one separate
`-d <verified-base-path>` argv pair. The base pair is revalidated when the spell child starts, so disappearance
after discovery fails closed rather than silently selecting another dictionary. No document path is passed to
Hunspell.

The Dictionary combo is dialog-local only: no value is written to ViewSettings, JSON, document metadata or
restart state. Changing dictionary fences old callbacks, reaps the old Hunspell session, rejects an externally
stale editor state, snapshots the current Graphium-owned text through a fresh `SpellCheckController`, resets
Ignore All and restarts from the beginning under the selected dictionary. Prior Replace operations remain
ordinary Graphium edits and normal Undo/Redo history; dictionary selection itself never changes text, dirty
state, savepoint, representation profile or file bytes.



### G15-S4 Transform Text shortcut authority

The product-owned command catalog is the single accelerator authority for the two case transforms. Uppercase
uses exactly `<Ctrl>U`; Lowercase uses exactly `<Ctrl><Shift>L`. The same command specs drive GTK application
accelerator registration, menu projection and Help documentation. The transform implementations, selection
availability, document transaction/history ownership and no-op behavior are unchanged by this slice.

`<Ctrl><Shift>U` is a permanent negative oracle because GTK3 reserves Ctrl+Shift+U for Unicode code-point
input. `<Ctrl><Alt>L` remains forbidden because Cinnamon uses it for lock screen; Graphium does not introduce
Ctrl+Alt letter bindings or multi-stroke/chord infrastructure for these actions. The exact accepted pair was
validated read-only on the T480 against GTK3/Gtk.TextView, Graphium's current accelerator namespace and active
Cinnamon global bindings. No keyboard manager, new module, dependency, preference, persistence or per-document
metadata is permitted by G15-S4.

### G15-S5 Help / About / legal authority

Graphium's project license authority is exactly one top-level `LICENSE`. It begins with the Graphium
GPL-3.0-or-later grant (`either version 3 ... or (at your option) any later version`) and then contains the
unchanged complete GNU GPL version 3 body. `graphium/product.py` remains the single product metadata owner and
contains the exact values `AUTHOR = leviagravia@zohomail.eu`, `COPYRIGHT = Copyright © 2026 leviagravia`,
`LICENSE_ID = GPL-3.0-or-later`, repository URL `https://github.com/leviagravia/graphium` and repository label
`Graphium repository`. Version remains 0.0.14 throughout NON-CANDIDATE slices.

Help > About remains a standard `Gtk.AboutDialog`. It projects the product author, copyright and repository
metadata and uses `Gtk.License.GPL_3_0`, whose GTK3 contract is GNU GPL 3.0 or later. Existing Python/GTK/display
support information remains present. About owns no icon asset, file path, pixbuf loader or resource framework:
with no independent logo, it reuses the already-certified G15-S1 default application/window icon authority.
The private repository link remains present even while the repository is not public; Graphium performs no
network/reachability check.

Installation copies the single repository `LICENSE` byte-for-byte into the private installed Graphium root;
no second COPYING/license authority or license viewer is created. Help topology remains exactly User Guide,
Keyboard Shortcuts and About. The User Guide introduction has no source hard break inside `Graphium does not
use tabs...` and ends with exactly one compact Latin-name explanation. This slice creates no new Python product
module, dependency, configuration/persistence key, thread, subprocess, network boundary, i18n subsystem or
source-wide license-header churn.



### G15-S6 integral structural closure and Candidate-readiness authority

G15-S1 through G15-S5 are closed at NON-CANDIDATE True-GTK PASS. S6 introduces no product delta and proves
34/34 structural gates plus 190/190 Behavioral, 176/176 Integration and 40/40 Packaging/Release = 406/406
on the exact cumulative line. Runtime module topology remains 57 modules with no new import root/dependency;
only seven pre-existing runtime owners differ from G14. `composition.py`, `architecture.py`, `ViewSettings`
and `JsonViewSettingsStore` remain byte-identical to G14. The +248-line S3 spelling-boundary growth is accepted
as essential complexity because it owns bounded/cancellable distro-agnostic external Hunspell discovery,
reap and stale fencing without gspell/libspelling, startup discovery or hard-coded dictionary paths.

Candidate readiness advances only the product release identity from published `0.0.14` to unpublished
`0.0.15`, plus the corresponding release-test expectation and canonical/evidence convergence. Every S1-S5
feature implementation byte outside `graphium/product.py`, all launchers and all `docs/user/` bytes remain
frozen to the final S5 True-GTK-proven source. The 0.0.15 identity-only delta does not require another T480
or manual test. Candidate R1 is NOT declared; attempts remain 0/2; Git mutation and publication are not
authorized. Graphium Plus remains NOT OPENED.

### G15 Candidate R1 certification and publication boundary — 2026-08-26

G15 Candidate R1 is certified on version `0.0.15`, exact source tree
`42884dfbd4c5abd725d928bcb76e1064dbec23b7`, product subtree
`1f63eca6724b379abab8e8d534667723e57276f6`, tests subtree
`875cae3f501fd566b49ee25b5bf613f72cedb1d7`, user-docs subtree
`8f5d3ef7dbe936eab18c2ed8447a487a6fe337df`, bin subtree
`585f06bf0ad4dada4675bfd5c11eb9fc793057ef` and data subtree
`042e5dc2d043061c89e33170f5e35cd54a17e328`. Certification passed 190/190 Behavioral, 176/176 Integration
and 40/40 Packaging/Release = **406/406 PASS**, plus **34/34 structural gates PASS**. The already completed
S1-S5 focused T480 True-GTK receipts are the binding platform evidence for the cumulative feature bytes;
manual tests are 0. Candidate accounting is 1/2 used, 1/2 remaining.

The user separately authorized the fail-closed G15 publication transaction. Publication must start only from
canonical post-G14-sync HEAD `cd685ecf060a57e5239f641e9e30dd7a7b8144e5`, tree
`8cfe2c194829e3d59487b2f596129c36cfe1856f`, with real `main` remote synchronized and a clean worktree/index.
Relative to certified Candidate R1, publication may change **exactly five paths**: the three canonical documents,
additive `evidence/G15_DESKTOP_CERTIFICATION_RECEIPT_20260826.txt`, and regenerated
`evidence/SHA256SUMS.txt`. `graphium/`, `bin/`, `tests/`, `docs/user/`, `data/` and `LICENSE` are immutable
Candidate-protected bytes. The commit subject is frozen as **`G15: complete core corrective maintenance`**.
Publication itself consumes no additional Candidate attempt and requires no new T480/manual test. Until the
finalizer proves commit, push, fetch, `HEAD=origin/main=remote main` and CLEAN worktree, G15 remains
**CANDIDATE R1 CERTIFIED / PUBLICATION AUTHORIZED / FINALIZER REQUIRED**, not yet PUBLISHED. Graphium Plus
remains **DEFINED / NOT OPENED**.


### G15 publication closure and post-publication canonical convergence — 2026-08-26

The authorized fail-closed G15 publication finalizer succeeded on the canonical repository and published
commit `16b645ed653be5b44efa8721db11cca63f0633bd`, tree `e433758d1d68ef5bea6528e15e65d786e0679d31`, product subtree `1f63eca6724b379abab8e8d534667723e57276f6`, version `0.0.15`, with subject
`G15: complete core corrective maintenance`. The transaction requalified 190/190 Behavioral, 176/176
Integration and 40/40 Packaging/Release = **406/406 PASS**, plus **34/34 G15 structural gates PASS**; it
adopted the binding S1-S5 focused T480 True-GTK evidence, performed no new T480 functional or manual test,
proved `HEAD=origin/main=remote main`, and left the worktree CLEAN. Candidate accounting remains 1/2 used
and 1/2 unused historically.

The mandatory post-publication read-only audit found no product, test, platform, structural or packaging
failure. Its only convergence item is the expected pre-finalizer canonical-state drift: the publication target
could not contain the final commit hash before that commit existed. This separately authorized convergence
therefore changes only the three canonical documents, adds
`evidence/G15_PUBLICATION_FINAL_RECEIPT_20260826.txt`, and regenerates `evidence/SHA256SUMS.txt`.
`graphium/`, `bin/`, `tests/`, `docs/user/`, `data/` and `LICENSE` remain byte/mode-identical to the published
G15 product. Historical pre-publication and True-GTK evidence remains immutable.

G15 and Graphium Core 0.0.15 are **CLOSED / CERTIFIED / PUBLISHED**. No G15 Candidate is reopened and no
remaining attempt is consumed. Graphium Plus and Graphium Ultra remain separate product-line definitions and
are not opened by this convergence. The authoritative G15 product publication identity remains commit
`16b645ed653be5b44efa8721db11cca63f0633bd` / tree `e433758d1d68ef5bea6528e15e65d786e0679d31` / product subtree `1f63eca6724b379abab8e8d534667723e57276f6` even if this governance-only convergence advances
canonical repository HEAD.

### G16 About-icon corrective authority — supersedes the G15 implicit-logo assumption

A post-G15 real screenshot proved that relying on an unset GtkAboutDialog logo is not a valid projection of the
application icon. GtkAboutDialog's `logo-icon-name` default may resolve to `image-missing`; therefore About must
explicitly project Graphium's existing application-icon authority.

The single icon identity remains `graphium.product.APPLICATION_ICON_NAME` and the five G15-S1 hicolor assets
remain the only icon assets. About may not own an SVG path, About-specific file/resource or second icon name.
When the current Gtk.IconTheme resolves `APPLICATION_ICON_NAME`, About sets that exact named identity. When the
name is not theme-resolvable in a direct source run, About may reuse `Gtk.Window.get_default_icon_list()` and
select only the existing exact 48x48 Graphium pixbuf already loaded by application bootstrap. This fallback does
not create a new authority or loader.

True-GTK certification must prove identity, not mere pixbuf existence: source mode must compare the About logo
pixels with the canonical 48x48 Graphium asset under an icon-theme search path that cannot accidentally see an
installed Graphium icon; staged-installed mode must prove the theme resolves `APPLICATION_ICON_NAME` and that
About projects that name. A generic `image-missing` pixbuf or 16x16 placeholder can never satisfy this contract.


### G16 pre-Candidate gutter and Hunspell response-group corrective authority

Graphium's line-number implementation continues to use Gtk.TextView's native LEFT border window. Because Graphium draws this gutter itself, its background is part of the same editor appearance authority: the existing GraphiumTextView GtkStyleContext must render the gutter background before line-number glyphs. No independent gutter color constants, widget, GtkSourceView dependency, preference or CSS/palette subsystem may be introduced. Explicit Light/Dark and System restoration must therefore propagate through one style authority.

The external Hunspell process remains the only optional spell-engine boundary. A `hunspell -a` request owns a bounded response group consisting of one or more nonblank result records followed by one blank terminator. Graphium must consume the full group under one timeout, per-line limits, a 64-record group limit and a 64-KiB group limit before issuing the next request. Single-record groups retain current exact suggestion semantics. For multi-record groups, all-correct means the Graphium lexical span is correct; any miss means the span is incorrect and component-level suggestions are not exposed as whole-span replacements. The Graphium apostrophe/hyphen lexical model remains unchanged. Once executable and dictionary discovery succeed, protocol/timeout/process failures must not be presented as an installation-absence error. Existing child cancellation, terminate/kill/reap, dictionary revalidation, one-worker ownership, stale-result fencing and startup laziness remain mandatory.


### G16 Candidate-readiness freeze — corrective closure authority

The G16 cumulative corrective product is closed at NON-CANDIDATE True-GTK PASS before Candidate declaration. The existing application-icon authority is explicitly projected into About; the custom Gtk.TextView LEFT border-window gutter is painted through the same editor GtkStyleContext before line-number glyphs; the optional external `hunspell -a` boundary consumes bounded complete response groups and separates installation absence from protocol/timeout/runtime failures. No new runtime module, dependency, config key, icon asset, appearance palette authority, spell worker, subprocess type or lexical model is introduced.

After the final focused T480 proof, no functional byte may change for Candidate readiness. The only product delta permitted by the readiness freeze is `graphium.product.VERSION` `0.0.15` -> `0.0.16`; matching release-test identity plus canonical/evidence convergence are non-feature authority updates. Candidate R1 remains undeclared until separately authorized.


### G16 GtkAboutDialog Credits appearance authority

`Gtk.AboutDialog` remains the sole About implementation. Its internal Credits `GtkViewport.view` is not a separate visual authority: when Graphium explicit Light or Dark mode is active, that viewport participates in the same `GtkAppearanceRenderer` / single screen CSS provider and the same editor-family background/foreground rule as other text-bearing views. `graphium.adapters.gtk.dialogs` may not own Credits-specific CSS, widget-tree recoloring or a custom Credits surface. System mode removes the application provider and restores the GTK baseline. No second palette, CSS provider, module, dependency or persistent setting is permitted for Credits styling.

### G16 final Credits qualification authority

The standard GtkAboutDialog Credits viewport participates in the single Graphium appearance authority and has real GTK proof in both source-run and staged-installed projections. Explicit Light must render the Credits viewport in the same light family with readable foreground; Dark must remain coherent and readable; System must restore the underlying GTK baseline without stale Graphium projection. The About logo identity must remain Graphium during this transition. The validation harness may inspect rendered colors, but deprecated or diagnostic-only GTK calls used by the harness are not product dependencies. No custom Credits implementation or second appearance authority is permitted.

### G16 Candidate R1 certification and publication boundary — 2026-08-27

G16 Candidate R1 is certified on version `0.0.16`, exact source tree `48ef29541e1068cb890c305c4ddfa57aab7310bd`, product subtree `e09d45ec07aad4956c0edead777cb61588eb758a`, tests `f86a01225586cb88133c053c21e9829f82ab5581`, user docs `8f5d3ef7dbe936eab18c2ed8447a487a6fe337df`, bin `585f06bf0ad4dada4675bfd5c11eb9fc793057ef` and data `042e5dc2d043061c89e33170f5e35cd54a17e328`. The complete G16 platform evidence chain and final user desktop verification are PASS. Candidate attempt 1/2 is consumed; 1/2 remains.

The user explicitly authorized publication. Publication may alter exactly the three canonical authority documents, additive `evidence/G16_DESKTOP_CERTIFICATION_RECEIPT_20260827.txt`, and regenerated `evidence/SHA256SUMS.txt` relative to Candidate R1. `graphium/`, `bin/`, `tests/`, `docs/user/`, `data/` and `LICENSE` are publication-protected and must remain byte/mode-identical. The transaction must start from canonical HEAD `15ae13fa153d77db74470d5718e8ab9bbbb5708c` / tree `0bb9335c717f371481c752818c5f83fdb9cb16f3`, use commit subject `G16: finalize core corrective release`, push to real `origin/main`, fetch and prove `HEAD=origin/main=remote main`, then leave the worktree CLEAN. No new functional T480 test is justified because publication cannot change product bytes.

Until that transaction completes, G16 is **CANDIDATE R1 CERTIFIED / PUBLICATION AUTHORIZED / FINALIZER REQUIRED**. Graphium Plus and Ultra remain **DEFINED / NOT OPENED**.



### G16 publication closure and post-publication canonical convergence — 2026-08-27

The authorized fail-closed G16 publication transaction succeeded at commit
`b4b447423de8eb6f6d4022639497ca1f6b3daca6`, tree `90c651815400851ebcc0ff5300b2807261fb33fe`, product subtree
`e09d45ec07aad4956c0edead777cb61588eb758a`, version `0.0.16`, with subject
`G16: finalize core corrective release`. The publication preserved the certified Candidate product/tests/user-doc/
bin/data/LICENSE bytes, passed 190/190 Behavioral and 54/54 Packaging/Release, adopted the previously qualified
181/181 Integration authority on byte-identical product/integration owners, preserved the complete focused G16
True-GTK evidence chain and final user desktop validation, and ended with zero known user-visible G16 defects.
The canonical repository finished with `HEAD=origin/main=remote main` and CLEAN worktree. Candidate accounting
remains 1/2 used and 1/2 unused historically.

The first publication-finalizer execution was an invalid harness stop in canonical preflight caused solely by
manifest working-directory context; it reached no stage, commit or push and is not a product/Candidate failure.
The authorized harness-only reissue changed no Graphium or publication-target byte and completed publication.

The post-publication convergence is therefore restricted to the three canonical documents, additive
`evidence/G16_PUBLICATION_FINAL_RECEIPT_20260827.txt`, and regenerated `evidence/SHA256SUMS.txt`.
`graphium/`, `tests/`, `docs/user/`, `bin/`, `data/` and `LICENSE` remain byte/mode-identical to the published G16
product. No Candidate is reopened, no attempt is consumed, and no new T480 functional/manual test is justified.

Graphium Core 0.0.16 is **CLOSED / CERTIFIED / PUBLISHED / CANONICALLY CONVERGED** by this revision. The next
product-adjacent activity is the public GitHub surface/release preparation and full Git-history hygiene audit;
Graphium Plus and Graphium Ultra remain separately defined and **NOT OPENED**.

### Graphium Plus 0.0.1 cumulative-edition publication authority — 2026-08-28

Graphium Plus is a separate cumulative product line, not a Core runtime feature flag. Its canonical repository is
`leviagravia/graphium-plus`, with one-time Git lineage from exact public Graphium Core HEAD
`8899c94006757c066c88739ff84bf8e1a6cb1b35`. Core remains independently usable and imports no Plus module.
Plus may reuse inherited Core modules and may introduce only minimal generic seams in inherited `graphium/` when
Core-default behavior remains equivalent and the inherited Core layer gains no Plus import.

The Plus 0.0.1 additive runtime is `graphium_plus/` plus the `graphium-plus` launcher/installer and independent
`io.github.leviagravia.GraphiumPlus` desktop/XDG/icon identity. The editor continues to own exactly one active
DocumentSession, one editor buffer/view authority, one physical writer and one canonical command authority.
The compact GTK toolbar is only a projection of existing actions. The Workspace owns one local root and uses
lazy one-directory loading; it adds no watcher, indexer, database, project/session graph, recursive startup scan
or background worker. `.txt` and `.md` activation routes through Graphium's canonical Open lifecycle. Filesystem
mutations remain bounded, root-confined and fail-closed; Move to Trash has no permanent-delete fallback.

Graphium Plus uses the exact Graphium icon geometry with a red colorway. The original Graphium icon remains the
Core identity and may be shown on the repository public page only as lineage attribution; it must not replace or
compete with the red Graphium Plus icon as the Plus product identity.

Candidate R2 is certified on runtime manifest
`756d7978bc651b1e0b54973ccdb06d777fa15e22fdacbe8089250947675e8dd7` with zero known open product blockers.
Publication may alter only the three canonical documents, one additive Candidate-R2 certification receipt and
`evidence/SHA256SUMS.txt`. Runtime, tests, user Help, launchers/installers, desktop/icon assets, LICENSE and the
inherited public-surface README/assets are publication-protected. The first remote is created private; public
README/logo/release metadata and visibility are a later repository-surface transaction.


### Graphium Plus 0.0.1 GitHub public-surface authority — 2026-08-28

Graphium Plus 0.0.1 product publication is complete at commit
`b6b3709d9fbb100844302625adacd014b95a1c96`, tree
`a558bbb3a6cee3dbd412e909df1a1e67ce636340`, parent exact public Graphium Core commit
`8899c94006757c066c88739ff84bf8e1a6cb1b35`. GitHub public-surface work is distribution/governance only and
must not change any certified runtime, test, installed Help, launcher/installer, desktop or product icon byte.

The public Graphium Plus identity uses the existing scalable red Plus application icon as the README hero. The
original dark Graphium icon may appear only as a smaller lineage marker linking to Graphium Core. README wording
must keep Plus architecturally accurate: one Graphium document authority plus compact toolbar and bounded lazy
Workspace; no project/session authority, watcher, indexer, recursive startup scan, background Workspace worker,
database, tabs, plugin platform or cloud service may be implied.

The public README must include the name origin: Latin `graphium`, meaning a stylus/writing implement, associated
with writing on wax tablets. This naming text is descriptive branding only and creates no runtime authority.

A GitHub `v0.0.1` release must not claim or attach an installer/package until that release artifact is separately
frozen. Repository visibility may become PUBLIC after exact Git/source identity, public-surface target, history
hygiene, authenticated metadata and anonymous-read verification gates are satisfied.

### Graphium Plus 0.0.1 final release and post-release convergence authority — 2026-08-29

Graphium Plus 0.0.1 release source is frozen at commit
`3b97781b9713b76c0f51eb6e229323db2fd512a6`, tree
`f185d453c13679b52e6c45ef6dc67d8279e8a7b7`, public tag `v0.0.1`. The tag is immutable release authority for
0.0.1 and MUST remain on that commit even if `main` later receives governance/evidence-only convergence commits.

The final Debian distribution artifact is `graphium-plus_0.0.1-1_all.deb`, SHA-256
`de2e371f7efb8b096be0f30af9c37dd536842ae48b25f21a3b499db72a33bf8f`. It is a separate co-installable Debian
identity from Graphium Core and passed reproducible build, exact installed projection, zero concrete-file collision
with installed Core, real T480 apt installation and user runtime smoke. Distribution certification does not create
any new runtime authority.

The public GitHub surface is part of distribution authority, not editor architecture. Its primary identity is the
red Graphium Plus icon; the original Graphium icon is lineage attribution only. The README name-origin statement —
Latin `graphium`, a stylus/writing implement associated with wax-tablet writing — is branding/documentation and has
no runtime effect. GitHub Release `v0.0.1` attaches only the exact frozen `.deb` plus `SHA256SUMS.txt`; anonymous
re-download/hash verification passed.

Post-release canonical convergence may alter only the three canonical documents, additive
`evidence/GRAPHIUM_PLUS_0.0.1_FINAL_RELEASE_RECEIPT_20260829.txt`, and regenerated `evidence/SHA256SUMS.txt`.
`graphium/`, `graphium_plus/`, `bin/`, `data/`, `tests/`, `docs/user/`, `README.md`, `assets/`, `LICENSE` and all
other released product/public-surface paths are protected and must remain byte/mode-identical to release source.
No Candidate is reopened and no T480 functional retest is justified by governance-only convergence.


### Graphium Plus 0.0.2 maintenance boundary — Core 0.0.17 guarded-save propagation — 2026-08-29

Graphium Plus 0.0.2 is a maintenance successor to immutable release 0.0.1. It does not fork or reinterpret the Core writer. `graphium/infrastructure/guarded_file_writer.py` and `tests/integration/test_guarded_writer.py` are adopted byte-for-byte from the supplied Core 0.0.17 derived-line authority because the Plus 0.0.1 inherited owner hashes matched the accepted pre-corrective pair exactly. The resulting writer hash is `c3972a980229b64d96c864d4462472be44820be485d02757d1dd02105f86dad2`; permanent regression hash is `5d3fbfb85e1b8cefedf8978696a3893baedc196464993f9d9185aee0a0c984f2`.

The EXPECTED_ABSENT namespace commit contract is therefore: fd-relative `renameat2(..., RENAME_NOREPLACE)` primary, hard-link+unlink only when no-replace is genuinely unsupported, no replacing/direct-write/exists-then-rename fallback, and post-link stage-unlink failure classified as post-commit warning-shaped state. No FAT32-specific product branch is permitted. Existing-target guarded atomic replacement remains unchanged.

Plus-only toolbar/Workspace/document authorities remain byte-identical to 0.0.1. The only Plus runtime identity delta is `PLUS_PRODUCT_IDENTITY.version = 0.0.2`. The exact Core writer bytes already possess physical FAT32/vfat proof; derived-line certification adopts that proof while requiring exact-byte identity and permanent Plus tests. Release `v0.0.1` and its artifact remain immutable; publication of this maintenance source uses new tag `v0.0.2` and package version `0.0.2-1`.

### Graphium Plus 0.0.2 final maintenance release and convergence authority — 2026-08-29

Graphium Plus 0.0.2 is released at commit `302bae32f37cb7c5f9140389ff7510b5cedd6194`, tree
`1f7b6b3967d9ee6d151670ad7fd3ef7ff1988b58`, public tag `v0.0.2`. The tag is immutable release authority and
must remain on that commit after governance convergence advances `main`. The released Debian artifact is
`graphium-plus_0.0.2-1_all.deb`, SHA-256
`973c6ecef6c94a47deace671de3ad6a358474bf4325e05aaa1b4070ffa36ae11`.

The maintenance product delta remains architecturally bounded to the exact Core 0.0.17 guarded-writer/test owner
bytes, Plus version identity 0.0.2 and matching release/help/public documentation authority. Plus toolbar, Workspace,
document lifecycle, appearance, spellcheck, desktop identity and installer architecture are unchanged. Real user
validation confirms corrected About projection and successful pendrive save. The exact Core writer bytes retain the
Core physical FAT32/vfat proof; Plus adds no filesystem-specific branch or second writer authority.

Post-release convergence may alter only the three canonical documents, additive
`evidence/GRAPHIUM_PLUS_0.0.2_FINAL_RELEASE_RECEIPT_20260829.txt`, and regenerated `evidence/SHA256SUMS.txt`.
All product/runtime/test/user-Help/README/icon/LICENSE/installer bytes remain byte/mode-identical to release source.
No Candidate is reopened. Release `v0.0.1` and its tag/assets remain immutable historical authority.
