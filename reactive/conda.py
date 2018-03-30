import subprocess

from charmhelpers.core import hookenv
from charmhelpers.core.host import chownr
from charmhelpers.fetch.archiveurl import ArchiveUrlFetchHandler
from charms.reactive import endpoint_from_flag, when, when_not, set_flag


@when('endpoint.conda.joined')
@when_not('conda.installed')
def install_conda():
    aufh = ArchiveUrlFetchHandler()
    endpoint = endpoint_from_flag('endpoint.conda.joined')
    conda_data = endpoint.relation_data()[0]

    hookenv.log("Install Conda")
    hookenv.status_set('maintenence', "Installing Conda")

    # Download and install conda
    conda_installer_path = aufh.download_and_validate(
        conda_data.get('url'),
        conda_data.get('sha'),
        validate="sha256"
    )
    if conda_installer_path:
        subprocess.call(['bash', conda_installer_path, '-b', '-f', '-p',
                         '/home/ubuntu/anaconda'])
        subprocess.call(['/home/ubuntu/anaconda/bin/conda', 'update', '-y',
                         '-n', 'base', 'conda'])

        # Create virtualenv and install jupyter
        subprocess.call(['/home/ubuntu/anaconda/bin/conda', 'create', '-y',
                         '-n', 'jupyter', 'python=3.5', 'jupyter', 'nb_conda'])
        subprocess.call(['/home/ubuntu/anaconda/bin/conda', 'install', '-y',
                         'jupyter'])

        # Install any extra conda packages
        if conda_data.get('conda_extra_packages'):
            subprocess.call(['/home/ubuntu/anaconda/bin/conda', 'install',
                             '-y', conda_data.get('conda_extra_packages')])

        # Pip install findspark
        subprocess.call(['/home/ubuntu/anaconda/envs/jupyter/bin/pip',
                         'install', 'findspark'])

        # Install any extra conda pip packages
        if conda_data.get('conda_extra_pip_packages'):
            subprocess.call(
                ['/home/ubuntu/anaconda/envs/jupyter/bin/pip',
                 'install', conda_data.get('conda_extra_pip_packages')])
        # Chown the perms to ubuntu
        chownr('/home/ubuntu/anaconda', 'ubuntu', 'ubuntu', chowntopdir=True)

        # Set installed flag
        set_flag('conda.installed')
        hookenv.status_set('active', "Conda ready")
    else:
        hookenv.status_set('blocked',
                           "Could not verify conda installer, please DEBUG")
        return
