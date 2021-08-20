from brownie import *

import calendar
import time
import json
import csv
import math

def main():
    ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"

    thisNetwork = network.show_active()
    if thisNetwork == "development":
        acct = accounts[0]
        configFile =  open('./scripts/contractInteraction/testnet_contracts.json')
    elif thisNetwork == "testnet":
        acct = accounts.load("rskdeployer")
        configFile =  open('./scripts/contractInteraction/testnet_contracts.json')
    elif thisNetwork == "rsk-mainnet":
        acct = accounts.load("rskdeployer")
        configFile =  open('./scripts/contractInteraction/mainnet_contracts.json')
    else:
        raise Exception("network not supported")

    # load deployed contracts addresses
    contracts = json.load(configFile)

    staking = Contract.from_abi("Staking", address=contracts['Staking'], abi=Staking.abi, owner=acct)
    registries = []
    registries.append(Contract.from_abi("VestingRegistry", address=contracts['VestingRegistry'], abi=VestingRegistry.abi, owner=acct))
    registries.append(Contract.from_abi("VestingRegistry", address=contracts['VestingRegistry2'], abi=VestingRegistry.abi, owner=acct))
    registries.append(Contract.from_abi("VestingRegistry", address=contracts['VestingRegistry3'], abi=VestingRegistry.abi, owner=acct))

    # lines = []
    # with open('./scripts/staking/vestings.json') as file:
    #     lines = file.readlines()
    # for line in lines:
    #     vestingData = json.loads(line)
    #     print(vestingData["dates"])

    # with open('./scripts/staking/vestings.json', 'r') as file:
    #     reader = csv.reader(file)
    #     for row in reader:
    #         # vestingData = json.loads(row)[0]
    #         # print(vestingData.user)
    #         print("===============")
    #         print(row)

    jsonFile = open("./scripts/staking/vestings.json", "a")
    with open('./scripts/staking/list.csv', 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            user = row[0]
            print(user)
            vestings = getUserVestings(registries, user)
            for vesting in vestings:
                stakes = staking.getStakes(vesting)
                if (len(stakes[0]) > 0):
                    vestingData = {
                        "user": user,
                        "vesting": vesting,
                        "dates": stakes[0],
                        "amounts": stakes[1]
                    }
                    jsonFile.write(json.dumps(vestingData) + "\n")


def getUserVestings(registries, user):
    vestings = []
    for registry in registries:
        vesting = registry.getVesting(user)
        if (vesting != ZERO_ADDRESS):
            vestings.append(vesting)
        vesting = registry.getTeamVesting(user)
        if (vesting != ZERO_ADDRESS):
            vestings.append(vesting)
    return vestings
