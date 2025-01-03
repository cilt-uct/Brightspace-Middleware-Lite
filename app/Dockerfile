# Base Image
FROM python:3.11-slim

ADD VERSION .

# Install curl
RUN apt-get update && apt-get install -y curl pkg-config build-essential default-libmysqlclient-dev

# Set Timezone for Docker Container
RUN apt-get update && apt-get install -y tzdata
ENV TZ=Africa/Johannesburg
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Create directory for the app user
RUN mkdir -p /home/app

# Create the app user
RUN groupadd app && useradd -g app app

# Create the home directory
ENV HOME=/home/app
ENV APP_HOME=/home/app

WORKDIR $APP_HOME

# Install python dependencies
COPY ./requirements.txt $APP_HOME
RUN pip install --no-cache-dir --upgrade -r $APP_HOME/requirements.txt

# copy project
COPY ./VERSION $APP_HOME
COPY ./service $APP_HOME

# chown all the files to the app user
RUN chown -R app:app $APP_HOME

# change to the app user
USER app

# Run
ENTRYPOINT ["/home/app/entrypoint.sh"]
