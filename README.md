# foto-kocourkovi

MVP Django aplikace pro fotografku.

## Lokální spuštění přes Docker

1. Zkopíruj `.env.example` na `.env`.
2. Spusť kontejnery:

```bash
docker compose up --build
```

3. V další konzoli spusť migrace:

```bash
docker compose exec web python manage.py migrate
```

4. Vytvoř superusera:

```bash
docker compose exec web python manage.py createsuperuser
```

5. Otevři administraci na `http://localhost:8880/admin/`.

## Produkce

Pro VPS je připravený `docker-compose.prod.yml`. Počítá s tím, že Nginx běží na hostu a směruje doménu `fotky.foto-kocourkovi.cz` na `127.0.0.1:8001`.
