import eth_account
from eth_account import Account
from eth_account.messages import encode_defunct

def sign_challenge(challenge):
    #My details
    sk = "b6b07402191ac2a961ce645d303b1b5e1a6c73afdf8b953d18ff1ab1cf61cbd2"
    account = Account.from_key(sk)
    private_key = account._private_key

    
    print(sk)
    print(account)
    print(private_key)
    
    eth_encoded_msg = encode_defunct(text=challenge)
    signature = account.sign_message(eth_encoded_msg)
    return account.address, signature.signature.hex()

if __name__ == "__main__":
 
    #private_key = 'YOUR_PRIVATE_KEY_HERE'  # Replace with your private key
    challenge = ''.join(random.choice(string.ascii_letters) for i in range(32)) 

    addr, sig = sign_challenge(challenge)

    eth_encoded_msg = eth_account.messages.encode_defunct(text=challenge)

    if eth_account.Account.recover_message(eth_encoded_msg,signature=sig) == addr:
        print( f"Success: signed the challenge {challenge} using address {addr}!")
    else:
        print( f"Failure: The signature does not verify!" )
        print( f"signature = {sig}" )
        print( f"address = {addr}" )
        print( f"challenge = {challenge}" )

