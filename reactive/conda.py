from charmhelpers.core.hookenv import log, status_set
from charmhelpers.core.host import chownr

from charms.reactive import endpoint_from_flag, when, when_not, set_flag

from charms.layer.conda_api import init_install_conda, CONDA_HOME


@when('endpoint.conda.available')
@when_not('conda.installed')
def install_conda():
    log("Installing Conda")
    status_set('maintenance', "Installing Conda")

    endpoint = endpoint_from_flag('endpoint.conda.joined')
    conda_data = endpoint.relation_data()[0]

    init_install_conda(
        conda_data['url'],
        conda_data['sha'],
        validate='sha256'
    )

    create_conda_venv(python_version="3.5")
    chownr(CONDA_HOME, 'ubuntu', 'ubuntu', chowntopdir=True)

    log("Conda installed")
    status_set('active', "Conda installed")
    set_flag('conda.installed')


@when_not('endpoint.conda.available')
def status_blocked():
    hookenv.status_set('blocked',
                       "Need relation to conda provider to continue.")
    return
