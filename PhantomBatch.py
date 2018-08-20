import argparse
import os
import json


def load_config(filename):
    with open(filename) as f:
        d = json.load(f)
    f.close()
    return d


def check_running_jobs():
    pass


def submit_job():
    pass


def dir_func(dirs, string, dict_arr):
    if len(dirs) is not 0:
        dirs = [i+'_' for i in dirs]
        dirs *= len(dict_arr)

    else:
        dirs = [string+str(i).replace('.', '') for i in dict_arr]
        return dirs

    tmp_dir = ['']*len(dict_arr)
    for i in range(0, len(dict_arr)):
        tmp_dir[i] = string+str(dict_arr[i]).replace('.', '')

    dirs = [dirs[i] + tmp_dir[j] for i in range(0, len(dirs)) for j in range(0, len(tmp_dir))]
    return dirs


def loop_keys_dir(pconf):
    dirs = []
    for key in pconf:
        if isinstance(pconf[key], list):
            if key == 'binary_e':
                dirs = dir_func(dirs, 'e', pconf[key])

            if key == 'binary_a':
                dirs = dir_func(dirs, 'a', pconf[key])

            if key == 'm2':
                dirs = dir_func(dirs, 'br', pconf[key])

            if key == 'alphaSS':
                dirs = dir_func(dirs, 'aSS', pconf[key])

            if key == 'binary_i':
                dirs = dir_func(dirs, 'i', pconf[key])

    return dirs


def create_dirs(pconf, pbconf):

    suite_directory = os.path.join(os.environ['PHANTOM_DATA'], pbconf['name'])

    dirs = loop_keys_dir(pconf)

    for dir in dirs:
        cdir = os.path.join(suite_directory, 'simulations', dir)
        if not os.path.exists(cdir):
            os.mkdir(cdir)

    pbconf['dirs'] = dirs


def initialise(pconf, pbconf):
    suite_directory = os.path.join(os.environ['PHANTOM_DATA'], pbconf['name'])

    if not os.path.exists(suite_directory):
        os.mkdir(suite_directory)

    sims_dir = os.path.join(suite_directory, 'simulations')

    if not os.path.exists(sims_dir):
        os.mkdir(sims_dir)

    initiliase_phantom(pbconf)
    create_dirs(pconf, pbconf)

    for dir in pbconf['dirs']:
        os.system('cp ' + os.path.join(os.environ['PHANTOM_DATA'], pbconf['name'], 'phantom_'+pbconf['setup']) + '/* '
                  + os.path.join(sims_dir, dir))


def initiliase_phantom(pbconf):
    if isinstance(pbconf['setup'], list):
        for setup in pbconf['setup']:
            setup_dir = os.path.join(os.environ['PHANTOM_DATA'], pbconf['name'], 'phantom_'+setup)

            if not os.path.exists(setup_dir):
                os.mkdir(setup_dir)

            if not os.path.exists(os.path.join(setup_dir, 'Makefile')):
                os.system(os.path.join(os.environ['PHANTOM_DIR'], 'scripts', 'writemake.sh')+' ' +
                          setup + ' > ' + os.path.join(setup_dir, 'Makefile'))
                os.chdir(setup_dir)
                os.system('make '+pbconf['make_options'])
                os.system('make setup '+pbconf['make_setup_options'])

                if pbconf['make_setup_options'] is not None:
                    os.system('make moddump ' + pbconf['make_moddump_options'])

                os.chdir(os.environ['PHANTOM_DATA'])

    else:
        setup_dir = os.path.join(os.environ['PHANTOM_DATA'], pbconf['name'], 'phantom_' + pbconf['setup'])

        if not os.path.exists(setup_dir):
            os.mkdir(setup_dir)

        if not os.path.exists(os.path.join(setup_dir, 'Makefile')):
            os.system(os.path.join(os.environ['PHANTOM_DIR'], 'scripts', 'writemake.sh') + ' ' +
                      pbconf['setup'] + ' > ' + os.path.join(setup_dir, 'Makefile'))

            os.chdir(setup_dir)
            os.system('make ' + pbconf['make_options'])
            os.system('make setup ' + pbconf['make_setup_options'])

            if 'make_moddump_options' in pbconf:
                os.system('make moddump ' + pbconf['make_moddump_options'])

            os.chdir(os.environ['PHANTOM_DATA'])


def setup_from_array(setup_strings, string, dict_arr):
    if len(setup_strings) is 0:
        setup_strings = [string + ' = ' + str(i) for i in dict_arr]
        return setup_strings

    setup_strings = setup_strings * len(dict_arr)

    tmp_setup_strings = ['']*len(dict_arr)
    for i in range(0, len(dict_arr)):
        tmp_setup_strings[i] = string + ' = ' + str(dict_arr[i])
    setup_strings = [[setup_strings[i], tmp_setup_strings[j]] for i in range(0, len(setup_strings))
                     for j in range(0, len(tmp_setup_strings))]
    return setup_strings


def get_setup_strings(pconf, pbconf):
    setup_strings = []
    for key in pconf:
        if isinstance(pconf[key], list):
            if key == 'binary_e':
                setup_strings = setup_from_array(setup_strings, key, pconf[key])

            if key == 'binary_a':
                setup_strings = setup_from_array(setup_strings, key, pconf[key])

            if key == 'm2':
                setup_strings = setup_from_array(setup_strings, key, pconf[key])

            if key == 'alphaSS':
                setup_strings = setup_from_array(setup_strings, key, pconf[key])

            if key == 'binary_i':
                setup_strings = setup_from_array(setup_strings, key, pconf[key])

    return setup_strings
    

def write_setup_comment(key):
    if key == 'np':
        return ' ! number of gas particles'
    if key == 'dist_unit':
        return ' ! distance unit (e.g. au,pc,kpc,0.1pc)'
    if key == 'primary_mass':
        return ' ! primary mass'
    if key == 'binary_a':
        return ' ! binary semi-major axis'
    if key == 'binary_e':
        return ' ! binary eccentricity'


def create_setups(pconf, pbconf):

    setup_filename = os.path.join(pbconf['setup'] + '.setup')
    # looped_keys = loop_keys_dir(pconf)
    setup_dirs = [os.path.join(os.environ['PHANTOM_DATA'], pbconf['name'], 'simulations', dir) for dir in pbconf['dirs']]
    # setup_dirs = pbconf['dirs']
    setup_strings = get_setup_strings(pconf, pbconf)
    print(setup_dirs)

    i = 0
    for dir in setup_dirs:
        filename = os.path.join(dir, setup_filename)
        with open(filename, 'w') as new_setup:
            print('Entering ' + filename + '..')
            if 'binary' in pbconf:
                if pbconf['binary']:
                    binary_setup = open('setup/binary.setup', 'r')
                    for line in binary_setup:
                        key_added = False
                        for key in pconf:
                            if isinstance(pconf[key], list):
                                for string in setup_strings[i]:
                                    if key in line and key in string:
                                        if verbose: print('Writing to setup file..')
                                        new_setup.write(string + write_setup_comment(key) + '\n')
                                        key_added = True
                            else:
                                key_added = False
                                if key in line:
                                    new_setup.write(key + ' = ' + str(pconf[key]) + write_setup_comment(key) +  '\n')
                                    key_added = True

                        if not key_added:
                            new_setup.write(line)

            new_setup.close()
            i += 1


def run_phantom_setup(pbconf):
    setup_dirs = pbconf['dirs']

    for dir in setup_dirs:
        os.chdir(dir)
        os.system('./phantomsetup ' + pbconf['setup'])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Submit batches of Phantom simulations.')
    parser.add_argument('config', type=str)
    args = parser.parse_args()

    verbose = True

    config = load_config(args.config)

    phantom_config = config['phantom_setup']
    phantombatch_config = config['phantombatch_setup']

    initialise(phantom_config, phantombatch_config)
    create_setups(phantom_config, phantombatch_config)
    run_phantom_setup(phantombatch_config)






