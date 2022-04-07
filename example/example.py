from phantombatch import PhantomBatch

config_filename = 'binary_config.json'
setup_filename = 'disc.setup'

pb = PhantomBatch(config_filename=config_filename, setup_filename=setup_filename, verbose=True, terminate_at_exit=True, fresh_start=True, submit_jobs=False)

pb.phantombatch_monitor()
