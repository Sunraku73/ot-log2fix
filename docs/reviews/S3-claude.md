# Review S3.1 — Claude (task S3.2)

- Commit: `ba277da` fix: S3.1 autolink residui, messaggi config, test (F39,F41,F42) + CI/packaging
- Anche: `3390fe4` chore: funding Ko-fi e URL repo reali, più `pyproject.toml` modificato e **non committato** nel working tree.
- Repo pubblico: `https://github.com/Sunraku73/ot-log2fix` (gli SHA qui sono quelli pubblici, post `filter-repo`: vedi `docs/reviews/README.md`).
- Venv temporanei sotto `~/Downloads`: `venv-s32` (renderer cmark-gfm), `venv-s32-3.10`, `venv-s32-3.13`.
- Renderer GFM reale usato: **API Markdown di GitHub** (`POST /markdown`, `mode=gfm`, solo stringhe sintetiche) e **cmark-gfm** (`cmarkgfm`, nel venv temporaneo).

## 0. `make check` e gate

| Prova | Esito |
|---|---|
| `make check` (py3.12, `.venv`) | ruff pulito; **171 passed, 4 xfailed**, come atteso |
| Matrice CI riprodotta in locale con `uv` | py3.10.22: 171 passed, 4 xfailed · py3.13.18: 171 passed, 4 xfailed; ruff pulito su entrambi |
| Gate MUST indipendente su bytes | **50/50 ID MUST** (59/59 needle); i SHOULD C50, C51, C53, C54 restano in leak (xfail strict coerenti) |

## 1. F39 — autolink: **non chiuso per le email**

Ho generato un report con `markdown()`. Il payload, ripetuto in `root_cause`, `fix_steps`, `missing_context` e `notes`, contiene:
- `www.`, `WWW.`, un'email, `mailto:`, `xmpp:`
- `http://`, `https://`, `ftp://`, `javascript:`
- `<http://…>`, `<a@…>`, `[x](http://…)`

Anche il nome del file nell'header contiene `www.` e `@`. Ho renderizzato il risultato con cmark-gfm e con l'API di GitHub.

| Input (fuori dal fence) | Markdown prodotto | GitHub / cmark-gfm |
|---|---|---|
| `www.evil.test/x`, `WWW.EVIL.TEST` | `www&#46;evil.test/x` | ✅ testo, nessun link |
| `http://`, `https://`, `ftp://` | `http&#58;//…` | ✅ testo (F32 regge) |
| `javascript:` | `javascript&#58;` | ✅ testo |
| `[x](http://…)`, `<http://…>` | escape + `&lt;…&gt;` | ✅ testo |
| `a@evil.test` | `a&#64;evil.test` | ❌ **`<a href="mailto:a@evil.test">`** |
| `mailto:a@evil.test` | `mailto&#58;a&#64;evil.test` | ❌ **`<a href="mailto:a@evil.test">`** |
| `xmpp:a@evil.test` | `xmpp:a&#64;evil.test` | ❌ **`<a href="xmpp:a@evil.test">`** |
| nome file `www.evil.test@x.log` (header) | `www&#46;evil.test&#64;x.log` | ❌ **`mailto:` link** |

**Perché succede:**
- `www.` e `scheme:` vengono riconosciuti già durante il parsing inline, sul sorgente grezzo. Lì `www&#46;` e `&#58;` non combaciano, quindi la neutralizzazione funziona.
- L'autolink email di cmark-gfm è invece un **post-processing sui nodi di testo** già decodificati e fusi. A quel punto `&#64;` è di nuovo `@`.
- Prova isolata con l'API di GitHub: `a&#64;evil.test`, `a&#x40;evil.test` e `a\@evil.test` diventano tutti link `mailto:`.

**Fix verificato** con l'API di GitHub e cmark-gfm. Basta un nodo non-testo accanto alla `@`, così il testo non si fonde:

| Forma | GitHub | cmark-gfm (safe) |
|---|---|---|
| `a&#64;<!-- -->evil.test` | `a@evil.test`, nessun link | `a@<!-- raw HTML omitted -->evil.test`, nessun link |
| ``a`@`evil.test`` | nessun link (code span visibile) | nessun link |
| `a<!-- -->&#64;evil.test` | nessun link | nessun link |

Proposta per Codex: in `_escape`, `.replace("@", "&#64;<!-- -->")` invece di `"&#64;"`. Il commento HTML va inserito **dopo** `html.escape`, quindi l'attaccante non può produrlo. È invisibile su GitHub e nei renderer che omettono l'HTML grezzo. Copre anche `mailto:`/`xmpp:`, perché senza `@` contigua non c'è autolink email.

**Test:** l'attuale `test_autolinks_outside_fence_are_neutralized` verifica stringhe nel Markdown grezzo (`"a@evil.test" not in before`), non il comportamento del renderer, ed è per questo che passa. Proposta:
- asserire che nessuna `&#64;` sia seguita direttamente da un carattere di dominio, cioè `re.search(r"&#64;[A-Za-z0-9]", before) is None`
- verificare la presenza di `&#64;<!-- -->`

Niente nuova dipendenza: cmark-gfm resta uno strumento di review, non entra in `[dev]`.

**Regressioni:**
- **F27 ✅** Dentro il fence l'evidence (con `www.`, `@`, `mailto:`, `http://`, tre backtick) è byte-identica; nel render è un `<pre>` senza link.
- **F32 ✅** `12:30` e `ORA-01652:` sono invariati, `http://evil` non è cliccabile.

## 2. F41 — messaggi di configurazione: CLOSED

CLI reale da `~/Downloads`, provider su una porta loopback chiusa (una chiamata al provider darebbe exit 2):

| Env | Exit | Output |
|---|---|---|
| `OTLF_REDACT=maybe` | 1 | `OTLF_REDACT: valore non valido.` |
| `OTLF_REDACT=sk-FAKE-SYNTH-0000SECRET` | 1 | idem; il valore non compare |
| `OTLF_MAX_CHUNK_CHARS=sk-FAKE-SYNTH-1111SECRET` + `OTLF_REDACT=FAKE-SYNTH-2222` | 1 | due righe, una per variabile; nessun valore |
| `OTLF_MAX_CHUNK_CHARS=500` | 1 | `OTLF_MAX_CHUNK_CHARS: deve essere un intero con valore minimo 1000.` |
| `.env` con `OTLF_REDACT=FAKE-SYNTH-3333` | 1 | `OTLF_REDACT: valore non valido.` |

In nessun caso compare un traceback. `exc.errors(include_input=False, include_url=False, include_context=False)` più un testo fisso per campo garantisce per costruzione che `input` e `msg` di pydantic (che può citare il valore) non vengano mai stampati. Il test parametrizzato copre `maybe` e un finto segreto.

## 3. F42

**(a) Test sul budget: discriminante solo in parte.**
- Ora con `"<" * 1992` si verifica `== "<" * 166`, `len == 998` e `chunk 12 di 12`. Questo cattura una `measure` sbagliata: mutazione `measure=len` → 1 test fallisce.
- Non cattura il margine delle virgolette. Con la mutazione `budget = max_chunk_chars - 0` passano **tutti** i test (5/5 selezionati). Il motivo: `<` costa 6, quindi 166 caratteri danno 996 sia con budget 998 sia con budget 1000.
- Nuovo finding **F44 (MINOR)**: aggiungere un caso con granularità 1, per esempio `"a" * 1996`, che dà 2 chunk pieni con encoded = 1000 = limite. Togliendo il `- 2` si passerebbe a 1002 e il test fallirebbe.
- `cli.py` è stato ripristinato dopo la mutazione; `git diff src` è vuoto.

**(b) ✅** `encoded_length` è definita una sola volta (`chunker.py:8-12`), importata da `cli.py` e da `test_chunker.py`; `perf_chunker.py` la usa. Non resta nessuna copia di `measure`.

## 4. CI (`.github/workflows/ci.yml`)

| Punto | Esito |
|---|---|
| Trigger push + PR, matrice 3.10-3.13, `pip install -e ".[dev]"`, ruff, pytest | ✅ riprodotto in locale sugli estremi della matrice |
| Dipendenze non approvate | ✅ nessuna; nessuna nuova dipendenza di runtime |
| `perf_chunker.py` non raccolto da `pytest -q` | ✅ il nome non corrisponde a `test_*.py` |
| Job `perf` "oggi solo manuale" | ❌ **gira a ogni push e PR**: nessun `workflow_dispatch`, nessun `if:` (F45) |
| Copertura di `perf` | ⚠ misura solo lo `split_chunks`; la redaction, che sui 10 MiB è il costo dominante, resta fuori (F45) |
| Riproducibilità | ⚠ action su tag mobili (`@v4`/`@v5`), `ruff>=0.6` non bloccato (una release nuova può rompere il lint senza cambi di codice), nessun `permissions:` né `timeout-minutes` (F48) |

**Margine del job perf** (Ryzen 9800X3D, `taskset -c 0`, 3 run):
- `perf_chunker.py`: 0.72–0.74 s, 97 MB RSS.
- `redact()` + split sui 10 MiB: 3.79 + 0.66 s ≈ 4.5 s. Il CLI completo in S2.7 impiegava 4.74 s.

Stima prudente su un runner da 2 vCPU con un rallentamento single-thread di 3–4×:
- solo chunker: circa 3 s, quindi un timeout di 30 s non dà rischio di flakiness;
- con la redaction inclusa (consigliato): circa 14–18 s, e 30 s diventa stretto. Proposta: `timeout 90s` più `timeout-minutes: 5` sul job.

La regressione che il job deve catturare (F37) era in minuti, non in secondi: anche 90 s la separano nettamente.

## 5. FUNDING e pyproject

- **`.github/FUNDING.yml`:** `ko_fi: G1J72ANIUV` ✅ (formato corretto). La riga `github:` commentata è innocua.
- **`pyproject.toml`:**
  - Nel commit `ba277da`, **e quindi su `origin/main`**, restano i placeholder `<GITHUB_OWNER>`.
  - Il working tree li sostituisce, ma **non è committato**: `3390fe4` ("URL repo reali") contiene solo `FUNDING.yml`.
  - Gli URL del working tree usano `OT-Log2Fix`, mentre il repo è `ot-log2fix`. GitHub li risolve comunque, ma per i metadati conviene il nome canonico.
  - Finding **F46 (MINOR)**.
- **Wheel** (`pip wheel` nel venv temporaneo):
  - costruito senza errori;
  - `LICENSE` in `dist-info/licenses/` e i prompt `analyze_v1*.md` inclusi;
  - `README.md` diventa il `long_description`.
  - Il campo `License:` contiene però l'intero testo MIT (forma legacy `license = {file = …}`). Finding **F49 (MINOR)**: `license = "MIT"` più `license-files = ["LICENSE"]` con `setuptools>=77`, eventualmente aggiungendo `"Programming Language :: Python :: 3 :: Only"`.

## 6. Processo

- **Tag `last-reviewed` (F47, MINOR):** punta già a `ba277da`, cioè al commit che questa review sta valutando, spostato prima del verdetto. Il prossimo bundle di `report.sh` userebbe come baseline un commit non approvato. Da riportare su `da681fa` (docs: review S2.7, l'ultimo stato approvato).

## 7. Deliverable docs (Claude)

| # | File | Note |
|---|---|---|
| 7 | `README.md` (EN) | Una riga di scopo, GIF placeholder, `pipx install git+…`, quickstart Ollama/OpenRouter, tabella provider, Security model tradotto, limiti, roadmap v0.2, Support con badge Ko-fi, disclaimer. Dichiara che l'output è **in italiano**. |
| 8 | `docs/reviews/README.md` | Nota F43 su `filter-repo` e SHA non risolvibili; indice delle review. |
| 9 | `SECURITY.md` | Come segnalare un bypass (fixture sintetica + riga nel manifest), canale privato per il resto, cosa è e cosa non è garantito, canary gate come soglia anti-regressione. |
| 10 | `docs/demo.tape` | vhs sulla fixture `01_cs_ora_tablespace.txt` (sintetica) con Ollama locale, prompt neutro. **Non renderizzata**: vhs non è installato qui. |
| 11 | `docs/launch-copy.md` | 3 bozze (LinkedIn, Show HN, r/devops), con limiti dichiarati e nessuna promessa di completezza. |

## 8. Findings

| ID | Severita' | File:linea | Problema | Fix proposto |
|---|---|---|---|---|
| F39 | **MAJOR (launch blocker, riaperto)** | `src/otlog2fix/report.py:31` | `&#64;` non impedisce l'autolink email di GFM: email, `mailto:`, `xmpp:` e il nome file nell'header restano link cliccabili (provato con l'API di GitHub e con cmark-gfm). Il test passa perché verifica il sorgente, non il render | `@` → `&#64;<!-- -->` (dopo `html.escape`); test con `re.search(r"&#64;[A-Za-z0-9]", before) is None` |
| F41 | — | `src/otlog2fix/cli.py:52-67` | ✅ CLOSED | — |
| F42 | — | `src/otlog2fix/chunker.py:8-12`, test | ✅ CLOSED (b); (a) parziale, vedi F44 | — |
| F43 | — | `docs/reviews/README.md` | ✅ CLOSED (deliverable Claude) | — |
| F44 | MINOR | `tests/test_cli.py:307-326` | Nessun test cattura la perdita del margine di 2 caratteri per le virgolette (mutazione `- 0` sopravvive) | Aggiungere il caso `"a" * 1996` → `len == 1000` |
| F45 | MINOR | `.github/workflows/ci.yml:22-30` | Il job `perf` gira a ogni push/PR (spec: solo manuale) e copre solo lo split, non la redaction | `on: workflow_dispatch` più `if: github.event_name == 'workflow_dispatch'` sul job; includere `redact()` nello script; `timeout 90s` e `timeout-minutes: 5` |
| F46 | MINOR | `pyproject.toml:29-32` | Placeholder `<GITHUB_OWNER>` ancora su `main`; la correzione non è committata e usa `OT-Log2Fix` invece di `ot-log2fix` | Committare con gli URL canonici `https://github.com/Sunraku73/ot-log2fix` |
| F47 | MINOR | tag `last-reviewed` | Spostato su `ba277da` prima della review | `git tag -f last-reviewed da681fa` |
| F48 | MINOR | `.github/workflows/ci.yml`, `pyproject.toml` (`[dev]`) | Riproducibilità: action su tag mobili, `ruff` non bloccato, nessun `permissions: contents: read` né `timeout-minutes` | Bloccare `ruff` (`ruff==<versione attuale>`), `permissions: contents: read` a livello di workflow, `timeout-minutes: 10`; facoltativo: action pinnate per SHA |
| F49 | MINOR | `pyproject.toml:10` | Il metadato `License` contiene il testo integrale (forma legacy) | `license = "MIT"`, `license-files = ["LICENSE"]`, `setuptools>=77` |
| F40 | MINOR, by-design | `src/otlog2fix/chunker.py` (`select_chunk`) | Invariato | Roadmap v0.2 (analisi di tutti i chunk) |

## 9. Verdetto

### `ba277da` — fix: S3.1 autolink residui, messaggi config, test (F39,F41,F42) + CI/packaging

**CHANGES_REQUESTED.**
F39 era il launch blocker: con un renderer GFM reale email, `mailto:` e `xmpp:` restano link cliccabili, e il test non se ne accorge perché controlla il sorgente.
F41 e F42(b) sono chiusi; la CI riproduce la matrice. Scope S3.3: F39 (obbligatorio), più F44, F45 e F46, piccoli e consigliati nello stesso commit. F47 è manuale; F48 e F49 vanno in backlog.

### Azioni conseguenti

- `docs/PLAN.md` **non aggiornato**: la condizione era "se APPROVED".
- `git tag -f last-reviewed HEAD` **non autorizzato**. Autorizzato invece `git tag -f last-reviewed da681fa` (F47).
- **Lancio:** non pubblicare i post di `docs/launch-copy.md` prima di S3.3 APPROVED e della registrazione di `docs/demo.gif`.
