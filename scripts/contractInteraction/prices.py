from brownie import *
from brownie.network.contract import InterfaceContainer
import json
import time;
import copy
from scripts.utils import * 
import scripts.contractInteraction.config as conf

def updatePriceFeedToRSKOracle():
    newPriceFeed = conf.acct.deploy(PriceFeedRSKOracle, conf.contracts['RSKOracle'])
    print("new price feed: ", newPriceFeed)
    feeds = Contract.from_abi("PriceFeeds", address= conf.contracts['PriceFeeds'], abi = PriceFeeds.abi, owner = conf.acct)
    feeds.setPriceFeed([conf.contracts['WRBTC']], [newPriceFeed.address])

def updatePriceFeedToMOCOracle():
    newPriceFeed = conf.acct.deploy(PriceFeedsMoC, conf.contracts['medianizer'], conf.contracts['RSKOracle'])
    print("new price feed: ", newPriceFeed)
    feeds = Contract.from_abi("PriceFeeds", address= conf.contracts['PriceFeeds'], abi = PriceFeeds.abi, owner = conf.acct)
    data = feeds.setPriceFeed.encode_input([conf.contracts['WRBTC']], [newPriceFeed.address])
    sendWithMultisig(conf.contracts['multisig'], feeds.address, data, conf.acct)


def readPrice(source, destination):
    feeds = Contract.from_abi("PriceFeeds", address= conf.contracts['PriceFeeds'], abi = PriceFeeds.abi, owner = conf.acct)
    rate = feeds.queryRate(source, destination)
    print('rate is ', rate)
    return rate[0]



def readSwapRate(source, destination):
    abiFile =  open('./scripts/contractInteraction/ABIs/SovrynSwapNetwork.json')
    abi = json.load(abiFile)
    swapNetwork = Contract.from_abi("SovrynSwapNetwork", address=conf.contracts['swapNetwork'], abi=abi, owner=conf.acct)
    path = swapNetwork.conversionPath(source,destination)
    #print("path:", path)
    expectedReturn = swapNetwork.getReturnByPath(path, 1e18)
    print('rate is ', expectedReturn)
    return expectedReturn[0]

def readConversionFee(converterAddress):
    abiFile =  open('./scripts/contractInteraction/ABIs/LiquidityPoolV1Converter.json')
    abi = json.load(abiFile)
    converter = Contract.from_abi("Converter", address=converterAddress, abi=abi, owner=conf.acct)
    fee = converter.conversionFee()
    print('fee is ', fee)


def readPriceFromOracle(oracleAddress):
    oracle = Contract.from_abi("Oracle", address=oracleAddress, abi=PriceFeedsMoC.abi, owner=conf.acct)
    price = oracle.latestAnswer()
    print('rate is ', price/1e18)

def readTargetWeights(converter, reserve):
    abiFile =  open('./scripts/contractInteraction/ABIs/LiquidityPoolV2Converter.json')
    abi = json.load(abiFile)
    converter = Contract.from_abi("LiquidityPoolV2Converter", address=converter, abi=abi, owner=conf.acct)
    res = converter.reserves(reserve).dict()
    print(res)
    print('target weight is ',res['weight'])

def readFromMedianizer():
    medianizer = Contract.from_abi("Medianizer", address=conf.contracts['medianizer'], abi=PriceFeedsMoCMockup.abi, owner=conf.acct)
    print(medianizer.peek())

def updateOracleAddress(newAddress):
    print("set oracle address to", newAddress)
    priceFeedsMoC = Contract.from_abi("PriceFeedsMoC", address = '0x066ba9453e230a260c2a753d9935d91187178C29', abi = PriceFeedsMoC.abi, owner = conf.acct)
    priceFeedsMoC.setMoCOracleAddress(newAddress)


def checkRates():
    print('reading price from WRBTC to DOC')
    readPrice(conf.contracts['WRBTC'], conf.contracts['DoC'])
    print('reading price from WRBTC to USDT')
    readPrice(conf.contracts['WRBTC'], conf.contracts['USDT'])
    print('reading price from WRBTC to BPRO')
    readPrice(conf.contracts['WRBTC'], conf.contracts['BPro'])
    print('read price from USDT to DOC')
    readPrice(conf.contracts['USDT'], conf.contracts['DoC'])

    print('read swap rate from WRBTC to DOC')
    readSwapRate(conf.contracts['WRBTC'], conf.contracts['DoC'])
    print('read swap rate from WRBTC to USDT')
    readSwapRate(conf.contracts['WRBTC'], conf.contracts['USDT'])
    print('read swap rate from WRBTC to BPRO')
    readSwapRate(conf.contracts['WRBTC'], conf.contracts['BPro'])
    print('read swap rate from USDT to DOC')
    readSwapRate(conf.contracts['USDT'], conf.contracts['DoC'])
    print('read swap rate from BPro to DOC')
    readSwapRate(conf.contracts['BPro'], conf.contracts['DoC'])
    print('read swap rate from BPro to USDT')
    readSwapRate(conf.contracts['BPro'], conf.contracts['USDT'])
    print('read swap rate from USDT to WRBTC')
    readSwapRate(conf.contracts['USDT'], conf.contracts['WRBTC'])
    print('read swap rate from DOC to WRBTC')
    readSwapRate(conf.contracts['DoC'], conf.contracts['WRBTC'])

    print("price from the USDT oracle on AMM:")
    readPriceFromOracle('0x78F0b35Edd78eD564830c45F4A22e4b553d7f042')

    readTargetWeights('0x133eBE9c8bA524C9B1B601E794dF527f390729bF', conf.contracts['USDT'])
    readTargetWeights('0x133eBE9c8bA524C9B1B601E794dF527f390729bF', conf.contracts['WRBTC'])


def readPriceFeedFor(tokenAddress):
    feeds = Contract.from_abi("PriceFeeds", address= conf.contracts['PriceFeeds'], abi = PriceFeeds.abi, owner = conf.acct)
    address = feeds.pricesFeeds(tokenAddress)
    print("price feed: "+address);
    return(address)

def deployOracleV1Pool(tokenAddress, oracleAddress):
    oracleV1PoolPriceFeed = conf.acct.deploy(PriceFeedV1PoolOracle, oracleAddress, conf.contracts['WRBTC'], conf.contracts['DoC'], tokenAddress)
    print("new oracle v1 pool price feed: ", oracleV1PoolPriceFeed.address)

    feeds = Contract.from_abi("PriceFeeds", address= conf.contracts['PriceFeeds'], abi = PriceFeeds.abi, owner = conf.acct)
    data = feeds.setPriceFeed.encode_input([tokenAddress], [oracleV1PoolPriceFeed.address])
    multisig = Contract.from_abi("MultiSig", address=conf.contracts['multisig'], abi=MultiSigWallet.abi, owner=conf.acct)
    tx = multisig.submitTransaction(feeds.address,0,data)
    txId = tx.events["Submission"]["transactionId"]
    print("txid: ",txId)

def readv1PoolOracleAddress(tokenAddress):
    feedAddress = readPriceFeedFor(tokenAddress)
    oracle = Contract.from_abi("PriceFeedV1PoolOracle", address= feedAddress, abi = PriceFeedV1PoolOracle.abi, owner = conf.acct)
    print("v1 pool oracle: ",oracle.v1PoolOracleAddress())