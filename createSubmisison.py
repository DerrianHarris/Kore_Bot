import tarfile

files = ["BoardHelpers.py", "Directions.py", "FleetRoute.py", "ShipyardCommands.py", "main.py"]

with tarfile.open("submission.tar.gz", "w:gz") as tar:
    for name in files:
        tar.add(name)
