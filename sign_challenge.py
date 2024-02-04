import eth_account
from eth_account.messages import encode_defunct

def sign_challenge(challenge, private_key):
    account = eth_account.Account.from_key(private_key)
    eth_encoded_msg = encode_defunct(text=challenge)
    signature = account.sign_message(eth_encoded_msg)
    return account.address, signature.signature.hex()

if __name__ == "__main__":

    #My details
    sk = "b6b07402191ac2a961ce645d303b1b5e1a6c73afdf8b953d18ff1ab1cf61cbd2"
    acct = w3.eth.account.from_key(sk)
    private_key = acct._private_key

    #private_key = 'YOUR_PRIVATE_KEY_HERE'  # Replace with your private key
    challenge = ''.join(random.choice(string.ascii_letters) for i



