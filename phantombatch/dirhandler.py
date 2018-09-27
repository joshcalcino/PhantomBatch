import os
import logging as log


def loop_keys_dir(pconf, pbconf):
    """ A function for generating both directory names and job names for the job scripts. """
    dirs = []
    no_loop_keys = []

    if 'no_loop' in pbconf and len(pbconf['no_loop']) > 0:
        nl_keys = list(pbconf['no_loop'].keys())
        fw_keys = list(pbconf['fix_with'].keys())

        for i in range(0, pbconf['no_loop']):
            dirs = keys_dir(dirs, fw_keys[i], pconf, no_loop=True)
            no_loop_keys.append(fw_keys[i])

            dirs = keys_dir(dirs, nl_keys[i], pconf, no_loop=True)
            no_loop_keys.append(nl_keys[i])

    for key in pconf:
        if isinstance(pconf[key], list) and key not in no_loop_keys:
            dirs = keys_dir(dirs, key, pconf, pbconf)

    return dirs


def keys_dir(dirs, key, pconf, no_loop=False):
    if key == 'pindex':
        dirs = dir_func(dirs, 'p', pconf[key], no_loop=no_loop)

    if key == 'qindex':
        dirs = dir_func(dirs, 'q', pconf[key], no_loop=no_loop)

    if key == 'binary_e':
        # Build up an array of e's that isn't too long and disregard the '0.'
        dict_arr = [format(i, '.2f')[2:] for i in pconf[key]]
        dirs = dir_func(dirs, 'e', dict_arr, no_loop=no_loop)

    if key == 'binary_a':
        # Build array of a's, which are rounded, to get rid of unnecessary decimal places
        dict_arr = [round(i, 1) for i in pconf[key]]
        dirs = dir_func(dirs, 'a', dict_arr, no_loop=no_loop)

    if key == 'm2':
        dirs = dir_func(dirs, 'm2', pconf[key], no_loop=no_loop)

    if key == 'alphaSS':
        dirs = dir_func(dirs, 'aSS', pconf[key], no_loop=no_loop)

    if key == 'binary_i':
        dirs = dir_func(dirs, 'i', pconf[key], no_loop=no_loop)

    # Loop over planet parameters
    if 'mplanet' in key:
        #  Adding in key[-1] makes sure that we select the write planet number
        dirs = dir_func(dirs, 'mp' + key[-1], pconf[key], no_loop=no_loop)

    if 'rplanet' in key:
        dirs = dir_func(dirs, 'rp' + key[-1], pconf[key], no_loop=no_loop)

    if 'inclplanet' in key:
        dirs = dir_func(dirs, 'ip' + key[-1], pconf[key], no_loop=no_loop)

    return dirs


def create_dirs(pconf, pbconf, run_dir):
    """ Create the simulation directories. """

    log.info('Checking if simulation directories exist..')

    suite_directory = os.path.join(run_dir, pbconf['name'])

    dirs = loop_keys_dir(pconf, pbconf)

    for tmp_dir in dirs:
        cdir = os.path.join(suite_directory, 'simulations', tmp_dir)
        if not os.path.exists(cdir):
            os.mkdir(cdir)

    pbconf['dirs'] = dirs
    log.info('Completed.')


def dir_func(dirs, string, dict_arr, no_loop=False):
    if len(dirs) is not 0:
        dirs = [i+'_' for i in dirs]

    else:
        dirs = [string+str(i).replace('.', '') for i in dict_arr]
        return dirs

    if no_loop:
        # For now, this is only going to work if you're wanting no_loop over one set of parameters...
        dirs = [dirs[i] + string + str(i).replace('.', '') for i in dict_arr]
        return dirs

    tmp_dir = ['']*len(dict_arr)
    for i in range(0, len(dict_arr)):
        tmp_dir[i] = string+str(dict_arr[i]).replace('.', '')

    dirs = [dirs[i] + tmp_dir[j] for i in range(0, len(dirs)) for j in range(0, len(tmp_dir))]
    return dirs
