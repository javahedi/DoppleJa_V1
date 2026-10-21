FROM python:3.12-slim

WORKDIR /code

COPY backend/requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY backend /code/backend
COPY alembic.ini /code/alembic.ini

EXPOSE 8000

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
