Ecco l'intero `README.md` riscritto in italiano, mantenendo tutti i dettagli tecnici, le variabili, i comandi, i codici d'uscita e le note del tuo progetto, e aggiungendo in cima l'intestazione richiesta e la sezione `## Riepilogo` (di circa 235 caratteri).

```markdown
# OT-Log2Fix

Progetto del corso di costruzione di IA

## Riepilogo

CLI in Python per il triage dei log OpenText Content Server e AppWorks con redazione dei dati sensibili e analisi tramite LLM locali (Ollama) o cloud (OpenRouter), restituendo causa probabile, evidenze e tre azioni correttive.

Triage da riga di comando per i log di OpenText Content Server e AppWorks: un LLM legge il log e restituisce una probabile causa radice, le righe di evidenza e tre passaggi di correzione.

**Stato:** alpha (0.1). I messaggi della CLI e i report sono attualmente in italiano. L'output in inglese è nella roadmap della v0.2.

## Esempio di output

Output reale di `otlog2fix analyze tests/fixtures/01_cs_ora_tablespace.txt --md report.md`, con Ollama locale e `qwen3:8b`, su un log sintetico di Content Server con errori Oracle `ORA-01653`. Qui sotto è riportato il file `report.md` non modificato (sorgente Markdown). I report sono attualmente in italiano.

```markdown
# Analisi del log

**File:** 01\_cs\_ora\_tablespace.txt  
**Chunk:** 1 di 1  
**Provider:** ollama · **Modello:** qwen3:8b  
**Timestamp UTC:** 2026-11-15T11:45:34.673645+00:00  
**Stato:** ok  
**Confidenza:** medium

## Causa

Errore ORA-01653: il tablespace OTCS\_SYNTH\_DATA non ha spazio sufficiente per espandere le tabelle DVersData e DTreeCore. I tentativi di aggiungere versioni e creare documenti falliscono a causa della mancanza di spazio disco.

## Evidenze

```text
11/14/2026 09:12:31.912 [Thread 14] ERROR   ORA-01653: unable to extend table OTCS_SYNTH.DVERSDATA by 8192 in tablespace OTCS_SYNTH_DATA
11/14/2026 09:12:33.802 [Thread 9]  ERROR   ORA-01653: unable to extend table OTCS_SYNTH.DTREECORE by 1024 in tablespace OTCS_SYNTH_DATA

```

## Azioni

1. Verifica lo spazio disponibile nel tablespace OTCS_SYNTH_DATA e le dimensioni delle tabelle DVersData/DTreeCore
2. Espandi il tablespace incrementando la dimensione o aggiungendo nuovi file di dati
3. Monitora l'uso dello spazio e ottimizza la gestione dei dati (es. purge vecchi versioni)

## Contesto mancante

* Versione del Content Server
* Configurazione del tablespace OTCS_SYNTH_DATA
* Altri chunk del log per verificare pattern ricorrenti

**Injection rilevata:** no

## Note

Errori ORA-01653 ricorrenti su tablespace OTCS_SYNTH_DATA

```

Lo stesso contenuto viene stampato nel terminale. Ogni riga di evidenza viene controllata rispetto al log redatto: deve corrispondere all'inizio di una riga di log. I passaggi di correzione sono suggerimenti: verificali prima di agire.

## Installazione

**Windows:** non ancora verificato su un host reale. I comandi PowerShell in questo README seguono la sintassi standard e la suite di test gira su `windows-latest` in CI, ma nessuno ha ancora eseguito l'intero percorso di installazione e analisi su una macchina Windows. Le segnalazioni sono benvenute.

### Prerequisiti

- **git**: `pipx` lo usa per recuperare il pacchetto da GitHub.
- **Python 3.10 o superiore**.
- **pipx**: installa la CLI in un proprio ambiente isolato.

**Ubuntu 22.04+ / Debian 12+:**

```bash
sudo apt update && sudo apt install -y git python3 pipx
pipx ensurepath    # poi apri un nuovo terminale

```

**Altri sistemi** (Windows, macOS, altre distribuzioni Linux): consulta `pipx.pypa.io` per `pipx`, `git-scm.com` per `git` e `python.org` per Python.

### Installare la CLI

```bash
pipx install git+[https://github.com/Sunraku73/ot-log2fix.git](https://github.com/Sunraku73/ot-log2fix.git)
otlog2fix version     # stampa: OT-Log2Fix 0.1.0
otlog2fix --help      # elenca i comandi: version, analyze

```

La configurazione proviene da variabili d'ambiente (prefisso `OTLF_`) oppure da un file `.env` nella directory da cui esegui il comando. Vedi `.env.example`.

| Variabile | Predefinito | Significato |
| --- | --- | --- |
| `OTLF_PROVIDER` | `ollama` | `ollama` o qualsiasi nome di provider compatibile con OpenAI |
| `OTLF_BASE_URL` | `http://localhost:11434/v1` | endpoint del provider |
| `OTLF_MODEL` | `qwen3:8b` | nome del modello |
| `OTLF_API_KEY` | vuoto | obbligatoria per i provider cloud |
| `OTLF_TIMEOUT` | `300` | secondi di attesa per il modello, 10–3600 |
| `OTLF_ENCODING` | `utf-8` | codifica del file di log (vedi *Codifica dei log*) |
| `OTLF_MAX_CHUNK_CHARS` | `12000` | dimensione del chunk, minimo 1000 |
| `OTLF_REDACT` | `true` | può essere `false` solo con Ollama locale |

### Modello locale con Ollama

La modalità locale richiede Ollama, disponibile per Linux, macOS e Windows.

```bash
ollama pull qwen3:8b      # circa 5 GB di download
ollama list               # qwen3:8b deve essere elencato

```

Per verificare che Ollama sia in esecuzione, interroga la sua API: deve rispondere con l'elenco dei modelli.

```bash
curl http://localhost:11434/api/tags                  # bash

```

```powershell
Invoke-RestMethod http://localhost:11434/api/tags     # PowerShell

```

**Hardware.** Misurato sul log di esempio qui sopra (14 righe, circa 2600 token di prompt), Ollama 0.23.1, almeno 3 esecuzioni per riga:

| Modello | GPU NVIDIA (24 GB VRAM) | Solo CPU (16 core) |
| --- | --- | --- |
| `qwen3:8b` (5.2 GB) | 6–13 s, risposta valida in ogni esecuzione | 80–120 s, risposta valida in ogni esecuzione |
| `qwen3:4b` (2.5 GB) | 20–37 s, risposta valida in ogni esecuzione | 220–380 s, nessuna risposta valida in 3 esecuzioni |

Il timeout predefinito (`OTLF_TIMEOUT=300`) copre `qwen3:8b` su CPU. Log più lunghi richiedono più tempo: aumentalo se vedi un timeout.

Usa `qwen3:8b`. `qwen3:4b` è più piccolo da scaricare ma non più veloce: ragiona molto più a lungo rispetto all'8b. Su CPU non ha prodotto una risposta valida nelle nostre prove, quindi consideralo solo per una GPU con poca memoria.

## Avvio rapido

### Locale con Ollama (i log non lasciano mai la macchina)

I valori predefiniti puntano già a `http://localhost:11434/v1` e `qwen3:8b`, quindi non serve alcuna configurazione.

**bash:**

```bash
otlog2fix analyze /percorso/di/thread.log --md report.md

```

**Windows PowerShell** (metti il percorso tra virgolette, specialmente se contiene spazi):

```powershell
otlog2fix analyze "C:\Logs\thread.log" --md report.md

```

### Cloud con OpenRouter (solo log sintetici o anonimizzati)

**bash:**

```bash
export OTLF_PROVIDER=openrouter
export OTLF_BASE_URL=[https://openrouter.ai/api/v1](https://openrouter.ai/api/v1)
export OTLF_API_KEY=<la-tua-chiave-openrouter>
export OTLF_MODEL=<id-modello>
otlog2fix analyze /percorso/di/thread.log --md report.md

```

**Windows PowerShell** (le variabili restano attive solo nella finestra corrente):

```powershell
$env:OTLF_PROVIDER = "openrouter"
$env:OTLF_BASE_URL = "[https://openrouter.ai/api/v1](https://openrouter.ai/api/v1)"
$env:OTLF_API_KEY  = "<la-tua-chiave-openrouter>"
$env:OTLF_MODEL    = "<id-modello>"
otlog2fix analyze "C:\Logs\thread.log" --md report.md

```

Puoi scegliere qualsiasi modello elencato su `openrouter.ai/models`. La redazione non può essere disabilitata con un provider cloud.

## Output

* **Terminale:** stato, causa radice, confidenza, righe di evidenza, tre passaggi di correzione e flag di injection.
* **`--md`:** lo stesso contenuto in formato Markdown, con nome del file, provider, modello e timestamp UTC.
* Quando il modello non ha le informazioni necessarie, deve rispondere `NON HO ABBASTANZA CONTESTO` ("not enough context") ed elencare cosa manca, invece di inventare funzioni OScript o endpoint REST.
* **Output del modello non valido:** se il modello restituisce un output non valido due volte, `otlog2fix` scrive un report di fallback invece di fallire ed esce con codice `3`. Il report inizia con `Report di fallback — analisi non completata`, indica `NON HO ABBASTANZA CONTESTO`, fornisce tre suggerimenti generici e cita la prima riga citabile del chunk come riferimento, non come diagnosi. La prompt injection viene indicata come `non valutata` ("not assessed"), perché non è avvenuta alcuna analisi. Negli script, controlla il codice di uscita: `0` è l'unico caso di analisi completa.
* **Codici di uscita:**
* `0` successo
* `1` errore di input o configurazione
* `2` errore del provider, oppure il modello ha restituito un output non valido due volte e il chunk analizzato non ha alcuna riga citabile (vedi *Risoluzione dei problemi*)
* `3` report di fallback: il modello ha restituito un output non valido due volte; il report (terminale e `--md`) viene scritto ma non contiene alcuna analisi



## Codifica dei log

I log vengono letti come UTF-8 per impostazione predefinita. I log OpenText scritti su server Windows sono spesso in CP1252 (Windows-1252). Un file simile fallisce con `Errore decodifica con utf-8; imposta OTLF_ENCODING (es. cp1252 per log Windows).` (uscita `1`) e nulla viene inviato al modello. Imposta esplicitamente la codifica:

**bash:**

```bash
OTLF_ENCODING=cp1252 otlog2fix analyze /percorso/di/thread.log

```

**Windows PowerShell:**

```powershell
$env:OTLF_ENCODING = "cp1252"
otlog2fix analyze "C:\Logs\thread.log"

```

Non c'è un rilevamento automatico di proposito. CP1252 decodifica quasi qualunque sequenza di byte senza errore, quindi una stima errata non fallirebbe: trasformerebbe silenziosamente i caratteri in altri, sia in ciò che legge il modello sia nelle evidenze citate nel report. Un'impostazione esplicita fallisce invece in modo evidente.

## Quali log analizzare

Il prompt è scritto per prodotti OpenText: Content Server, AppWorks e OTDS. Le fixture di test coprono attualmente questi casi:

* **Content Server:** errori di database (es. codici Oracle `ORA-`), errori di permessi sui nodi, errori di licenza, stack trace OScript.
* **AppWorks:** errori di autenticazione REST API (HTTP 401).

Non ci sono ancora fixture per OTDS.

`otlog2fix` accetta qualsiasi log in testo semplice fino a 10 MiB. Su log di altri prodotti la risposta è più spesso `NON HO ABBASTANZA CONTESTO` ("not enough context"). Questo è il comportamento previsto: il prompt chiede al modello di dirlo invece di inventare una diagnosi.

I nomi dei file di log e i percorsi predefiniti variano in base alla versione del prodotto e alla configurazione. Punta lo strumento al log che contiene l'errore su cui stai indagando, ritagliato sull'intervallo temporale rilevante.

## Provider

| Provider | `OTLF_PROVIDER` | `OTLF_BASE_URL` | API key | Redazione |
| --- | --- | --- | --- | --- |
| Ollama (locale) | `ollama` | `http://localhost:11434/v1` | nessuna | attiva per impostazione predefinita; disattivabile solo qui |
| OpenRouter (cloud) | `openrouter` | `https://openrouter.ai/api/v1` | obbligatoria | obbligatoria |
| Altro endpoint compatibile OpenAI | qualsiasi | relativo URL `/v1` | se richiesta | obbligatoria tranne che per `ollama` su loopback |

Per "locale" si intende il provider `ollama` con host `localhost`, `127.0.0.1` o `::1`. Qualsiasi altra combinazione è trattata come remota.

## Modello di sicurezza

In breve: la redazione riduce il rischio, non lo elimina. Per log sensibili, usa la modalità locale.

### Cosa fa la redazione

* Prima di ogni chiamata al modello, `otlog2fix` rimuove:
* password, token e ticket OpenText (`OTCSTicket`, `LLCookie`, `OTDSTicket`)
* header `Authorization` e chiavi API
* chiavi private PEM/PGP
* credenziali in URL, stringhe JDBC e comandi `sqlplus`
* indirizzi email


* I valori vengono sostituiti con segnaposto `[REDACTED:<type>]`.
* Vengono riconosciute anche codifiche comuni: percent-encoding, entità HTML, escape JSON, valori spezzati su più righe e base64 sotto chiavi sensibili.
* **Codifiche annidate:** una riga codificata a un livello più profondo del limite di decodifica viene redatta interamente (`[REDACTED:opaque_line]`). Nel dubbio, viene rimossa.
* **Nessuna riga forgiata:** la decodifica non crea mai nuove righe, quindi un `%0A` all'interno di un campo non può forgiare un record di log.

### Cosa NON garantisce

* La redazione è *best-effort* e basata su pattern. Non garantisce che il testo inviato sia privo di segreti. Un segreto in una forma imprevista può passare: una chiave sconosciuta, una codifica insolita o un valore senza etichetta.
* La copertura minima è vincolata da un *canary gate* (`tests/fixtures/redaction_canaries.tsv`). Il gate è una soglia di regressione, non una prova di completezza:
* **MUST:** segreti nelle forme tipiche dei log OpenText. La build fallisce se anche uno solo trapela.
* **SHOULD:** offuscamenti più rari non ancora coperti, tracciati come `strict xfail`. Quando uno viene coperto, il test ne impone la promozione a `MUST`.


* I log `DEBUG`/`trace` comportano un rischio maggiore. A quei livelli (body di richieste, header, dump di configurazione) i segreti compaiono più spesso e in più forme rispetto ai livelli predefiniti.

### Regole operative

| Scenario | Provider | Redazione |
| --- | --- | --- |
| Log sensibili, di produzione o di clienti | `ollama` su `localhost`/`127.0.0.1`/`::1` | consigliata; disattivabile solo qui |
| Log sintetici o già anonimizzati | cloud (es. `openrouter`) | obbligatoria: con `OTLF_REDACT=false` e un provider non locale il comando esce con codice `1` prima di qualsiasi chiamata |

* **I proxy vengono ignorati in locale.** Con un provider locale il client HTTP ignora `HTTP(S)_PROXY`/`ALL_PROXY`, così il log non può lasciare la macchina tramite un proxy.
* **"Locale" deve essere locale fino in fondo.** Un gateway su localhost che inoltra al cloud (es. LiteLLM) invalida questa garanzia.
* **Il log è input non attendibile.** Viaggia codificato in JSON tra delimitatore con nonce casuale, e il system prompt vieta di seguire istruzioni trovate al suo interno. Questo mitiga la prompt injection; non la impedisce.
* **Controlla a campione prima di andare sul cloud.** Verifica il testo redatto prima di usare un provider cloud. Non fare mai commit di log reali: tienili in `samples/private/` (ignorato da Git).
* **Segnalazione di bypass:** vedi `SECURITY.md`.

## Risoluzione dei problemi

I messaggi sono in italiano; la tabella li riporta così come vengono stampati.

| Sintomo (codice di uscita, messaggio) | Causa | Azione |
| --- | --- | --- |
| `2` `Provider non raggiungibile su http://localhost:11434. Verifica che Ollama sia attivo.` | Ollama non è in esecuzione oppure `OTLF_BASE_URL` è errato | Avvia Ollama e verificalo con `curl http://localhost:11434/api/tags`. Controlla `OTLF_BASE_URL` nell'ambiente e in `.env` |
| `2` `Timeout del provider dopo 300s. Su CPU aumenta OTLF_TIMEOUT (es. 600).` | Il modello non ha risposto entro `OTLF_TIMEOUT` secondi: probabile su macchine solo CPU o con log lunghi | Aumenta `OTLF_TIMEOUT` (fino a 3600), es. `OTLF_TIMEOUT=600` |
| `2` `Errore provider HTTP 404. Modello non trovato. Esegui: ollama pull qwen3:8b` | Il modello non è scaricato oppure `OTLF_MODEL` è scritto male | Esegui il comando `ollama pull` suggerito, poi `ollama list` per verificare il nome esatto |
| `2` `Errore provider HTTP <code>` (altri codici) | Il provider ha rifiutato la richiesta, es. `401` per una chiave API errata | Controlla `OTLF_API_KEY`, `OTLF_MODEL` e `OTLF_BASE_URL` |
| `3` con report di fallback: banner `Report di fallback: il modello non ha prodotto una risposta valida.`, causa `NON HO ABBASTANZA CONTESTO`, `Injection rilevata: non valutata` | Il modello ha restituito JSON non valido due volte: più probabile con modelli piccoli o log fuori da OpenText. I tre suggerimenti sono generici, non una diagnosi | Se succede spesso, prova un modello più grande (es. `qwen3:8b` invece di `qwen3:4b`) o estrai la porzione rilevante del log |
| `2` `Risposta del provider non valida e nessuna riga citabile nel chunk: impossibile produrre un report.` | JSON non valido due volte, e il chunk analizzato non ha alcuna riga citabile come evidenza (es. solo spazi bianchi, o righe fatte di un breve prefisso seguito da lungo padding) | Estrai la porzione rilevante del log, oppure rimuovi il padding, e riprova |
| `1` `Errore decodifica con utf-8; imposta OTLF_ENCODING (es. cp1252 per log Windows).` | Il log non è UTF-8 | Imposta `OTLF_ENCODING`, vedi *Codifica dei log* |
| `1` `Il file supera il limite di 10 MiB.` | Il file è più grande di 10 MiB | Estrai la porzione rilevante, es. la finestra temporale attorno all'errore |
| `1` `La redaction può essere disabilitata solo con provider locale ollama.` | `OTLF_REDACT=false` con un provider cloud o non loopback | È la policy di sicurezza, non un bug. Mantieni attiva la redazione oppure usa Ollama locale |
| `1` `OTLF_MAX_CHUNK_CHARS: deve essere un intero con valore minimo 1000.` | `OTLF_MAX_CHUNK_CHARS` è sotto 1000 o non è un numero | Usa un valore di almeno 1000 (predefinito 12000) |
| `1` `OTLF_<NAME>: valore non valido.` | Un'impostazione ha un valore non valido (es. `OTLF_TIMEOUT` fuori da 10–3600, un `OTLF_ENCODING` sconosciuto) | Correggi la variabile indicata; il valore in sé non viene mai stampato |
| `1` `Errore lettura file: …` | Percorso errato o file mancante | Controlla il percorso (mettilo tra virgolette in PowerShell) |

## Limiti noti

* **Analisi parziale.** Un log viene diviso in chunk di `OTLF_MAX_CHUNK_CHARS` (predefinito 12000, minimo 1000) e viene analizzato un solo chunk: quello con il maggior numero di livelli `ERROR`/`FATAL`, il più recente a parità. Il report lo indica ("chunk X di Y"). L'euristica di selezione può essere influenzata da contenuti di log costruiti ad arte.
* **Redazione *best-effort*.** Vedi sopra.
* **Suggerimenti, non risposte certe.** I passaggi di correzione sono suggerimenti da verificare. Il modello può sbagliare anche con confidenza alta, e le righe di evidenza vengono controllate per esistere nel log, non per essere quelle giuste.
* **Output solo in italiano per ora.**

## Roadmap (v0.2)

Questi sono piani, non impegni:

* Analizzare tutti i chunk e unire i risultati, invece di sceglierne uno (rimuove l'euristica di selezione).
* Output CLI e report in inglese.
* Pubblicazione del pacchetto su PyPI.
* Promozione dei canary `SHOULD` a `MUST` quando supportati da catture reali anonimizzate.

## Sviluppo

**Linux / macOS:**

```bash
python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"
make check   # ruff + pytest, incluso il canary gate

```

**Windows PowerShell** (senza `make`; non ancora verificato su un host reale):

```powershell
py -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
ruff check src tests
pytest -q

```

`scripts/report.sh` e `docs/demo.tape` (VHS) sono strumenti riservati ai manutentori su sistemi Unix; non servono per usare o testare la CLI.

La cronologia delle revisioni e le decisioni sono in `docs/reviews/` e `docs/PLAN.md` (in italiano).

## Licenza

MIT, vedi `LICENSE`.

## Supporto e ringraziamenti

Non affiliato né approvato da OpenText. OpenText, Content Server e AppWorks sono marchi di OpenText Corporation.

Ispirato alle attività pratiche e ai concetti del percorso *Elements of AI* / *Building AI*.

```

```
