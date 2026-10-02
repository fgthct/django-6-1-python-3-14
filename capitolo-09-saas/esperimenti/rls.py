"""La seconda cintura: Row Level Security di PostgreSQL, su una tabella di prova."""

import os

import psycopg

SAAS = "host=localhost port=5433 dbname=saas user=saas password=saas"
# Per l'ultima prova serve un superutente con password: SUPER_DSN="host=localhost port=5433 dbname=saas user=... password=..."
SUPER = os.environ.get("SUPER_DSN")


def righe(conn, org):
    with conn.cursor() as c:
        c.execute("SELECT set_config('app.org', %s, false)", [org])
        c.execute("SELECT count(*) FROM prova_rls")
        return c.fetchone()[0]


with psycopg.connect(SAAS, autocommit=True) as conn:
    conn.execute("DROP TABLE IF EXISTS prova_rls")
    conn.execute("CREATE TABLE prova_rls (id serial PRIMARY KEY, organizzazione text NOT NULL, titolo text)")
    conn.execute("INSERT INTO prova_rls (organizzazione, titolo) SELECT 'acme', 'a' || n FROM generate_series(1, 5) n")
    conn.execute("INSERT INTO prova_rls (organizzazione, titolo) SELECT 'rossi', 'r' || n FROM generate_series(1, 3) n")
    print("senza RLS, tenant 'acme':                  ", righe(conn, "acme"), "righe (8 in tutto)")

    conn.execute("ALTER TABLE prova_rls ENABLE ROW LEVEL SECURITY")
    conn.execute("CREATE POLICY solo_il_mio_tenant ON prova_rls "
                 "USING (organizzazione = current_setting('app.org', true)) "
                 "WITH CHECK (organizzazione = current_setting('app.org', true))")
    print("RLS attiva, ma il proprietario è esentato:  ", righe(conn, "acme"), "righe  <- la trappola")

    conn.execute("ALTER TABLE prova_rls FORCE ROW LEVEL SECURITY")
    print("RLS forzata, tenant 'acme':                 ", righe(conn, "acme"), "righe")
    print("RLS forzata, tenant 'rossi':                ", righe(conn, "rossi"), "righe")
    print("RLS forzata, nessun tenant:                 ", righe(conn, ""), "righe")
    try:
        conn.execute("SELECT set_config('app.org', 'acme', false)")
        conn.execute("INSERT INTO prova_rls (organizzazione, titolo) VALUES ('rossi', 'intruso')")
    except psycopg.errors.InsufficientPrivilege as e:
        print("scrittura sul tenant sbagliato:             ", str(e).splitlines()[0])

if SUPER:
    with psycopg.connect(SUPER, autocommit=True) as conn:
        print("un superutente, anche con RLS forzata:      ", righe(conn, "acme"), "righe  <- ignora tutto")

with psycopg.connect(SAAS, autocommit=True) as conn:
    conn.execute("DROP TABLE prova_rls")
