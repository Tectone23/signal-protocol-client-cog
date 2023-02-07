""" Entire file is an entry point """
from datetime import datetime
now = datetime.now()
current_time = now.strftime("%H:%M:%S")

return f"Hello from TCore at {current_time}"