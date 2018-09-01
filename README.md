# PhantomBatch

PhantomBatch is being written to take the hassle out of running many simulations simulatenously by doing all of the hard work for you!
The philosophy behind PhantomBatch is to think, set, and forget; Think about what set of parameters would be nice to explore, set a 
PhantomBatch config file, and forget since PhantomBatch will create, submit, check, and cancel your Phantom simulations for you!

PhantomBatch is only compatible with Python 3.

Below is a list of features that have been added, or that will be added, in no particular order of importance.

# Current features:
- Support for SLURM and PBS job schedulers
- Binary simulations
    - Currently gas only
    - Sink particles only
    - Primary, secondary, and circumbinary discs supported
    - Disc warping supported
    - Exponential disc taper supported
- Circumstellar disks
- Dust on start up (testing)
- Adding in planets
    - Support for looping over planet parameters
- Terminates jobs if PhantomBatch is interrupted


# Features to add:
- Full support for binary discs
    - Disc mass setting (Currently only supports total disc mass)
    - Support for potential
- Support for all disc setups
- Support for non-disc setups
- Editing setup.in files before running phantom simulations
- Ability to pick up where it left off if aborted (should be easy to implement)
- Ability to render splash images/movies
- Support for more job schedulers (e.g. SGE)
- Ability to stop simulations, moddump, and restart.


And below is a list of known issues.

# Known issues:
- Some job and dir names might be excessively long if user specifies unusual numbers

Excessive number of commits is due to me writing the code on my laptop, but running on a cluster. I will eventually
make a new branch for testing and implementing changes to prevent this interfering with users in the future.

# Brief User guide
I will turn this into a wiki if PhantomBatch generates enough interest

The correct way to run PhantomBatch is something like:

`python3 example.py > example.out 2>&1 &`

This will make sure that nothing is printed to the terminal, all output is printed to `example.out`.
This means that PhantomBatch will run in the background on the login node of a cluster, and will continue to run when
you log out.

`example.py` contains very little code, and is used to provide PhantomBatch with the filename to your `config.json`
file, and to initiate PhantomBatch.

The `config.json` file should look like something like this (minus the inline comments I have added):
```{
"phantom_setup": {               # Actual setup options for Phantom. MAKE SURE YOU USE CORRECT PHANTOM NAMES!!
  "np": 50000,                   # Number of gas particles (dust not supported fow now)
  "binary_e": [0, 0.5],          # We are doing a binary simulation, and want to do e = 0 and e = 0.5
  "binary_a": 20,                # Semi-major axis of the companion
  "binary_i": [0, 10, 20, 30],   # Also looping over inclination
  "disc_mbinary": 0.005,         # Mass of the disc, this is currently the only supported method of setting disc mass
  "R_inbinary": 30,              # The inner edge of the gas disc
  "R_outbinary": 80,             # The outer edge of the gas disc...
  "R_cbinary": 80,               # etc ....
  "R_refbinary": 40,
  "itapergasbinary": "F",
  "iwarpbinary": "F",
  "use_primarydisc": "F",
  "detat": 1                     # How frequently you want to dump
  },

"phantom_batch_setup": {         # This dict contains all of the PhantomBatch settings. These MUST be set correctly
                                 # for sensible output from PhantomBatch.
  "name": "binary_test",         # The name of the simulation suite you are performing. Call this whatever
  "short_name": "bt",            # A short name of your simulation suite, keep this short! It is added to job script names
  "num_dumps": 200,              # Number of dump files you want.
  "sleep_time": 1,               # How long (in minutes) PhantomBatch waits between checking job progress
  "setup": "disc",               # The Phantom setup you are simulating. "disc" is the only supported setup for now
  "job_scheduler": "slurm",      # The job handler of your cluster. Only two options exist at the moment: "slurm", "pbs"
  "ncpus": 4,                    # number of cpus per job. If your SYSTEM env variable is set, this will overwrite that value
  "memory": "16G",               # How much RAM you want to request per job
  "user": "uqjcalci",            # Your username on the cluster
  "no_email": 1,                 # 0 = receive spam emails from cluster, 1 = no emails
  "job_limit": 4,                # Maximum number of jobs you want PhantomBatch monitoring at a time
  "binary": 1,                   # Are you running a binary system? binary = 1
  "add_dust": 0,                 # Add dust? only 0 is supported for now
  "make_options": "",            # Any additional make settings for Phantom
  "make_setup_options": ""       # As above for make setup options
  }
}```

The above `config.json` file would simulate a total of 8 discs, each with 50k SPH particles for 200 orbits of the
companion. If you define unused values in `phantom_setup`, do not worry, as these will be ignored for your particular
choice of `setup`. For example, if you defined values for planets, but do no specifically set `setplanets = T`, then any
other variables specifying planet parameters will be neglected in creating your Phantom `setup` files.

There are a few example config files. Please look at them if you need help making your `config.json` files.

