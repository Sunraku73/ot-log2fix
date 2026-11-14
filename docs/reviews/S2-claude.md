# Review S2.0 + S2.1 — Claude (task S2.2)

- Data: 2026-11-14
- Commit: `49dbf8e` fix: S2.0 redaction batch (C41-C48, F22, F11) · `e638e98` feat: S2.1 schema validation, report, chunker, prompt v1.1
- Working tree: `scripts/report.sh` v3 non committato (F23/F24).
- Deliverable miei: `tests/fixtures/adv_06_redaction_bypass_s22.txt` + C50, C51, C53, C54 (SHOULD).

> **Limite di questa review:** la tabella F25-F33 del planner non e' arrivata con il prompt S2.2. Non e' nel repo, non e' nei bundle in `~/Downloads` e non e' nei file di testo vicini. Ho verificato in modo eseguibile i quattro finding per cui il task da' l'ipotesi di prova (F25, F27, F28, F33). **F26 e F29-F32 sono PENDING**: servono i testi originali.

## 0. `make check` e gate MUST

Eseguito in prima persona su `e638e98`:

```
.venv/bin/ruff check src tests
All checks passed!
.venv/bin/pytest -q
150 passed, 1 skipped in 0.81s
```

Lo `skipped` e' il set SHOULD vuoto. Dopo l'aggiunta di C50-C54 (§3): `150 passed, 4 xfailed in 0.77s`.

**Gate MUST indipendente** (script mio, lettura `bytes → decode("utf-8")`): **50/50**, come atteso, nessun residuo. C40-C48 sono stati coperti e promoti; C14 e' stato riscritto (`sk-or-v1-SynthCANARY14-not-a-real-key-000000`) e il pattern `sk-` lo copre ancora.

## 1. Finding del planner F25-F33

| ID | Esito | Prova eseguita |
|---|---|---|
| F25 | **CONFERMATO** | `AnalysisResult.model_validate({... "evidence": ["1"]}, context={"log": fixture_01})` → **ACCEPTED**. Anche `"11/14/2026 09:1"` passa. `schema.py:32` usa `line.startswith(value)`: basta un prefisso qualunque di una riga, anche il solo inizio del timestamp. Il controllo anti-allucinazione e' soddisfatto banalmente |
| F26 | PENDING | Testo del finding non ricevuto |
| F27 | **CONFERMATO** | Log: `b'... name="Q3 ![x](http://collector.example.invalid/c) ...'`. Nel Markdown: `b'... name="Q3 \\![x]\\(http://collector.example.invalid/c) ...'`, quindi **non** identico byte per byte. `report.py:20` inserisce backslash nell'evidence, che pero' sta dentro un blocco recintato (` ```text `), dove i backslash sono letterali e le immagini non vengono renderizzate. L'escape non protegge nulla e corrompe la citazione: un consulente che fa `grep` della riga non la trova |
| F28 | **CONFERMATO** | File con una riga di 20.000 caratteri, `max_chunk_chars` di default 12000: `otlog2fix analyze` → `Errore input: Una riga del log supera il limite del chunk`, **exit 1**. Una sola riga lunga (stack trace JSON su una riga, URL lunga in un access log, anche iniettata da un attaccante) blocca l'analisi dell'intero file |
| F29-F32 | PENDING | Testo dei finding non ricevuto |
| F33 | **REFUTATO** (come vulnerabilita' raggiungibile) | La primitiva esiste: `redact("...\ud800...")` funziona, `json.dumps(..., ensure_ascii=False)` conserva il surrogato, `.encode("utf-8")` → `UnicodeEncodeError`. Ma nessun percorso dal CLI produce un surrogato isolato: (1) i byte `ED A0 80` nel file vengono rifiutati da `decode("utf-8")` → exit 1 gestito; (2) `%ED%A0%80` → `unquote` da' U+FFFD; (3) `&#xD800;` → `html.unescape` da' U+FFFD; (4) il testo `\uD800` nel file resta testo; (5) `\ud800` nella risposta del modello → pydantic rifiuta il JSON (`json_invalid`). Hardening facoltativo, non un finding |

### Cosa verifica davvero `tests/test_report.py` (letto sul file, non sul bundle)

- `:26` `assert r"\![img]\(http://evil)" in md`: verifica la **presenza** dell'escape, ma sulla stringa di **evidence** (dentro il blocco recintato), non sulla root cause. La root cause escapata produce `\!\[img\]\(http&#58;//evil\)`, che non contiene quel frammento. Il test quindi **fissa il comportamento di F27**: corregge in modo sbagliato l'evidence e fallira' quando F27 verra' sistemato. Va riscritto per verificare che l'evidence nel blocco sia identica byte per byte e che il fence sia piu' lungo di qualunque sequenza di backtick.
- `:25` `"````text" in md`: verifica che il fence cresca con i backtick dell'evidence. Corretto.
- `:27` `"&lt;a href=evil&gt;"` e `:28` `r"\[link\]\(http&#58;//evil\)"`: verificano la **presenza** dell'escape nei campi di testo libero (`missing_context`, `notes`). Corretto: fuori dal fence l'escape serve.
- `test_render_sentinel`: verifica che la sentinella sia mostrata in un pannello giallo (`\x1b[33m`). Corretto.

## 2. Altri problemi trovati in S2.1 (prove eseguite)

| Prova | Risultato |
|---|---|
| Evidence copiata da una riga di log che contiene `ESC]8;;http://evil.example.invalid ESC\` (hyperlink OSC 8) e `notes` del modello con `ESC[2J ESC[1;32mTUTTO OK`, poi `render()` su un terminale | Le sequenze **arrivano raw al terminale**: OSC 8 = True, clear-screen = True. Un log ostile (o il modello manipolato da un'injection) puo' mostrare link falsi, cancellare lo schermo, colorare un falso "TUTTO OK". `rich.Text` impedisce il markup Rich ma non filtra i caratteri di controllo |
| Il vero `ORA-01653` nel chunk 1, poi 400 righe INFO, poi `user-agent="ERROR nothing to see"` nell'ultimo chunk | `select_chunk` → chunk 4/4, che **non contiene** l'errore reale. Una stringa "ERROR" controllata dall'attaccante decide quale chunk analizzare (viene stampato un avviso, ma la diagnosi e' sbagliata) |
| Chunk di 12.000 `<` | Dopo l'encoding diventano **71.998 caratteri** (`<` = 6 caratteri). `max_chunk_chars` misura il testo prima dell'encoding, non quello inviato: budget di contesto superato fino a 6× sui log XML |

## 3. Avversario limitato (5 varianti, solo C40-C48)

Rubrica S2.2: nuovi MUST solo con evidenza da capture reali anonimizzate. Non ne ho, quindi tutto va a SHOULD.

| Variante | Esito | Canary |
|---|---|---|
| W1 (C41) `%2C` nel valore di `password=` in query string | LEAK parziale: `_ENCODED_SEPARATOR` copre `%26`/`%3B`/`%20`, ma `_VALUE` si ferma anche a `,` | C50 SHOULD |
| W2 (C48) stringa di connessione PostgreSQL/Npgsql `Host=...;Password=Synth CANARY51;` | LEAK parziale: `_CONNECTION` riconosce solo `jdbc:`/`Server=`/`Data Source=` (CS supporta PostgreSQL) | C51 SHOULD |
| W3 (C46) `"password":"Synth\\"` (backslash escapato prima della virgoletta) | ok | — |
| W4 (C45) `Basic` spezzato **senza** indentazione | LEAK della seconda meta': `_BASIC_START` richiede che la riga successiva inizi con spazio o TAB | C53 SHOULD |
| W5 (C47) `<cfg:password><![CDATA[...]]></cfg:password>` | LEAK: `_CDATA_START` non accetta prefissi di namespace | C54 SHOULD |

Fixture: `tests/fixtures/adv_06_redaction_bypass_s22.txt`, strict xfail.

## 4. F23/F24 — `report.sh` v3 con decoy

`SEGRETO_decoy.txt` nella root (contenuto `password=DECOY_CANARY_S22_do_not_ship`) → `scripts/report.sh` → `/home/epatella/Downloads/otlf-review-20261114-145229.md`.

| Controllo | Esito |
|---|---|
| `git diff --cached --quiet` prima e dopo | exit 0 / exit 0 ✅ |
| `sha256(git ls-files -s)` e `sha256(git status --short)` | invariati ✅ |
| Sezione "Git status (allowlist)" | solo file in allowlist + `(1 file non in allowlist esclusi)` ✅ |
| Contenuto del decoy nel bundle | 0 ✅ |
| Nome del decoy nel bundle | 4 occorrenze, **tutte** dentro il testo della mia review S1.7 (che descrive il test del decoy), sia nel diff sia nella sezione review. Nessuna da `git status` ✅ |
| "Commit da revieware" | presente: `e638e98`, `49dbf8e`, `a60751e` ✅ |

Decoy rimosso. Nota: senza il tag `last-reviewed` il baseline ripiega su `HEAD~3` (`6632a01`) e include `a60751e`, gia' approvato. Si risolve da solo appena il tag esiste.

## 5. Prompt v1.1 e package-data

- `src/otlog2fix/cli.py:64`: `load_prompt("analyze_v1.1")`. ✅
- Wheel installata in una venv temporanea `/home/epatella/Downloads/otlf-s22-*`: contiene `prompts/analyze_v1.md`, `analyze_v1.1.md` e `CHANGELOG.md`. ✅
- Da fuori dal repo, con un finto server OpenAI-compatible e la fixture 01: exit 0; il payload contiene SYSTEM v1.1 ("UNA SOLA stringa JSON") e USER v1.1 ("JSON-encoded", "chunk 1 di 1"); `--md report.md` scritto con l'evidence corretta. Venv rimossa. ✅

## 6. Tabella findings

| ID | Severita' | File:linea | Problema | Stato | Fix proposto |
|---|---|---|---|---|---|
| F1-F8, F10, F12-F14, F16-F21 | — | — | Sprint 1 | ✅ CLOSED | — |
| F9 | MINOR | `.gitignore:10` | `*.log` ignora le fixture | ⏸ MITIGATED | — |
| F11 | MINOR | `tests/fixtures/adv_02_redaction_bypass.txt` | Il finto `sk-or-v1-` a 64 hex poteva far scattare la push protection | ✅ CLOSED (`49dbf8e`) | — |
| F15 | MINOR | `src/otlog2fix/cli.py:64` | Prompt v1.1 non attivo | ✅ CLOSED (`e638e98`) | — |
| F22 | MINOR | `src/otlog2fix/redaction.py` (`_is_count`) | Falsi positivi su chiavi di conteggio | ✅ CLOSED (`49dbf8e`) | `pass_count=3` e `ticket_count=4` restano invariati; `pass_count=abc` viene redatto |
| F23 | MINOR | `scripts/report.sh` (v3, non committato) | Nomi dei file esclusi nello status | ✅ CLOSED (working tree) | Da committare |
| F24 | MINOR | `scripts/report.sh` (v3, non committato) | Baseline / sezione commit | ✅ CLOSED (working tree) | Da committare |
| F25 | MAJOR | `src/otlog2fix/schema.py:30-33` | L'evidence accetta qualunque prefisso, anche di 1 carattere | ❌ CONFERMATO | Accettare solo la riga intera (dopo `strip`) oppure il suo prefisso troncato a esattamente 200 caratteri. Test con `"1"` e con un prefisso del timestamp → rifiutati |
| F26 | ? | ? | — | ⏳ PENDING | Serve il testo |
| F27 | MAJOR | `src/otlog2fix/report.py:19-21` + `tests/test_report.py:26` | Evidence alterata dentro il blocco recintato | ❌ CONFERMATO | Rimuovere i `.replace(...)` sull'evidence (il fence dinamico basta). Riscrivere il test: evidence nel blocco == riga del log, byte per byte |
| F28 | MAJOR | `src/otlog2fix/chunker.py:14-15` | Una riga oltre `max_chunk_chars` → exit 1 sull'intero file | ❌ CONFERMATO | Spezzare la riga in segmenti di `max_chars` (con un marker di continuazione) oppure troncarla con un marker; test con una riga di 20.000 caratteri → exit 0 |
| F29-F32 | ? | ? | — | ⏳ PENDING | Serve il testo |
| F33 | — | `src/otlog2fix/cli.py:75-77` | Surrogato isolato → crash in encoding | ✅ REFUTATO | Primitiva non raggiungibile (5 percorsi provati, §1) |
| **F34** | MAJOR | `src/otlog2fix/report.py:55-73` (`render`) e `markdown` | Sequenze di escape del terminale (OSC 8, CSI) dal log (evidence) o dal modello arrivano raw: link falsi, clear-screen, falso "TUTTO OK" | 🆕 OPEN | Prima di `Text(...)` e nel Markdown sostituire i caratteri di controllo C0/C1 tranne `\t`: `re.sub(r"[\x00-\x08\x0b-\x1f\x7f-\x9f]", "�", s)`. Test con OSC 8 e `ESC[2J`. Nota: F25 non basta, perche' l'evidence e' gia' nel log |
| **F35** | MINOR | `src/otlog2fix/chunker.py:27-34` | `select_chunk` pilotabile da una stringa "ERROR" controllata dall'attaccante | 🆕 OPEN | Contare solo i livelli nella colonna del livello (o l'ultimo chunk con piu' righe ERROR/FATAL); in S3 analizzare tutti i chunk |
| **F36** | MINOR | `src/otlog2fix/cli.py:62,75-77` | `max_chunk_chars` misura il testo prima dell'encoding (fino a 6× con `<`) | 🆕 OPEN | Dimensionare il chunk sulla lunghezza **codificata** |

## 7. Verdetti per commit

### `49dbf8e` — fix: S2.0 redaction batch (C41-C48, F22, F11)

**APPROVED**

Gate MUST 50/50 verificato in modo indipendente (bytes); F11 e F22 chiusi con prova; le 5 varianti avversarie producono solo SHOULD (C50-C54).
Riserva: se uno tra F26 e F29-F32 riguarda questo commit, rivaluto appena ricevo il testo.

### `e638e98` — feat: S2.1 schema validation, report, chunker, prompt v1.1

**CHANGES_REQUESTED**

Il cuore della feature non regge: l'evidence passa la validazione con 1 carattere (F25), il report la altera (F27) e una riga lunga blocca l'analisi (F28).
Inoltre le sequenze di escape del terminale passano raw (F34): quattro MAJOR da correggere in S2.3, piu' F26 e F29-F32 da verificare.

### Conseguenze

- **`git tag -f last-reviewed HEAD`: NON autorizzato.** HEAD e' `e638e98` (CHANGES_REQUESTED). Se il planner vuole far avanzare il baseline dei bundle, il tag ammissibile e' `git tag -f last-reviewed 49dbf8e`. Lo autorizzo solo dopo la verifica di F26 e F29-F32.
- **`docs/PLAN.md`: non aggiornato.** La condizione del task e' "se APPROVED", e lo stato complessivo non lo e'. Al prossimo APPROVED segnero' S2.0, S2.1, la rubrica (MUST solo con evidenza da capture reali anonimizzate) e la chiusura di F11, F22 e F23.
- **Da committare (Codex):** `scripts/report.sh` v3, che chiude F23/F24.
