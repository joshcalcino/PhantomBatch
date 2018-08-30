from phantombatch import PhantomBatch

config_filename = 'config.json'

pb = PhantomBatch(config_filename=config_filename, verbose=False, terminate_at_exit=True)

pb.phantombatch_monitor()
