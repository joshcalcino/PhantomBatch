# PhantomBatch

PhantomBatch has been written to take the hassle out of running many simulations simulatenously by doing all of the hard work for you!
The philosophy behind PhantomBatch is to think, set, and forget; Think about what set of parameters would be nice to explore, set a 
PhantomBatch config file, and forget since PhantomBatch will create, submit, check, and cancel your Phantom simulations for you!

Below is a list of features that have been added, or that I have already added, in no particular order of importance.

# Features to add:
- Support for looping over planet parameters (should be easy to implement)
- Support for dust
- Support for all disc setups
- Support for non-disc setups
- Ability to pick up where it left off if accidentally aborted
- Ability to render splash images/movies
- Support for other job schedulers aside from SLURM (e.g. PBS)
- Ability to stop simulations, moddump, and restart.

# Current features:
- Binary simulations, gas only for now
- Adding in planets

Excessive number of commits is due to me writing the code on my laptop, but running on a cluster. I will eventually
make a new branch for testing and implementing changes to prevent this interfering with any users in the future.
