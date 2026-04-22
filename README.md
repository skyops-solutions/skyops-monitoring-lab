# SkyOps Monitoring Lab

**GitHub:** `skyops-solutions/skyops-monitoring-lab`  
**Docker Hub:** `error404gg/skyops-monitoring-lab`

Повний DevOps стек: Python FastAPI + Nginx + Prometheus + Grafana + Loki + GitHub Actions CI/CD.

---

## Структура проекту

```
project/
├── app/                         # FastAPI застосунок
│   └── main.py
├── tests/                       # pytest тести
│   └── test_main.py
├── nginx/
│   └── nginx.conf               # Reverse proxy
├── monitoring/
│   ├── prometheus.yml           # Конфігурація Prometheus
│   ├── alert_rules.yml          # Правила алертів
│   ├── alertmanager.yml         # Alertmanager + Telegram
│   ├── loki-config.yml          # Loki (збір логів)
│   ├── promtail-config.yml      # Promtail (агент логів)
│   └── grafana/                 # Grafana дашборди та datasources
├── .github/workflows/
│   ├── ci.yml                   # Тести на всіх гілках
│   ├── staging.yml              # Staging pipeline
│   └── production.yml           # Production pipeline
├── Dockerfile
├── docker-compose.yml           # App stack (app + nginx)
└── docker-compose.monitoring.yml # Monitoring stack
```

---

## Швидкий старт

### 1. Клонувати репозиторій

```bash
git clone https://github.com/skyops-solutions/skyops-monitoring-lab.git
cd skyops-monitoring-lab
```

### 2. Запустити застосунок

```bash
docker compose up -d --build
```

Доступно:
| Сервіс | URL |
|--------|-----|
| App (через Nginx) | http://localhost |
| App напряму | http://localhost:8000 |
| Метрики | http://localhost:8000/metrics |
| Health check | http://localhost:8000/health |

### 3. Запустити monitoring stack

> Спочатку налаштуй Telegram алерти (div нижче), потім:

```bash
docker compose -f docker-compose.monitoring.yml up -d
```

Доступно:
| Сервіс | URL | Логін |
|--------|-----|-------|
| Grafana | http://localhost:3000 | admin / admin123 |
| Prometheus | http://localhost:9090 | — |
| Alertmanager | http://localhost:9093 | — |
| Loki | http://localhost:3100 | — |

### 4. Зупинити всі сервіси

```bash
docker compose down
docker compose -f docker-compose.monitoring.yml down
```

---

## Налаштування Telegram алертів

### Крок 1: Отримати Bot Token

1. Відкрий Telegram → знайди `@BotFather`
2. Відправ `/newbot` → дай назву боту
3. Скопіюй токен формату `7123456789:AAF...`

### Крок 2: Отримати Chat ID

1. Додай бота до групи або напиши йому напряму
2. Відкрий в браузері:
   ```
   https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates
   ```
3. У відповіді знайди `"id"` в блоці `"chat"` — це і є chat_id

### Крок 3: Відредагувати alertmanager.yml

```yaml
receivers:
  - name: "telegram"
    telegram_configs:
      - bot_token: "7123456789:AAF..."  # ← твій токен
        chat_id: -1001234567890         # ← твій chat_id (від'ємний для груп)
```

---

## GitHub Actions — налаштування секретів

Перейди в GitHub репо → **Settings → Secrets and variables → Actions → New repository secret**

| Secret | Значення |
|--------|----------|
| `DOCKER_USERNAME` | `error404gg` |
| `DOCKER_PASSWORD` | твій Docker Hub пароль або Access Token |

> Access Token краще ніж пароль: Docker Hub → Account Settings → Security → New Access Token

### Як отримати Docker Hub Access Token

1. Зайди на [hub.docker.com](https://hub.docker.com)
2. Натисни на свій аватар → **Account Settings**
3. **Security** → **New Access Token**
4. Дай назву `github-actions`, дозвіл `Read & Write`
5. Скопіюй токен — він показується лише один раз

---

## Поведінка CI/CD по гілках

| Гілка | Що відбувається |
|-------|----------------|
| `main`, `feature/*` | Запускаються тести |
| `staging` | Тести → build → push `:staging` tag |
| `production` | Тести → build → push `:latest` + `:<sha>` + git tag |

### Workflow гілок

```
main ─────────────────────────────── CI тести
    └─── merge → staging ──────────── CI + build + push :staging
              └─── merge → production ─ CI + build + push :latest
```

---

## Rollback

### Docker Compose rollback (локально)

Кожен production deploy пушить образ з конкретним SHA. Щоб відкотитись:

```bash
# Подивись доступні теги на Docker Hub
# Формат: error404gg/skyops-monitoring-lab:<sha>

# Відредагуй docker-compose.yml — заміни image на попередній тег
image: error404gg/skyops-monitoring-lab:abc1234

# Перезапусти
docker compose up -d
```

### GitHub rollback (через git)

```bash
# Знайди попередній commit
git log --oneline production

# Скинь production гілку на попередній commit
git checkout production
git revert HEAD          # створює новий commit з відміною змін
git push origin production

# або жорсткий rollback (обережно!)
git reset --hard <commit-hash>
git push --force origin production
```

---

## Grafana — як читати дашборди

Відкрий http://localhost:3000 → Dashboards → **SkyOps Application Dashboard**

### Панелі та що вони показують

| Панель | Що читати |
|--------|-----------|
| **CPU Usage %** | Поточне навантаження на CPU. Жовтий > 70%, червоний > 85% |
| **Memory Usage %** | Використання RAM. Якщо > 85% — застосунок може почати свопити |
| **HTTP Request Rate** | Кількість запитів в секунду по кожному endpoint'у |
| **HTTP Latency (p50/p95/p99)** | p50 = медіанний час відповіді. p99 = найгірші 1% запитів. Якщо p99 >> p50 — є outliers |
| **Memory (bytes)** | Абсолютні значення used/available RAM |
| **App Status** | GREEN = app відповідає, RED = app недоступний |
| **Container Logs** | Логи всіх Docker контейнерів через Loki |

### Корисні PromQL запити для дослідження

```promql
# Кількість запитів по статус кодам
sum by(status) (rate(http_request_duration_seconds_count[5m]))

# Відсоток помилок
rate(http_request_duration_seconds_count{status=~"5.."}[5m]) /
rate(http_request_duration_seconds_count[5m]) * 100

# Топ повільних endpoints
topk(5, histogram_quantile(0.95, sum by(le, handler)(
  rate(http_request_duration_seconds_bucket[5m])
)))
```

### Перевірка алертів

Prometheus alerts: http://localhost:9090/alerts  
Alertmanager: http://localhost:9093

---

## Локальний запуск тестів

```bash
# Встанови залежності
pip install -r requirements.txt

# Запусти тести
pytest tests/ -v
```

---

## Kubernetes deployment

Маніфести знаходяться в `k8s/`. Кластер: `docker-desktop`.

### Передумови

```bash
# Встановити Helm репозиторії (один раз)
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update
```

### Розгорнути app

```bash
# Namespace + app маніфести
kubectl apply -f k8s/namespace.yml
kubectl apply -f k8s/app/

# Перевірити стан (2 pods мають бути Running)
kubectl get pods -n skyops
```

### Розгорнути monitoring в K8s

```bash
# Prometheus + Grafana + Alertmanager
helm install kube-prometheus-stack prometheus-community/kube-prometheus-stack \
  --namespace monitoring --create-namespace \
  -f k8s/monitoring/kube-prometheus-stack-values.yml

# Loki
helm install loki grafana/loki \
  --namespace monitoring \
  -f k8s/monitoring/loki-values.yml \
  --set loki.useTestSchema=true
```

### Доступ до сервісів (port-forward)

```bash
# App
kubectl port-forward -n skyops svc/skyops-app 8080:80
# → http://localhost:8080/health

# Grafana
kubectl port-forward -n monitoring svc/kube-prometheus-stack-grafana 3001:80
# → http://localhost:3001  (admin / admin123)

# Prometheus
kubectl port-forward -n monitoring svc/kube-prometheus-stack-prometheus 9091:9090
# → http://localhost:9091
```

### Структура k8s/

```
k8s/
├── namespace.yml              # namespace: skyops
├── app/
│   ├── deployment.yml         # 2 replicas, readiness/liveness probes
│   ├── service.yml            # ClusterIP :80 → pod :8000
│   ├── ingress.yml            # nginx ingress, host: skyops.local
│   └── hpa.yml                # автомасштабування: 2–5 pods при CPU>70%
└── monitoring/
    ├── kube-prometheus-stack-values.yml   # Prometheus + Grafana + Alertmanager
    └── loki-values.yml                    # Loki single-binary mode
```

### Rollback в Kubernetes

```bash
# Переглянути історію деплоїв
kubectl rollout history deployment/skyops-app -n skyops

# Відкотитись на попередню версію
kubectl rollout undo deployment/skyops-app -n skyops

# Відкотитись на конкретну ревізію
kubectl rollout undo deployment/skyops-app -n skyops --to-revision=2

# Змінити образ вручну на конкретний тег
kubectl set image deployment/skyops-app app=error404gg/skyops-monitoring-lab:<sha> -n skyops
```

---

## Корисні команди

```bash
# Перевірити логи застосунку
docker compose logs -f app

# Перевірити статус всіх контейнерів
docker compose ps
docker compose -f docker-compose.monitoring.yml ps

# Перезапустити тільки app
docker compose restart app

# Оновити образ з Docker Hub
docker compose pull app
docker compose up -d app

# Перевірити метрики вручну
curl http://localhost/metrics | grep http_request

# K8s — логи app
kubectl logs -n skyops -l app=skyops-app -f

# K8s — статус всіх ресурсів
kubectl get all -n skyops
```
