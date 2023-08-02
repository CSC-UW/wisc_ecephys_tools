from ecephys.wne.sglx.subjects import SGLXSubjectLibrary
import pandas as pd
import wisc_ecephys_tools as wet

lib = SGLXSubjectLibrary(
    wet.get_subjects_directory()
)

previous_cache = lib.read_cache()

print("Refreshing cache..", end="")
lib.refresh_cache()
print("Done\n")

print("Diff with previous:")
print(pd.concat([previous_cache, lib.cache]).drop_duplicates(keep=False))


print("Writing cache.")
lib.write_cache()





