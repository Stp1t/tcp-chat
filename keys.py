import rsa

# needs to be executed once to create public and private keys for rsa encryption

(public_key, private_key) = rsa.newkeys(1024)
try:
    with open("public_key.pem", "wb") as public_file:
        public_file.write(public_key.save_pkcs1("PEM"))

    with open("private_key.pem", "wb") as private_file:
        private_file.write(private_key.save_pkcs1("PEM"))

    print("Keys created successfully.")

except:
    print("Error while creating keys.")