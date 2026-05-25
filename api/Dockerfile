# syntax=docker/dockerfile:1

FROM python:3.12-slim AS builder

WORKDIR /build

RUN apt-get update \
  && apt-get install -y --no-install-recommends build-essential \
  && rm -rf /var/lib/apt/lists/*

COPY backend/push_swap/ ./backend/push_swap/
RUN make -C backend/push_swap

FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN addgroup --system app \
  && adduser --system --ingroup app app

COPY api/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
  && pip install --no-cache-dir -r requirements.txt

COPY api/ ./api/
RUN mkdir -p ./backend/push_swap
COPY --from=builder /build/backend/push_swap/push_swap ./backend/push_swap/push_swap

RUN chmod +x ./backend/push_swap/push_swap \
  && chown -R app:app /app

USER app

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
