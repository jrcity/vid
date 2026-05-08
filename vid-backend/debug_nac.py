import network_as_code as nac
import os
from dotenv import load_dotenv

load_dotenv()

token = os.getenv("NOKIA_NAC_TOKEN")
client = nac.NetworkAsCodeClient(token=token)

print(f"KYC namespace attributes: {dir(client.kyc)}")

phone = "+99999991000"
device = client.devices.get(phone_number=phone)

# Guessing the method name: match? verify?
# Let's try to find it.
