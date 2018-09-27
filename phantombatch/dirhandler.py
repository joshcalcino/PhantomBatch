import os
import logging as log


def loop_keys_dir(pconf):
    """ A function for generating both directory names and job names for the job scripts. """
    dirs = []
    for key in pconf:
        if isinstance(pconf[key], list):
            if key == 'pindex':
                dirs = dir_func(dirs, 'p', pconf[key])

            if key == 'qindex':
                dirs = dir_func(dirs, 'q', pconf[key])

            if key == 'binary_e':
                # Build up an array of e's that isn't too long and disregard the '0.'
                dict_arr = [format(i, '.2f')[2:] for i in pconf[key]]
                dirs = dir_func(dirs, 'e', dict_arr)

            if key == 'binary_a':
                # Build array of a's, which are rounded, to get rid of unnecessary decimal places
                dict_arr = [round(i, 1) for i in pconf[key]]
                dirs = dir_func(dirs, 'a', dict_arr)

            if key == 'm2':
                dirs = dir_func(dirs, 'm2', pconf[key])

            if key == 'alphaSS':
                dirs = dir_func(dirs, 'aSS', pconf[key])

            if key == 'binary_i':
                dirs = dir_func(dirs, 'i', pconf[key])

            # Loop over planet parameters
            if 'mplanet' in key:
                #  Adding in key[-1] makes sure that we select the write planet number
                dirs = dir_func(dirs, 'mp' + key[-1], pconf[key])

            if 'rplanet' in key:
                dirs = dir_func(dirs, 'rp' + key[-1], pconf[key])

            if 'inclplanet' in key:
                dirs = dir_func(dirs, 'ip' + key[-1], pconf[key])

    return dirs


def create_dirs(pconf, pbconf, run_dir):
    """ Create the simulation directories. """

    log.info('Checking if simulation directories exist..')

    suite_directory = os.path.join(run_dir, pbconf['name'])

    dirs = loop_keys_dir(pconf)

    for tmp_dir in dirs:
        cdir = os.path.join(suite_directory, 'simulations', tmp_dir)
        if not os.path.exists(cdir):
            os.mkdir(cdir)

    pbconf['dirs'] = dirs
    log.info('Completed.')


def dir_func(dirs, string, dict_arr):
    if len(dirs) is not 0:
        dirs = [i+'_' for i in dirs]

    else:
        dirs = [string+str(i).replace('.', '') for i in dict_arr]
        return dirs

    tmp_dir = ['']*len(dict_arr)
    for i in range(0, len(dict_arr)):
        tmp_dir[i] = string+str(dict_arr[i]).replace('.', '')

    dirs = [dirs[i] + tmp_dir[j] for i in range(0, len(dirs)) for j in range(0, len(tmp_dir))]
    return dirs
