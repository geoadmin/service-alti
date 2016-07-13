service-alti
============


Height and profile services for [http://api3.geo.admin.ch](http://api3.geo.admin.ch)

# Getting started

Checkout the source code:

    git clone https://github.com/geoadmin/service-alti.git

or when you're using ssh key (see https://help.github.com/articles/generating-ssh-keys):

    git clone git@github.com:geoadmin/service-alti.git


## Deploying to dev, int, prod and demo


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

## Git hooks

3 git hooks are installed automatically when `make user` is called.

All the hooks check that we don't accidently publish sensitive AWS keys to
github - in the files as well as in the commit messages. We also execute
`make lint` in the pre-commit hook.

Other checks can be added freely to any hook.

### `pre-commit` hook

Called before committing changes locally. The commands in the `scripts/pre-commit.sh` script are executed.

### `commit-msg` hook

Called before comitting changes locally and checks the commit message. The commands in the `scripts/commit-msg.sh` script are executed.

### `prepare-commit-msg` hook

Called before comitting changes locally and checks pre-commit messages (usually from --fast-forward merges. The commands in the `scripts/prepare-commit-msg.sh` are executed.
