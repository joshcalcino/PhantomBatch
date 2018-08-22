import json
import logging as log
import pickle
import os


def load_init_config(filename):
    """ Load in the json configuration file. """

    with open(filename) as f:
        d = json.load(f)
    f.close()
    return d


def save_config(pbconf):
    """ Save the phantombatch config file to disk. """

    log.debug('Saving PhantomBatch config to disk.')

    with open(pbconf['name'] + '_pbconf.pkl', 'wb') as f:
        pickle.dump(pbconf, f, pickle.HIGHEST_PROTOCOL)


def load_config(pbconf):
    """ Load a saved copy of phantombatch config. Note that this function takes the initial json phantombatch config
    file as an argument. This will get overwritten. """

    log.debug('Loading in a saved copy of PhantomBatch config..')

    with open(pbconf['name'] + '_pbconf.pkl', 'rb') as f:
        return pickle.load(f)


def check_for_phantom_warnings(output):
    """ Check for any warnings in the phantom routines. """

    log.debug('Checking for warnings in phantom output..')

    warnings_kw = ['WARNING', 'Warning', 'warning']

    for line in output:
        print([warning in line for warning in warnings_kw])
        if any([warning in line for warning in warnings_kw]):
            log.warning('Phantom warning found: ' + line)


def check_pbconf_sim_dir_consistency(job_name, sim_dir, pbconf):
    """ Check to make sure that job_name corresponds to the correct sim_dir """

    short_sim_dir = os.path.basename(sim_dir)

    if job_name.startswith(pbconf['name']):
        return short_sim_dir.startswith(job_name[len(pbconf['name'])+1:])  # +1 since there is an underscore in the name

    elif job_name.startswith(pbconf['short_name']):
        return short_sim_dir.startswith(job_name[len(pbconf['short_name'])+1:])

    else:
        return False


def save_phantom_output(output, pbconf):
    """ Save the output from phantom into a separate file. """

    output_filename = os.path.join(os.environ['PHANTOM_DATA'], pbconf['name'], 'phantom_output')

    if os.path.exists(output_filename):
        with open(output_filename, 'a') as f:
            # pickle.load(f)
            f.write(output)

    else:
        with open(output_filename, 'w') as f:
            f.write(output)
