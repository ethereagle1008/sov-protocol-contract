'''
Implements SOV distribution via vesting contracts
'''
from scripts.contractInteraction.contract_interaction import *
import csv

def createVestings(path, dryRun):
    '''
    vested token sender script - takes addresses from the file by path
    dryRun - true to check that the data will be processed correctly, false - execute distribution
    '''

    # abiFile =  open('./scripts/contractInteraction/VestingRegistryLogic.json')
    # abi = json.load(abiFile)
    vestingRegistry = Contract.from_abi("VestingRegistryLogic", address=conf.contracts['VestingRegistryProxy'], abi=VestingRegistryLogic.abi, owner=conf.acct)

    staking = Contract.from_abi("Staking", address=conf.contracts['Staking'], abi=conf.Staking.abi, owner=conf.acct)
    SOVtoken = Contract.from_abi("SOV", address=conf.contracts['SOV'], abi=SOV.abi, owner=conf.acct)

    DAY = 24 * 60 * 60
    FOUR_WEEKS = 4 * 7 * DAY

    balanceBefore = conf.acct.balance()
    totalAmount = 0

    # amounts examples: "6,516.85", 912.92 - 2 decimals strictly!
    data = parseFile(path, 1e16)
    totalAmount += data["totalAmount"]

    for teamVesting in data["teamVestingList"]:
        tokenOwner = teamVesting[0]
        amount = int(teamVesting[1])
        cliff = int(teamVesting[2]) * FOUR_WEEKS
        duration = int(teamVesting[3]) * FOUR_WEEKS
        isTeam = bool(teamVesting[4])

        if teamVesting[3] == 10:
            vestingCreationType = 3
        elif teamVesting[3] == 26:
            vestingCreationType = 1
        elif teamVesting[3] == 48:
            vestingCreationType = 4
            print("Make sure 4 year vesting is really expected!")
        else:
            vestingCreationType = 0
            print("OUCH!!!! ZERO!!!")

        if isTeam:
            vestingAddress = vestingRegistry.getTeamVesting(tokenOwner, cliff, duration, vestingCreationType)
        else:
            vestingAddress = vestingRegistry.getVestingAddr(tokenOwner, cliff, duration, vestingCreationType)
        if (vestingAddress != "0x0000000000000000000000000000000000000000"):
            vestingLogic = Contract.from_abi("VestingLogic", address=vestingAddress, abi=VestingLogic.abi, owner=conf.acct)
            if (cliff != vestingLogic.cliff() or duration != vestingLogic.duration()):
                raise Exception("Address already has team vesting contract with different schedule")
        print("=======================================")
        if isTeam:
            if(not dryRun):
                vestingRegistry.createTeamVesting(tokenOwner, amount, cliff, duration, vestingCreationType)
            vestingAddress = vestingRegistry.getTeamVesting(tokenOwner, cliff, duration, vestingCreationType)
            print("TeamVesting: ", vestingAddress)
        else:
            if(not dryRun):
                vestingRegistry.createVestingAddr(tokenOwner, amount, cliff, duration, vestingCreationType)
            vestingAddress = vestingRegistry.getVestingAddr(tokenOwner, cliff, duration, vestingCreationType)
            print("Vesting: ", vestingAddress)

        print(tokenOwner)
        print(isTeam)
        print(amount)
        print(cliff)
        print(duration)
        print((duration - cliff) / FOUR_WEEKS + 1)
        
        if(not dryRun):
            SOVtoken.approve(vestingAddress, amount)
            vestingLogic = Contract.from_abi("VestingLogic", address=vestingAddress, abi=VestingLogic.abi, owner=conf.acct)
            vestingLogic.stakeTokens(amount)

        stakes = staking.getStakes(vestingAddress)
        print(stakes)

    print("=======================================")
    print("SOV amount:")
    print(totalAmount / 1e18)

    print("deployment cost:")
    print((balanceBefore - conf.acct.balance()) / 1e18)


def parseFile(fileName, multiplier):
    print(fileName)
    totalAmount = 0
    teamVestingList = []
    with open(fileName, 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            tokenOwner = row[3].replace(" ", "")
            amount = row[0].replace(",", "").replace(".", "")
            amount = int(amount) * multiplier
            cliff = int(row[5])
            duration = int(row[6])
            isTeam = True
            if (row[7] == "OwnerVesting"):
                isTeam = False
            totalAmount += amount

            teamVestingList.append([tokenOwner, amount, cliff, duration, isTeam])

            print("=======================================")
            print("'" + tokenOwner + "', ")
            print(amount)
    return {
               "totalAmount": totalAmount,
               "teamVestingList": teamVestingList,
            }
