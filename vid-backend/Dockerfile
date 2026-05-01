FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_DEFAULT_TIMEOUT=600
ENV PIP_RETRIES=10
ENV PIP_DISABLE_PIP_VERSION_CHECK=1


WORKDIR /app

RUN addgroup --system vid && adduser --system --ingroup vid vid

COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt

COPY app ./app

RUN mkdir -p /data && chown -R vid:vid /app /data
USER vid

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
