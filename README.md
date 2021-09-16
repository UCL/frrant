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

### 2. Generate ssh keys for GitHub (if not already done)

- Log into GitHub
- Select 'Settings' from the drop down on the top right menu
- Select 'SSH and GPG keys' from the left menu
- Follow the [instructions in their guide](https://docs.github.com/articles/generating-an-ssh-key/)

### 3. Checkout the RARD source code

- Create a working folder, e.g. `~/projects/` and `cd` into it

- Clone the repo

```git clone git@github.com:UCL/frrant.git```

- Checkout the development branch:

```git checkout development```

### 4. Tell Docker about your folder

Docker needs to know the full path of your project folder (so it can look for changes)

- Open the Docker application
- Find 'Preferences' and then 'Resources'
- Click 'File Sharing'
- Remove any unnecesary folders e.g. `/tmp`, `/var`
(Docker can use a lot of resources when watching folders for changes so it is best to keep this list to the absolute minimum)
- Click 'Add' (or '+') to add a new folder
- Browse to your projects folder and click 'Open'
- Click 'Apply and Restart'

(Docker needs to restart for the changes to take effect).

More info is available online for your specific client, e.g. here for the Mac client:
https://docs.docker.com/docker-for-mac/#file-sharing

### 5. Build the containers

- For the example project location above:

```cd ~/projects/frrant/src```

Note that for running locally (on our own machines) we use the `local.yml` config and not `production.yml` which is for deployment to the production platform.

```docker-compose -f local.yml build```

to ensure everything is built from scratch, you can add `--no-cache`
```docker-compose -f local.yml build --no-cache```

- Bring up the project

```docker-compose -f local.yml up```

or as a background process:

```docker-compose -f local.yml up -d```

NB the output will be hidden when run in the background. To inspect the logs after the fact:

```docker-compose -f local.yml logs -f```

(the `-f` will update the output as more log messages come in. Omit `-f` to just see a snapshot).

- With the container running, browse to `localhost:8000` in your browser and you should see the project's home page.

To restart the project, e.g. if some changes have been made to code that don't need the container to be rebuilt then use:

```docker-compose -f local.yml down```

```docker-compose -f local.yml up```

If any changes are made to the machine configuration, e.g. new pip packages installed, then the project will need to be rebuilt. Safest is to rebuild with no cache (see above) though this will take longer. Depending on the change it might be advisable to try rebuilding first without the `--no-cache` option to save time.

```docker-compose -f local.yml down```

```docker-compose -f local.yml build [--no-cache]```

```docker-compose -f local.yml up```

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

### 8. Running Tests:

#### Run unit tests:

Note that by adding `--rm` to the commands then the container in which the tests are run is deleted once the tests have finished.

```docker-compose -f local.yml run --rm django pytest```

#### Run unit tests with coverage:

```docker-compose -f local.yml run --rm django coverage run -m pytest```

NB to view coverage results,

```docker-compose -f local.yml run --rm django coverage report```

which prints a top-level summary to the console. Alternatively for more detail, run

```docker-compose -f local.yml run --rm django coverage html```

which creates a local folder `htmlcov`. Browse to the file `index.html` in that folder

#### Check code comprehensively:

```docker-compose -f local.yml run --rm django flake8```

(no errors means check passed)

#### Check code style only:

```docker-compose -f local.yml run --rm django pycodestyle```

(no errors means style check passed)

#### Check object types:

```docker-compose -f local.yml run --rm django mypy rard```

#### Fix import order:

The command below will correct the order of your python imports to meet the standard

```docker-compose -f local.yml run --rm django isort .```

(import order errors when running the flake8 command should be fixed automatically by running the above command)

### Django Migrations

If you make changes to model definitions (i.e. in the `models.py` files) then these need to be reflected in a migration file.

A migration file is a Python 'patch' file generated by Django to apply the changes you have made to the definition to the actual database to keep it up to date.

If you have made a change to a model and need to generate a migration file:

```docker-compose -f local.yml run django python manage.py makemigrations```

You will then either need to restart your container so that these changes are applied:

```docker-compose -f local.yml down```

```docker-compose -f local.yml up```

and these migrations are applied. Alternatively, to apply the latest migrations without restarting the container:

```docker-compose -f local.yml run django python manage.py migrate```

Sometimes migrations cannot be automatically generated, e.g. if two developers have both generated migration files and Django doesn't know which in which order they should be applied. If the two migrations are independent of one another (i.e. relate to different models) then Django can automatically merge these migration files for you by running:

```docker-compose -f local.yml run django python manage.py makemigrations --merge```

and following the instructions.

If you have made changes to your models and have not generated a migration file then Django will warn you in the console output something like:

```
  Your models have changes that are not yet reflected in a migration, and so won't be applied.
  Run 'manage.py makemigrations' to make new migrations, and then re-run 'manage.py migrate' to apply them.
```

NB In our case we would run the suggested `manage.py` commands via the Docker container in the way shown above, i.e.

```docker-compose -f local.yml run django python manage.py makemigrations```

and

```docker-compose -f local.yml run django python manage.py migrate```


If your static files (css, js, fonts etc) have changed then on the production environments you will also need to refresh all of the static files in the deployed static folder.

```docker-compose -f production.yml run django python manage.py collectstatic```

Answer 'yes' to the 'are you sure question'. It might say something like '0 files updated' but this message is notoriously misleading. Check to see whether the static files (js etc) being used are the ones you expect.

### Loading data fixtures

To take a snapshot of e.g. the production database and install it locally we do the following:

Go to the production machine and run the following command:

```sudo docker-compose -f production.yml run --rm django python manage.py dumpdata --indent=4  --natural-foreign --natural-primary -a  > dump.json```

This dumps all (-a) the data in the database into a json file that we can load locally.

Now scp the json file to your local machine and run the following commands:


First, remove existing database:

```docker-compose -f local.yml down -v```

Rebuild database:

```docker-compose -f local.yml up -d --build```

Run the `src/loaddata.sh` script to load this:

```sh
./loaddata.sh dump.json
```

### Requirements

Requirements are applied when the containers are built.

## Continuous Integration

# Deployment

To deploy we need to set some variables.

(example shown for development, replace with production folder on production)

Under the folder `.envs` in the project folder (`ls -la` shows folders starting with `.`)

`mkdir .development`

`cd .development`

`sudo vi .django`

And enter the following:

```
USE_DOCKER=yes
IPYTHONDIR=/app/.ipython
DJANGO_SETTINGS_MODULE=config.settings.development
DJANGO_SECRET_KEY=<secret key>
DJANGO_ADMIN_URL=admin/
DJANGO_ALLOWED_HOSTS=<domain name>
```

In the above, the domain name will be e.g. `frrd-dev.addev.ucl.ac.uk` for development. If more than one are required then they can be comma-separated (NB do not put inside braces `[]`)

Next

`sudo vi .pgadmin`

enter the following:

```
PGADMIN_DEFAULT_EMAIL=<username>
PGADMIN_DEFAULT_PASSWORD=<password>
```

for the username/password combo to use for pgadmin. This admin interface allows you to manage backups etc.

Finally

`sudo vi .postgres`

and enter the following

```
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=frrant
POSTGRES_USER=devuser
POSTGRES_PASSWORD=<secret password>
```

for the username/password to use for postgres database.


If your static files have changed in a deployment (css, js, fonts etc) then you need to run the 'collectstatic' command described earlier.


## SSL Certificates

Before building the nginx container we need to do the following for development (and production)

`cd compose/development/nginx/certs`

`sudo openssl req -x509 -nodes -days 365 -config rardselfsigned.cnf -newkey rsa:2048 -keyout rardselfsigned.key -out rardselfsigned.crt`

This will generated a certificate and corresponding key file.

# Troubleshooting

If your deployment machine is light on space on `/var` then it is possible to request that Docker builds containers elsewhere by modifying the following file:

The file in question is:

```sudo vi /etc/docker/daemon.json```

Set its content to

```
{
   "graph": "/data/docker"
}
```

Then run:


`sudo systemctl daemon-reload`
`sudo systemctl restart docker`


Then restart your container. This example will build containers on the `/data` directory instead of `/var`


To view running containers as a list:

`sudo docker ps`

to view logs for a particular container in the above list

`sudo docker logs <containerid> -f`

the `-f` prints new lines as they are written. The `<containerid>` is the same shown in the output of `docker ps`


## To clean up space on /var

Remove yum caches

`sudo yum clean all`

If your containers are built to `/var` this will clean those up

`sudo docker system prune`


## If your server becomes unreachable 30 minutes after restarting Docker

You need to ensure IP forwarding is enabled:

Edit or create the file `/etc/sysctl.conf`

add or change the following line:

`net.ipv4.ip_forward = 1`

Then apply the settings with e.g.

`service network restart`


If the Javascript and css is not looking how you expect after production, ensure you have run 'collectstatic' on the target machine(s). See the description given earlier.

# Project management
During the software development stage, we work in sprint cycles that go from 2 to 4 weeks, depending on workload and availability. These have a planning meeting at the beginning, a meeting with the research team to demo all new changes, and a deployment to production if all changes have been approved by the research team during the meeting. We are currently using [this Zenhub workspace](https://app.zenhub.com/workspaces/frrant-public-612e33d9c2bb690015527ab6/board?repos=312338365) to plan tasks in each sprint, and we share a [GitHub priority board](https://github.com/UCL/frrant/projects/7) with the research team to better understand what tasks are essential for them, and which can wait.

Plans for next steps include running retrospectives in each internal sprint cycle, as well as making the pre-production/development server ready for the researchers so they can test and approve changes as we make them instead of waiting until the next meeting when we'll demo them live. 
