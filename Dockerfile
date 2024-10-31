FROM python:3.12.5-alpine3.19
LABEL maintainer="matthammond.com"

ENV PYTHONUNBUFFERED=1

COPY ./requirements.txt /requirements.txt
COPY ./docs /docs
COPY ./scripts /scripts

WORKDIR /docs
EXPOSE 8000

RUN python -m venv /py && \
    /py/bin/pip install --upgrade pip && \
    apk add --update --no-cache postgresql-client && \
    apk add --update --no-cache --virtual .tmp-deps \
       build-base postgresql-dev musl-dev linux-headers && \ 
    /py/bin/pip install -r /requirements.txt && \
    apk del .tmp-deps && \
    adduser --disabled-password --no-create-home leadpilot && \
    mkdir -p /vol/web/static && \
    mkdir -p /vol/web/media && \
    chown -R leadpilot:leadpilot /vol && \
    chmod -R 755 /vol && \
    chmod -R +x /scripts && \
    chown -R leadpilot:leadpilot /docs && \
    chmod -R 755 /docs

ENV PATH="/scripts:/py/bin:$PATH"

USER leadpilot

CMD ["run.sh"]
