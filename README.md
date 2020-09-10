# FRRA

Research management platform for the Fragments of the Roman Republican Antiquarians grant.

# Documentation

High level design: https://wiki.ucl.ac.uk/display/IA/Republican+Antiquarian+HLD

# Development

## Branches

`master` holds production code installed in the production server.
Feature branches are named `feature/<branch_name>`, and contain work in progress that will be merged onto the `development` branch via approved pull requests.

## Running locally

This project uses containers. Below are set up instructions and useful commands.

### 1. Install Docker Engine

- Follow the instructions here for your platform: https://docs.docker.com/get-docker/
- You will need to create a free Docker account and sign into it

### 2. Generate ssh keys for GitLab

- Log into GitLab
- Select 'Settings' from the drop down on the top right menu
- Select 'SSH Keys' from the left menu
- Follow the instructions on the page. Your key is normally in the file `~/.ssh/id_rsa.pub`

### 3. Checkout the RARD source code

- Create a working folder, e.g. `~/projects/` and `cd` into it

- Clone the repo

```git clone git@git.automation.ucl.ac.uk:rits/rsdg/rard.git```

- Checkout the development branch:

```git checkout development```

### 4. Tell Docker about your folder

Docker needs to know the full path of your project folder 

- Open the Docker application
- Find 'Preferences' and then 'Resources'
- Click 'File Sharing'
- Click 'Add' (or '+') to add a new folder
- Browse to the project folder and click 'Open'
- Click 'Apply and Restart'

(Docker needs to restart for the changes to take effect).

More info is available online for your specific client, e.g. here for the Mac client:
https://docs.docker.com/docker-for-mac/#file-sharing

### 5. Build the containers

- For the example project location above:

```cd ~/projects/rard/src```

```docker-compose -f local.yml build --no-cache```

- Bring up the project

```docker-compose -f local.yml up```

or as a background process:

```docker-compose -f local.yml up -d```

NB the output will be hidden when run in the background. To inspect the logs after the fact:

```docker-compose -f local.yml logs -f```

(the `-f` will update the output as more log messages come in. Omit `-f` to just see a snapshot).

- With the container running, browse to `localhost:8000` in your browser and you should see the project's home page.


### 6. User Accounts

User accounts are created by the superuser. For convenience, and *on local development containers only* a superuser account is automatically created when the container is built.

Log into the admin area `localhost:8000/admin` using username: `developer` password: `developer`

Create users in the standard Django admin.

Log out of the admin and navigate to `localhost:8000` and follow the links to log in with the credentials you entered.

### 7. Useful Docker commands

Commands (shell or Django commands etc) are run on the Docker container via `docker-compose` using the local configuration. 

Your container needs to be running while these commands are run.

#### To stop a container:

```docker-compose -f local.yml down```

#### To stop a container and remove the volumes 
The `-v` option will delete any volume data e.g. Postgres data

```docker-compose -f local.yml down -v```

#### Open a Django shell:

```docker-compose -f local.yml run django python manage.py shell```

#### Run a general Django management command:

(for example `createsuperuser`)

```docker-compose -f local.yml run django python manage.py <command> [arguments]```

### 7. Running Tests:

#### Run unit tests:

```docker-compose -f local.yml run django pytest```

#### Run unit tests with coverage:

```docker-compose -f local.yml run django coverage run -m pytest```

NB to view coverage results, 

```docker-compose -f local.yml run django coverage html```

which creates a local folder `htmlcov`. Browse to the file `index.html` in that folder

#### Check code comprehensively:

```docker-compose -f local.yml run django flake8```

(no errors means check passed)

#### Check code style only:

```docker-compose -f local.yml run django pycodestyle```

(no errors means style check passed)

#### Check object types:

```docker-compose -f local.yml run django mypy rard```


### Requirements

Requirements are applied when the containers are built. 

## Continuos Integration

# Deployment
