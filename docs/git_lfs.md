# Git LFS — required setup

The ten SRI CSVs under `data/clean/` total **523 MB** and are stored with
[Git LFS](https://git-lfs.com/). In a correctly configured clone, git only ever sees a 133-byte
pointer per file:

```
version https://git-lfs.github.com/spec/v1
oid sha256:60d2457a242df539fb30beba3471a6e9e6833cb7b513946664fcc644aac071db
size 27082824
```

## Setup after cloning

`.gitattributes` alone is **not** enough. It declares which paths should use LFS, but the
declaration is inert unless the LFS filters are registered in your `.git/config`. Registering
them is what `git lfs install` does, and it is per-machine (or per-clone), so it is not
something the repository can do for you.

```bash
git lfs install          # once per machine
git lfs install --local  # inside this clone
git lfs pull             # download the actual CSVs (~523 MB)

# Optional but recommended -- the guard described below:
ln -sf ../../.githooks/pre-commit .git/hooks/pre-commit
```

Verify it worked:

```bash
head -c 20 data/clean/SRI_Vehiculos_Nuevos_2026.csv
```

You should see CSV text (`CATEGORÍA;CÓDIGO DE...`). If you see `version https://git-lfs...`,
the pointer was never resolved — run `git lfs pull`.

## Why this matters

Without the filters installed, `git add data/clean/` stores the **file contents** as ordinary
git blobs. The commit succeeds and looks normal locally, but it permanently adds half a
gigabyte to everyone's clone, and `git rm` afterwards does not reclaim it — only a coordinated
history rewrite does.

This has already happened once on a fork of this repository: a single commit put 523 MB of CSV
into the tree, and it had to be rebuilt from scratch rather than merged.

## The guard

`.githooks/pre-commit` refuses any commit that stages a file under `data/clean/` or `data/raw/`
whose content is not an LFS pointer, and tells you how to recover. Git does not distribute
hooks automatically, so install it with the `ln -sf` line above.

The hook is deliberately installed as `.git/hooks/pre-commit` rather than via
`core.hooksPath`. Setting `core.hooksPath` makes git ignore `.git/hooks/` entirely, which would
disable the `pre-push`, `post-checkout`, `post-commit` and `post-merge` hooks that `git lfs
install` puts there — breaking LFS uploads on push. Git LFS does not install a `pre-commit`
hook, so there is no collision.
