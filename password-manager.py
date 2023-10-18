import os
from Crypto.Protocol.KDF import scrypt
from Crypto.Random import get_random_bytes
from Crypto.Cipher import AES
from base64 import b64decode
import json
from base64 import b64encode
import os.path
import hashlib
import random
import string
import sys
import secrets


#encryptFile: String(bytes) X String(bytes) -> JSON object of representing a zipped dictionary of 4 Key-Value Pairs
# encryptFile: The plaintext vault x The encryption key -> The encrypted vault represented as a zipped dictionary of 4 Key-Value Pairs
# The keys for the JSON zipped dictionary will be "nonce", "header", "ciphertext", and "tag"
# the tag here represents the message authentication code or MAC
# Use AES GCM for encryption
# Use the binary of Empty String as the "header" needed for AES GCM
def encryptFile(plaintextData,key):
    header = b''
    cipher = AES.new(key, AES.MODE_GCM)
    cipher.update(header)
    ciphertext, tag = cipher.encrypt_and_digest(plaintextData)
    json_k = [ 'nonce', 'header', 'ciphertext', 'tag' ]
    json_v= [ b64encode(x).decode('utf-8') for x in (cipher.nonce, header, ciphertext, tag) ] 
    encryptionResults = json.dumps(dict(zip(json_k, json_v)))
    return encryptionResults


# decryptFile: Encrypted JSON Object X String(bytes) -> String(bytes)
# decryptFile: Encrypted vault as a JSON object X the symmetric decryption key -> Just the plaintext (not nonce, header, or tag)
# Please make sure the tag/MAC value verifies before returning the plaintext JSON object
def decryptFile(encryptedJson,key):
    b64 = json.loads(encryptedJson)
    json_k = [ 'nonce', 'header', 'ciphertext', 'tag' ]
    jv = {k:b64decode(b64[k]) for k in json_k}

    cipher = AES.new(key, AES.MODE_GCM, nonce=jv['nonce'])
    cipher.update(jv['header'])
    decryptionResults = cipher.decrypt_and_verify(jv['ciphertext'], jv['tag'])
    
    return decryptionResults


#computerMasterKey: String -> String(bytes)
# This function calculates the encryption key from the input password
# Use the scrypt function with the appropriate arguments mentioned in the assignment document
def computerMasterKey(password):
    salt = '<\n<~\x0e\xeetGR\xfe;\xec \xfc)8'
    key_len = 16 # length in bytes
    N = 2**14
    r = 8
    p = 1
    key = scrypt(password, salt, key_len, N, r, p)
    return key


#decryptAndReconstructVault : String x String -> List(Strings)'
# decryptAndReconstructVault: Name of the encrypted vault file X the password -> The decrypt password vault
# each String in the output list essentially has the form: "username:password:domain"
def decryptAndReconstructVault(hashedusername, password):
    key = computerMasterKey(password)
    magicString = '101010101010101010102020202020202020202030303030303030303030\n'

    with open(hashedusername, "r") as file:
        fileread = file.read()
    file.close()
    decryptedresults = decryptFile(fileread,key)
    decodedContent = decryptedresults.decode('utf-8')
    
    if magicString in decodedContent:
      decodedContent = decodedContent[len(magicString):]
    else:
      raise ValueError
    
    passwordvault = []
    for line in decodedContent.splitlines():
        passwordvault.append(line)
    return passwordvault


# checkVaultExistenceOrCreate: String x String -> String x String x String x List(Strings)
# In all honesty, the function does not explicitly take any arguments
# It gives a user the option to entry its username and password
# It then checks to see whether a password vault exists for the user name (Is there a file with the name SHA256(username)?)
# If it exists, then the decrypted password vault is returned
# Otherwise, a new password vault is created for the user
# The return value of the function is tuple <username, password, password vault file name, the plaintext password vault>
# recall that the plaintext password vault is nothing but a List of strings where each string has the form: "username:password:domain"
def checkVaultExistenceOrCreate():
    passwordvault = []
    while True:
        username = input('enter vault username: ')
        password = input('enter vault password: ')

        if username and password:
            break
        else:
          print("cannot enter empty strings please try again!")

    # added hashing code
    hashedusername = hashlib.sha256(username.encode('utf-8')).hexdigest()
    if (os.path.exists(hashedusername)):
      try:
        passwordvault = decryptAndReconstructVault(hashedusername,password)
      except ValueError:
        print("Error: wrong password or wrong username. Please try again")
        return "","","",[]

    else:
        print("Password vault not found, creating a new one")
        pass

    return username, password, hashedusername, passwordvault


# generatePassword: VOID -> STRING
# When called this function returns a random password
def generatePassword():
    
    alphabet = string.ascii_letters + string.digits
    password = ''.join(secrets.choice(alphabet) for i in range(16))
    return password
    

# AddPassword : List(String) -> VOID
# AddPassword : PLAINTEXT Password vault -> VOID
# It gives a user prompt to add a username, password, and a domain
# It then adds the triple to the Password vault
def AddPassword(passwordvault):
    
    username, domain = '',''
    while True:
        username = input('enter entry username: ')
        password = input('enter entry password: ')
        domain = input('enter entry domain: ')

        if username and domain and password:
            break
        else:
            print("cannot enter empty strings, please try again!")

    entry = username + ":" + password + ":" + domain
    passwordvault.append(entry)
    
    print('Record Entry added')


# CreatePassword : List(String) -> VOID
# CreatePassword : PLAINTEXT Password vault -> VOID
# It gives a user prompt to add a username, and domain
# It randomly generates the password
# It then adds the triple <username:password:domain> to the Password vault
def CreatePassword(passwordvault):
    
    username, domain = '',''
    while True:
        username = input('enter entry username: ')
        domain = input('enter entry domain: ')

        if username and domain:
            break
        else: print("cannot enter empty strings, please try again!")

    password = generatePassword()
    entry = username + ":" + password + ":" + domain
    passwordvault.append(entry)
    
    print('Record Entry added')


# UpdatePassword: List(String) -> VOID
# UpdatePassword: PLAINTEXT Password vault -> VOID
# It takes as input from the user the name of the domain to change password and the password to update it with.
# It then updates the password vault of the domain with the new password
def UpdatePassword(passwordvault):
    
    while True:
        domain = input('enter entry domain: ')
        newpass = input('enter new password: ')
        if domain and newpass: break
        else: print('cannot enter empty strings, please try again!')

    for i in range(len(passwordvault)):
        user,oldpass,entry_domain = passwordvault[i].split(":")
        if domain == entry_domain:
            passwordvault[i] = user+":"+newpass+":"+domain
            break
    print('Record Entry Updated')

# LookupPassword: List(String) -> VOID
# LookupPassword: PLAINTEXT Password vault -> VOID
# It takes as input from the user the name of the domain
# It then prints the username and password of that domain
def LookupPassword(passwordvault):
    
    while True:
        domain = input('enter entry domain: ')
        if domain: break
        else: print('cannot enter empty strings, please try again!')

    for entry in passwordvault:
        user,password,entry_domain = entry.split(":")
        if domain == entry_domain:
            print('username associated with domain: ' + user)
            print('password associated with domain: ' + password)
            break


# DeletePassword: List(String) -> VOID
# DeletePassword: PLAINTEXT Password vault -> VOID
# It takes as input from the user the name of the domain
# It then removes the entry of that domain from the password vault
def DeletePassword(passwordvault):
    while True:
        domain = input('enter entry domain: ')
        if domain: break
        else: print('cannot enter empty strings, please try again!')

    for entry in passwordvault:
        entry_domain = entry.split(":")[2]
        if domain == entry_domain:
            passwordvault.remove(entry)
            break

    print('Record Entry Deleted')


# displayVault : List(String) -> VOID
# Given the PLAINTEXT password vault, this function prints it in the standard output
def displayVault(passwordvault):
    print(passwordvault)


# EncryptVaultAndSave: List(String) x String x String -> VOID
# EncryptVaultAndSave: PLAINTEXT PASSWORD VAULT  x PASSWORD x PASSWORD VAULT FILE NAME -> VOID
# This function essentially prepends the magic string in a separate line with the
# PLAINTEXT password vault, then writes it back in the encrypted format to the encrypted password vault file ....
def EncryptVaultAndSave(passwordvault, password, hashedusername):
    writeString = ''
    magicString = '101010101010101010102020202020202020202030303030303030303030\n'
    writeString + magicString
    key = computerMasterKey(password)
    finalString = ''
    finalString = finalString + magicString

    for i in passwordvault:
        record = i + '\n'
        finalString = finalString + record

    finaldbBytes = bytes(finalString, 'utf-8')
    finaldbBytesEncrypted = encryptFile(finaldbBytes,key)


    with open(hashedusername, "w") as file:
        file.write(finaldbBytesEncrypted)
    file.close()
    print("Password Vault encrypted and saved to file")



def main():
    while(True):
        username, password, hashedusername, passwordvault = checkVaultExistenceOrCreate()
        if username or password or hashedusername or passwordvault: break
    while(True):

        print('Password Management')
        print('-----------------------')
        print('-----------------------')
        print('1 - Add password')
        print('2 - Create password')
        print('3 - Update password')
        print('4 - Lookup password')
        print('5 - Delete password')
        print('6 - Display Vault')
        print('7 - Save Vault and Quit')
        choice = input('')


        if choice == ('1'):
            AddPassword(passwordvault)

        elif choice == ('2'):
            CreatePassword(passwordvault)

        elif choice == ('3'):
            UpdatePassword(passwordvault)

        elif choice == ('4'):
            LookupPassword(passwordvault)

        elif choice == ('5'):
            DeletePassword(passwordvault)
        elif choice == ('6'):
            displayVault(passwordvault)

        elif choice == ('7'):
            EncryptVaultAndSave(passwordvault, password, hashedusername)
            quit()
        else:
            print('Invalid choice please try again')