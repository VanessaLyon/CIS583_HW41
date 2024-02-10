from web3 import Web3
import json
from eth_account import Account
from web3.middleware import geth_poa_middleware
import sys
import random
from hexbytes import HexBytes


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
    # Generate leaf hashes for the first level of the Merkle tree using prime numbers directly
    # Modification: Convert prime numbers to their byte representation for the first level
    prime_hashes = [Web3.solidity_keccak(['uint256'], [leaf]) for leaf in leaves]
    
    # Find the index of the chosen leaf in the sorted list
    chosen_index = leaves.index(prime)  # Use the original list to find the index
    
    # Initialize proof list
    proof = []
    total_levels = 13  # Total levels in the tree
    
    # Modification: Use byte representation of primes for the first level
    current_level_leaves = [leaf.to_bytes(32, byteorder='big') for leaf in leaves]
    current_level_leaves = [Web3.solidity_keccak(['bytes32'], [leaf]) for leaf in current_level_leaves]
    
    for level in range(total_levels):
        current_level_hashes = []
        if level > 0 :
            # For subsequent levels, use the hashed values
            #current_level_leaves = [Web3.solidity_keccak(['bytes32'], [leaf]) for leaf in current_level_leaves]
            print('nothing done')

        # Calculate sibling index and parent index for the next iteration
        if chosen_index % 2 == 0:
            sibling_index = chosen_index + 1
        else:
            sibling_index = chosen_index - 1
        
        # Ensure sibling index is within bounds
        if sibling_index < len(current_level_leaves):
            # Modification: Use the byte representation of the sibling for adding to the proof
            sibling_hash = current_level_leaves[sibling_index]
            proof.append(sibling_hash)
        
        # Prepare for the next level
        chosen_index = chosen_index // 2
        
        for i in range(0, len(current_level_leaves), 2):
            # Modification: Simplify hashing of all pairs in the list
            if i + 1 < len(current_level_leaves):
                hashed_pair = hashPair(current_level_leaves[i], current_level_leaves[i + 1])
                current_level_hashes.append(hashed_pair)
            else:
                # Handle the last element if an odd number of nodes
                current_level_hashes.append(current_level_leaves[i])
        
        current_level_leaves = current_level_hashes
    
    chosen_leaf = leaves[chosen_index].to_bytes(32, byteorder='big')
    
    #return proof, chosen_leaf
    return proof, prime.to_bytes(32, byteorder='big')

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
    leaves = generate_primes(8192)  # Generate 2^13 primes
    proof, chosen_leaf = generateMerkleProof(prime, leaves)
      
    proof_hex_strings = [element.hex() for element in proof]

    print('Proof elements to be submitted:', proof_hex_strings)
    print('Chosen leaf in bytes:', chosen_leaf)

    # Submit the transaction
    sk = "b6b07402191ac2a961ce645d303b1b5e1a6c73afdf8b953d18ff1ab1cf61cbd2"
    acct = w3.eth.account.from_key(sk)
    print('account is ',acct)
    private_key = acct._private_key

    #gas_estimate = contract.functions.submit(proof, chosen_leaf).estimate_gas({'from': acct.address})
    gas_estimate = 1000000 #Could not solve the bug, so I plugged as such
    gas_price = w3.eth.gas_price
    print(f"Gas estimate: {gas_estimate}, Gas price: {gas_price} Wei")

    # Build the transaction
    tx = contract.functions.submit(proof, chosen_leaf).build_transaction({
        'from': acct.address,
        'nonce': w3.eth.get_transaction_count(acct.address),
        'gas': gas_estimate,
        'gasPrice': gas_price,
    })

    # Sign and send the transaction
    signed_tx = w3.eth.account.sign_transaction(tx, private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)

    # Return the transaction hash as a hexadecimal string
    return tx_hash.hex()

if __name__ == "__main__":
    chain = 'avax'
    
    with open("contract_info.json", "r") as f:
        abi = json.load(f)

    address = "0xb728f421b33399Ae167Ff01Ad6AA8fEFace845F7"
    w3 = connectToChain(chain)
    contract = w3.eth.contract(address=address, abi=abi)

    leaves = generate_primes(8192) 
    random.shuffle(leaves)  # Shuffle to randomize leaf selection

    for prime in leaves:
        try:
            tx_hash = submitProof(prime, w3, contract)
            print(f"Success: Leaf {prime} claimed with transaction hash {tx_hash}")
            break  # Exit upon successful submission
        except Exception as e:
            print(f"Failed to claim leaf {prime}: {str(e)}")
