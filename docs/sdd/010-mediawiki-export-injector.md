# SDD Pack — 010 MediaWiki Native Export Injector

This pack adds a **new injector** for indexing a local MediaWiki mirror produced by native MediaWiki export scripts.

Unlike the existing wget-generated static HTML mirror flow, this input consists of:
- XML export file(s)
- an `assets/` subtree containing local images/files

The pack is designed so the export mirror root can be explored recursively from the CLI.
