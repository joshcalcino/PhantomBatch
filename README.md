# PhantomBatch

PhantomBatch is being written to take the hassle out of running many simulations simulatenously by doing all of the hard work for you!
The philosophy behind PhantomBatch is to think, set, and forget; Think about what set of parameters would be nice to explore, set a 
PhantomBatch config file, and forget since PhantomBatch will create, submit, check, and cancel your Phantom simulations for you!

PhantomBatch is only compatible with Python 3.

Below is a list of features that have been added, or that will be added, in no particular order of importance.

To install, clone this repository, `cd` into it, and run `python setup.py develop` so that you can automatically become
a developer of the code and help me maintain it :) 

## Current features:
- Support for SLURM and PBS job schedulers
- Any arbitrary Phantom setup is supported
- Terminates jobs if PhantomBatch is interrupted

Adding in any additional Phantom setup should be trivial. All we require is a copy of the `.setup` file,
and a few lines in the code to make the setup available for use.

## Features to add:
- Ability to pick up where it left off if aborted (basic implementation for now)
- Support for more job schedulers (e.g. SGE)
- Ability to stop simulations, moddump, and restart.
- Support to change parameters being looped over

And below is a list of known issues.

## Known issues:
- Some job and dir names might be excessively long if user specifies unusual numbers
- Definitely numerous bugs.. As I am currently the sole writer/user, I only find issues I stumble on

Excessive number of commits is due to me writing the code on my laptop, but running on a cluster. I will eventually
make a stable to prevent this interfering with users in the future.

# Brief User guide
I will turn this into a wiki if PhantomBatch generates enough interest

The correct way to run PhantomBatch is:

`python3 example.py > example.out 2>&1 &`\

which will return something like\

``[1] 12345``

This will make sure that nothing is printed to the terminal, all output is printed to `example.out`.
This means that PhantomBatch will run in the background on the login node of a cluster, and will continue to run when
you log out. But this probably depends on how long your particular cluster will let background jobs run for..

If you want to cancel running a PhantomBatch job running in the background, do not `kill` it. This will prevent any exit
functions from running. Instead, you want to interrupt PhantomBatch.

``kill -2 12345``

This will interrupt the process.

## The Config File

The `config.json` file should look like something like this (minus the inline comments I have added):
```
"phantom_batch_setup": {              # This contains all of the PhantomBatch settings. These MUST be set correctly
                                      # for sensible output from PhantomBatch.
  "name": "binary_test",              # The name of the simulation suite you are performing. Call this whatever
  "short_name": "bt",                 # A short name of your simulation suite, keep this short! 
  "sleep_time": 1,                    # How long (in minutes) PhantomBatch waits between checking job progress
  "setup": "disc",                    # The Phantom setup you are simulating. Only used for naming things.
  "no_loop": ["binary_e", "binary_i"] # Parameters that you do not want to be looped over.
  "fix_wth": ["binary_a", "binary_a"] # Parameters fixed with no loop parameters
  "job_scheduler": "slurm",           # The job handler of your cluster. Two options exist for now: "slurm", "pbs"
  "ncpus": 4,                         # Num of cpus per job. If your SYSTEM env variable is set, will overwrite that value
  "memory": "16G",                    # How much RAM you want to request per job
  "user": "uqjcalci",                 # Your username on the cluster
  "no_email": 1,                      # 0 = receive spam emails from cluster, 1 = no emails
  "job_limit": 4,                     # Maximum number of jobs you want PhantomBatch monitoring at a time
  "binary": 1,                        # Are you running a binary system? binary = 1
  "make_options": "",                 # Any additional make settings for Phantom
  "make_setup_options": ""            # As above for make setup options
  }

```
The user then provides a phantom setup file and add into the parameters they would like to explore. For example,
if you have a circumbinary disc simulation and you want to change the semi-major axis, eccentricity, inclination,
and the mass of the companion, your setup file would look something like this:

```
# input file for disc setup routine

# resolution
                  np =     1000000    ! number of gas particles

# units
           dist_unit =          au    ! distance unit (e.g. au,pc,kpc,0.1pc)
           mass_unit =      solarm    ! mass unit (e.g. solarm,jupiterm,earthm)

# central object(s)/potential
            icentral =           1    ! use sink particles or external potential (0=potential,1=sinks)
              nsinks =           2    ! number of sinks
             ibinary =           0    ! binary orbit (0=bound,1=unbound [flyby])

# options for binary
                  m1 =       1.000              ! primary mass
                  m2 =       [0.1, 0.2, 0.3]    ! secondary mass
            binary_a =       [20, 15, 10]       ! binary semi-major axis
            binary_e =       [0, 0.2, 0.4]      ! binary eccentricity
            binary_i =       [0, 15, 60]        ! i, inclination (deg)
```

Let's assume you're using the `config.json` file above. This would simulate `3*3=9` different simulations.
The parameters `binary_a`, `binary_e`, and `binary_i` would all be fixed with one another (e.g. the first simulation
would have `a=20, e=0, i=1`, the second `a=15, e=-0.2, i=15`, etc). Thus we would have 3 different binary orbits 
multiplied by 3 different companion masses for a total of 9 simulations. If `binary_i` was left out of the 
`no_loop` parameter, we would have `3*3*3=27` simulations where the inclination and companion mass is 
varied for each combination of `a` and `e`.

Please make sure that you add your cluster into the Phantom `Makefile`, and set your `SYSTEM` environment variable.
PhantomBatch WILL NOT WORK if you do not do this!

You must set an environment variable that specifies the `phantom` directory, `PHANTOM_DIR`.
This is usually `~/phantom` in most cases.

You can run PhantomBatch from where ever you like, but make sure that the directory has plenty
of space available for the number of dump files you expect to generate.

There are an example config file with accompanying setup file. Please look at it if you need help making your `config.json` files.

