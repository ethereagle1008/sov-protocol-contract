from brownie import *
from brownie.network.contract import InterfaceContainer
import json
import time
import copy
from scripts.utils import * 
import scripts.contractInteraction.config as conf

def sendSOVFromVestingRegistry():
    amount = 307470805 * 10**14
    vestingRegistry = Contract.from_abi("VestingRegistry", address=conf.contracts['VestingRegistry'], abi=VestingRegistry.abi, owner=conf.acct)
    data = vestingRegistry.transferSOV.encode_input(conf.contracts['multisig'], amount)
    print(data)

    sendWithMultisig(conf.contracts['multisig'], vestingRegistry.address, data, conf.acct)

def vestingRegistryAddAdmin(admin, vestingRegistryAddress):
    multisig = Contract.from_abi("MultiSig", address=conf.contracts['multisig'], abi=MultiSigWallet.abi, owner=conf.acct)
    vestingRegistry = Contract.from_abi("VestingRegistry", address=vestingRegistryAddress, abi=VestingRegistry.abi, owner=conf.acct)
    data = vestingRegistry.addAdmin.encode_input(admin)
    sendWithMultisig(conf.contracts['multisig'], vestingRegistry.address, data, conf.acct)

def vestingRegistryProxyAddAdmin(admin):
    vestingRegistry = Contract.from_abi("VestingRegistryLogic", address=conf.contracts['VestingRegistryProxy'], abi=VestingRegistry.abi, owner=conf.acct)
    vestingRegistryAddAdmin(admin, vestingRegistry.address)    

def vestingRegistryRemoveAdmin(admin, vestingRegistryAddress):
    multisig = Contract.from_abi("MultiSig", address=conf.contracts['multisig'], abi=MultiSigWallet.abi, owner=conf.acct)
    vestingRegistry = Contract.from_abi("VestingRegistry", address=vestingRegistryAddress, abi=VestingRegistry.abi, owner=conf.acct)
    data = vestingRegistry.removeAdmin.encode_input(admin)
    sendWithMultisig(conf.contracts['multisig'], vestingRegistry.address, data, conf.acct)

def vestingRegistryProxyRemoveAdmin(admin):
    vestingRegistry = Contract.from_abi("VestingRegistryLogic", address=conf.contracts['VestingRegistryProxy'], abi=VestingRegistry.abi, owner=conf.acct)
    vestingRegistryRemoveAdmin(admin, vestingRegistry.address)    

def isVestingRegistryAdmin(admin, vestingRegistryAddress):
    vestingRegistry = Contract.from_abi("VestingRegistry", address=vestingRegistryAddress, abi=VestingRegistry.abi, owner=conf.acct)
    print(vestingRegistry.admins(admin))

def isVestingRegistryProxyAdmin(admin):
    vestingRegistry = Contract.from_abi("VestingRegistry", address=conf.contracts['VestingRegistryProxy'], abi=VestingRegistry.abi, owner=conf.acct)
    isAdmin = vestingRegistry.admins(admin)
    print(admin, 'is already' if isAdmin else 'is not yet admin - setting as', 'Vesting Registry Admin')
    return isAdmin

def readVestingContractForAddress(userAddress):
    vestingRegistry = Contract.from_abi("VestingRegistry", address=conf.contracts['VestingRegistry'], abi=VestingRegistry.abi, owner=conf.acct)
    address = vestingRegistry.getVesting(userAddress)
    if(address == '0x0000000000000000000000000000000000000000'):
        vestingRegistry = Contract.from_abi("VestingRegistry", address=conf.contracts['VestingRegistry2'], abi=VestingRegistry.abi, owner=conf.acct)
        address = vestingRegistry.getVesting(userAddress)

    print(address)

def readTeamVestingContractForAddress(userAddress):
    vestingRegistry = Contract.from_abi("VestingRegistry", address=conf.contracts['VestingRegistry'], abi=VestingRegistry.abi, owner=conf.acct)
    address = vestingRegistry.getTeamVesting(userAddress)
    print(address)

def readLMVestingContractForAddress(userAddress):
    vestingRegistry = Contract.from_abi("VestingRegistry", address=conf.contracts['VestingRegistry3'], abi=VestingRegistry.abi, owner=conf.acct)
    address = vestingRegistry.getVesting(userAddress)
    print(address)

def readAllVestingContractsForAddress(userAddress):
    vestingRegistry = Contract.from_abi("VestingRegistry", address=conf.contracts['VestingRegistryProxy'], abi=VestingRegistryLogic.abi, owner=conf.acct)
    addresses = vestingRegistry.getVestingsOf(userAddress)
    print(addresses)

def addVestingAdmin(admin):
    multisig = Contract.from_abi("MultiSig", address=conf.contracts['multisig'], abi=MultiSigWallet.abi, owner=conf.acct)
    vestingRegistry = Contract.from_abi("VestingRegistryLogic", address=conf.contracts['VestingRegistryProxy'], abi=VestingRegistryLogic.abi, owner=conf.acct)
    data = vestingRegistry.addAdmin.encode_input(admin)
    sendWithMultisig(conf.contracts['multisig'], vestingRegistry.address, data, conf.acct)

def removeVestingAdmin(admin):
    multisig = Contract.from_abi("MultiSig", address=conf.contracts['multisig'], abi=MultiSigWallet.abi, owner=conf.acct)
    vestingRegistry = Contract.from_abi("VestingRegistryLogic", address=conf.contracts['VestingRegistryProxy'], abi=VestingRegistryLogic.abi, owner=conf.acct)
    data = vestingRegistry.removeAdmin.encode_input(admin)
    sendWithMultisig(conf.contracts['multisig'], vestingRegistry.address, data, conf.acct)

def isVestingAdmin(admin):
    vestingRegistry = Contract.from_abi("VestingRegistryLogic", address=conf.contracts['VestingRegistryProxy'], abi=VestingRegistryLogic.abi, owner=conf.acct)
    print(vestingRegistry.admins(admin))

def readStakingKickOff():
    staking = Contract.from_abi("Staking", address=conf.contracts['Staking'], abi=Staking.abi, owner=conf.acct)
    print(staking.kickoffTS())

def stake80KTokens():
    # another address of the investor (addInvestorToBlacklist)
    tokenOwner = "0x21e1AaCb6aadF9c6F28896329EF9423aE5c67416"
    # 80K SOV
    amount = 80000 * 10**18

    vestingRegistry = Contract.from_abi("VestingRegistry", address=conf.contracts['VestingRegistry'], abi=VestingRegistry.abi, owner=conf.acct)
    vestingAddress = vestingRegistry.getVesting(tokenOwner)
    print("vestingAddress: " + vestingAddress)
    data = vestingRegistry.stakeTokens.encode_input(vestingAddress, amount)
    print(data)

    # multisig = Contract.from_abi("MultiSig", address=conf.contracts['multisig'], abi=MultiSigWallet.abi, owner=conf.acct)
    # tx = multisig.submitTransaction(vestingRegistry.address,0,data)
    # txId = tx.events["Submission"]["transactionId"]
    # print(txId)

def createVesting():
    DAY = 24 * 60 * 60
    FOUR_WEEKS = 4 * 7 * DAY

    tokenOwner = "0x21e1AaCb6aadF9c6F28896329EF9423aE5c67416"
    amount = 27186538 * 10**16
    # TODO cliff 4 weeks or less ?
    # cliff = CLIFF_DELAY + int(vesting[2]) * FOUR_WEEKS
    # duration = cliff + (int(vesting[3]) - 1) * FOUR_WEEKS

    # i think we don't need the delay anymore
    # because 2 weeks after TGE passed already
    # we keep the 4 weeks (26th of march first payout)

    cliff = 1 * FOUR_WEEKS
    duration = cliff + (10 - 1) * FOUR_WEEKS

    vestingRegistry = Contract.from_abi("VestingRegistry", address=conf.contracts['VestingRegistry'], abi=VestingRegistry.abi, owner=conf.acct)
    data = vestingRegistry.createVesting.encode_input(tokenOwner, amount, cliff, duration)
    print(data)

    sendWithMultisig(conf.contracts['multisig'], vestingRegistry.address, data, conf.acct)

def transferSOVtoVestingRegistry(vestingRegistryAddress, amount):

    SOVtoken = Contract.from_abi("SOV", address=conf.contracts['SOV'], abi=SOV.abi, owner=conf.acct)
    data = SOVtoken.transfer.encode_input(vestingRegistryAddress, amount)
    print(data)

    sendWithMultisig(conf.contracts['multisig'], SOVtoken.address, data, conf.acct)

# Check Block Number

def getBlockOfStakingInterval(timestamp):
    # Get the contract instance
    stakingRewards = Contract.from_abi("StakingRewards", address=conf.contracts['StakingRewardsProxy'], abi=StakingRewards.abi, owner=conf.acct)
    return stakingRewards.checkpointBlockDetails(timestamp)

# Read last staking timestamp

def readLockDate(timestamp):
    staking = Contract.from_abi("Staking", address=conf.contracts['Staking'], abi=Staking.abi, owner=conf.acct)
    return staking.timestampToLockDate(timestamp)

# Upgrade StakingRewards

def upgradeStakingRewards():
    print('Deploying account:', conf.acct.address)
    print("Upgrading staking rewards")

    # Deploy the staking logic contracts
    stakingRewards = conf.acct.deploy(StakingRewards)
    print("New staking rewards logic address:", stakingRewards.address)
    
    # Get the proxy contract instance
    stakingRewardsProxy = Contract.from_abi("StakingRewardsProxy", address=conf.contracts['StakingRewardsProxy'], abi=StakingRewardsProxy.abi, owner=conf.acct)

    # Register logic in Proxy
    data = stakingRewardsProxy.setImplementation.encode_input(stakingRewards.address)
    sendWithMultisig(conf.contracts['multisig'], conf.contracts['StakingRewardsProxy'], data, conf.acct)

# Set Average Block Time

def setAverageBlockTime(blockTime):
    # Get the contract instance
    stakingRewards = Contract.from_abi("StakingRewards", address=conf.contracts['StakingRewardsProxy'], abi=StakingRewards.abi, owner=conf.acct)

    # Set average block time
    data = stakingRewards.setAverageBlockTime.encode_input(blockTime)
    sendWithMultisig(conf.contracts['multisig'], conf.contracts['StakingRewardsProxy'], data, conf.acct)

# Set Block

def setBlockForStakingRewards():
    # Get the staking rewards proxy contract instance
    stakingRewardsProxy = Contract.from_abi("StakingRewards", address=conf.contracts['StakingRewardsProxy'], abi=StakingRewards.abi, owner=conf.acct)
    stakingRewardsProxy.setBlock()

# Set Historical Block

def setHistoricalBlockForStakingRewards(blockTime):
    # Get the staking rewards proxy contract instance
    stakingRewards = Contract.from_abi("StakingRewards", address=conf.contracts['StakingRewardsProxy'], abi=StakingRewards.abi, owner=conf.acct)
    stakingRewards.setHistoricalBlock(blockTime)

# Upgrade Staking

def upgradeStaking():
    print('Deploying account:', conf.acct.address)
    print("Upgrading staking")

    # Deploy the staking logic contracts
    stakingLogic = conf.acct.deploy(Staking)
    print("New staking logic address:", stakingLogic.address)
    
    # Get the proxy contract instance
    stakingProxy = Contract.from_abi("StakingProxy", address=conf.contracts['Staking'], abi=StakingProxy.abi, owner=conf.acct)

    # Register logic in Proxy
    data = stakingProxy.setImplementation.encode_input(stakingLogic.address)
    sendWithMultisig(conf.contracts['multisig'], conf.contracts['Staking'], data, conf.acct)

# deployStakingLogic

def deployStakingLogic():
    print('Deploying account:', conf.acct.address)
    print('Deploying Staking Logic')

    # Deploy the staking logic contracts
    stakingLogic = conf.acct.deploy(Staking)
    print("New staking logic address:", stakingLogic.address)

# Upgrade Vesting Registry

def upgradeVesting():
    print('Deploying account:', conf.acct.address)
    print("Upgrading vesting registry")

    # Deploy the staking logic contracts
    vestingRegistryLogic = conf.acct.deploy(VestingRegistryLogic)
    print("New vesting registry logic address:", vestingRegistryLogic.address)
    
    # Get the proxy contract instance
    vestingRegistryProxy = Contract.from_abi("VestingRegistryProxy", address=conf.contracts['VestingRegistryProxy'], abi=VestingRegistryProxy.abi, owner=conf.acct)

    # Register logic in Proxy
    data = vestingRegistryProxy.setImplementation.encode_input(vestingRegistryLogic.address)
    sendWithMultisig(conf.contracts['multisig'], conf.contracts['VestingRegistryProxy'], data, conf.acct)

# Set Vesting Registry Address for Staking

def updateVestingRegAddr():

    # Get the proxy contract instance
    stakingProxy = Contract.from_abi("Staking", address=conf.contracts['Staking'], abi=Staking.abi, owner=conf.acct)

    # Get the proxy contract instance
    vestingRegistryProxy = Contract.from_abi("VestingRegistryProxy", address=conf.contracts['VestingRegistryLogic'], abi=VestingRegistryProxy.abi, owner=conf.acct)

    #Send with Multisig
    data = stakingProxy.setVestingRegistry.encode_input(vestingRegistryProxy)
    print(data)
    sendWithMultisig(conf.contracts['multisig'], stakingProxy.address, data, conf.acct)

# Link Staking to StakingRewards, Vesting Registry and FeeSharing
def updateAddresses():

    # Get the proxy contract instance
    staking = Contract.from_abi("Staking", address=conf.contracts['Staking'], abi=Staking.abi, owner=conf.acct)
    print(staking)

    # Get the proxy contract instance
    vestingRegistryProxy = Contract.from_abi("VestingRegistryProxy", address=conf.contracts['VestingRegistryProxy'], abi=VestingRegistryProxy.abi, owner=conf.acct)
    print(vestingRegistryProxy)

    # Get the staking rewards proxy contract instance
    stakingRewardsProxy = Contract.from_abi("StakingRewardsProxy", address=conf.contracts['StakingRewardsProxy'], abi=StakingRewardsProxy.abi, owner=conf.acct)
    print(stakingRewardsProxy)

    # Get the fee sharing proxy contract instance
    feeSharingProxy = Contract.from_abi("FeeSharingProxy", address=conf.contracts['FeeSharingProxy'], abi=FeeSharingProxy.abi, owner=conf.acct)
    print(feeSharingProxy)

    #Link Staking with Vesting
    data = staking.setVestingRegistry.encode_input(vestingRegistryProxy)
    print(data)
    sendWithMultisig(conf.contracts['multisig'], staking.address, data, conf.acct)

    #Link Staking with Staking Rewards
    # data = staking.setStakingRewards.encode_input(stakingRewardsProxy)
    # print(data)
    # sendWithMultisig(conf.contracts['multisig'], staking.address, data, conf.acct)

    #Link Staking with Fee Sharing
    data = staking.setFeeSharing.encode_input(feeSharingProxy)
    print(data)
    sendWithMultisig(conf.contracts['multisig'], staking.address, data, conf.acct)

def getStakes(address):
    # Get the proxy contract instance
    stakingProxy = Contract.from_abi("Staking", address=conf.contracts['Staking'], abi=Staking.abi, owner=conf.acct)
    print(stakingProxy.getStakes(address))

def getStakingLogicAddess():
    # Get the proxy contract instance
    stakingProxy = Contract.from_abi("Staking", address=conf.contracts['Staking'], abi=StakingProxy.abi, owner=conf.acct)
    print("Staking contract logic address:", stakingProxy.getImplementation())

def stakeTokens(sovAmount, stakeTime, acctAddress, delegateeAddress):
    SOVtoken = Contract.from_abi("SOV", address=conf.contracts['SOV'], abi=SOV.abi, owner=acctAddress)
    staking = Contract.from_abi("Staking", address=conf.contracts['Staking'], abi=Staking.abi, owner=acctAddress)

    until = int(time.time()) + int(stakeTime)
    amount = int(sovAmount) * (10 ** 18)

    SOVtoken.approve(staking.address, amount)
    tx = staking.stake(amount, until, acctAddress, delegateeAddress)

def withdrawStakes(amount, until, receiver):
    # Get the proxy contract instance
    staking = Contract.from_abi("Staking", address=conf.contracts['Staking'], abi=Staking.abi, owner=conf.acct)
    staking.withdraw(amount, until, receiver)

def pauseOrUnpauseStaking(flag):
    # Get the proxy contract instance
    staking = Contract.from_abi("Staking", address=conf.contracts['Staking'], abi=Staking.abi, owner=conf.acct)
    data = staking.pauseUnpause.encode_input(flag)
    sendWithMultisig(conf.contracts['multisig'], staking.address, data, conf.acct)

def isStakingPaused():
    # Get the proxy contract instance
    staking = Contract.from_abi("Staking", address=conf.contracts['Staking'], abi=Staking.abi, owner=conf.acct)
    print("isStakingPaused:", staking.paused())

def freezeOrUnfreezeStakingWithdawal(flag):
    # Get the proxy contract instance
    staking = Contract.from_abi("Staking", address=conf.contracts['Staking'], abi=Staking.abi, owner=conf.acct)
    data = staking.freezeUnfreeze.encode_input(flag)
    sendWithMultisig(conf.contracts['multisig'], staking.address, data, conf.acct)

def addPauser(address):
    # Get the proxy contract instance
    staking = Contract.from_abi("Staking", address=conf.contracts['Staking'], abi=Staking.abi, owner=conf.acct)
    data = staking.addPauser.encode_input(address)
    sendWithMultisig(conf.contracts['multisig'], staking.address, data, conf.acct)

def removePauser(address):
    # Get the proxy contract instance
    staking = Contract.from_abi("Staking", address=conf.contracts['Staking'], abi=Staking.abi, owner=conf.acct)
    data = staking.removePauser.encode_input(address)
    sendWithMultisig(conf.contracts['multisig'], staking.address, data, conf.acct)
    
    
def readVestingData(vestingAddress):
    vesting = Contract.from_abi("VestingLogic", address=vestingAddress, abi=VestingLogic.abi, owner=conf.acct)
    print(vesting.startDate())
    print(vesting.endDate())
    print(vesting.cliff())
    print(vesting.duration())

def updateLockedSOV():
    lockedSOV = Contract.from_abi("LockedSOV", address=conf.contracts['LockedSOV'], abi=LockedSOV.abi, owner=conf.acct)

    DAY = 24 * 60 * 60
    FOUR_WEEKS = 4 * 7 * DAY

    cliff = int(lockedSOV.cliff() / FOUR_WEEKS)
    duration = int(lockedSOV.duration() / FOUR_WEEKS)

    print("cliff =", cliff)
    print("duration =", duration)
    print("multisig: isAdmin =", lockedSOV.adminStatus(conf.contracts['multisig']))

    data = lockedSOV.changeRegistryCliffAndDuration.encode_input(conf.contracts['VestingRegistryProxy'], cliff, duration)
    print(data)
    # sendWithMultisig(conf.contracts['multisig'], lockedSOV.address, data, conf.acct)

def governanceWithdrawVesting( vesting,  receiver):
    stakingProxy = Contract.from_abi("Staking", address=conf.contracts['Staking'], abi=Staking.abi, owner=conf.acct)
    data = stakingProxy.governanceWithdrawVesting.encode_input( vesting,  receiver)
    print(data)
    sendWithMultisig(conf.contracts['multisig'], conf.contracts['Staking'], data, conf.acct)

def transferStakingOwnershipToGovernance():
    print("Add staking admin for address: ", conf.contracts['TimelockAdmin'])
    staking = Contract.from_abi("Staking", address=conf.contracts['Staking'], abi=Staking.abi, owner=conf.acct)
    data = staking.addAdmin.encode_input(conf.contracts['TimelockAdmin'])
    sendWithMultisig(conf.contracts['multisig'], staking.address, data, conf.acct)

def transferStakingRewardsOwnershipToGovernance():
    print("Transferring StakingRewards ownership to: ", conf.contracts['TimelockAdmin'])
    stakingRewards = Contract.from_abi("StakingRewards", address=conf.contracts['StakingRewardsProxy'], abi=StakingRewards.abi, owner=conf.acct)
    data = stakingRewards.transferOwnership.encode_input(conf.contracts['TimelockAdmin'])
    sendWithMultisig(conf.contracts['multisig'], stakingRewards.address, data, conf.acct)

def transferVestingRegistryOwnershipToGovernance():
    # add governor admin as admin
    print("Add Vesting Registry admin for address: ", conf.contracts['TimelockAdmin'])
    vestingRegistry = Contract.from_abi("VestingRegistry", address=conf.contracts['VestingRegistryProxy'], abi=VestingRegistry.abi, owner=conf.acct)
    data = vestingRegistry.addAdmin.encode_input(conf.contracts['TimelockAdmin'])
    sendWithMultisig(conf.contracts['multisig'], vestingRegistry.address, data, conf.acct)

    '''
    # add Exchequer admin as admin
    print("Add Vesting Registry admin for multisig: ", conf.contracts['multisig'])
    data = vestingRegistry.addAdmin.encode_input(conf.contracts['multisig'])
    sendWithMultisig(conf.contracts['multisig'], vestingRegistry.address, data, conf.acct)
    '''

def getStakedBalance(account):
    stakingProxy = Contract.from_abi("Staking", address=conf.contracts['Staking'], abi=Staking.abi, owner=conf.acct)
    bal = stakingProxy.balanceOf(account)
    print(bal)
    return bal

def stopStakingRewards():
    print("Stop Staking Rewards Program from the stop() func call tx block")
    stakingRewards = Contract.from_abi("StakingRewards", address=conf.contracts['StakingRewardsProxy'], abi=StakingRewards.abi, owner=conf.acct)
    data = stakingRewards.stop.encode_input()
    sendWithMultisig(conf.contracts['multisig'], stakingRewards.address, data, conf.acct)
