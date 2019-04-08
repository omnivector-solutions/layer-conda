from charmhelpers.core import hookenv
from charmhelpers.core.host import chownr

from charms.reactive import (
    clear_flag,
    endpoint_from_flag,
    hook,
    set_flag,
    when,
    when_any,
    when_not,
)
from charms.layer import status

from charms.layer.conda_api import (
    CONDA_HOME,
    create_conda_venv,
    remove_conda_venv,
    init_install_conda,
    install_conda_packages,
    install_conda_pip_packages
)


APPLICATION_NAME = hookenv.application_name()


@hook('start')
def set_started_flag():
    """
    This flag is used to gate against certain
    charm code runnig until the start state has been reached.
    """
    set_flag('conda.juju.started')


@when_not('conda.installed')
def install_conda():
    """Install anaconda
    """
    if not CONDA_HOME.exists():
        hookenv.log("Installing Conda")
        status.maint("Installing Conda")

        conf = hookenv.config()

        # Download and install conda
        init_install_conda(
            conf.get('conda-installer-url'),
            conf.get('conda-installer-sha256'),
            validate="sha256"
        )

    else:
        hookenv.log("Conda already installed.")
        status.maint("Conda already installed.")

    hookenv.log("Conda installed")
    status.active("Conda installed")
    set_flag('conda.installed')


@when('conda.installed')
@when_not('conda.venv.available')
def init_venv():
    """Create conda virtual environment.
    """
    hookenv.log("Installing Conda Env: {}".format(APPLICATION_NAME))
    status.maint("Installing Conda Env: {}".format(APPLICATION_NAME))

    conf = hookenv.config()

    remove_conda_venv(env_name=APPLICATION_NAME)

    create_conda_venv(
        env_name=APPLICATION_NAME,
        python_version=conf.get('python-version')
    )
    if conf.get('conda-extra-packages'):
        install_conda_packages(
            env_name=APPLICATION_NAME,
            conda_packages=conf.get('conda-extra-packages').split()
        )
    if conf.get('conda-extra-pip-packages'):
        install_conda_pip_packages(
            env_name=APPLICATION_NAME,
            conda_pip_packages=conf.get('conda-extra-pip-packages').split()
        )

    chownr(str(CONDA_HOME), 'ubuntu', 'ubuntu', chowntopdir=True)

    set_flag('conda.venv.available')


@when('conda.installed',
      'conda.venv.available')
def set_conda_available_status():
    status.active('Conda Env Installed: {}'.format(APPLICATION_NAME))


@when_any('config.changed.conda-extra-packages',
          'config.changed.conda-extra-pip-packages')
@when('conda.venv.available',
      'conda.installed',
      'conda.juju.started')
def recreate_conda_env():
    clear_flag('conda.venv.available')
    clear_flag('config.changed.conda-extra-packages')
    clear_flag('config.changed.conda-extra-pip-packages')


@hook('stop')
def clear_venv():
    status.maint('Removing Conda Env: {}'.format(APPLICATION_NAME))
    remove_conda_venv(env_name=APPLICATION_NAME)
    status.active('Conda Env: {} removed'.format(APPLICATION_NAME))
