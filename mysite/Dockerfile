FROM python:3.12.0b3-slim-bookworm

LABEL maintainer="Karm Patel"

ENV PYTHONUNBUFFERED=1

COPY . /app
WORKDIR /app

RUN apt-get update && apt-get install -y gcc  # optional: helpful for some pip packages
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

EXPOSE 8000

CMD ["python3", "manage.py", "runserver", "0.0.0.0:8000"]
