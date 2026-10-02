# Backup e ripristino dei dati

## I backup

Il backup dei database di produzione viene eseguito ogni notte alle 02:30 con pg_dump e copiato su un server in un'altra sede. Le copie vengono conservate per 30 giorni, poi sostituite dalle più recenti.

I file dei documenti condivisi hanno un backup separato, incrementale, eseguito ogni quattro ore durante l'orario di lavoro.

## Quanto si può perdere

L'obiettivo di punto di ripristino (RPO) è di 24 ore: in caso di guasto si può perdere al massimo il lavoro di una giornata. L'obiettivo di tempo di ripristino (RTO) è di quattro ore: il servizio deve tornare operativo entro quattro ore dalla segnalazione.

## Come si chiede un ripristino

Chi ha cancellato per errore un file o una riga di dati deve aprire un ticket sul portale dell'assistenza indicando che cosa manca, in quale cartella o tabella si trovava e quando è stato visto per l'ultima volta. L'ufficio informatico risponde entro la giornata lavorativa.

## Le prove

Ogni trimestre l'ufficio informatico esegue una prova di ripristino su un server di collaudo, per essere sicuro che i backup siano davvero leggibili. Un backup che non è mai stato ripristinato non è un backup.
