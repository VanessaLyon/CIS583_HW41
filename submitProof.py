from web3 import Web3
import json
from eth_account import Account
from web3.middleware import geth_poa_middleware
import sys
import random
from hexbytes import HexBytes

def hashPair(a, b):
    """
        The OpenZeppelin Merkle Tree Validator we use sorts the leaves
        https://github.com/OpenZeppelin/openzeppelin-contracts/blob/master/contracts/utils/cryptography/MerkleProof.sol#L217
        So you must sort the leaves as well

        Also, hash functions like keccak are very sensitive to input encoding, so the solidity_keccak function is the function to use

        Another potential gotcha, if you have a prime number (as an int) bytes(prime) will *not* give you the byte representation of the integer prime
        Instead, you must call int.from_bytes(prime,'big').

        This function will hash leaves in a Merkle Tree in a way that is compatible with the way the on-chain validator hashes leaves
    """
    if a < b:
        return Web3.solidity_keccak(['bytes32', 'bytes32'], [a, b])
    else:
        return Web3.solidity_keccak(['bytes32', 'bytes32'], [b, a])

def generateMerkleProof(prime, leaves):
    # Sort the leaves and convert them to bytes
    sorted_leaves = sorted([Web3.solidity_keccak(['uint256'], [leaf]) for leaf in leaves])
    index = sorted_leaves.index(Web3.solidity_keccak(['uint256'], [prime]))
    proof = []
    while len(sorted_leaves) > 1:
        if index % 2 == 0:
            if index + 1 < len(sorted_leaves):
                proof.append(sorted_leaves[index + 1])
            hashed = hashPair(sorted_leaves[index], sorted_leaves[index + 1] if index + 1 < len(sorted_leaves) else sorted_leaves[index])
        else:
            proof.append(sorted_leaves[index - 1])
            hashed = hashPair(sorted_leaves[index - 1], sorted_leaves[index])
        index = index // 2
        sorted_leaves = [hashed] + sorted_leaves[2:][::2]
    return proof

def connectTo2(chain): #Can we simplify?
    if chain == 'avax':
        api_url = "https://api.avax-test.network/ext/bc/C/rpc"  # AVAX C-chain testnet
        w3 = Web3(Web3.HTTPProvider(api_url))
        w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        return w3

def connectTo(chain):
    if chain == 'avax':
        api_url = f"https://api.avax-test.network/ext/bc/C/rpc" #AVAX C-chain testnet

    if chain == 'bsc':
        api_url = f"https://data-seed-prebsc-1-s1.binance.org:8545/" #BSC testnet

    if chain in ['avax','bsc']:
        w3 = Web3(Web3.HTTPProvider(api_url))
        # inject the poa compatibility middleware to the innermost layer
        w3.middleware_onion.inject(geth_poa_middleware, layer=0)
    return w3

def submitProof(prime, w3, contract):
    leaves = [i for i in range(2, 8193)]  # Dummy primes for illustration
    proof = generateMerkleProof(prime, leaves)
    leaf_in_bytes = Web3.solidity_keccak(['uint256'], [prime])
    tx = contract.functions.submit(proof, leaf_in_bytes).buildTransaction({
        'from': w3.eth.default_account,
        'nonce': w3.eth.getTransactionCount(w3.eth.default_account),
        # Additional transaction parameters (gas, gasPrice) may be required.
    })
    signed_tx = w3.eth.account.sign_transaction(tx, private_key='YOUR_PRIVATE_KEY_HERE')
    tx_hash = w3.eth.sendRawTransaction(signed_tx.rawTransaction)
    return Web3.toHex(tx_hash)

if __name__ == "__main__":
    chain = 'avax'
    with open("contract_info.json", "r") as f:
        abi = json.load(f)
    address = "0xb728f421b33399Ae167Ff01Ad6AA8fEFace845F7"
    w3 = connectTo(chain)

    #My details
    sk = "b6b07402191ac2a961ce645d303b1b5e1a6c73afdf8b953d18ff1ab1cf61cbd2"
    acct = w3.eth.account.from_key(sk)

    #w3.eth.default_account = 'YOUR_ACCOUNT_ADDRESS_HERE'  # Set your account address here
    #contract = w3.eth.contract(abi=abi, address=address)

    contract = w3.eth.contract(abi=abi, address=acct)
    prime = 17  # Example prime number
    print(submitProof(prime, w3, contract))
