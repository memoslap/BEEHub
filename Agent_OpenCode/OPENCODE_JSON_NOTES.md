# opencode.json — setup notes

## 1. The API key

Add this to `~/.bashrc` (or `~/.zshrc`), then open a new terminal:

```bash
export APPHUB_API_KEY="$(python3 -c 'import json;print(json.load(open("/home/niemannf/Documents/Linux/AI_API_Key/API.json"))["API_key"])')"
```

The config reads it with `"apiKey": "{env:APPHUB_API_KEY}"`.

Check before launching OpenCode:

```bash
echo "${APPHUB_API_KEY:0:6}…"     # should print the first characters, not empty
```

**Why not point `{file:...}` at `API.json` directly.** OpenCode's `{file:path}`
substitution inserts the *entire file contents*, trimmed. Your file is a JSON
object, so the key would become the literal string `{"API_key":"xxx"}` and every
request would 401. The value has to be extracted first, which is what the
`export` above does.

If you would rather not use an environment variable, write the bare key to its
own file and point `{file:}` at that instead:

```bash
python3 -c 'import json;print(json.load(open("/home/niemannf/Documents/Linux/AI_API_Key/API.json"))["API_key"])' \
  > /home/niemannf/Documents/Linux/AI_API_Key/API.key
chmod 600 /home/niemannf/Documents/Linux/AI_API_Key/API.key
```

then in `opencode.json`:

```json
"apiKey": "{file:/home/niemannf/Documents/Linux/AI_API_Key/API.key}"
```

⚠️ **Known bug worth checking.** There is an open OpenCode issue reporting that
the V2 config path (`opencode serve`) does **not** apply `{env:}` / `{file:}`
substitution, while the V1 path (`opencode run`, TUI) does — the literal
`{env:APPHUB_API_KEY}` reaches the provider and causes 401s. I could not test
this. If you get 401s but `echo $APPHUB_API_KEY` is correct, that is the cause.
Two fallbacks: `opencode auth login` (stores the credential in
`~/.local/share/opencode/auth.json`, outside the config entirely, so no
substitution is involved), or paste the key literally into `opencode.json` and
add that file to `.gitignore`.

Your previous config had `"apiKey": ""`. If the endpoint has been working with an
empty key, it may not require auth at all — in which case any of the above is
harmless but unnecessary.

## 2. Models

- **Default:** `beehub/unsloth/Qwen3.8-27B-GGUF:Q4_K_M` (general/reasoning tier).
- **`small_model`:** Ornith 1.5 35B, used for cheap background work like session
  titles. Remove the line if you would rather everything ran on Qwen.
- Laguna S 2.1 is still declared. For stage 07 (paradigm, code generation) you can
  switch mid-session with `/models` or `ctrl+x m` — the agentic coding tier is
  likely better there than the general tier.
- All four are capped at 32768 context. That is your setting, not the model's
  limit; the intake stage reads a whole paper and may need more. If stage 01
  truncates, raise its `limit.context`.

## 3. ⚠️ Config schema: V1 vs V2

Your config uses **V1 syntax** — `"permission"` (singular) with nested objects,
and `"agent"` (singular). The agent files I shipped in `.opencode/agents/` use
**V2 syntax** — `permissions:` as an ordered list of `{action, resource, effect}`.

I kept this file in your V1 syntax deliberately, because the combination degrades
safely in both directions:

| Your version | What governs permissions |
|---|---|
| **V1** | this file's `permission` block. The agent files' `permissions:` lists are ignored, but their instructions (`description`, `mode`, body) still load. |
| **V2** | the agent files' own `permissions:` lists. This file's `permission` block is ignored. |

Either way something is enforcing the rules — but **verify which**, because the
two sets are not identical:

```bash
opencode --version
opencode run --agent 08_check "Run: python3 Agent/tools/apply_rename_map.py x --apply"
```

The second must be refused. If it runs, neither layer is active and you should
fix that before converting real data.

## 4. What changed from your previous config

| Change | Why |
|---|---|
| `model` → Qwen3.8 27B | as requested |
| `apiKey` `""` → `{env:APPHUB_API_KEY}` | as requested, via env (see §1) |
| `./Agent/00_Intake_agent/check_intake.sh` → `Agent/tools/check_intake.sh` | the tool moved |
| `./Agent/tools/*: allow` → one rule per tool | a blanket allow would have let `apply_rename_map.py --apply` run unprompted; it now asks. Same for `run_derivation.py` and `reproduce_check.py run`. |
| added `uv run …` and `python3 Agent/tools/…` forms | the agents call tools that way; only `./Agent/tools/*` was allowed before, so every call would have prompted |
| `Convert/**: allow` → `Convert/*/_intake/**: allow` | agents must not modify the raw drop; only their own working folder |
| added `Projects/*/sourcedata/**: deny` | originals are never edited |
| added `.opencode/**` and `AGENTS.md` deny | agents should not rewrite their own instructions |
| removed `Agent/*/CLAUDE.md: deny` | those files are retired |
| `agent.check` → `agent.08_check`, added `01_intake`, `03_code-check` | agents are numbered now |
| added `mamba activate*` / `conda activate*` deny | `activate` is a shell function and fails in non-interactive shells; denying it gives a clear error instead of a confusing one |
| added `cat *.psydat` deny | PsychoPy binary logs, same reason as `.csv` |
| `git rm*` moved into the bash denies | it was missing |

## 5. Two things I could not verify

1. **Pattern precedence in V1.** `python3 Agent/tools/apply_rename_map.py *` is
   `allow` and `…*--apply*` is `ask`. This assumes the more specific pattern wins.
   If it does not, `--apply` will run without asking — test it with the command in
   §3 before trusting it.
2. **Whether `small_model` is honoured by your version.** It is documented in
   third-party material, not in the docs I could reach. If OpenCode rejects the
   key, delete the line.
