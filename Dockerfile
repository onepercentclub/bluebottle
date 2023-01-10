# Based on best practices from Snyk: https://snyk.io/blog/best-practices-containerizing-python-docker/
# It builds the container in two steps for maximum caching 

################
# DEPENDENCIES #
################
FROM python:3.8 as deps

# Install missing dependencies
RUN apt-get update
RUN apt-get install -y --no-install-recommends \
  libxml2 \
  libxmlsec1 \
  libxmlsec1-dev \
  postgresql \
  postgis

# Set environment variables
ENV PIP_DISABLE_PIP_VERSION_CHECK 1
# will not try to write .pyc files
ENV PYTHONDONTWRITEBYTECODE 1  
# console output is not buffered by Docker
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /bluebottle

# Create the env (for caching)
RUN python -m venv /usr/app/venv
ENV PATH="/usr/app/venv/bin:$PATH"

# Copy files necessary for install
RUN mkdir bluebottle
COPY bluebottle/__init__.py ./bluebottle
COPY ["README.rst", "setup.py", "./"]

# Install any (missing) requirements
RUN pip install -e .

################
#  BLUEBOTTLE  #
################

FROM python:3.8

# Set work directory
WORKDIR /bluebottle

# Copy files
COPY --from=deps /bluebottle/venv ./venv
COPY . .

# Set the env
ENV PATH="/usr/app/venv/bin:$PATH"

# Run migrations
RUN python manage.py migrate_schemas --shared --settings=bluebottle.settings.testing