<p align="center">
  <img src="assets/graphium-plus.svg" width="128" height="128" alt="Graphium Plus logo">
</p>

<h1 align="center">Graphium Plus</h1>

<p align="center">
  <strong>Graphium Core + compact toolbar + local Workspace</strong>
</p>

<p align="center"><strong>Current release: 0.0.2</strong></p>

<p align="center">
  A lightweight native GTK text editor for Linux with a bounded filesystem Workspace and strict file-safety semantics.
</p>

Graphium Plus is the cumulative edition of **Graphium** for users who want a small file-oriented writing workspace without turning the editor into an IDE.

It preserves Graphium's single-document editor and file-safety model, then adds two deliberately bounded UI layers: a compact native toolbar and a local Workspace tree.

## What Plus adds

- compact GTK toolbar for New, Open, Save, Undo, Redo, Cut, Copy, Paste, Reload, Find and Replace;
- independent show/hide controls for Toolbar and Workspace;
- one local Workspace root with lazy directory expansion;
- internal opening of regular `.txt` and `.md` files through Graphium's canonical Open lifecycle;
- right-click Workspace actions, including **Open with Graphium Plus**;
- New Text, New Folder, Rename, Duplicate and Move to Trash;
- natural filename sorting and persistent visible selection in Light mode;
- Refresh with selection preservation;
- Locate Active Document and Reveal in the system file manager;
- separate Recent Workspaces.

## Lightweight architecture

The Workspace is intentionally **not** a project system.

Graphium Plus adds no Workspace database, indexer, watcher, recursive startup scan, background filesystem worker, tab/session graph, plugin platform or cloud service. Directories are read only when needed. Opening a Workspace does not create a second document authority: editing still flows through the same Graphium document/session/writer lifecycle.

## File safety

Graphium Plus inherits Graphium's guarded save model: destination identity is revalidated before replacement, external filesystem changes are not silently adopted, and encoding/BOM/line-ending representation is preserved unless the user explicitly converts it.

Workspace mutations are similarly bounded. Paths are revalidated before mutation, Workspace-boundary symlink traversal is rejected, and **Move to Trash** uses the system Trash without a permanent-delete fallback.

## Built on Graphium Core

<p>
  <a href="https://github.com/leviagravia/graphium">
    <img src="assets/graphium.svg" width="64" height="64" alt="Graphium Core logo">
  </a>
</p>

Graphium Plus 0.0.2 remains a cumulative descendant of **Graphium Core 0.0.16** and additionally inherits the exact **Graphium Core 0.0.17 guarded-save corrective** for FAT32/vfat compatibility. The original Graphium icon above identifies that lineage; the **red icon is the primary Graphium Plus identity**.

The Plus repository begins from the exact published Graphium Core lineage and adds the Plus layer without replacing the Core editor authorities.

## About the name

**Graphium** is Latin for a **stylus or writing implement** — the pointed tool used for writing, especially on wax tablets. The name reflects the project's aim: a direct tool for writing rather than a platform around the document.

**Graphium Plus** keeps that same writing-tool identity and adds a small, local Workspace around it.

## Run from source

Requirements:

- Linux
- Python 3
- PyGObject
- GTK 3
- Hunspell (optional, for spell checking)

```bash
git clone https://github.com/leviagravia/graphium-plus.git
cd graphium-plus
./bin/graphium-plus
```

### Install for the current user

```bash
./bin/graphium-plus-install
```

The default installation prefix is `~/.local`. Graphium Plus uses its own `graphium-plus` XDG namespace.

## Documentation

- [`Graphium Plus User Guide`](docs/user/GRAPHIUM_PLUS_USER_GUIDE.txt)
- [`Keyboard Shortcuts`](docs/user/GRAPHIUM_KEYBOARD_SHORTCUTS.txt)

Both are also available offline from the application's **Help** menu.

## Deliberate non-goals

Graphium Plus is not a smaller IDE. It deliberately avoids tabs, project/session machinery, syntax highlighting, plugin systems, Workspace indexing, cloud services and background filesystem scanning.

## License

Graphium Plus is free software released under the **GNU General Public License v3.0 or later (GPL-3.0-or-later)**. See [`LICENSE`](LICENSE).

## Author

**leviagravia**  
`leviagravia@zohomail.eu`

---

**Graphium Plus** — a lightweight Graphium workspace without turning the editor into an IDE.
