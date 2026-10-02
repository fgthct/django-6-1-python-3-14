-- Eseguito da PostgreSQL una sola volta, alla creazione del database, con l'utente amministratore:
-- l'estensione vector richiede privilegi che l'utente dell'applicazione non ha (e non deve avere).
CREATE EXTENSION IF NOT EXISTS vector;
