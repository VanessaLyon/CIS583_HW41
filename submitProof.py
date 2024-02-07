from web3 import Web3
import json
from eth_account import Account
from web3.middleware import geth_poa_middleware
import sys
import random
from hexbytes import HexBytes

# Prime number generation and Merkle proof generation functions are assumed to be defined here

def is_prime(n):
    if n <= 1:
        return False
    if n <= 3:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6
    return True

def generate_primes(n):
    primes = []
    candidate = 2
    while len(primes) < n:
        if is_prime(candidate):
            primes.append(candidate)
        candidate += 1
    return primes


def hashPair(a, b):
    # Sorts and hashes a pair of nodes
    if a < b:
        return Web3.solidity_keccak(['bytes32', 'bytes32'], [a, b])
    else:
        return Web3.solidity_keccak(['bytes32', 'bytes32'], [b, a])


def generateMerkleProof(prime, leaves):
    # Generate and sort leaf hashes
    leaf_hashes = [Web3.solidity_keccak(['uint256'], [leaf]) for leaf in leaves]
    sorted_leaf_hashes = sorted(leaf_hashes)
    # Find the index of the chosen leaf
    chosen_leaf_hash = Web3.solidity_keccak(['uint256'], [prime])
    index = sorted_leaf_hashes.index(chosen_leaf_hash)
    
    proof = []
    # Calculate total levels in the tree, given 8192 leaves (2^13 = 8192, so 13 levels)
    total_levels = 13
    # Generate proof
    for _ in range(total_levels):
        # Determine the sibling index
        sibling_index = index ^ 1
        # Add the sibling to the proof
        proof.append(sorted_leaf_hashes[sibling_index])
        
        # Calculate the parent index for the next iteration
        index = index // 2
        
        # Generate new sorted leaf hashes for the next level up
        temp_hashes = []
        for i in range(0, len(sorted_leaf_hashes), 2):
            # Pair and hash together, handling the case of an odd number of nodes at the end of the array
            if i + 1 < len(sorted_leaf_hashes):
                hashed_pair = hashPair(sorted_leaf_hashes[i], sorted_leaf_hashes[i+1])
            else:
                hashed_pair = sorted_leaf_hashes[i]  # No pairing if it's the last odd element
            temp_hashes.append(hashed_pair)
        
        sorted_leaf_hashes = temp_hashes
    
    # Ensure the proof has exactly 13 entries
    assert len(proof) == total_levels, f"Proof length should be {total_levels}, but was {len(proof)}."
    #print ('proof at that step is ', proof)
    return proof, chosen_leaf_hash

def connectToChain(chain):
    if chain == 'avax':
        api_url = "https://api.avax-test.network/ext/bc/C/rpc"
    elif chain == 'bsc':
        api_url = "https://data-seed-prebsc-1-s1.binance.org:8545/"
    else:
        raise ValueError("Unsupported chain")
    
    w3 = Web3(Web3.HTTPProvider(api_url))
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)
    return w3

def submitProof(prime, w3, contract):
    leaves = generate_primes(8192)  # Adjust if needed to match the exact requirement
    proof, chosen_leaf = generateMerkleProof(prime, leaves)

    # Convert the proof elements to the required format for submission
    proof_hex_strings = [element.hex() for element in proof]
    proof_in_bytes = [bytes.fromhex(hex_element[2:]) for hex_element in proof_hex_strings]
    hex_strings = ['0x' + bs.hex() for bs in proof_in_bytes]

    #print('Hex strings to input directly in transaction:', hex_strings)

    leaf_in_bytes = chosen_leaf.hex()
    #print('Leaf in bytes is:', leaf_in_bytes)

    # Submit the transaction
    sk = "b6b07402191ac2a961ce645d303b1b5e1a6c73afdf8b953d18ff1ab1cf61cbd2"
    acct = w3.eth.account.from_key(sk)
    private_key = acct._private_key

    #print('Hello')
    #print('what is submitted is ', hex_strings)
    #print('and ',leaf_in_bytes )

    # Build the transaction with the contract function call
    tx = contract.functions.submit(hex_strings, leaf_in_bytes).build_transaction({
        'from': acct.address,
        'nonce': w3.eth.get_transaction_count(acct.address),
        # Additional parameters like 'gas' and 'gasPrice' could be specified here
    })

    # Sign and send the transaction
    signed_tx = w3.eth.account.sign_transaction(tx, private_key=private_key)
    tx_hash = w3.eth.sendRawTransaction(signed_tx.rawTransaction)

    # Return the transaction hash as a hexadecimal string
    return Web3.toHex(tx_hash)

if __name__ == "__main__":
    chain = 'avax'
    
    with open("contract_info.json", "r") as f:
        abi = json.load(f)

    address = "0xb728f421b33399Ae167Ff01Ad6AA8fEFace845F7"
    w3 = connectToChain(chain)
    contract = w3.eth.contract(address=address, abi=abi)

    leaves = generate_primes(8192)  # This assumes your generate_primes function is correctly implemented
    random.shuffle(leaves)  # Shuffle to randomize leaf selection

    for prime in leaves:
        try:
            tx_hash = submitProof(prime, w3, contract)
            print(f"Success: Leaf {prime} claimed with transaction hash {tx_hash}")
            break  # Exit upon successful submission
        except Exception as e:
            print(f"Failed to claim leaf {prime}: {str(e)}")
