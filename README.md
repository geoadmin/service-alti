service-alti
============


Height and profile services for [http://api3.geo.admin.ch](http://api3.geo.admin.ch)

# Getting started

Checkout the source code:

    git clone https://github.com/geoadmin/service-alti.git

or when you're using ssh key (see https://help.github.com/articles/generating-ssh-keys):

    git clone git@github.com:geoadmin/service-alti.git


## Deploying to dev, int, prod and demo


Do the following commands **inside your working directory**. Here's how a standard
deploy process is done.

`make deploydev SNAPSHOT=true`

This updates the source in /var/www... to the latest master branch from github,
creates a snapshot and runs nosetests against the test db. The snapshot directory
will be shown when the script is done. *Note*: you can omit the `-s` parameter if
you don't want to create a snapshot e.g. for intermediate releases on dev main.

Once a snapshot has been created, you are able to deploy this snapshot to a
desired target. For integration, do

`make deployint SNAPSHOT=201512011411`

This will run the full nose tests **from inside the 201512011411 snapshot directory** against the **integration db cluster**. Only if these tests are successfull, the snapshot is deployed to the integration cluster.

`make deployprod SNAPSHOT=201512011411`

This will do the corresponding thing for prod (tests will be run **against prod backends**)
The same is valid for demo too:

`make deploydemo SNAPSHOT=201512011411`

You can disable the running of the nosetests against the target backends by adding
`notests` parameter to the snapshot command. This is handy in an emergency (when
deploying an old known-to-work snapshot) or when you have to re-deploy
a snapshot that you know has passed the tests for the given backend.
To disable the tests, use the following command:

`make deployint SNAPSHOT=201512011411 NO_TESTS=notests`

Use `notests` parameter with care, as it removes a level of tests.

Per default the deploy command uses the deploy configuration of the snapshot directory.
If you want to use the deploy configuration of directory from which you are executing this command, you can use:

`make deployint SNAPSHOT=201512011411 DEPLOYCONFIG=from_current_directory`

## Deploying a branch

Call the `make deploybranch` command **in your working directory** to deploy your current
branch to test (Use `make deploybranchint` to also deploy it to integration).
The code for deployment, however, does not come from your working directory,
but does get cloned (first time) or pulled (if done once) **directly from github**.
So you'll likely use this command **after** you push your branch to github.

The first time you use the command will take some time to execute.

The code of the deployed branch is in a specific directory
`/var/www/vhosts/service-alti/private/branch` on both test and integration.
The command adds a branch specific configuration to
`/var/www/vhosts/service-alti/conf`. This way, the deployed branch
behaves exactly the same as any user specific deploy.
A deploy to a "demo" instance is possible too (simply use ./deploybranch.sh demo).

Sample path:
http://service-alti.int.bgdi.ch/gjn_deploybranch/ (Don't forget the slash at the end)

## Deleting a branch

To list all the deployed branch:
`make deletebranch`

To delete a given branch:
`make deletebranch BRANCH_TO_DELETE=my_deployed_branch`

## Run nosetests manual on different environments
We are able to run our integration tests against different staging environments

To run against prod environment:
`scripts/nose_run.sh -p`

To run against int environment:
`scripts/nose_run.sh -i`

To run against dev/test environment:
`scripts/nose_run.sh`

To run against your private environment:
`make test`


## Python Code Styling

We are currently using the FLAKES 8 convention for Python code.
You can find more information about our code styling here:

    http://www.python.org/dev/peps/pep-0008/
    http://pep8.readthedocs.org/en/latest/index.html

You can find additional information about autopep8 here:

    https://pypi.python.org/pypi/autopep8/

To check the code styling:

  ```bash
make lint
  ```

To autocorrect most linting mistakes

  ```bash
make autolint
  ```
