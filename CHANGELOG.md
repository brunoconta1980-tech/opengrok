# 1.0.24 — 2026-09-07

## Bug Fixes

- **Esc** no longer cancels a running turn and instead reminds you to use Ctrl+C.


# 1.0.23 — 2026-09-07

## Bug Fixes

- **Fixed bare URLs and emails** inside table cells so every wrapped line remains a working hyperlink.


# 1.0.22 — 2026-09-07

## Features

- **Built-in agent tools** now take precedence over user MCP servers when tool names collide.
- **Desktop app tools** are now available through a dedicated first-party MCP server.
- **Remote control pickers** can now group servers by device using announced device identity.
- **edit_file diffs** now show real file line numbers instead of starting at line 1.
- **Permission prompts for file edits** now auto-expand the diff row so you can see the change before approving.
- **Sending a message to a finished subagent** now continues that same subagent instead of failing.
- **Background subagent completion messages** now show the actual output instead of just a pointer to run the tool.
- **Dashboard** now shows a unified header with location picker and an actions row for creating agents or resuming previous sessions.
- **New `grok-workspaced daemon`** mode lets a long-lived process expose folders to the Computer Hub (separate from the Desktop-supervised sidecar).

## Bug Fixes

- **MCP connectors** now correctly show when they need re-authentication even if no tools are listed.
- **Extensions modal** shortcuts now work when the tab bar is focused, and invalid actions on headers show helpful messages.
- **Send now** button and shortcuts now work correctly when an automatic background turn is running.
- **Resumed sessions** now show the exact text you typed for mid-turn follow-ups instead of the wrapped system message.
- **`/skills`** command now updates the model with newly installed skills even when written from another NFS client.
- **Auto mode** no longer instantly runs destructive `git checkout --` commands; they now go through the model for safety.
- **Fixed a crash** that could occur when restoring pasted content after certain skill injections or rewinds.
- **Subagents and workflows** now respect the same bash timeout and auto-background settings configured for the parent session.
- **Fixed model backend selection** so an explicit chat_completions setting in config.toml is no longer overwritten by same-slug siblings.
- **Slash command advertisements** no longer spam repeatedly when your current directory is your home folder.
- **Foreground shell commands** no longer produce spurious background-task reminders or incorrect kill results.
- **Queued follow-up buttons** now appear in the order [Send now][edit][cancel].
- **`/compact instructions`** in the pager are now passed to the compaction backend (bare `/compact` is unchanged).
- **`/goal`** (and resume) after pressing Esc now correctly starts the goal planner instead of failing with "Planning failed".
- **run_terminal_cmd** now correctly tells the model that foreground commands are backgrounded after ~15s instead of the 120s timeout value.
- **Skill announcements** no longer repeat the same list of available skills multiple times in a session.
- **Monitor events** in multi-session processes now correctly wake idle sessions instead of being buffered until the next prompt.

## Performance

- **Opening or resuming sessions** no longer pauses the interface while reading MCP config files.


# 1.0.21 — 2026-09-04

## Bug Fixes

- **Permission mode** (auto / always-approve) now stays visible when the agent enters plan mode and is restored on exit.
- Typing, pasting, or pressing Shift+Tab on the welcome screen now immediately opens the session instead of creating a duplicate one.
- Dock sections, queue body, and reveal rows now stay within their documented height rules even on crowded terminals.


# 1.0.20 — 2026-09-04

## Bug Fixes

- **Scroll history** after sending a prompt no longer loses the reserved bottom padding or jumps the viewport unexpectedly.


# 1.0.19 — 2026-09-04

## Breaking Changes

- **Scheduled /loop tasks always run in the background**; they no longer inject turns into your conversation.

## Features

- **New terminal theme** option makes backgrounds transparent so the terminal's own colors show through.
- **MCP servers blocked by organization policy** now show clear messages and are refused before any config change.
- **Session resume now tells the model** what loops, subagents, and workflows were still running.
- **Dashboard** now shows newly dispatched sessions immediately instead of waiting for the store.
- **Headless sessions** (`grok -p`) now support the `--worktree` flag to run in a separate git worktree.
- **Dashboard** now says 'Open session' instead of 'Add session' for the session picker button.
- **Multi-line bash commands** now render with proper wrapping and highlighting when opening the block viewer.
- **/usage** now works from the dashboard and shows account allowance when no session is active.

## Bug Fixes

- **Fixed mid-turn UI freezes** when the terminal stops reading output.
- **Fixed crashes** that occurred when the terminal pane was closed while grok was exiting.
- **MCP server list** in minimal mode now correctly shows policy-blocked servers.
- URLs that wrap across multiple lines inside quotes or lists are now fully clickable.
- **The welcome screen** composer now grows taller when you paste multi-line text.
- **Enterprise policy files** are no longer deleted on startup when your team login is stored at a custom `GROK_AUTH_PATH`.
- **/feedback** now drops unsupported images with a notice (matching the modal) and never loses your report text on save errors.
- **Feedback drafts** keep their paragraph breaks when updated, and the modal no longer switches tabs unexpectedly.
- **Turn summary lines** no longer lose their spacing after background tasks finish.
- **Thinking blocks** no longer stay expanded after switching between fullscreen and minimal modes.

## Performance

- **First prompt after login is faster** when MCP servers are configured; they connect in the background.


# 1.0.18 — 2026-09-02

## Features

- **Managed policy** now blocks disallowed MCP servers and marketplace installs before any change is written.
- **Quoting** a previous message from the block viewer now works directly from the viewer.
- **Welcome screen** now stays until you actually send a prompt; a session is prepared in the background.
- **Feedback** is now collected in a centered modal instead of a bottom card.
- **Feedback submissions** now include structured type, task, and failure information.
- **Feedback modal** now has a Drafts tab to manage and send saved drafts.
- **Models** can now render interactive charts using Chart.js.
- **grok inspect** and **grok mcp doctor** now show managed policy details.
- **Image generation** now supports richer parameters via composer state.
- **Retry behavior** for rate-limited requests is now configurable per model.
- Models can now be configured with per-model mTLS client certificates for secure upstream connections.
- **`/feedback <text>`** now saves a local draft before invoking the feedback skill.

## Bug Fixes

- **Authentication recovery** during turns no longer fails immediately on transient errors.
- The session dock now aligns consistently, shows more rows inline when expanded, and reveals stop controls on hover.
- **Pastes** from rich-text sources no longer stay inline or corrupt the composer when they contain special Unicode line separators.
- **Mouse wheel** over a one-line prompt now scrolls the conversation history instead of being ignored.
- **Slash dropdowns** no longer truncate long command names when a short sibling is also visible.
- **Subagent sessions** now respect the retry and rate-limit settings of their selected model.
- **Session picker** now opens with Ctrl+R everywhere; redo uses Ctrl+Shift+Z or Alt+Z.
- **Subagent views** no longer duplicate the task prompt on first open after a live echo.
- **Strikethrough text** now renders correctly inside markdown tables in the pager.
- **Resume picker** now labels local sessions with a single disk walk instead of per-row lookups.

## Performance

- **Startup** no longer hangs on slow networks while fetching remote settings.
- **Responses** now complete faster; uploads and session bookkeeping happen in the background.
- **Startup** now makes fewer network requests by sharing settings fetches.
- **New sessions** start responding faster by running start hooks in the background.


# 1.0.17 — 2026-09-01

## Features

- **MCP tools** now support the 2026-07-28 multi-round-trip elicitation flow where a tool call can return an input_required state that is resumed on retry.
- **Next-prompt ghost suggestions** now appear less often and are more accurate by preferring silence when the next line is not obvious.

## Bug Fixes

- **Table cell selection** inside /btw panels now correctly highlights cells and copies as TSV instead of drawing a linear rectangle.


# 1.0.16 — 2026-09-01

## Breaking Changes

- **Enterprise policies** can now restrict which models users may select via signed requirements.toml.

## Features

- **MCP servers** can now be supplied at session bind time for workspace integrations.

## Bug Fixes

- **Long-running sessions** interrupted by expired tokens during network issues no longer lose work.
- **Slash command suggestions** with very long names no longer show blank labels in the dropdown.
- **Sending a message immediately after spawning a subagent** no longer fails while the child is still starting.
- **Loading spinners** inside the extensions modal (/mcps and other tabs) now animate correctly.
- **MCP server OAuth authentication** triggered from /mcps no longer deadlocks the session.

## Performance

- **Long-running subagent and task output waits** now default to a one-hour ceiling instead of ten minutes.


# 1.0.15 — 2026-08-31

## Features

- **Tip appears** after repeated scrollback drag-copies suggesting /copy and /export commands.

## Bug Fixes

- **Session close** is now faster because memory consolidation runs at the next launch instead of blocking exit.
- **Typed input including Enter** during pager startup is now preserved and correctly interpreted as submit or newline.
- **Dock panel** input and rollout now respect remote settings and correctly handle keyboard focus when hidden or empty.

## Performance

- **First reply latency** is reduced by opening the model connection in the background when a session starts.
- **Signed-in startup** is faster because an expired token refresh now begins in the background at agent spawn.
- **Creating a new session** returns faster; MCP tools and other startup work happen in the background.


# 1.0.14 — 2026-08-31

## Features

- **OIDC token refresh** is now proactive by default for better reliability.
- **PostToolUse hooks** can now provide feedback and context to the model after tool execution.
- **SDK-registered PostToolUse hooks** now provide model-facing feedback.
- **grok usage <session-id>** now shows persisted per-turn token and cost data.
- **Retry status** in composer and title now shows a short reason for the retry.
- **Models can now declare** a different identifier for each reasoning-effort level instead of always sending the same id.
- **Prompt suggestions** now respect remote configuration and default to the current session model.
- **Windows CLI downloads** are now ~70% smaller using the same compressed sidecars as macOS and Linux.

## Bug Fixes

- **grok inspect** now correctly shows Claude bypass locks as advisory rather than enforced.
- **Subagent sessions** no longer leak threads or file descriptors when the parent is busy.
- **Cold startup** no longer performs duplicate remote settings fetches.
- **Compaction failures** due to context size now degrade input instead of retrying identically.
- **--sandbox strict** now restricts writes to ~/.grok/sessions only.
- **Subagent spawning** now waits longer on a busy coordinator and shows clearer retry guidance instead of "unreachable".
- **Failed task and todo tool calls** now appear in the transcript instead of disappearing without a trace.
- **Composer status row** no longer collapses or flashes when using double-Enter to send now.
- **Session close** is no longer delayed by a single slow hook; each SessionEnd hook now has its own timeout.
- **Hook removal** in the extensions modal no longer offers actions that the handler will refuse.
- **Interjections** during a turn are now delivered atomically or not at all.
- **Subagent tasks** no longer get incorrectly cancelled when the parent session is waiting for completion.
- **Workflow detail view** now closes the overlay on X or outside click instead of returning to the run list.
- **Resuming subagents** now succeeds for larger transcripts that still fit the model context with headroom.

## Performance

- **Startup** now fetches remote settings only once per boot instead of potentially twice.
- **First message** on large repositories no longer waits on repository status scan.
- **Large session memory** no longer blocks the agent during turn completion or subagent spawning.
- **Signed-in CLI starts** faster by serving remote settings from a local cache on warm boots.


