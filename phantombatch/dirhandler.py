import os
import logging as log
from phantombatch import util


def loop_keys_dir(pconf, pbconf):
    """ A function for generating both directory names and job names for the job scripts. """
    dirs = []
    no_loop_keys = []

    if 'no_loop' in pbconf and len(pbconf['no_loop']) > 0:
        nl_keys = pbconf['no_loop']
        fw_keys = pbconf['fix_with']

        for key in fw_keys + nl_keys:
            # Assert that the parameters listed in no_loop are actually lists
            try:
                assert isinstance(pconf[key], list)
                # type(pconf[key]) isinstance() type(list())
            except AssertionError:
                no_loop_or_fix_with = 'fix_with' if key in fw_keys else 'no_loop'
                log.error('You have added parameter ' + str(key) + ' to the ' + str(no_loop_or_fix_with) +
                          ' options, but ' + str(key) + ' does not contain a list.')
                util.call_exit()

        for i in range(0, len(pbconf['no_loop'])):
            if pbconf['no_loop'][i] not in no_loop_keys:
                dirs = keys_dir(dirs, fw_keys[i], pconf, no_loop=False)
                no_loop_keys.append(fw_keys[i])

                # dirs = keys_dir(dirs, nl_keys[i], pconf, no_loop=True)
                no_loop_keys.append(nl_keys[i])

    for key in pconf:
        if isinstance(pconf[key], list) and (key not in no_loop_keys):
            print(key)
            dirs = keys_dir(dirs, key, pconf, no_loop=False)

    return dirs


def keys_dir(dirs, key, pconf, no_loop=False):

    key_dict = {'pindex': 'p', 'qindex': 'q', 'm2': 'm2', 'accr2': 'acr2', 'alphaSS': 'aSS', 'binary_i': 'i'}

    if key in key_dict:
        dirs = dir_func(dirs, key_dict[key], pconf[key], no_loop=no_loop)

    if key == 'binary_a':
        # Build array of a's, which are rounded, to get rid of unnecessary decimal places
        dict_arr = [round(i, 1) for i in pconf[key]]
        dirs = dir_func(dirs, 'a', dict_arr, no_loop=no_loop)

    if key == 'binary_e':
        # Build up an array of e's that isn't too long and disregard the '0.'
        dict_arr = [format(i, '.2f')[2:] for i in pconf[key]]
        dirs = dir_func(dirs, 'e', dict_arr, no_loop=no_loop)
    
    # ---------------------------------------------------------------------------
    # |                         BINARY DISC PARAMETERS                          |
    # ---------------------------------------------------------------------------
    
    binary_disc_keys = { # Binary
                        'disc_mbinary': 'dmb', 'R_inbinary': 'Rinb', 'R_refbinary': 'Rrefb', 'R_outbinary': 'Rob',
                        'qindexbinary': 'qib', 'pindexbinary': 'pib', 'H_Rbinary': 'hrb',
                        # Primary
                        'disc_mprimary': 'dmp', 'R_inprimary': 'Rinp', 'R_refprimary': 'Rrefp', 'R_outprimary': 'Rop',
                        'qindexprimary': 'qip', 'pindexprimary': 'pip',
                        # Secondary
                        'disc_msecondary': 'dmp', 'R_insecondary': 'Rinp', 'R_refsecondary': 'Rrefp',
                        'R_outsecondary': 'Rop', 'qindexsecondary': 'qis', 'pindexsecondary': 'pis',
                        }

    if key in binary_disc_keys:
        dirs = dir_func(dirs, binary_disc_keys[key], pconf[key], no_loop=no_loop)

    # ---------------------------------------------------------------------------
    # |                            PLANET PARAMETERS                            |
    # ---------------------------------------------------------------------------

    planet_keys = {'mplanet': 'mp', 'rplanet': 'rp', 'inclplanet': 'ip'}

    for param in planet_keys:
        if param in key:
            #  Adding in key[-1] makes sure that we select the write planet number
            dirs = dir_func(dirs, planet_keys[param] + key[-1], pconf[key], no_loop=no_loop)

    return dirs


def create_dirs(pconf, conf, setup_directory):
    """ Create directories and save them into conf dictionary. """

    log.debug('Checking if ' + setup_directory + ' directory exist..')

    suite_directory = os.path.join(conf['run_dir'], conf['name'])

    dir_names = loop_keys_dir(pconf, conf)
    dirs = []

    for tmp_dir in dir_names:
        cdir = os.path.join(suite_directory, setup_directory, tmp_dir)
        dirs.append(cdir)
        if not os.path.exists(cdir):
            os.mkdir(cdir)
        else:
            log.debug('Directory ' + cdir + ' already exists.')

    conf['dirs'] = dirs
    log.debug('Completed.')


def dir_func(dirs, string, dict_arr, no_loop=False):
    if len(dirs) is not 0:
        dirs = [i+'_' for i in dirs]

    else:
        dirs = [string+str(i).replace('.', '') for i in dict_arr]
        return dirs

    if no_loop:
        # For now, this is only going to work if you're wanting no_loop over one set of parameters...
        dirs = [dirs[i] + string + str(dict_arr[i % len(dict_arr)]).replace('.', '')
                for i in range(0, len(dirs))]
        return dirs

    tmp_dir = ['']*len(dict_arr)
    for i in range(0, len(dict_arr)):
        tmp_dir[i] = string+str(dict_arr[i]).replace('.', '')

    dirs = [dirs[i] + tmp_dir[j] for i in range(0, len(dirs)) for j in range(0, len(tmp_dir))]
    return dirs

