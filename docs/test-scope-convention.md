# Test-scope convention (layer 2) — draft from the yt-client pilot

Status: decided by Yosuke on 2026-11-21 for yt-client; this document is the
basis for rolling the same convention out to the other Android apps.

## Marker

- The commit message may carry a scope marker: `[test: <scope>]`.
- No marker means **all** (run everything). When in doubt, widen the scope.
- Each app defines its own section contents. yt-client's scopes:
  `all` / `player` / `feed` / `none` (build only, no emulator).
- `workflow_dispatch` exposes the same scope names as an override input.

## Parser rule (learned from a real failure)

- **The last marker in the message wins.** Parsers must take the last
  match, not the first.
- The operational marker goes **at the very end of the commit message**.
- Why: a commit that quoted the `[test: all]` notation in its body while
  ending with `[test: none]` ran the full suite (5m13s), because the parser
  took the first match. Fixed in yt-client `b92f4c0` (head -1 → tail -1);
  verified by run 44876062354: success in ~64s with every emulator step
  skipped — the first time a push marker selected `none` end to end.

## Scope policy

- `all` is reserved for minor-version releases (the 0.2.0 class).
- Ordinary changes use the narrowest scope that covers the change
  (player-only change → `player`, feed-only → `feed`, no-test-value
  change → `none`).
- The scope is chosen by the committing agent (LLM), not inferred from
  changed paths.

## Compensating gate: VM-side kotlinc check before push

Because `all` no longer runs on ordinary pushes, a compile check runs on
Moka's VM **before** every push:

- Reference implementation: `ci/kotlin-check.sh` in yt-client-android
  (commit `f4c1532`). It compiles all app Kotlin sources with kotlinc
  (same version as the app build; 2.0.20 for yt-client) against
  android.jar (API 35), the app's real dependency jars, and a stub
  BuildConfig. No Gradle (Gradle cannot run on this VM).
- Dependency jars persist per app under
  `~/workspace/toolchains/<app>-kcheck/jars/`; the script records where
  each jar came from so the set can be rebuilt.
- Measured on yt-client: PASS ≈ 33s on current sources; a deliberately
  broken copy is rejected in ≈ 20s. This is the gate that would have
  caught the v0.1.18 nested-class-in-inner-class compile error locally
  instead of after a CI round trip.
- Pitfall: multiplatform libraries (e.g. lifecycle 2.8.4) ship
  manifest-only plain AARs; the real classes are in the `*-android` /
  `*-common-jvm` artifacts. Extract `classes.jar` from those.

## Rollout checklist per app

1. Split the emulator test into named sections; add the marker parser
   (last match wins) and the dispatch override.
2. Add `ci/kotlin-check.sh` with the app's kotlinc version, dependency
   jar set, and BuildConfig stub fields.
3. Verify each scope once via dispatch, and `none` once via a real push
   marker.
