import os
import logging as log


def loop_keys_dir(pconf, pbconf):
    """ A function for generating both directory names and job names for the job scripts. """
    dirs = []
    no_loop_keys = []

    if 'no_loop' in pbconf and len(pbconf['no_loop']) > 0:
        nl_keys = pbconf['no_loop']
        fw_keys = pbconf['fix_with']

        for i in range(0, len(pbconf['no_loop'])):
            print(dirs)
            dirs = keys_dir(dirs, fw_keys[i], pconf, no_loop=True)
            no_loop_keys.append(fw_keys[i])

            dirs = keys_dir(dirs, nl_keys[i], pconf, no_loop=True)
            no_loop_keys.append(nl_keys[i])

    for key in pconf:
        if isinstance(pconf[key], list) and key not in no_loop_keys:
            print(dirs)
            dirs = keys_dir(dirs, key, pconf, no_loop=False)

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

    if key == 'accr2':
        dirs = dir_func(dirs, 'acr2', pconf[key], no_loop=no_loop)

    if key == 'alphaSS':
        dirs = dir_func(dirs, 'aSS', pconf[key], no_loop=no_loop)

    if key == 'binary_i':
        dirs = dir_func(dirs, 'i', pconf[key], no_loop=no_loop)

    if key == 'disc_mbinary':
        dirs = dir_func(dirs, 'dm', pconf[key], no_loop=no_loop)

    # Loop over planet parameters
    if 'mplanet' in key:
        #  Adding in key[-1] makes sure that we select the write planet number
        dirs = dir_func(dirs, 'mp' + key[-1], pconf[key], no_loop=no_loop)

    if 'rplanet' in key:
        dirs = dir_func(dirs, 'rp' + key[-1], pconf[key], no_loop=no_loop)

    if 'inclplanet' in key:
        dirs = dir_func(dirs, 'ip' + key[-1], pconf[key], no_loop=no_loop)

    return dirs


def create_dirs(pconf, conf, setup_directory):
    """ Create directories and save them into conf dictionary. """

    log.info('Checking if ' + setup_directory + ' directory exist..')

    suite_directory = os.path.join(conf['run_dir'], conf['name'])

    dir_names = loop_keys_dir(pconf, conf)
    dirs = []

    for tmp_dir in dir_names:
        cdir = os.path.join(suite_directory, setup_directory, tmp_dir)
        dirs.append(cdir)
        if not os.path.exists(cdir):
            os.mkdir(cdir)

    conf['dirs'] = dirs
    log.info('Completed.')


def dir_func(dirs, string, dict_arr, no_loop=False):
    if len(dirs) is not 0:
        dirs = [i+'_' for i in dirs]

    else:
        dirs = [string+str(i).replace('.', '') for i in dict_arr]
        return dirs

    if no_loop:
        # For now, this is only going to work if you're wanting no_loop over one set of parameters...
        dirs = [dirs[j] + string + str(dict_arr[i]).replace('.', '') for i in range(0, len(dict_arr)) for j in range(0, len(dirs))]
        return dirs

    tmp_dir = ['']*len(dict_arr)
    for i in range(0, len(dict_arr)):
        tmp_dir[i] = string+str(dict_arr[i]).replace('.', '')

    dirs = [dirs[i] + tmp_dir[j] for i in range(0, len(dirs)) for j in range(0, len(tmp_dir))]
    return dirs
