FROM python:3.9-alpine as base
ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1
ENV PIP_NO_CACHE_DIR false
RUN pip install --upgrade pip
RUN apk update && apk upgrade && \
    apk add --update --no-cache python3-dev gcc libc-dev libffi-dev
WORKDIR /app
COPY ./envs ./envs
COPY ./models ./models
COPY ./utils ./utils
COPY ./requirements.txt .
RUN pip install -r requirements.txt
COPY exchanges_manage ./exchanges_manage

FROM base as discord_bot
COPY ./discord_bot ./discord_bot
CMD sh -c "python -m discord_bot"

#FROM base as discord_display_bot
#COPY ./discord_display_bot ./discord_display_bot
#CMD sh -c "python -m discord_display_bot"

FROM base as orders_monitoring
COPY ./orders_monitoring ./orders_monitoring
CMD sh -c "python -m orders_monitoring"

FROM base as orders_creator
COPY ./orders_creator ./orders_creator
CMD sh -c "python -m orders_creator"
