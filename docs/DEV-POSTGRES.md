# Local development database (Windows, no Docker)

Docker Desktop is the documented path (`docker compose up`, Postgres on **5433**). When the Docker daemon is
unavailable, this machine uses a throwaway PostgreSQL 16 cluster built from the already-installed PostgreSQL 16
binaries — no credentials, local-only, port **5434**.

## Create it (already done once)

```bash
PGBIN="/c/Program Files/PostgreSQL/16/bin"
export PGDATA="$LOCALAPPDATA/Temp/nyra-pg"
"$PGBIN/initdb.exe" -D "$PGDATA" -U nyra --auth=trust --encoding=UTF8 --locale=C
"$PGBIN/createdb.exe" -h 127.0.0.1 -p 5434 -U nyra nyra
```

## Start / stop

Start it **detached** so it survives the shell that launched it (a foreground `pg_ctl start` dies with the
session on Windows — the server processes get killed and the cluster reports `0xC0000142`):

```powershell
Start-Process -FilePath 'C:\Program Files\PostgreSQL\16\bin\postgres.exe' `
  -ArgumentList '-D',"$env:LOCALAPPDATA\Temp\nyra-pg",'-p','5434','-c','listen_addresses=127.0.0.1' `
  -WindowStyle Hidden
```

Stop it:

```bash
"/c/Program Files/PostgreSQL/16/bin/pg_ctl.exe" -D "$LOCALAPPDATA/Temp/nyra-pg" stop
```

## Point the app at it

```bash
export DATABASE_URL="postgresql://nyra@127.0.0.1:5434/nyra"
cd apps/api && python -m nyra_api.cli db:migrate && python -m nyra_api.cli db:seed
python -m nyra_api.cli smoke          # 16 end-to-end checks
python -m nyra_api.cli db:reset --yes # wipe + reload demo data
```

A native PostgreSQL 16 Windows service also listens on **5432**; that is why the Docker stack maps 5433 and this
cluster uses 5434. Nothing here touches the service or its databases.
