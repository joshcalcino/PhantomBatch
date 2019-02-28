from phantombatch import PhantomBatch

config_filename = 'binary_config.json'

pb = PhantomBatch(config_filename=config_filename, verbose=True, terminate_at_exit=True, fresh_start=True)

pb.phantombatch_monitor()
