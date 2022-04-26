from brownie import *
from brownie.network.contract import InterfaceContainer

import json
import csv
import time

def main():
    global contracts, acct
    thisNetwork = network.show_active()

    # == Load config =======================================================================================================================
    if thisNetwork == "development":
        acct = accounts[0]
        configFile =  open('./scripts/contractInteraction/testnet_contracts.json')
    elif thisNetwork == "testnet":
        acct = accounts.load("rskdeployer")
        configFile =  open('./scripts/contractInteraction/testnet_contracts.json')
    elif thisNetwork == "rsk-testnet":
        acct = accounts.load("rskdeployer")
        configFile =  open('./scripts/contractInteraction/testnet_contracts.json')
    elif thisNetwork == "rsk-mainnet":
        acct = accounts.load("rskdeployer")
        configFile =  open('./scripts/contractInteraction/mainnet_contracts.json')
    else:
        raise Exception("network not supported")

    # load deployed contracts addresses
    contracts = json.load(configFile)

    # Read last staking timestamp
    def readLockDate(timestamp):
        staking = Contract.from_abi("Staking", address=contracts['Staking'], abi=Staking.abi, owner=acct)
        return staking.timestampToLockDate(timestamp)

    # open the file in universal line ending mode 
    with open('./scripts/fouryearvesting/addfouryearvestingstoregistry.csv', 'rU') as infile:
        #read the file as a dictionary for each row ({header : value})
        reader = csv.DictReader(infile)
        data = {}
        for row in reader:
            for header, value in row.items():
                try:
                    data[header].append(value)
                except KeyError:
                    data[header] = [value]

    # extract the variables you want
    tokenOwners = data['tokenOwner']
    vestingAddresses = data['vestingAddress']

    for i in vestingAddresses:
        print('vestingAddress:', i)
        fourYearVestingLogic = Contract.from_abi(
            "FourYearVestingLogic",
            address=i,
            abi=FourYearVestingLogic.abi,
            owner=acct)
        startDate = fourYearVestingLogic.startDate()
        print('startDate:', startDate)
        timeLockDate = readLockDate(time.time())
        print('timeLockDate:', timeLockDate)
        DAY = 24 * 60 * 60
        FOUR_WEEKS = 4 * 7 * DAY
        result = ((timeLockDate - startDate) % FOUR_WEEKS) # the cron should run every four weeks from start date
        newResult = ((timeLockDate - startDate) / FOUR_WEEKS) # the cron should run for first 13 intervals = 52 weeks
        print('result:', result)
        print('newResult:', newResult)
        print('-----------------------------------------------------')
        if ((result == 0) and (newResult <= 13)):
            fourYearVestingLogic.extendStaking()