# Handoff for the next agent

Read this before exploring. Branch `config-class`. Pull request: https://github.com/chazlarson/Media-Scripts/pull/65 (into `main`). Stay on this branch. Do not open a second PR.

This file is session notes. It is not product documentation. Delete it before merge if it is still here.

## Do this next

Docker is installed in the Cloud Agent environment as of build `bld-20261016-de0a8a85-52b4-4235-ad3b-0a29372ba6ac`. The previous agent could not build the image because that machine had no Docker daemon.

1. Confirm `docker version`. If the daemon is down, `sudo service docker start`.
2. `docker build -t media-scripts .`
3. Run with one mount:

```bash
docker run --rm -v /path/to/config:/config media-scripts list
docker run --rm -v /path/to/config:/config media-scripts grab-all-posters --help
```

A live Plex server was not part of the request. `docker build` is the unchecked item in the PR test plan.

## Already decided

- `orchestrator.py` is the image entry point. `menu.py` is the interactive menu it opens on a TTY.
- One mount, `/config`. The image sets `MEDIA_SCRIPTS_CONFIG_DIR=/config`.
- First run copies `config.template.yaml` to `/config/config.yaml` only when that file is missing, and creates `/config/plex`, `/config/kometa`, and `/config/tmdb`.
- Scripts run with cwd `/config/<category>`, so `../config.yaml` and relative writes stay on the mount. Local runs leave the env var unset and still use the script directory plus repo-root `config.yaml`.
- The Plex Image Picker is excluded. Its app and `Plex Image Picker/Dockerfile` stay. `.dockerignore` excludes that directory. `orchestrator.py picker` exits 2. `menu.py` has no picker item.
- `kometa.config_dir` is an external Kometa install path. The image does not create it. `originals-to-assets` needs that path mounted separately.
- Config migration is done. Do not revive `.env` or `python-dotenv`. Do not rewrite git history for the old GitGuardian sample-key finding. Do not rotate keys unless asked.

## Checks already run

`ruff check .` passed. `python -m compileall` passed. Temp-dir checks covered config seeding, not overwriting an existing `config.yaml`, cwd selection, and `check-square-art --help`. Logs from the previous session are not in this checkout.
