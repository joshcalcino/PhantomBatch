# PhantomBatch

PhantomBatch is being written to take the hassle out of running many simulations simulatenously by doing all of the hard work for you!
The philosophy behind PhantomBatch is to think, set, and forget; Think about what set of parameters would be nice to explore, set a 
PhantomBatch config file, and forget since PhantomBatch will create, submit, check, and cancel your Phantom simulations for you!

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
- Adding in planets
    - Support for looping over planet parameters
- Terminates jobs if PhantomBatch is interrupted


# Features to add:
- Full support for binary discs
    - Disc mass setting (Currently only supports total disc mass)
    - Support for potential
- Support for dust on start up
- Support for all disc setups
- Support for non-disc setups
- Editing setup.in files before running phantom simulations
- Ability to pick up where it left off if aborted (should be easy to implement)
- Ability to render splash images/movies
- Support for more job schedulers (e.g. SGE)
- Ability to stop simulations, moddump, and restart.


And below is a list of known issues.

# Known issues:
- I don't think SLURM actually works..
- Some job and dir names might be excessively long if user specifies unusual numbers

Excessive number of commits is due to me writing the code on my laptop, but running on a cluster. I will eventually
make a new branch for testing and implementing changes to prevent this interfering with users in the future.

The correct way to run PhantomBatch out be something like:
`python3 example.py > example.out 2> example.err &`
This will make sure that nothing is printed to the terminal, all output is printed to the two specified files.
This means that PhantomBatch will run in the background on the login node of a cluster.
