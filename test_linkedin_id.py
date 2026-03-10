import time

def decode_linkedin_id(activity_id_str):
    try:
        activity_id = int(activity_id_str)
        # LinkedIn epoch is approximately around end of 2003 or early 2004
        # We can find out by looking at a recent ID.
        # recent ID: 7434916116767870977
        extracted_time_ms = activity_id >> 22
        return extracted_time_ms
    except:
        return 0

print("Decoding ID: 7434916116767870977")
ms = decode_linkedin_id("7434916116767870977")
print(f"Decoded bits: {ms}")
