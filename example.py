from phantombatch import PhantomBatch

config_filename = 'config.json'

pb = PhantomBatch(config_filename=config_filename, verbose=True)

pb.phantombatch_monitor()
