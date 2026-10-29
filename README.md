# retail-recommendations-service

A small "customers who bought this also bought" recommendations API, built
as a companion service to
[retail-store-sample-app](https://github.com/LondheShubham153/retail-store-sample-app)
(itself a fork of AWS's
[retail-store-sample-app](https://github.com/aws-containers/retail-store-sample-app)).

That app ships five services (ui, cart, catalog, orders, checkout) but has
no recommendations — this fills that gap as a standalone microservice you
can run next to it, without touching its code.

## How it works

Item-based collaborative filtering with no offline training step:

- The `orders` service in the main app publishes an `OrderCreatedEvent` to a
  RabbitMQ fanout exchange called `orders-exchange` whenever a checkout
  completes.
- This service subscribes to that same exchange. For every order, it bumps
  a Redis sorted set per product: `cooccur:{productId}` scores every other
  product that showed up in the same order.
- `GET /recommendations/products/{id}` returns the top co-purchased
  products for `id`, then fills any remaining slots with store-wide popular
  products. The requested product and existing results are excluded from
  this fallback. The strategy remains `item-cooccurrence` when related
  products lead the results, or `popular-fallback` for a cold start.
- `GET /recommendations/popular` returns the most-purchased products overall.

Written in Python (FastAPI + Redis + aio-pika), a deliberately different
stack from the Java/Go/Node services in the main app, since a
recommendations service is a natural fit for Python's data tooling.

## Running locally

```bash
docker compose up --build
```

This starts the service on `http://localhost:8087`, plus its own Redis and
RabbitMQ. To see real recommendations come from real orders, point the
`orders` service's RabbitMQ connection at this same broker (or just use the
manual test endpoint below).

Without Docker:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
export RETAIL_RECOMMENDATIONS_MESSAGING_PROVIDER=none  # skip RabbitMQ for local dev
uvicorn app.main:app --reload --port 8080
```

## API

| Method | Path | Description |
|---|---|---|
| GET | `/recommendations/products/{productId}?limit=5` | Related products for one product |
| GET | `/recommendations/popular?limit=5` | Store-wide trending products |
| POST | `/internal/events/order-created` | Manually feed an order in (bypasses RabbitMQ, for local testing) |
| GET | `/health/liveness`, `/health/readiness` | Health checks |
| GET | `/metrics` | Prometheus metrics |

Full schema: [`openapi.yml`](./openapi.yml) (regenerate with
`scripts/generate-openapi-spec.sh` after changing a route).

Example:

```bash
curl -X POST localhost:8087/internal/events/order-created \
  -H 'content-type: application/json' \
  -d '{"order": {"id": "o1", "orderItems": [{"productId": "A"}, {"productId": "B"}]}}'

curl localhost:8087/recommendations/products/A
# {"productId":"A","strategy":"item-cooccurrence","recommendations":[{"productId":"B","score":1.0}]}
```

## Tests

```bash
source .venv/bin/activate
pytest
```

Uses `fakeredis`, so no services need to be running.

## Config

All env vars follow the `RETAIL_RECOMMENDATIONS_*` convention used by the
other services in the main app:

| Variable | Default | Notes |
|---|---|---|
| `RETAIL_RECOMMENDATIONS_REDIS_URL` | `redis://localhost:6379/0` | |
| `RETAIL_RECOMMENDATIONS_MESSAGING_PROVIDER` | `none` | `rabbitmq` to enable the order-event consumer |
| `RETAIL_RECOMMENDATIONS_MESSAGING_RABBITMQ_ADDRESSES` | `localhost:5672` | |
| `RETAIL_RECOMMENDATIONS_MESSAGING_RABBITMQ_USERNAME` / `_PASSWORD` | `guest` / `guest` | |
| `RETAIL_RECOMMENDATIONS_MESSAGING_RABBITMQ_EXCHANGE` | `orders-exchange` | Must match the orders service |

## What's intentionally not here

No Helm chart or Kubernetes/ArgoCD manifests — this is kept as a small,
standalone service you can run with Docker Compose. If you later want to
deploy it alongside the main app on Kubernetes, copy the pattern used by
`src/checkout/chart` in the main repo (Deployment + Service + ConfigMap +
a bundled Redis).
