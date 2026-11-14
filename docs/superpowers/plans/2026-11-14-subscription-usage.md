# Subscription usage implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Display real subscription quota beneath task progress and as an outer bubble ring, with renewal countdown text only in the card at 100%.

**Architecture:** Provider adapters write a validated local quota cache. A nonblocking reader shares the cache across bubbles. Pure quota state handles freshness, expiry, selection and countdown; native presentation preserves existing dimensions and QR view.

**Tech Stack:** Python standard library, official Codex app-server JSON-RPC, Claude Code statusLine JSON, existing Tk canvas and PNG renderer.

**Spec:** User approved the interactive subscription-usage preview and authorized implementation, then clarified that renewal text belongs only in the card. Bubble: keep task percentage, add color-coded quota ring, no quota percentage/countdown text. Card remains the same size.

## Constraints

- No credential extraction, model turns, extra paid services or cloud upload of account quota.
- Use provider values only. Missing/stale/expired quota is unavailable; never fabricate zero after reset.
- Keep each new first-party responsibility under approximately 350 implementation lines.
- Card can select primary/weekly windows. Green below 60%, yellow at 60%, orange at 80%, red at 95%.
- At 100%, show remaining duration until provider reset in card; unknown reset says unavailable. If reset has passed, wait for a fresh reading.
- Codex automatic official read validated locally. Claude uses documented statusline feed, without silently overwriting an existing statusline. Antigravity automatic schema is not validated here; hide unsupported data rather than estimating.

## Tasks

1. [x] TDD pure normalization/freshness/countdown and local cache/provider acquisition, including malformed input, missing windows, zero, 100%, reset, stale and background failures.
2. [x] TDD native card/ring integration, no window growth, no quota text on bubble, QR unchanged, local-only fields excluded from mobile payload.
3. [x] Add Claude bridge/setup instructions, English README and skill instructions; install locally, verify live Codex, full tests and native rendering.
4. [x] Fresh independent review; fix important findings with regression tests, update graph, commit/push and report limitations accurately.

## Review focus

- Cached account quota must not leak into mobile sessions or carry credential fields.
- Reset and stale state must not become false zero or preserve a false active 100% forever.
- Network/CLI reads must not block Tk; one shared cache prevents per-bubble account polling bursts.
- All quota text belongs in card/tooltips, never the bubble canvas; the task percentage remains intact.
- Rapid toggles, hidden QR view, all card/bubble sizes and malformed provider responses must remain safe.

## Execution ledger

- Local spike: official installed Codex app-server initialize and account/rateLimits/read succeeded, returning primary 300-minute and secondary 10080-minute windows. No model turn or auth-file reading occurred.
- Approval: user authorized implementation after preview and clarified countdown placement.
- Ruling: implement in the current main checkout, following established workspace preference and explicit prior merge/publication workflow. Cost: no separate worktree isolation.

- Task 1: quota normalization/cache/provider contract tests observed RED→GREEN. Codex official live read returned both windows. Invalid private fields are discarded when accepting and when loading cache.
- Task 2: ring-only bubble rendering and native PNG transparency/dimensions tests observed RED→GREEN. No quota text is created on the bubble canvas. Card dimensions and QR renderer remain unchanged.
- Ruling: quota is a native Windows feature; local/mobile HTML remains task-only. This preserves the approved local-only account-data boundary. Cost: browser viewers do not display subscription usage.
- Ruling: Claude setup is opt-in and refuses to overwrite custom statuslines; Antigravity supplies a normalized receiver only, pending a verified provider adapter. Cost: these clients may require setup and cannot be advertised as automatically verified.

- Final review: fresh independent reviewer quota_review checked all source integrations and privacy boundaries. Important findings: profile cache collisions, silent receiver output, explicit absent windows, extreme numeric overflow and multiline overlap; all fixed in one regression pass.
- Final: fixed profile isolation and CLAUDE_CONFIG_DIR setup — test_distinct_profiles_do_not_share_account_quota / test_claude_setup_respects_its_config_directory RED→GREEN.
- Final: fixed renewal output outside card — test_renewal_text_is_not_printed_into_claude_statusline RED→GREEN; bridge emits no quota text.
- Final: fixed confirmed absent data retaining false 100% — test_confirmed_absent_quota_clears_previous_full_snapshot RED→GREEN.
- Final: fixed huge numeric values stopping UI refresh — test_extreme_numbers_cannot_break_normalization_or_card_refresh RED→GREEN.
- Final: fixed message/footer overlap — test_multiline_messages_fit_a_single_measured_card_line RED→GREEN; real Windows Tk checks pass for multiline, wide Unicode and long words in all three sizes.
- Final: Ruling: reviewer excluded Antigravity upstream and live accounts — the automatic adapter remains explicitly unverified; real Codex official reads are verified locally, with no claim of live Claude/Antigravity testing. Cost: those providers require configuration/verification.
- Final: no deferred minor remains; profile setup was treated as a correctness fix rather than mere polish.
- Validation: 98 Python tests and 21 Node tests pass, including actual mobile payload assertions excluding quota fields, native dimensions and bubble image-only quota presentation. Current native render and live profile-scoped Codex reads passed.
