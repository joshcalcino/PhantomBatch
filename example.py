from phantombatch import PhantomBatch

config_filename = 'config.json'

pb = PhantomBatch(config_filename=config_filename, verbose=True, terminate_at_exit=True)

pb.phantombatch_monitor()
