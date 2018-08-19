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


def create_dirs(pconf, pbconf):

    suite_directory = os.path.join(os.environ['PHANTOM_DATA'], pbconf['name'])
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

    for dir in dirs:
        cdir = os.path.join(suite_directory, 'simulations', dir)
        if os.path.exists(cdir):
            pass
        else:
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


def create_setup(pconf, pbconf):
    setup_filename = os.path.join(os.environ['PHANTOM_DATA'], pbconf['name'], 'phantom_'+pbconf['setup'], pbconf['setup']+'.setup')
    with open(setup_filename, 'w') as new_setup:
        if 'binary' in pbconf:
            if pbconf['binary']:
                binary_setup = open('setup/binary.setup', 'r')
                for line in binary_setup:
                    for key in pconf:
                        key_added = False
                        if key in line:
                            new_setup.write(key + ' = ' + str(pconf[key]))
                            key_added = True

                    if not key_added:
                        new_setup.write(line)



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Submit batches of Phantom simulations.')
    parser.add_argument('config', type=str)
    args = parser.parse_args()

    config = load_config(args.config)

    phantom_config = config['phantom_setup']
    phantombatch_config = config['phantombatch_setup']

    initialise(phantom_config, phantombatch_config)
    create_setup(phantom_config, phantombatch_config)






