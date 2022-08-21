FROM python:3.10-slim-bullseye

# Creates application directory
WORKDIR /app

# Creates an appuser and change the ownership of the application's folder
RUN useradd appuser && chown appuser /app

RUN apt-get update \
    && apt-get -y install build-essential \
    && apt-get -y install gettext

# Installs poetry and pip
RUN pip install --upgrade pip && \
    pip install poetry==1.1.12

# Copy dependency definition to cache
COPY --chown=appuser poetry.lock pyproject.toml /app/

# Installs projects dependencies as a separate layer
RUN poetry export -f requirements.txt -o requirements.txt && \
    pip uninstall --yes poetry && \
    pip install --no-deps --require-hashes -r requirements.txt

# Copies and chowns for the userapp on a single layer
COPY --chown=appuser . /app

# Switching to the non-root appuser for security
USER appuser
