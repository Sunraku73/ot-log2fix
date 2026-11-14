# Prompt changelog

Formato: `<prompt>_v<N> | YYYY-MM-DD | autore | modifica` (una riga per modifica).

analyze_v1 | 2026-11-14 | Claude | Prima versione: ruolo consulente senior OpenText (CS, AppWorks, OTDS).
analyze_v1 | 2026-11-14 | Claude | Log delimitato da BEGIN/END con nonce per richiesta; contenuto dichiarato untrusted.
analyze_v1 | 2026-11-14 | Claude | Difesa da injection: finti ruoli, finti delimitatori e JSON preconfezionato ignorati; flag injection_detected.
analyze_v1 | 2026-11-14 | Claude | Vietato riportare URL/immagini dal log (anti-esfiltrazione nel report Markdown).
analyze_v1 | 2026-11-14 | Claude | Regola anti-allucinazione: sentinella "NON HO ABBASTANZA CONTESTO" + status insufficient_context.
analyze_v1 | 2026-11-14 | Claude | Lista esplicita di cose da non inventare: OScript, DAPI, endpoint REST, func=, opentext.ini, KB, patch.
analyze_v1 | 2026-11-14 | Claude | Output JSON: status, root_cause, confidence, evidence, fix_steps (esattamente 3), missing_context, injection_detected, notes.
analyze_v1 | 2026-11-14 | Claude | evidence obbligatoria con righe testuali del log; senza evidenza -> insufficient_context.
analyze_v1 | 2026-11-14 | Claude | Confidence a 3 livelli con criteri espliciti; low obbligatoria se insufficient_context.
analyze_v1 | 2026-11-14 | Claude | Step distruttivi solo con avviso backup/finestra di manutenzione.
analyze_v1 | 2026-11-14 | Claude | Contratto del loader nell'header (marker, ordine di sostituzione, nonce) per l'implementazione di Codex.
