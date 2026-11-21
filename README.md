# android-ci

Shared CI infrastructure for Moriya's Android apps (yt-client, apps-updater,
yt-player, findmy-mac, moka-vpn, phone-node).

## Purpose

Cut Android CI time across all apps, not per app. Three layers:

1. **Common groundwork** — the speedups proven in yt-client (single-job
   workflow, AVD/snapshot caching, skip SDK install when already present,
   condition-based waits instead of fixed sleeps) live here once, as a
   reusable workflow or shared scripts that each app repo calls.
2. **Test-scope convention** — commit-message markers `[test: <scope>]`
   (no marker = run everything) with a shared interpretation; each app
   defines its own section contents.
3. **Session CI server** — a GitHub Actions job with a lifetime of about an
   hour that keeps a warmed workspace (several repos) and a running emulator,
   and takes build/test requests from Moka over Tailscale. The per-run fixed
   costs (runner start, Gradle cache restore/save, AVD restore, emulator
   boot) are paid once at session start. The formal per-repo CI stays as the
   gate; the session server only accelerates the development loop.

## Reachability: Tailscale (decided 2026-11-21)

The session job joins the tailnet as an ephemeral node via
`tailscale/github-action`, and its server listens on the tailnet address.
Moka reaches it through the same tunnel route already used for Mac/moto
tailnet services, plus an auth token. The node's address is learned from the
run's log / step summary — never written into this repository (no tailnet
addresses in public code).

## Spike: `ci-session-spike`

A throwaway `workflow_dispatch` job that only proves reachability:

1. Joins the tailnet (auth key from the `TS_AUTHKEY` repository secret).
2. Starts `spike/server.py` (stdlib-only HTTP server, port 8765).
3. Prints the health URL (`http://<tailnet-ip>:8765/health`) to the step
   summary and log.
4. Stays alive for the requested lifetime (default 10 minutes).

Success criterion: Moka's VM gets HTTP 200 from `/health` through the
tailnet tunnel while the job is alive. If that fails, the session design
falls back to a polling transport.

### Setup (one time, by Yosuke)

1. Tailscale admin console → Settings → Keys → generate an auth key:
   **Reusable** + **Ephemeral**, longest expiry.
2. GitHub → this repo → Settings → Secrets and variables → Actions →
   new repository secret named `TS_AUTHKEY` with that key.
3. Never paste the key into chat; a pasted key is treated as exposed and
   revoked.

### Checking from the VM

`spike/check_from_vm.py <tailnet-ip>` opens a CONNECT tunnel through the
VM's tailnet proxy (the same helper used for SSH to the Mac) and requests
`/health`. It reads proxy credentials from the environment at run time and
stores nothing.

## Status

- 2026-11-21: repository created; spike workflow and server written.
  Waiting for the `TS_AUTHKEY` secret to be registered, then the spike run.

### 2026-11-21 — Spike result: REACHABLE

- Run 44878187967 failed at `tailscale up`: the v4 action sets `--hostname`
  itself, so passing it again via `args` made the flag "provided multiple
  times". Fixed by using the action's dedicated `hostname` input.
- Run 44878377495: joined the tailnet as `android-ci-spike`, server up,
  and Moka's VM received **HTTP 200** from `/health` through the tunnel
  proxy. The Tailscale route is proven; the polling fallback is not needed.
- Node discovery used the VM's own `tailscale status` peer list, so the
  session design does not depend on the Mac being reachable.
