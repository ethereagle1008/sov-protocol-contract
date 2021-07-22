
from brownie import *
from brownie.network.contract import InterfaceContainer
import json
import time;
import copy
from scripts.utils import * 
import scripts.contractInteraction.config as conf

def governorAcceptAdmin(type):
    governor = Contract.from_abi("GovernorAlpha", address=conf.contracts[type], abi=GovernorAlpha.abi, owner=conf.acct)
    data = governor.__acceptAdmin.encode_input()
    sendWithMultisig(conf.contracts['multisig'], governor.address, data, conf.acct)

def queueProposal(id):
    governor = Contract.from_abi("GovernorAlpha", address=conf.contracts['GovernorOwner'], abi=GovernorAlpha.abi, owner=conf.acct)
    tx = governor.queue(id)
    tx.info()

def executeProposal(id):
    governor = Contract.from_abi("GovernorAlpha", address=conf.contracts['GovernorOwner'], abi=GovernorAlpha.abi, owner=conf.acct)
    tx = governor.execute(id)
    tx.info()