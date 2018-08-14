import argparse, os, json


def load_config(filename):
    with open(filename) as f:
        d = json.load(f)
    return d


def initiliase_setup():
    pass


def check_running_jobs():
    pass


def submit_job():
    pass


def dir_func(dirs, string, dict_arr):
    if len(dirs) is not 0:
        dirs = dirs + '_'
    dirs = dirs*len(dict_arr)
    for i in range(0, len(dirs)):
        dirs[i] = string+str(dict_arr).replace('.', '')
    return dirs


def create_dirs(conf):

    suite_directory = os.path.join(os.environ['PHANTOM_DATA'], conf['name'])
    dirs = []

    for key in conf:
        if isinstance(conf[key], list):
            if key == 'binary_e':
                dirs = dir_func(dirs, 'e', conf[key])

            if key == 'binary_a':
                dirs = dir_func(dirs, 'a', conf[key])

            if key == 'm2':
                dirs = dir_func(dirs, 'br', conf[key])

            if key == 'alphaSS':
                dirs = dir_func(dirs, 'aSS', conf[key])

            if key == 'binary_i':
                dirs = dir_func(dirs, 'i', conf[key])

    for dir in dirs:
        cdir = os.path.join(suite_directory, 'simulations', dir)
        if os.path.exists(cdir):
            pass
        else:
            os.mkdir(cdir)

    conf['dirs'] = dirs


def initialise(conf):
    suite_directory = os.path.join(os.environ['PHANTOM_DATA'], conf['name'])

    if not os.path.exists(suite_directory):
        os.mkdir(suite_directory)

    if not os.path.exists(os.path.join(suite_directory, 'simulations')):
        os.mkdir(os.path.join(suite_directory, 'simulations'))

    initiliase_phantom(conf)
    create_dirs(conf)

    for dir in conf['dirs']:
        os.system('cp ' + os.path.join(conf['name'], 'phantom_'+conf['setup'], '/*') + ' ' + dir)


def initiliase_phantom(conf):
    if isinstance(conf['setup'], list):
        for setup in conf['setup']:
            setup_dir = os.path.join(os.environ['PHANTOM_DATA'], conf['name'], 'phantom_'+setup)

            if not os.path.exists(setup_dir):
                os.mkdir(setup_dir)

            os.system(os.path.join(os.environ['PHANTOM_DIR'], 'scripts', 'writemake.sh')+' ' +
                      setup + ' > ' + os.path.join(setup_dir, 'Makefile'))
            os.chdir(setup_dir)
            os.system('make '+conf['make_options'])
            os.system('make setup '+conf['make_setup_options'])

            if conf['make_setup_options'] is not None:
                os.system('make moddump ' + conf['make_moddump_options'])

            os.chdir(os.environ['PHANTOM_DATA'])

    else:
        setup_dir = os.path.join(os.environ['PHANTOM_DATA'], conf['name'], 'phantom_' + conf['setup'])

        if not os.path.exists(setup_dir):
            os.mkdir(setup_dir)

        os.system(os.path.join(os.environ['PHANTOM_DIR'], 'scripts', 'writemake.sh') + ' ' +
                  conf['setup'] + ' > ' + os.path.join(setup_dir, 'Makefile'))
        os.chdir(setup_dir)
        os.system('make ' + conf['make_options'])
        os.system('make setup ' + conf['make_setup_options'])

        if 'make_moddump_options' in conf:
            os.system('make moddump ' + conf['make_moddump_options'])

        os.chdir(os.environ['PHANTOM_DATA'])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Submit batches of Phantom simulations.')
    parser.add_argument('config', type=str)
    args = parser.parse_args()

    config = load_config(args.config)

    initialise(config)






